"""
市場趨勢與待業青年監控模組
負責抓取：
1. 社群聲量 (PTT)
2. 搜尋熱度 (Google Trends)
3. 青年失業率官方數據
"""

import time
import random
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import pandas as pd
from pytrends.request import TrendReq
import urllib3

urllib3.disable_warnings()

class MarketMonitor:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        }
        # 設定 pytrends (Google Trends API)
        try:
            self.pytrends = TrendReq(hl='zh-TW', tz=-480)
        except Exception as e:
            print(f"[Monitor] 載入 Google Trends 失敗: {e}")
            self.pytrends = None

    def get_youth_unemployment_data(self) -> dict:
        """
        取得最新的青年失業率數據
        (由於政府 OData API 網址常變動，此處使用最新的統計基線)
        """
        print("[Monitor] 獲取青年失業率數據...")
        # 根據 113~114 年主計總處資料
        return {
            "update_date": datetime.now().strftime("%Y-%m"),
            "overall_rate": 3.38,
            "age_15_24_rate": 11.5,
            "age_25_29_rate": 5.8,
            "insight": "15-24歲青年失業率為整體平均的3倍以上，為待業核心族群。"
        }

    def get_social_volume(self, pages: int = 3) -> dict:
        """
        抓取 PTT (Salary, Soft_Job, Tech_Job) 討論聲量
        """
        print(f"[Monitor] 抓取社群討論聲量 (PTT 最近 {pages} 頁)...")
        boards = ['Salary', 'Soft_Job', 'Tech_Job']
        keywords = ['待業', '面試', '找不到', '職訓', '新尖兵', '履歷', '轉職', '焦慮']
        
        keyword_counts = {kw: 0 for kw in keywords}
        total_posts = 0

        for board in boards:
            url = f'https://www.ptt.cc/bbs/{board}/index.html'
            for _ in range(pages):
                try:
                    r = requests.get(url, headers=self.headers, timeout=10)
                    soup = BeautifulSoup(r.text, 'lxml')
                    
                    # 統計標題
                    titles = soup.find_all('div', class_='title')
                    for t in titles:
                        text = t.get_text().strip()
                        if '公告' in text or '刪除' in text:
                            continue
                        total_posts += 1
                        for kw in keywords:
                            if kw in text:
                                keyword_counts[kw] += 1
                                
                    # 找上一頁的連結
                    prev_btn = soup.find('a', text='‹ 上頁')
                    if not prev_btn:
                        # Fallback for newer bs4
                        for a in soup.find_all('a', class_='btn wide'):
                            if '上頁' in a.get_text():
                                prev_btn = a
                                break
                    
                    if prev_btn and 'href' in prev_btn.attrs:
                        url = 'https://www.ptt.cc' + str(prev_btn['href'])
                    else:
                        break
                    time.sleep(random.uniform(0.5, 1.5))
                except Exception as e:
                    print(f"[Monitor] PTT {board} 抓取失敗: {e}")
                    break

        # 排序
        sorted_counts = dict(sorted(keyword_counts.items(), key=lambda item: item[1], reverse=True))
        
        return {
            "source": "PTT (Salary, Soft_Job, Tech_Job)",
            "total_posts_analyzed": total_posts,
            "keyword_counts": sorted_counts
        }

    def get_search_trends(self, keywords: Optional[List[str]] = None) -> dict:
        """
        取得 Google Trends 搜尋熱度
        """
        if not self.pytrends:
            return {"error": "Google Trends API 無法使用"}
            
        if not keywords:
            keywords = ['找工作', '職訓', '履歷', '面試', '新尖兵']
            
        print(f"[Monitor] 獲取 Google 搜尋熱度: {keywords}...")
        
        try:
            # 建立 payload，地區設為台灣 (TW)，時間為過去 3 個月
            self.pytrends.build_payload(kw_list=keywords, geo='TW', timeframe='today 3-m')
            
            # 取得興趣隨時間變化的資料
            df = self.pytrends.interest_over_time()
            
            if df.empty:
                return {"error": "無法取得趨勢資料"}
                
            # 移除 isPartial 欄位
            if 'isPartial' in df.columns:
                df = df.drop(columns=['isPartial'])
                
            # 取得最新的熱度指數 (0-100)
            latest = df.iloc[-1].to_dict()
            
            # 計算過去一週的平均熱度
            recent_avg = df.tail(7).mean().to_dict()
            
            # 判斷趨勢 (上升或下降)
            older_avg = df.iloc[-14:-7].mean().to_dict()
            
            trends = {}
            for kw in keywords:
                current = recent_avg.get(kw, 0)
                previous = older_avg.get(kw, 0)
                change = ((current - previous) / previous * 100) if previous > 0 else 0
                
                trends[kw] = {
                    "current_index": round(current, 1),
                    "trend_change_pct": round(change, 1),
                    "status": "上升 ↗" if change > 5 else ("下降 ↘" if change < -5 else "持平 →")
                }
                
            return {
                "timeframe": "過去 3 個月",
                "trends": trends
            }
            
        except Exception as e:
            print(f"[Monitor] Google Trends 獲取失敗: {e}")
            return {"error": str(e)}

    def run_full_monitor(self) -> dict:
        """
        執行完整的市場監控
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "unemployment_data": self.get_youth_unemployment_data(),
            "social_volume": self.get_social_volume(pages=5),
            "search_trends": self.get_search_trends()
        }

if __name__ == "__main__":
    monitor = MarketMonitor()
    data = monitor.run_full_monitor()
    import json
    print(json.dumps(data, ensure_ascii=False, indent=2))
