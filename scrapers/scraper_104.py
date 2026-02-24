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
    
    def _fetch_job_detail(self, job_no: str) -> Dict[str, Any]:
        """
        取得單一職缺的詳細資料
        
        Args:
            job_no: 職缺編號
            
        Returns:
            職缺詳細資料
        """
        url = f"https://www.104.com.tw/job/ajax/content/{job_no}"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[104] 取得職缺 {job_no} 詳細資料失敗: {e}")
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
                # 新API直接返回列表
                jobs = data_content
                total_page = page if len(jobs) < 20 else page + 1
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
            
            print(f"[104] 第 {page} 頁取得 {len(jobs)} 筆，總頁數: {total_page}")
            
            # 如果取得的職缺少於預期，可能是已經到最後一頁
            if len(jobs) < 20 or page >= max_pages:
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
        
        # 處理薪資 - 新 API 格式
        salary_text = job.get('salaryDesc', job.get('salary', '面議'))
        salary_min, salary_max = self._parse_salary_v2(salary_text)
        
        # 處理經驗要求
        exp_period = job.get('period', '')
        exp_desc = job.get('periodDesc', '')
        experience = exp_desc if exp_desc else str(exp_period)
        
        # 處理學歷
        edu_code = job.get('optionEdu', '')
        edu_map = {
            '1': '高中以下',
            '2': '高中',
            '3': '專科',
            '4': '大學',
            '5': '碩士',
            '6': '博士',
        }
        education = edu_map.get(str(edu_code), str(edu_code) if edu_code else '')
        
        # 處理產業別
        industry = job.get('coIndustry', '')
        if isinstance(industry, list):
            industry = industry[0] if industry else ''
        
        # 職務類別
        job_category = job.get('jobCategory', '')
        if isinstance(job_category, list):
            job_category = job_category[0].get('description', '') if job_category else ''
        
        result = {
            'source': '104',
            'job_id': job_no,
            'title': title,
            'company': company,
            'company_industry': industry,
            'location': location,
            'salary': salary_text,
            'salary_min': salary_min,
            'salary_max': salary_max,
            'experience': experience,
            'education': education,
            'job_description': '',  # 列表中沒有詳細描述
            'job_category': job_category,
            'search_keyword': search_keyword,
            'area': area,
            'url': f"https://www.104.com.tw/job/{job_no}",
            'posted_date': job.get('appearDate', ''),
            'scraped_at': datetime.now().isoformat(),
        }
        
        # 如果需要抓取詳細資料
        if fetch_details and job_no:
            print(f"[104] 抓取職缺 {job_no} 詳細資料...")
            detail = self._fetch_job_detail(job_no)
            if detail and 'data' in detail:
                detail_data = detail['data']
                # 更新職缺描述
                result['job_description'] = detail_data.get('jobDetail', {}).get('jobDescription', '')
                # 更新其他詳細資訊
                result['job_category'] = detail_data.get('jobDetail', {}).get('jobCategory', {}).get('description', result['job_category'])
                # 更新薪資（如果有更詳細的資訊）
                salary_detail = detail_data.get('jobDetail', {}).get('salary', '')
                if salary_detail:
                    result['salary'] = salary_detail
                    salary_min, salary_max = self._parse_salary_v2(salary_detail)
                    result['salary_min'] = salary_min
                    result['salary_max'] = salary_max
        
        return result
    
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
    
    def search_by_keywords(self, keywords: List[str], areas: List[str] = None, fetch_details: bool = False) -> List[Dict[str, Any]]:
        """
        批次搜尋多個關鍵字
        
        Args:
            keywords: 關鍵字列表
            areas: 地區列表，預設為全部監控地區
            fetch_details: 是否抓取詳細資料
            
        Returns:
            所有搜尋結果合併列表
        """
        if areas is None:
            areas = list(self.AREA_CODES.keys())
        
        all_jobs = []
        
        for keyword in keywords:
            for area in areas:
                jobs = self.search_jobs(keyword, area, fetch_details=fetch_details)
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
