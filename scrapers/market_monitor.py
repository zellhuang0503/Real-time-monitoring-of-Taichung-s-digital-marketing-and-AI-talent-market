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
    # 縣市別失業率開放資料（政府資料開放平臺 dataset 6640，每半年更新）
    # 2026-07 實測已涵蓋 114年下半年（2025/07-12）
    OPENDATA_COUNTY_RATES_URL = (
        'https://ws.dgbas.gov.tw/001/Upload/461/relfile/11525/230038/mp0101a10.xml'
    )

    # 全國年齡別失業率（主計總處每月「人力資源調查統計結果」新聞稿）
    # ⚠ 官方發布數據的靜態快照，主計總處無年齡別的機器可讀月資料，
    #   需隨每月新聞稿手動更新；資料期間與來源一律隨數據標示。
    # 最近更新：115年5月數據（2026-06-23 發布，整體失業率創 26 年同月新低）
    YOUTH_STATS = {
        'period': '115年5月',
        'source': '行政院主計總處 人力資源調查（2026/06/23 發布）',
        'overall_rate': 3.27,
        'age_15_24_rate': 11.14,
        'age_25_29_rate': 5.79,
    }

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

        # Step 1: 縣市失業「人數」來源：table32 半年報 XLSX（含失業者千人數）
        table32_url = self._find_latest_table32_url()
        raw_data = self._parse_table32(table32_url) if table32_url else []
        counts_period = '主計總處最新縣市別半年報'
        if not raw_data:
            # Fallback: 使用 114年上半年靜態數據 (2025/1-6)，明確標示為備援
            raw_data = self._static_114H1_data()
            counts_period = '114年上半年（2025/01-06，靜態備援）'

        # Step 2: 整理成分區格式
        result = self._organize_by_region(raw_data)
        result['counts_period'] = counts_period
        result['data_period'] = counts_period  # 開放資料成功時會再覆寫為失業率期間

        # Step 3: 縣市失業「率」以政府開放資料最新一期覆寫
        #（XML 每半年自動更新，比 table32 網址探測可靠）
        opendata = self.get_latest_county_rates()
        if opendata:
            rates = opendata['rates']
            for region in result['regions'].values():
                for county in region['counties']:
                    for name in (county['county'], county['county'].replace('台', '臺')):
                        if name in rates:
                            county['unemployment_rate'] = rates[name]
                            break
            if '臺灣地區' in rates:
                result['taiwan_unemployment_rate'] = rates['臺灣地區']
            result['data_period'] = opendata['period']
            result['note'] += (
                f"；縣市失業率為 {opendata['period']} 開放資料，"
                f"失業人數為 {counts_period}"
            )
            print(f"[Monitor] 已套用開放資料縣市失業率（{opendata['period']}）")

        return result

    def get_latest_county_rates(self) -> Optional[dict]:
        """
        從政府資料開放平臺抓取「人力資源調查縣市別失業率」最新一期。

        Returns:
            {'period': '114年下半年（2025/07-12）', 'rates': {'臺中市': 3.4, ...}}
            失敗時回傳 None
        """
        import xml.etree.ElementTree as ET

        try:
            r = requests.get(self.OPENDATA_COUNTY_RATES_URL, headers=self.headers,
                             verify=False, timeout=20)
            r.raise_for_status()
            root = ET.fromstring(r.content)
            records = root.findall('縣市別失業率')
            if not records:
                return None

            last = records[-1]
            period_raw = ''
            rates = {}
            for child in last:
                name = child.tag.split('_')[0]
                value = (child.text or '').strip()
                if '年月別' in child.tag:
                    period_raw = value
                elif value:
                    try:
                        rates[name] = float(value)
                    except ValueError:
                        continue

            if not rates:
                return None
            return {'period': self._format_opendata_period(period_raw), 'rates': rates}

        except Exception as e:
            print(f"[Monitor] 開放資料縣市失業率抓取失敗: {e}")
            return None

    @staticmethod
    def _format_opendata_period(raw: str) -> str:
        """開放資料年月別轉中文標籤：'2025July-Dec.' → '114年下半年（2025/07-12）'"""
        import re as _re
        m = _re.match(r'^(\d{4})\s*(Jan\.?\s*-\s*June|July\s*-\s*Dec\.?)?$', (raw or '').strip())
        if not m:
            return raw
        year = int(m.group(1))
        roc = year - 1911
        half = m.group(2) or ''
        if half.startswith('Jan'):
            return f'{roc}年上半年（{year}/01-06）'
        if half.startswith('July'):
            return f'{roc}年下半年（{year}/07-12）'
        return f'{roc}年全年（{year}）'

    def get_youth_stats(self) -> dict:
        """
        全國與年齡別失業率（含資料期間與來源標示）。
        數據為主計總處月度發布之靜態快照，見 YOUTH_STATS 註解。
        """
        stats = dict(self.YOUTH_STATS)
        ratio = round(stats['age_15_24_rate'] / stats['overall_rate'], 1)
        stats['insight'] = (
            f"{stats['period']} 全國失業率 {stats['overall_rate']}%，"
            f"15-24歲失業率 {stats['age_15_24_rate']}%（約為整體 {ratio} 倍），"
            f"25-29歲為 {stats['age_25_29_rate']}%，待業青年仍為招生核心族群。"
            f"資料來源：{stats['source']}"
        )
        return stats

    def _find_latest_table32_url(self) -> Optional[str]:
        """
        自動抓取主計總處最新的縣市別人力資源調查 table32.xlsx。

        主計總處的縣市別半年報每年發布 2 次（上/下半年），
        檔案路徑規律為：
          https://ws.dgbas.gov.tw/001/Upload/463/relfile/11040/{s}/table32.xlsx
        已知：114年上半年 = s=235335

        策略：從已知的 s 號碼往後掃描（每次+50），
        找到最大的、HTTP 200 的 s 號碼即為最新報告。
        若無更新，回傳已知最新的 URL。
        """
        WS_BASE = 'https://ws.dgbas.gov.tw/001/Upload/463/relfile/11040'
        KNOWN_LATEST_S = 235335   # 114年上半年（2025/1-6）

        def probe(s: int) -> bool:
            url = f'{WS_BASE}/{s}/table32.xlsx'
            try:
                r = requests.head(url, headers=self.headers,
                                  verify=False, timeout=5)
                return r.status_code == 200
            except Exception:
                return False

        try:
            # 從已知最新往後掃，步長 50，最多往後掃 6000（約 3 年內）
            latest_s = KNOWN_LATEST_S
            step = 50
            for candidate_s in range(KNOWN_LATEST_S + step,
                                     KNOWN_LATEST_S + 6001, step):
                if probe(candidate_s):
                    latest_s = candidate_s

            url = f'{WS_BASE}/{latest_s}/table32.xlsx'
            if latest_s == KNOWN_LATEST_S:
                print(f"[Monitor] 使用現有最新縣市別資料 s={latest_s}（114年上半年，下半年尚未發布）")
            else:
                print(f"[Monitor] 發現更新的縣市別資料 s={latest_s}，開始下載")
            return url

        except Exception as e:
            print(f"[Monitor] 搜尋最新 table32 失敗: {e}")
            return f'{WS_BASE}/{KNOWN_LATEST_S}/table32.xlsx'

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
                # 靜態備援資料的數值單位是「千人」，需乘以 1000
                raw_val = item[1]
                persons = int(raw_val * 1000)  # 千人 → 人
                item = {
                    'name': item[0],
                    'unemployed_persons': persons,
                    'unemployment_rate': item[2],
                }
            else:
                # 從 XLSX 解析出來的也是千人單位
                raw_val = item.get('unemployed_persons', 0)
                if raw_val < 10000:  # 還是千人單位，需乘以 1000
                    item['unemployed_persons'] = int(raw_val * 1000)
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
        # 注意：主計總處資料單位為「千人」，需乘以 1000 才是實際人數
        taiwan_total_k = taiwan.get('unemployed_persons', 400000)
        # 若 parse 出來的是千人單位（< 10000），需乘以 1000
        if taiwan_total_k < 10000:
            taiwan_total = taiwan_total_k * 1000
        else:
            taiwan_total = taiwan_total_k
        taiwan_rate = taiwan.get('unemployment_rate', 3.33)

        return {
            # 預設標籤，get_regional_unemployment() 會以開放資料實際期間覆寫
            'data_period': '主計總處最新縣市別統計',
            'source': '行政院主計總處 人力資源調查',
            'taiwan_total_unemployed': taiwan_total,   # 實際人數（個人）
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
            'youth_stats': self.get_youth_stats(),
            'social_volume': self.get_social_volume(pages=5),
            'search_trends': self.get_search_trends(),
        }


if __name__ == "__main__":
    import json, sys
    sys.stdout.reconfigure(encoding='utf-8')
    data = MarketMonitor().run_full_monitor()
    print(json.dumps(data, ensure_ascii=False, indent=2))
