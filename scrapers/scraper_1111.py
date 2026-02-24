"""
1111 人力銀行爬蟲模組
使用網頁解析方式取得職缺資料
"""

from typing import List, Dict, Any
from urllib.parse import quote
import re
from datetime import datetime
from .base_scraper import BaseScraper


class Scraper1111(BaseScraper):
    """
    1111 人力銀行職缺爬蟲
    """
    
    # 地區代碼映射
    AREA_CODES = {
        "taichung": "100900",   # 台中市
        "changhua": "100910",   # 彰化縣
        "nantou": "100911",     # 南投縣
    }
    
    def __init__(self, delay: float = 3.0):
        super().__init__("1111", "https://www.1111.com.tw", delay)
    
    def search_jobs(self, keyword: str, area: str, max_pages: int = 5) -> List[Dict[str, Any]]:
        """
        搜尋 1111 職缺
        注意：1111 有較強的反爬機制，此實作為基礎版本
        """
        # 取得地區代碼
        area_code = self.AREA_CODES.get(area, area)
        
        all_jobs = []
        
        # 1111 搜尋 URL 格式
        search_url = f"{self.base_url}/search/job"
        
        print(f"[1111] 開始搜尋: {keyword} @ {area}")
        
        for page in range(1, max_pages + 1):
            params = {
                'ks': keyword,
                'c0': area_code,
                'page': page,
            }
            
            try:
                soup = self._get_soup(search_url, params)
                if not soup:
                    print(f"[1111] 第 {page} 頁取得失敗")
                    break
                
                # 尋找職缺列表
                job_items = soup.find_all('div', class_='job_item_info') or \
                           soup.find_all('div', class_='item__job') or \
                           soup.find_all('div', {'data-job-no': True})
                
                if not job_items:
                    print(f"[1111] 第 {page} 頁無職缺資料，停止搜尋")
                    break
                
                for item in job_items:
                    try:
                        job = self._parse_job_item(item)
                        if job:
                            standardized = self._standardize_job(job, keyword, area)
                            all_jobs.append(standardized)
                    except Exception as e:
                        print(f"[1111] 解析職缺失敗: {e}")
                        continue
                
                print(f"[1111] 第 {page} 頁取得 {len(job_items)} 筆")
                
            except Exception as e:
                print(f"[1111] 搜尋第 {page} 頁時發生錯誤: {e}")
                break
        
        print(f"[1111] 搜尋完成: {keyword} @ {area}，共 {len(all_jobs)} 筆")
        return all_jobs
    
    def _parse_job_item(self, item) -> Dict[str, Any]:
        """
        解析單個職缺元素
        """
        job = {}
        
        # 嘗試多種可能的選擇器
        # 職缺標題
        title_elem = item.find('h2') or item.find('a', class_='job_title') or \
                    item.find('div', class_='title') or item.find('a', href=re.compile(r'/job/'))
        if title_elem:
            job['title'] = title_elem.get_text(strip=True)
            job['url'] = title_elem.get('href', '')
            if job['url'] and not job['url'].startswith('http'):
                job['url'] = f"{self.base_url}{job['url']}"
        
        # 公司名稱
        company_elem = item.find('div', class_='job_item_company') or \
                      item.find('a', class_='company') or \
                      item.find('span', class_='company')
        if company_elem:
            job['company'] = company_elem.get_text(strip=True)
        
        # 地點
        location_elem = item.find('div', class_='job_item_location') or \
                       item.find('span', class_='location')
        if location_elem:
            job['location'] = location_elem.get_text(strip=True)
        
        # 薪資
        salary_elem = item.find('div', class_='job_item_salary') or \
                     item.find('span', class_='salary')
        if salary_elem:
            salary_text = salary_elem.get_text(strip=True)
            job['salary'] = salary_text
            job['salary_min'], job['salary_max'] = self._parse_salary(salary_text)
        
        # 經驗要求
        exp_elem = item.find('div', class_='job_item_exp') or \
                  item.find('span', class_='exp')
        if exp_elem:
            job['experience'] = exp_elem.get_text(strip=True)
        
        # 學歷要求
        edu_elem = item.find('div', class_='job_item_edu') or \
                  item.find('span', class_='edu')
        if edu_elem:
            job['education'] = edu_elem.get_text(strip=True)
        
        # 職缺 ID
        job['id'] = item.get('data-job-no', '') or item.get('id', '')
        
        return job if job.get('title') else None
    
    def _parse_salary(self, salary_text: str) -> tuple:
        """解析薪資"""
        if not salary_text or '面議' in salary_text:
            return None, None
        
        # 嘗試提取數字範圍
        numbers = re.findall(r'[\d,]+', salary_text.replace(',', ''))
        if len(numbers) >= 2:
            return int(numbers[0]), int(numbers[1])
        elif len(numbers) == 1:
            return int(numbers[0]), int(numbers[0])
        
        return None, None
