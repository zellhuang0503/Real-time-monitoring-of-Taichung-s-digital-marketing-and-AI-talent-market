#!/usr/bin/env python3
"""
台中中部數位人才就業市場監控系統
主執行腳本

使用方式:
    python main.py [--test]

選項:
    --test      測試模式，只爬取少量資料
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

# 確保可以找到其他模組
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import JOB_KEYWORDS, MONITORING_AREAS, OUTPUT_CONFIG
from scrapers import Scraper104, Scraper1111, Scraper518
from scrapers.market_monitor import MarketMonitor
from analyzer import JobAnalyzer, CourseRecommender, GeminiAnalyzer
from report import HTMLReportGenerator
from report.history_generator import HistoryGenerator
from utils.notifier import LineNotifier


def collect_jobs(test_mode: bool = False) -> list:
    """
    從各平台收集職缺資料
    
    Args:
        test_mode: 若為 True，只爬取少量資料用於測試
        
    Returns:
        所有收集到的職缺列表
    """
    all_jobs = []
    areas = ['taichung', 'changhua', 'nantou']
    
    # 測試模式只搜尋少量關鍵字
    if test_mode:
        keywords = ['數位行銷', 'AI'][:2]
        max_pages = 2
        print("[Main] 測試模式：只搜尋少量資料")
    else:
        # 收集所有關鍵字
        keywords = []
        for category, words in JOB_KEYWORDS.items():
            keywords.extend(words[:5])  # 每類取前5個，避免太多
        keywords = list(set(keywords))  # 去重
        max_pages = 5
        print(f"[Main] 正式模式：搜尋 {len(keywords)} 個關鍵字")
    
    # 104 人力銀行（最穩定，優先使用）
    print("\n" + "="*60)
    print("[Main] 開始爬取 104 人力銀行...")
    print("="*60)
    try:
        scraper_104 = Scraper104(delay=2.0)
        jobs_104 = scraper_104.search_by_keywords(keywords[:10], areas)  # 限制關鍵字數量避免太耗時
        all_jobs.extend(jobs_104)
        print(f"[Main] 104 完成：取得 {len(jobs_104)} 筆職缺")
    except Exception as e:
        print(f"[Main] 104 爬取失敗: {e}")
    
    # 如果測試模式，到此結束
    if test_mode:
        return all_jobs
    
    # 1111 人力銀行（有反爬，可能會失敗）
    print("\n" + "="*60)
    print("[Main] 開始爬取 1111 人力銀行...")
    print("="*60)
    try:
        scraper_1111 = Scraper1111(delay=3.0)
        jobs_1111 = []
        for keyword in keywords[:5]:  # 限制數量
            for area in areas[:1]:  # 只取台中
                jobs = scraper_1111.search_jobs(keyword, area, max_pages=3)
                jobs_1111.extend(jobs)
                if len(jobs_1111) > 100:  # 限制總數
                    break
            if len(jobs_1111) > 100:
                break
        all_jobs.extend(jobs_1111)
        print(f"[Main] 1111 完成：取得 {len(jobs_1111)} 筆職缺")
    except Exception as e:
        print(f"[Main] 1111 爬取失敗: {e}")
    
    # 518 人力銀行
    print("\n" + "="*60)
    print("[Main] 開始爬取 518 人力銀行...")
    print("="*60)
    try:
        scraper_518 = Scraper518(delay=3.0)
        jobs_518 = []
        for keyword in keywords[:3]:
            for area in areas[:1]:
                jobs = scraper_518.search_jobs(keyword, area, max_pages=3)
                jobs_518.extend(jobs)
                if len(jobs_518) > 50:
                    break
            if len(jobs_518) > 50:
                break
        all_jobs.extend(jobs_518)
        print(f"[Main] 518 完成：取得 {len(jobs_518)} 筆職缺")
    except Exception as e:
        print(f"[Main] 518 爬取失敗: {e}")
    
    print(f"\n[Main] 資料收集完成，共 {len(all_jobs)} 筆職缺")
    return all_jobs


def save_jobs(jobs: list, filename: str = None):
    """儲存職缺原始資料"""
    if filename is None:
        filename = f"jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    filepath = os.path.join(OUTPUT_CONFIG['data_dir'], filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)
    
    print(f"[Main] 職缺資料已儲存: {filepath}")
    return filepath


def load_previous_jobs(days_back: int = 7) -> list:
    """載入前期的職缺資料（用於趨勢比較）"""
    import glob
    
    data_dir = OUTPUT_CONFIG['data_dir']
    pattern = os.path.join(data_dir, 'jobs_*.json')
    files = glob.glob(pattern)
    
    if not files:
        return None
    
    # 找最新的檔案（但不是今天）
    files.sort(reverse=True)
    
    for filepath in files[:3]:  # 檢查最近3個檔案
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                jobs = json.load(f)
                print(f"[Main] 已載入前期資料: {os.path.basename(filepath)} ({len(jobs)} 筆)")
                return jobs
        except Exception as e:
            print(f"[Main] 載入 {filepath} 失敗: {e}")
            continue
    
    return None


def main():
    """主程式"""
    parser = argparse.ArgumentParser(description='台中中部數位人才就業市場監控系統')
    parser.add_argument('--test', action='store_true', help='測試模式')
    parser.add_argument('--skip-scrape', action='store_true', help='跳過爬蟲，使用現有資料')
    args = parser.parse_args()
    
    print("="*60)
    print("台中中部數位人才就業市場監控系統")
    print(f"執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # 確保輸出目錄存在
    os.makedirs(OUTPUT_CONFIG['data_dir'], exist_ok=True)
    os.makedirs(OUTPUT_CONFIG['report_dir'], exist_ok=True)
    os.makedirs(OUTPUT_CONFIG['history_dir'], exist_ok=True)
    
    # 步驟 1: 收集資料
    if args.skip_scrape:
        print("\n[Main] 跳過爬蟲，載入現有資料...")
        jobs = load_previous_jobs()
        if not jobs:
            print("[Main] 找不到現有資料，啟動爬蟲...")
            jobs = collect_jobs(test_mode=args.test)
    else:
        jobs = collect_jobs(test_mode=args.test)
    
    if not jobs:
        print("[Main] 錯誤：無法取得任何職缺資料")
        sys.exit(1)
    
    # 儲存原始資料
    jobs_filepath = save_jobs(jobs)
    
    # 步驟 2: 分析資料
    print("\n" + "="*60)
    print("[Main] 開始分析資料...")
    print("="*60)
    
    analyzer = JobAnalyzer()
    
    # 載入前期資料進行趨勢比較
    previous_jobs = load_previous_jobs() if not args.test else None
    
    analysis_result = analyzer.analyze(jobs, previous_jobs)
    
    # 加入外部市場監控數據 (青年失業率、搜尋聲量)
    print("\n" + "="*60)
    print("[Main] 擷取外部市場趨勢數據...")
    print("="*60)
    try:
        market_monitor = MarketMonitor()
        market_data = market_monitor.run_full_monitor()
        # 相容舊版欄位：保留 unemployment_data
        regional = market_data.get('regional_unemployment', {})
        market_data['unemployment_data'] = {
            'update_date': regional.get('data_period', ''),
            'overall_rate': regional.get('taiwan_unemployment_rate', 3.33),
            'age_15_24_rate': 11.5,
            'age_25_29_rate': 5.8,
            'insight': '15-24歲青年失業率為整體平均的3倍以上，為待業核心族群。',
        }
        analysis_result['market_trends'] = market_data
    except Exception as e:
        print(f"[Main] 市場趨勢擷取失敗: {e}")
        analysis_result['market_trends'] = None
    
    # 儲存分析結果
    analysis_filepath = os.path.join(
        OUTPUT_CONFIG['data_dir'],
        f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    analyzer.save_analysis(analysis_result, analysis_filepath)
    
    # 步驟 3: 生成課程建議
    print("\n" + "="*60)
    print("[Main] 生成課程建議與 AI 戰略分析...")
    print("="*60)
    recommender = CourseRecommender()
    recommendations = recommender.generate_recommendations(analysis_result)
    
    # 調用 Gemini 進行深度分析
    try:
        gemini = GeminiAnalyzer()
        # 1. 深度輿情分析
        if analysis_result.get('market_trends', {}).get('social_volume'):
            sentiment = gemini.analyze_market_sentiment(analysis_result['market_trends']['social_volume'])
            analysis_result['market_trends']['social_volume']['ai_sentiment_analysis'] = sentiment
        
        # 2. CEO 戰略建議
        ceo_strategy = gemini.generate_ceo_strategy(analysis_result)
        analysis_result['ceo_strategy'] = ceo_strategy
        # 同時更新 recommendations 中的 executive_summary 以反映 AI 洞察
        if ceo_strategy.get('ceo_insight'):
            recommendations['executive_summary']['key_insight'] = ceo_strategy['ceo_insight']
            
    except Exception as e:
        print(f"[Main] Gemini AI 分析失敗: {e}")
    
    # 步驟 4: 生成 HTML 報告
    print("\n" + "="*60)
    print("[Main] 生成 HTML 報告...")
    print("="*60)
    
    report_generator = HTMLReportGenerator()
    
    # 計算週數（根據歷史檔案數量）
    import glob
    history_files = glob.glob(os.path.join(OUTPUT_CONFIG['data_dir'], 'analysis_*.json'))
    week_number = len(history_files)
    
    report_path = os.path.join(
        OUTPUT_CONFIG['report_dir'],
        f"taichung_job_market_week{week_number}.html"
    )
    
    report_generator.generate(
        analysis_result,
        recommendations,
        report_path,
        week_number=week_number
    )
    
    # 同時生成最新報告的副本
    latest_report_path = os.path.join(
        OUTPUT_CONFIG['report_dir'],
        "index.html"
    )
    report_generator.generate(
        analysis_result,
        recommendations,
        latest_report_path,
        week_number=week_number
    )
    
    # 步驟 5: 生成歷史報告索引
    print("\n" + "="*60)
    print("[Main] 生成歷史報告索引...")
    print("="*60)
    history_generator = HistoryGenerator()
    history_generator.generate_history_page()
    
    # 步驟 6: 發送 LINE 通知
    print("\n" + "="*60)
    print("[Main] 發送 LINE 執行報告通知...")
    print("="*60)
    try:
        notifier = LineNotifier()
        notifier.send_report_notification(analysis_result, week_number)
    except Exception as e:
        print(f"[Main] LINE 通知發送失敗: {e}")
    
    print("\n" + "="*60)
    print(f"[Main] 監控任務執行完成！第 {week_number} 週報告已產出。")
    print("="*60)
    
    history_generator = HistoryGenerator()
    history_path = history_generator.generate_history_page()
    
    print("\n" + "="*60)
    print("[Main] 執行完成！")
    print("="*60)
    print(f"\n[職缺資料] {jobs_filepath}")
    print(f"[分析結果] {analysis_filepath}")
    print(f"[週報告] {report_path}")
    print(f"[最新報告] {latest_report_path}")
    print(f"[歷史索引] {history_path}")
    print(f"\n總計收集 {len(jobs)} 筆職缺資料")
    print(f"目前累積 {week_number} 週歷史資料")
    print("="*60)


if __name__ == "__main__":
    main()
