"""
518 人力銀行爬蟲模組
"""

from typing import List, Dict, Any
import re
from datetime import datetime
from .base_scraper import BaseScraper


class Scraper518(BaseScraper):
    """
    518 人力銀行職缺爬蟲
    """
    
    AREA_CODES = {
        "taichung": "3001007",   # 台中市
        "changhua": "3001009",   # 彰化縣
        "nantou": "3001010",     # 南投縣
    }
    
    def __init__(self, delay: float = 3.0):
        super().__init__("518", "https://www.518.com.tw", delay)
    
    def search_jobs(self, keyword: str, area: str, max_pages: int = 5) -> List[Dict[str, Any]]:
        """
        搜尋 518 職缺
        """
        area_code = self.AREA_CODES.get(area, area)
        all_jobs = []
        
        print(f"[518] 開始搜尋: {keyword} @ {area}")
        
        for page in range(1, max_pages + 1):
            try:
                # 518 搜尋 URL
                search_url = f"{self.base_url}/job-index.html"
                params = {
                    'ab': area_code,
                    'aa': '3001000',  # 中部地區大分類
                    'ai': '',  # 職務大分類
                }
                
                # 如果有關鍵字，使用搜尋功能
                if keyword:
                    search_url = f"{self.base_url}/job-index.html"
                    params['ro'] = '1'
                    params['keyword'] = keyword
                    params['ab'] = area_code
                
                soup = self._get_soup(search_url, params)
                if not soup:
                    break
                
                # 解析職缺列表
                job_items = soup.find_all('li', class_='job-item') or \
                           soup.find_all('div', class_='job-item')
                
                if not job_items:
                    break
                
                for item in job_items:
                    try:
                        job = self._parse_job_item(item)
                        if job:
                            standardized = self._standardize_job(job, keyword, area)
                            all_jobs.append(standardized)
                    except Exception as e:
                        continue
                
                print(f"[518] 第 {page} 頁取得 {len(job_items)} 筆")
                
            except Exception as e:
                print(f"[518] 搜尋錯誤: {e}")
                break
        
        print(f"[518] 搜尋完成: {keyword} @ {area}，共 {len(all_jobs)} 筆")
        return all_jobs
    
    def _parse_job_item(self, item) -> Dict[str, Any]:
        """解析職缺元素"""
        job = {}
        
        # 職缺標題
        title_elem = item.find('h2') or item.find('a', class_='job-title') or \
                    item.find('div', class_='title')
        if title_elem:
            job['title'] = title_elem.get_text(strip=True)
        
        # 公司名稱
        company_elem = item.find('div', class_='company') or \
                      item.find('span', class_='company-name')
        if company_elem:
            job['company'] = company_elem.get_text(strip=True)
        
        # 薪資
        salary_elem = item.find('div', class_='salary') or \
                     item.find('span', class_='pay')
        if salary_elem:
            salary_text = salary_elem.get_text(strip=True)
            job['salary'] = salary_text
            job['salary_min'], job['salary_max'] = self._parse_salary(salary_text)
        
        # 地點
        location_elem = item.find('div', class_='location') or \
                       item.find('span', class_='area')
        if location_elem:
            job['location'] = location_elem.get_text(strip=True)
        
        job['id'] = item.get('data-job-id', '') or item.get('id', '')
        
        return job if job.get('title') else None
    
    def _parse_salary(self, salary_text: str) -> tuple:
        """解析薪資"""
        if not salary_text or '面議' in salary_text:
            return None, None
        
        numbers = re.findall(r'\d+', salary_text.replace(',', ''))
        if len(numbers) >= 2:
            return int(numbers[0]), int(numbers[1])
        elif len(numbers) == 1:
            return int(numbers[0]), int(numbers[0])
        
        return None, None
