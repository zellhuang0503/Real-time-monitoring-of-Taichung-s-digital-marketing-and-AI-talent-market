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
        # 收集所有關鍵字（每類前5個）。
        # 用 dict.fromkeys 去重以保持「固定順序」——之前用 set 會因為
        # Python 雜湊隨機化導致每次執行搜尋到不同的關鍵字子集，
        # 使每天監控的市場切面不一致。
        keywords = []
        for category, words in JOB_KEYWORDS.items():
            keywords.extend(words[:5])
        keywords = list(dict.fromkeys(keywords))
        max_pages = 5
        print(f"[Main] 正式模式：搜尋 {len(keywords)} 個關鍵字（固定清單，全數搜尋）")

    # 104 人力銀行（最穩定，優先使用）
    print("\n" + "="*60)
    print("[Main] 開始爬取 104 人力銀行...")
    print("="*60)
    try:
        scraper_104 = Scraper104(delay=2.0)
        # 搜尋全部關鍵字（列表階段不抓詳細頁），去重後再統一補抓詳細工作條件
        jobs_104 = scraper_104.search_by_keywords(keywords, areas, max_pages=max_pages)
        # 補抓詳細頁：擅長工具、完整描述、準確經驗/學歷（真實工作條件的來源）
        detail_cache = os.path.join(OUTPUT_CONFIG['data_dir'], 'job_details_cache_104.json')
        scraper_104.enrich_jobs_with_details(jobs_104, cache_path=detail_cache)
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


def load_previous_jobs(exclude_files: set = None):
    """
    載入最近一次的職缺資料檔（用於趨勢比較）。

    注意：呼叫時機必須在「儲存本次資料之前」，或用 exclude_files 排除本次檔案。
    修正前的版本在 save_jobs() 之後呼叫，永遠載到剛存的檔案，
    導致趨勢比較「拿本期跟本期比」，變化永遠為零。

    Returns:
        (jobs, filepath) 或 None
    """
    import glob

    data_dir = OUTPUT_CONFIG['data_dir']
    # 只比對正式資料檔（jobs_YYYYMMDD_*.json），排除 jobs_test_* 測試檔
    files = sorted(glob.glob(os.path.join(data_dir, 'jobs_[0-9]*.json')), reverse=True)
    exclude = {os.path.abspath(p) for p in (exclude_files or set()) if p}

    for filepath in files:
        if os.path.abspath(filepath) in exclude:
            continue
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                jobs = json.load(f)
            print(f"[Main] 已載入前期資料: {os.path.basename(filepath)} ({len(jobs)} 筆)")
            return jobs, filepath
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
    current_source_file = None  # --skip-scrape 時記錄本次資料來源檔，避免趨勢比較拿同一檔比
    if args.skip_scrape:
        print("\n[Main] 跳過爬蟲，載入現有資料...")
        loaded = load_previous_jobs()
        if loaded:
            jobs, current_source_file = loaded
        else:
            print("[Main] 找不到現有資料，啟動爬蟲...")
            jobs = collect_jobs(test_mode=args.test)
    else:
        jobs = collect_jobs(test_mode=args.test)

    if not jobs:
        print("[Main] 錯誤：無法取得任何職缺資料")
        sys.exit(1)

    # 載入前期資料進行趨勢比較——必須在 save_jobs() 之前載入，
    # 並排除 --skip-scrape 時作為本期資料的檔案
    previous_jobs = None
    if not args.test:
        prev = load_previous_jobs(
            exclude_files={current_source_file} if current_source_file else None
        )
        previous_jobs = prev[0] if prev else None

    # 儲存原始資料（測試模式用 jobs_test_ 前綴，避免混入正式資料的趨勢比較池）
    if args.test:
        jobs_filepath = save_jobs(jobs, filename=f"jobs_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    else:
        jobs_filepath = save_jobs(jobs)

    # 步驟 2: 分析資料
    print("\n" + "="*60)
    print("[Main] 開始分析資料...")
    print("="*60)

    analyzer = JobAnalyzer()
    analysis_result = analyzer.analyze(jobs, previous_jobs)
    
    # 加入外部市場監控數據 (青年失業率、搜尋聲量)
    print("\n" + "="*60)
    print("[Main] 擷取外部市場趨勢數據...")
    print("="*60)
    try:
        market_monitor = MarketMonitor()
        market_data = market_monitor.run_full_monitor()
        # 相容舊版欄位：保留 unemployment_data。
        # 年齡別失業率來自 market_monitor 的官方數據（含資料期間標示），
        # 不再使用無出處的寫死數字。
        regional = market_data.get('regional_unemployment', {})
        youth = market_data.get('youth_stats', {})
        market_data['unemployment_data'] = {
            'update_date': youth.get('period', regional.get('data_period', '')),
            'overall_rate': youth.get('overall_rate') or regional.get('taiwan_unemployment_rate'),
            'age_15_24_rate': youth.get('age_15_24_rate'),
            'age_25_29_rate': youth.get('age_25_29_rate'),
            'insight': youth.get('insight', ''),
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
        # 只有在 AI 分析真的成功時才覆寫 executive_summary，
        # 避免把「分析不可用」的訊息當成洞察放進摘要
        if ceo_strategy.get('ceo_insight') and not ceo_strategy.get('unavailable'):
            recommendations['executive_summary']['key_insight'] = ceo_strategy['ceo_insight']
            
    except Exception as e:
        print(f"[Main] Gemini AI 分析失敗: {e}")
    
    # 步驟 4: 生成 HTML 報告
    print("\n" + "="*60)
    print("[Main] 生成 HTML 報告...")
    print("="*60)
    
    report_generator = HTMLReportGenerator()
    
    # 計算週數（根據現有週報告的最大週數 + 1）
    import glob
    import re
    week_files = glob.glob(os.path.join(OUTPUT_CONFIG['report_dir'], 'taichung_job_market_week*.html'))
    existing_weeks = []
    for wf in week_files:
        m = re.search(r'week(\d+)\.html', wf)
        if m:
            existing_weeks.append(int(m.group(1)))
    week_number = max(existing_weeks) + 1 if existing_weeks else 1
    
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
    history_path = history_generator.generate_history_page()

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
