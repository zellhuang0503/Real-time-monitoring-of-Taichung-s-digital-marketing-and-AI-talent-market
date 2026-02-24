"""
通用爬蟲基礎類別
提供共用的 HTTP 請求、重試機制等功能
"""

import requests
import time
import random
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup


class BaseScraper(ABC):
    """
    爬蟲基礎類別
    """
    
    def __init__(self, name: str, base_url: str, delay: float = 2.0, max_retries: int = 3):
        """
        初始化爬蟲
        
        Args:
            name: 爬蟲名稱（用於日誌）
            base_url: 網站基礎 URL
            delay: 請求間隔秒數
            max_retries: 最大重試次數
        """
        self.name = name
        self.base_url = base_url
        self.delay = delay
        self.max_retries = max_retries
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self._get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        })
    
    def _get_random_user_agent(self) -> str:
        """取得隨機 User-Agent"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
        ]
        return random.choice(user_agents)
    
    def _get(self, url: str, params: dict = None) -> Optional[requests.Response]:
        """
        發送 GET 請求（含重試機制）
        
        Args:
            url: 目標 URL
            params: URL 參數
            
        Returns:
            Response 物件或 None（若全部重試失敗）
        """
        for attempt in range(self.max_retries):
            try:
                time.sleep(self.delay + random.uniform(0, 1))
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                return response
            except Exception as e:
                print(f"[{self.name}] 請求失敗（第 {attempt + 1}/{self.max_retries} 次）: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # 指數退避
        return None
    
    def _get_soup(self, url: str, params: dict = None) -> Optional[BeautifulSoup]:
        """
        取得頁面的 BeautifulSoup 物件
        
        Args:
            url: 目標 URL
            params: URL 參數
            
        Returns:
            BeautifulSoup 物件或 None
        """
        response = self._get(url, params)
        if response:
            return BeautifulSoup(response.text, 'lxml')
        return None
    
    @abstractmethod
    def search_jobs(self, keyword: str, area: str, max_pages: int = 5) -> List[Dict[str, Any]]:
        """
        搜尋職缺（子類別必須實作）
        
        Args:
            keyword: 搜尋關鍵字
            area: 地區名稱或代碼
            max_pages: 最大頁數
            
        Returns:
            職缺列表
        """
        pass
    
    def _standardize_job(self, raw_job: Dict, search_keyword: str, area: str) -> Dict[str, Any]:
        """
        標準化職缺資料格式
        所有爬蟲都應該輸出相同格式的資料
        """
        return {
            'source': self.name,
            'job_id': str(raw_job.get('id', '')),
            'title': raw_job.get('title', ''),
            'company': raw_job.get('company', ''),
            'company_industry': raw_job.get('industry', ''),
            'location': raw_job.get('location', ''),
            'salary': raw_job.get('salary', '面議'),
            'salary_min': raw_job.get('salary_min'),
            'salary_max': raw_job.get('salary_max'),
            'experience': raw_job.get('experience', ''),
            'education': raw_job.get('education', ''),
            'job_description': raw_job.get('description', ''),
            'job_category': raw_job.get('category', ''),
            'search_keyword': search_keyword,
            'area': area,
            'url': raw_job.get('url', ''),
            'posted_date': raw_job.get('posted_date', ''),
            'scraped_at': datetime.now().isoformat(),
        }
