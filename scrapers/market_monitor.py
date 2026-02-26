"""
市場趨勢與待業青年監控模組
負責抓取：
1. 主計總處分區失業率 + 失業人數 (DGBAS table32)
2. PTT 社群聲量
3. Google Trends 搜尋熱度
"""

import io
import time
import random
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Optional, List, Dict, Any

try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

try:
    from pytrends.request import TrendReq
    HAS_PYTRENDS = True
except ImportError:
    HAS_PYTRENDS = False

import urllib3
urllib3.disable_warnings()


class MarketMonitor:
    def __init__(self):
        self.headers = {
            'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                           'AppleWebKit/537.36 (KHTML, like Gecko) '
                           'Chrome/122.0.0.0 Safari/537.36'),
        }
        self.pytrends = None
        if HAS_PYTRENDS:
            try:
                self.pytrends = TrendReq(hl='zh-TW', tz=-480)
            except Exception as e:
                print(f"[Monitor] Google Trends 初始化失敗: {e}")

    # ------------------------------------------------------------------ #
    # 1. 主計總處 分區失業率 + 失業人數
    # ------------------------------------------------------------------ #
    def get_regional_unemployment(self) -> dict:
        """
        從主計總處 stat.gov.tw 最新月份人力資源調查報告
        抓取 table32 = 各縣市 15 歲以上失業率與失業人數（千人）
        並依黃老闆需求分為：北部、中部、雲嘉、南部（含高雄）、東部
        """
        print("[Monitor] 抓取主計總處分區失業統計...")

        # Step 1: 取得最新報告頁面，找 table32 的下載網址
        table32_url = self._find_latest_table32_url()

        # Step 2: 下載並解析 XLSX
        raw_data = self._parse_table32(table32_url) if table32_url else []

        if not raw_data:
            # Fallback: 使用 114年上半年靜態數據 (2025/1-6)
            raw_data = self._static_114H1_data()

        # Step 3: 整理成分區格式
        return self._organize_by_region(raw_data)

    def _find_latest_table32_url(self) -> Optional[str]:
        """從 stat.gov.tw 找最新月份報告的 table32 下載連結"""
        try:
            # 找最新的人力資源調查統計頁面
            search_url = 'https://www.stat.gov.tw/cl.aspx?n=4003'
            r = requests.get(search_url, headers=self.headers,
                             verify=False, timeout=10)
            soup = BeautifulSoup(r.content, 'lxml')

            # 找第一個「人力資源調查統計」連結
            for a in soup.find_all('a', href=True):
                href = a['href']
                text = a.get_text()
                if 'News_Content' in href and '人力資源' in text:
                    detail_url = 'https://www.stat.gov.tw/' + href.lstrip('/')
                    # 從詳細頁面找 table32
                    r2 = requests.get(detail_url, headers=self.headers,
                                      verify=False, timeout=10)
                    soup2 = BeautifulSoup(r2.content, 'lxml')
                    for a2 in soup2.find_all('a', href=True):
                        if 'table32.xlsx' in a2['href']:
                            return a2['href']
            return None
        except Exception as e:
            print(f"[Monitor] 找最新報告頁面失敗: {e}")
            return None

    def _parse_table32(self, url: str) -> list:
        """下載並解析 XLSX 中的縣市失業率資料"""
        if not HAS_OPENPYXL:
            print("[Monitor] 未安裝 openpyxl，使用靜態數據")
            return []
        try:
            r = requests.get(url, headers=self.headers,
                             verify=False, timeout=20)
            wb = openpyxl.load_workbook(io.BytesIO(r.content), data_only=True)
            ws = wb.active
            rows = list(ws.iter_rows(values_only=True))

            data = []
            for row in rows:
                name_raw = row[0]
                unemployed = row[4]   # 失業者（千人）
                unemp_rate = row[7]   # 失業率（%）
                if (name_raw and isinstance(name_raw, str)
                        and isinstance(unemp_rate, (int, float))
                        and isinstance(unemployed, (int, float))):
                    name = name_raw.strip()
                    data.append({
                        'name': name,
                        'unemployed_k': round(float(unemployed), 1),
                        'unemployed_persons': int(float(unemployed) * 1000),
                        'unemployment_rate': round(float(unemp_rate), 2),
                    })
            return data
        except Exception as e:
            print(f"[Monitor] 解析 table32 失敗: {e}")
            return []

    def _static_114H1_data(self) -> list:
        """114年上半年（2025年1-6月）靜態數據備援"""
        return [
            # (地區名稱, 失業者千人, 失業率%)
            ('臺灣地區',        400, 3.33),
            ('北部地區',        184, 3.30),
            ('新北市',           71, 3.30),
            ('臺北市',           40, 3.40),
            ('桃園市',           40, 3.30),
            ('基隆市',            6, 3.50),
            ('新竹市',            8, 3.30),
            ('宜蘭縣',            8, 3.20),
            ('新竹縣',           10, 3.30),
            ('中部地區',        100, 3.40),
            ('臺中市',           51, 3.40),
            ('苗栗縣',            9, 3.30),
            ('彰化縣',           21, 3.30),
            ('南投縣',            8, 3.30),
            ('雲林縣',           11, 3.30),
            ('南部地區',        107, 3.30),
            ('臺南市',           34, 3.40),
            ('高雄市',           45, 3.20),
            ('嘉義市',            4, 3.20),
            ('嘉義縣',            8, 3.20),
            ('屏東縣',           14, 3.30),
            ('澎湖縣',            2, 3.30),
            ('東部地區',          9, 3.20),
            ('臺東縣',            3, 3.30),
            ('花蓮縣',            5, 3.20),
        ]

    def _organize_by_region(self, raw_data: list) -> dict:
        """
        將縣市資料整理為黃老闆需要的分區格式：
        北部 / 中部 / 雲嘉（雲林+嘉義市+嘉義縣）/ 南部 / 東部
        並加上「年輕人數推估」= 失業人數 × 15-29歲失業者占比（約25%）
        """
        # 建立縣市名稱查找表
        lookup: Dict[str, Dict] = {}
        for item in raw_data:
            if isinstance(item, tuple):
                item = {
                    'name': item[0],
                    'unemployed_k': round(item[1] / 1000, 1) if item[1] >= 10 else item[1],
                    'unemployed_persons': int(item[1]) * (1 if item[1] >= 10 else 1000),
                    'unemployment_rate': item[2],
                }
                # fix units
                if item['unemployed_persons'] < 100:
                    item['unemployed_persons'] *= 1000
                    item['unemployed_k'] = round(item['unemployed_persons'] / 1000, 1)
            name = item['name'].strip().replace('\u3000', '')
            lookup[name] = item

        # 分區定義
        region_map = {
            '北部': ['臺北市', '新北市', '桃園市', '基隆市', '新竹市', '新竹縣', '宜蘭縣'],
            '中部（含苗栗）': ['苗栗縣', '臺中市', '彰化縣', '南投縣'],
            '雲嘉（雲林+嘉義）': ['雲林縣', '嘉義市', '嘉義縣'],
            '南部（含高雄）': ['臺南市', '高雄市', '屏東縣', '澎湖縣'],
            '東部': ['花蓮縣', '臺東縣'],
        }

        # 15-29歲在失業者中的估計比例（依勞動部 113年調查）
        YOUTH_RATIO = 0.248  # 約24.8%

        regions = {}
        for region_name, counties in region_map.items():
            total_unemployed = 0
            county_details = []
            for county in counties:
                # 模糊比對
                match = None
                for k, v in lookup.items():
                    if county in k or k in county:
                        match = v
                        break
                if match:
                    total_unemployed += match['unemployed_persons']
                    county_details.append({
                        'county': county,
                        'unemployed_persons': match['unemployed_persons'],
                        'unemployment_rate': match['unemployment_rate'],
                        'youth_est': int(match['unemployed_persons'] * YOUTH_RATIO),
                    })

            regions[region_name] = {
                'total_unemployed': total_unemployed,
                'youth_unemployed_est': int(total_unemployed * YOUTH_RATIO),
                'counties': county_details,
            }

        # 全台數據
        taiwan = next((v for k, v in lookup.items() if '臺灣地區' in k or '台灣地區' in k), {})
        taiwan_total = taiwan.get('unemployed_persons', 400000)
        taiwan_rate = taiwan.get('unemployment_rate', 3.33)

        return {
            'data_period': '114年上半年（2025/01-06）',
            'source': '行政院主計總處 人力資源調查',
            'taiwan_total_unemployed': taiwan_total,
            'taiwan_unemployment_rate': taiwan_rate,
            'youth_ratio_in_unemployed': YOUTH_RATIO,
            'regions': regions,
            'note': '青年(15-29歲)估計人數 = 失業人數 × 24.8%（依勞動部113年調查比例推估）',
        }

    # ------------------------------------------------------------------ #
    # 2. PTT 社群聲量
    # ------------------------------------------------------------------ #
    def get_social_volume(self, pages: int = 3) -> dict:
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
                    titles = soup.find_all('div', class_='title')
                    for t in titles:
                        text = t.get_text().strip()
                        if '公告' in text or '刪除' in text:
                            continue
                        total_posts += 1
                        for kw in keywords:
                            if kw in text:
                                keyword_counts[kw] += 1
                    prev_btn = soup.find('a', text='‹ 上頁')
                    if not prev_btn:
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

        return {
            'source': 'PTT (Salary, Soft_Job, Tech_Job)',
            'total_posts_analyzed': total_posts,
            'keyword_counts': dict(sorted(keyword_counts.items(),
                                          key=lambda x: x[1], reverse=True)),
        }

    # ------------------------------------------------------------------ #
    # 3. Google Trends 搜尋熱度
    # ------------------------------------------------------------------ #
    def get_search_trends(self, keywords: Optional[List[str]] = None) -> dict:
        if not self.pytrends:
            return {"error": "Google Trends API 無法使用"}
        if not keywords:
            keywords = ['找工作', '職訓', '履歷', '面試', '新尖兵']
        print(f"[Monitor] 獲取 Google 搜尋熱度: {keywords}...")
        try:
            self.pytrends.build_payload(kw_list=keywords, geo='TW',
                                        timeframe='today 3-m')
            df = self.pytrends.interest_over_time()
            if df.empty:
                return {"error": "無法取得趨勢資料"}
            if 'isPartial' in df.columns:
                df = df.drop(columns=['isPartial'])
            recent_avg = df.tail(7).mean().to_dict()
            older_avg = df.iloc[-14:-7].mean().to_dict()
            trends = {}
            for kw in keywords:
                current = recent_avg.get(kw, 0)
                previous = older_avg.get(kw, 0)
                change = ((current - previous) / previous * 100) if previous > 0 else 0
                trends[kw] = {
                    'current_index': round(current, 1),
                    'trend_change_pct': round(change, 1),
                    'status': '上升 ↗' if change > 5 else ('下降 ↘' if change < -5 else '持平 →'),
                }
            return {'timeframe': '過去 3 個月', 'trends': trends}
        except Exception as e:
            print(f"[Monitor] Google Trends 失敗: {e}")
            return {"error": str(e)}

    # ------------------------------------------------------------------ #
    # 完整執行
    # ------------------------------------------------------------------ #
    def run_full_monitor(self) -> dict:
        return {
            'timestamp': datetime.now().isoformat(),
            'regional_unemployment': self.get_regional_unemployment(),
            'social_volume': self.get_social_volume(pages=5),
            'search_trends': self.get_search_trends(),
        }


if __name__ == "__main__":
    import json, sys
    sys.stdout.reconfigure(encoding='utf-8')
    data = MarketMonitor().run_full_monitor()
    print(json.dumps(data, ensure_ascii=False, indent=2))
