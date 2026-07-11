"""
104人力銀行爬蟲模組
使用公開 API 取得職缺資料
"""

import requests
import time
import json
import random
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.parse import quote

class Scraper104:
    """
    104人力銀行職缺爬蟲
    使用公開 API: https://www.104.com.tw/jobs/search/api/jobs
    """
    
    BASE_URL = "https://www.104.com.tw/jobs/search/api/jobs"
    
    # 地區代碼
    AREA_CODES = {
        "taichung": "6001008000",  # 台中市
        "changhua": "6001010000",  # 彰化縣
        "nantou": "6001011000",    # 南投縣
    }

    # 104 API period 代碼對照表（class 層級，避免每次呼叫重新建立）
    # 官方代碼：1=1年以下, 2=1-3年, 3=3-5年, 4=5-10年, 5=10年以上, 6=不拘（含0）
    PERIOD_MAP = {
        '0': '不拘',  '1': '1年以下', '2': '1-3年',  '3': '3-5年',
        '4': '5-10年', '5': '10年以上', '6': '不拘',   '7': '1年以下',
        '8': '1-3年', '9': '3-5年',  '10': '5-10年', '11': '10年以上',
    }
    
    def __init__(self, delay: float = 2.0):
        """
        初始化爬蟲
        
        Args:
            delay: 請求間隔秒數（避免被封鎖）
        """
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://www.104.com.tw/jobs/search/',
        })
    
    def _fetch_page(self, keyword: str, area: str, page: int = 1) -> Dict[str, Any]:
        """
        取得單頁職缺資料
        
        Args:
            keyword: 搜尋關鍵字
            area: 地區代碼
            page: 頁碼
            
        Returns:
            API 回應的 JSON 資料
        """
        params = {
            'ro': '0',  # 全部
            'keyword': keyword,
            'area': area,
            'page': str(page),
            'jobsource': 'indexp',
            'mode': 's',  # 搜尋模式
            # 依「最近刊登日期」排序（實測 order=2 為日期新→舊）。
            # 若不指定，104 預設用「符合度」排序，會導致每天都抓到
            # 同一批熱門職缺、抓不到新刊登的職缺。
            'order': '2',
            'asc': '0',
        }
        
        try:
            response = self.session.get(
                self.BASE_URL,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            # 104 API 回傳的是 JSONP，需要解析
            text = response.text
            if text.startswith('__jsonp__'):
                # 移除 JSONP 包裝
                start = text.find('(') + 1
                end = text.rfind(')')
                json_str = text[start:end]
            else:
                json_str = text
                
            return json.loads(json_str)
            
        except Exception as e:
            print(f"[104] 取得資料失敗: {e}")
            return {'data': {'list': [], 'totalPage': 0, 'totalCount': 0}}
    
    def _fetch_job_detail(self, job_code: str) -> Dict[str, Any]:
        """
        取得單一職缺的詳細資料

        Args:
            job_code: 職缺代碼（link.job 網址結尾的英數代碼，例如 '4g5w3'）

        Returns:
            職缺詳細資料
        """
        url = f"https://www.104.com.tw/job/ajax/content/{job_code}"

        try:
            # 詳細頁 API 會驗證 Referer 必須是該職缺頁面
            response = self.session.get(
                url,
                headers={'Referer': f'https://www.104.com.tw/job/{job_code}'},
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[104] 取得職缺 {job_code} 詳細資料失敗: {e}")
            return {}
    
    def search_jobs(self, keyword: str, area: str, max_pages: int = 10, fetch_details: bool = False) -> List[Dict[str, Any]]:
        """
        搜尋職缺（多頁）
        
        Args:
            keyword: 搜尋關鍵字
            area: 地區代碼或名稱
            max_pages: 最大頁數
            fetch_details: 是否抓取詳細資料（會較慢）
            
        Returns:
            職缺列表
        """
        # 轉換地區名稱為代碼
        area_code = self.AREA_CODES.get(area, area)
        
        all_jobs = []
        page = 1
        
        print(f"[104] 開始搜尋: {keyword} @ {area}")
        
        while page <= max_pages:
            print(f"[104] 正在取得第 {page} 頁...")
            
            data = self._fetch_page(keyword, area_code, page)

            if 'data' not in data:
                print(f"[104] 無資料或格式錯誤: {data.keys()}")
                break

            # 104 API v2 格式處理
            data_content = data.get('data', {})
            if isinstance(data_content, list):
                # 新API直接返回列表，總頁數在 metadata.pagination.lastPage
                jobs = data_content
                pagination = (data.get('metadata') or {}).get('pagination') or {}
                total_page = pagination.get('lastPage') or 0
            elif isinstance(data_content, dict):
                # 舊API格式
                jobs = data_content.get('list', [])
                total_page = data_content.get('totalPage', 0)
            else:
                print(f"[104] 未知的資料格式: {type(data_content)}")
                break

            if not jobs:
                print(f"[104] 第 {page} 頁無資料，停止搜尋")
                break

            # 處理每個職缺
            for job in jobs:
                processed_job = self._process_job(job, keyword, area, fetch_details)
                if processed_job:  # 確保處理成功
                    all_jobs.append(processed_job)

                # 如果抓取詳細資料，增加延遲避免被封鎖
                if fetch_details:
                    time.sleep(0.5)

            print(f"[104] 第 {page} 頁取得 {len(jobs)} 筆，總頁數: {total_page or '未知'}")

            # 已到最後一頁（API 回報）或達到頁數上限就停止
            if page >= max_pages or (total_page and page >= total_page):
                break

            page += 1
            time.sleep(self.delay + random.uniform(0, 1))
        
        print(f"[104] 搜尋完成: {keyword} @ {area}，共 {len(all_jobs)} 筆")
        return all_jobs
    
    def _process_job(self, job: Dict, search_keyword: str, area: str, fetch_details: bool = False) -> Dict[str, Any]:
        """
        處理單個職缺資料，標準化格式
        
        Args:
            job: API 返回的原始職缺資料
            search_keyword: 搜尋關鍵字
            area: 地區名稱
            fetch_details: 是否抓取詳細資料
        """
        job_no = str(job.get('jobNo', ''))

        # 從列表資料提取基本資訊
        title = job.get('jobName', '')
        company = job.get('custName', '')
        location = job.get('jobAddrNoDesc', '')

        # 職缺連結（新版 API 的 link.job 含英數代碼，詳細頁 API 需要這個代碼）
        link_url = (job.get('link') or {}).get('job', '') if isinstance(job.get('link'), dict) else ''
        job_code = link_url.rstrip('/').split('/')[-1].split('?')[0] if link_url else ''

        # 處理薪資：新版 API 提供數字欄位 salaryLow / salaryHigh
        # （0 = 未提供，9999999 = 「以上」無上限）；舊格式才有 salaryDesc 文字
        salary_min = salary_max = None
        raw_low = job.get('salaryLow')
        raw_high = job.get('salaryHigh')
        if isinstance(raw_low, (int, float)) and 0 < raw_low < 9999999:
            salary_min = int(raw_low)
        if isinstance(raw_high, (int, float)) and 0 < raw_high < 9999999:
            salary_max = int(raw_high)

        salary_text = job.get('salaryDesc', job.get('salary', ''))
        if not salary_text:
            if salary_min and salary_max:
                salary_text = f"月薪 {salary_min:,}~{salary_max:,}元"
            elif salary_min:
                salary_text = f"月薪 {salary_min:,}元以上"
            else:
                salary_text = '面議'
        if salary_min is None and salary_max is None:
            salary_min, salary_max = self._parse_salary_v2(salary_text)

        # 處理經驗要求
        # 104 API 的 period 是數字代碼，periodDesc 才是文字（但通常為空）。
        # 代碼對照僅為近似值，詳細頁的 condition.workExp 才是準確文字，
        # 會在 enrich_jobs_with_details() 時覆寫。
        exp_period = str(job.get('period', ''))
        exp_desc = job.get('periodDesc', '')
        experience = exp_desc if exp_desc else self.PERIOD_MAP.get(exp_period, exp_period)

        # 處理學歷（新版 API 的 optionEdu 是代碼列表，例如 [3, 4] = 專科/大學）
        edu_map = {
            '1': '高中以下',
            '2': '高中',
            '3': '專科',
            '4': '大學',
            '5': '碩士',
            '6': '博士',
        }
        edu_raw = job.get('optionEdu', '')
        if isinstance(edu_raw, list):
            education = '/'.join(edu_map.get(str(c), str(c)) for c in edu_raw)
        else:
            education = edu_map.get(str(edu_raw), str(edu_raw) if edu_raw else '')

        # 處理產業別
        industry = job.get('coIndustryDesc', '') or job.get('coIndustry', '')
        if isinstance(industry, list):
            industry = industry[0] if industry else ''

        # 職務類別
        job_category = job.get('jobCategory', job.get('jobCat', ''))
        if isinstance(job_category, list):
            first = job_category[0] if job_category else ''
            job_category = first.get('description', '') if isinstance(first, dict) else str(first)

        result = {
            'source': '104',
            'job_id': job_no,
            'job_code': job_code,  # 詳細頁 API 用的英數代碼
            'title': title,
            'company': company,
            'company_industry': industry,
            'location': location,
            'salary': salary_text,
            'salary_min': salary_min,
            'salary_max': salary_max,
            'experience': experience,
            'education': education,
            # 列表 API 的 description 是截斷版描述，仍可先用於分析；
            # enrich_jobs_with_details() 會以詳細頁完整描述覆寫
            'job_description': job.get('description', '') or '',
            'specialties': [],   # 擅長工具（詳細頁 condition.specialty）
            'job_skills': [],    # 工作技能（詳細頁 condition.skill）
            'other_requirement': '',  # 其他條件（詳細頁 condition.other）
            'detail_fetched': False,
            'job_category': job_category,
            'search_keyword': search_keyword,
            'area': area,
            'url': link_url or f"https://www.104.com.tw/job/{job_no}",
            'posted_date': job.get('appearDate', ''),
            'scraped_at': datetime.now().isoformat(),
        }

        # 如果需要抓取詳細資料
        if fetch_details and (job_code or job_no):
            detail = self._fetch_job_detail(job_code or job_no)
            self._apply_detail(result, detail)

        return result

    def _apply_detail(self, result: Dict, detail: Dict) -> bool:
        """
        把詳細頁 API 回應中的真實工作條件套用到職缺資料上。

        重要欄位：
        - jobDetail.jobDescription: 完整職缺描述
        - condition.specialty: 擅長工具（雇主勾選的真實工具需求）
        - condition.skill: 工作技能
        - condition.other: 其他條件（常含 AI 工具等自由文字需求）
        - condition.workExp / condition.edu: 準確的經驗與學歷要求
        """
        if not detail or 'data' not in detail:
            return False

        detail_data = detail['data']
        job_detail = detail_data.get('jobDetail', {}) or {}
        condition = detail_data.get('condition', {}) or {}

        description = job_detail.get('jobDescription', '')
        if description:
            result['job_description'] = description

        result['specialties'] = [
            s.get('description', '') for s in (condition.get('specialty') or [])
            if isinstance(s, dict) and s.get('description')
        ]
        result['job_skills'] = [
            s.get('description', '') for s in (condition.get('skill') or [])
            if isinstance(s, dict) and s.get('description')
        ]
        result['other_requirement'] = condition.get('other', '') or ''

        work_exp = condition.get('workExp', '')
        if work_exp:
            result['experience'] = work_exp
        edu = condition.get('edu', '')
        if edu:
            result['education'] = edu

        # 職務類別（詳細頁為 list of {code, description}）
        categories = job_detail.get('jobCategory')
        if isinstance(categories, list) and categories:
            first = categories[0]
            if isinstance(first, dict) and first.get('description'):
                result['job_category'] = first['description']
        elif isinstance(categories, dict) and categories.get('description'):
            result['job_category'] = categories['description']

        # 薪資（詳細頁文字較完整，僅在解析成功時覆寫）
        salary_detail = job_detail.get('salary', '')
        if salary_detail:
            result['salary'] = salary_detail
            salary_min, salary_max = self._parse_salary_v2(salary_detail)
            if salary_min is not None:
                result['salary_min'] = salary_min
                result['salary_max'] = salary_max

        result['detail_fetched'] = True
        return True

    # 詳細資料快取中要保留的欄位（跨日重複職缺不需重新請求）
    DETAIL_CACHE_FIELDS = (
        'job_description', 'specialties', 'job_skills', 'other_requirement',
        'experience', 'education', 'job_category', 'salary', 'salary_min', 'salary_max',
    )

    def enrich_jobs_with_details(self, jobs: List[Dict[str, Any]],
                                 cache_path: Optional[str] = None,
                                 delay: float = 0.35) -> int:
        """
        為職缺列表補抓 104 詳細頁的真實工作條件（擅長工具、完整描述等）。

        職缺每天重疊度高，使用 JSON 快取避免重複請求同一職缺。

        Args:
            jobs: 職缺列表（就地更新，僅處理 source == '104' 的職缺）
            cache_path: 快取檔路徑（JSON，key 為 job_id）
            delay: 每次請求間隔秒數

        Returns:
            成功取得詳細資料的職缺數
        """
        import os

        cache = {}
        if cache_path and os.path.exists(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
            except Exception as e:
                print(f"[104] 讀取詳細資料快取失敗（將重新抓取）: {e}")
                cache = {}

        # 快取過期清理（45 天）：此檔會被 GitHub Actions 一起 commit，
        # 不清理會無限累積導致 repo 膨脹
        if cache:
            from datetime import timedelta
            cutoff = (datetime.now() - timedelta(days=45)).strftime('%Y%m%d')
            before = len(cache)
            cache = {k: v for k, v in cache.items() if v.get('_cached_at', '') >= cutoff}
            if len(cache) < before:
                print(f"[104] 快取過期清理: 移除 {before - len(cache)} 筆（保留 {len(cache)} 筆）")

        targets = [j for j in jobs if j.get('source') == '104' and not j.get('detail_fetched')]
        print(f"[104] 開始補抓 {len(targets)} 筆職缺的詳細工作條件（快取 {len(cache)} 筆）...")

        enriched = 0
        fetched = 0
        for i, job in enumerate(targets, 1):
            job_id = str(job.get('job_id', ''))

            cached = cache.get(job_id)
            if cached:
                job.update({k: cached.get(k) for k in self.DETAIL_CACHE_FIELDS if k in cached})
                job['detail_fetched'] = True
                enriched += 1
                continue

            code = job.get('job_code') or job_id
            if not code:
                continue

            detail = self._fetch_job_detail(code)
            fetched += 1
            if self._apply_detail(job, detail):
                enriched += 1
                entry = {k: job.get(k) for k in self.DETAIL_CACHE_FIELDS}
                entry['_cached_at'] = datetime.now().strftime('%Y%m%d')
                cache[job_id] = entry

            if i % 200 == 0:
                print(f"[104] 詳細資料進度: {i}/{len(targets)}（實際請求 {fetched} 次）")
                # 定期寫入快取，避免中斷後全部重來
                if cache_path:
                    self._save_detail_cache(cache, cache_path)

            time.sleep(delay + random.uniform(0, 0.2))

        if cache_path:
            self._save_detail_cache(cache, cache_path)

        print(f"[104] 詳細資料補抓完成: 成功 {enriched}/{len(targets)} 筆（新請求 {fetched} 次，其餘用快取）")
        return enriched

    @staticmethod
    def _save_detail_cache(cache: Dict, cache_path: str):
        """儲存詳細資料快取"""
        import os
        try:
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache, f, ensure_ascii=False)
        except Exception as e:
            print(f"[104] 寫入詳細資料快取失敗: {e}")
    
    def _parse_salary_v2(self, salary_text: str) -> tuple:
        """
        解析薪資文字（適用於新版 API）
        
        Returns:
            (最低薪資, 最高薪資) - 若無法解析則返回 (None, None)
        """
        import re
        
        if not salary_text or salary_text == '面議' or salary_text == '待遇面議':
            return None, None
        
        # 月薪格式："月薪 35,000~45,000元" 或 "月薪 35,000元以上"
        monthly_match = re.search(r'月薪\s*([\d,]+)\s*[~-]?\s*([\d,]*)', salary_text)
        if monthly_match:
            min_sal = int(monthly_match.group(1).replace(',', ''))
            max_sal_str = monthly_match.group(2).replace(',', '')
            max_sal = int(max_sal_str) if max_sal_str else min_sal
            return min_sal, max_sal
        
        # 年薪格式："年薪 500,000~600,000元"
        yearly_match = re.search(r'年薪\s*([\d,]+)\s*[~-]?\s*([\d,]*)', salary_text)
        if yearly_match:
            min_sal = int(yearly_match.group(1).replace(',', '')) / 12
            max_sal_str = yearly_match.group(2).replace(',', '')
            max_sal = int(max_sal_str) / 12 if max_sal_str else min_sal
            return int(min_sal), int(max_sal)
        
        # 時薪格式："時薪 200~250元"
        hourly_match = re.search(r'時薪\s*([\d,]+)\s*[~-]?\s*([\d,]*)', salary_text)
        if hourly_match:
            min_rate = int(hourly_match.group(1).replace(',', ''))
            max_rate_str = hourly_match.group(2).replace(',', '')
            max_rate = int(max_rate_str) if max_rate_str else min_rate
            # 假設每月工作 160 小時
            return min_rate * 160, max_rate * 160
        
        # 嘗試提取任何數字組合
        numbers = re.findall(r'[\d,]+', salary_text)
        if len(numbers) >= 2:
            return int(numbers[0].replace(',', '')), int(numbers[1].replace(',', ''))
        elif len(numbers) == 1:
            val = int(numbers[0].replace(',', ''))
            return val, val
        
        return None, None
    
    def search_by_keywords(self, keywords: List[str], areas: List[str] = None,
                           fetch_details: bool = False, max_pages: int = 5) -> List[Dict[str, Any]]:
        """
        批次搜尋多個關鍵字

        Args:
            keywords: 關鍵字列表
            areas: 地區列表，預設為全部監控地區
            fetch_details: 是否在搜尋時同步抓取詳細資料
                           （建議改用去重後的 enrich_jobs_with_details()，可少抓重複職缺）
            max_pages: 每個關鍵字x地區最多抓幾頁

        Returns:
            所有搜尋結果合併列表
        """
        if areas is None:
            areas = list(self.AREA_CODES.keys())

        all_jobs = []

        for keyword in keywords:
            for area in areas:
                jobs = self.search_jobs(keyword, area, max_pages=max_pages, fetch_details=fetch_details)
                all_jobs.extend(jobs)
                time.sleep(self.delay)
        
        # 去重（根據 job_id）
        seen_ids = set()
        unique_jobs = []
        for job in all_jobs:
            if job['job_id'] not in seen_ids:
                seen_ids.add(job['job_id'])
                unique_jobs.append(job)
        
        print(f"[104] 批次搜尋完成，共 {len(unique_jobs)} 筆不重複職缺")
        return unique_jobs


# 測試用
if __name__ == "__main__":
    scraper = Scraper104()
    
    # 測試搜尋
    jobs = scraper.search_jobs("數位行銷", "taichung", max_pages=2, fetch_details=False)
    print(f"\n測試結果：找到 {len(jobs)} 筆職缺")
    if jobs:
        print("\n第一筆職缺範例：")
        print(json.dumps(jobs[0], ensure_ascii=False, indent=2))
