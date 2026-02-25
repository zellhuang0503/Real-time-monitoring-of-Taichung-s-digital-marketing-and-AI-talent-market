"""
518 人力銀行爬蟲模組

【修正說明 2026-02-25】
518 網站是 server-side session 驅動的 AJAX 架構，並有 SSL 憑證問題。
正確流程：
  1. 先 GET /job-index.html?ro=keyword&ab=area_code -> server 把搜尋條件存入 PHPSESSID
  2. 再 POST /ajax/ module=job action=ajaxLoader_jobList page=N -> 按頁取得 JSON

原始爬蟲失敗的原因：
  a. SSL 憑證驗證失敗（Missing Subject Key Identifier）
  b. 直接 POST 不帶 session cookie，server 找不到搜尋條件
  c. 錯誤的 CSS selector（網站使用動態 JS 渲染，非靜態 HTML）
"""

import time
import random
import warnings
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

import requests
warnings.filterwarnings('ignore', message='Unverified HTTPS request')


class Scraper518:
    """
    518 人力銀行職缺爬蟲
    使用 session + AJAX API 方式抓取資料
    """

    BASE_URL = "https://www.518.com.tw"

    AREA_CODES = {
        "taichung": "3001007",   # 台中市
        "changhua": "3001009",   # 彰化縣
        "nantou": "3001010",     # 南投縣
    }

    def __init__(self, delay: float = 3.0):
        self.delay = delay

    def _make_session(self) -> requests.Session:
        """建立一個帶有隨機 UA 的 requests Session"""
        ua_list = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) "
            "Gecko/20100101 Firefox/124.0",
        ]
        s = requests.Session()
        s.verify = False  # 518 SSL 憑證有問題（Missing Subject Key Identifier）
        s.headers.update({
            "User-Agent": random.choice(ua_list),
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })
        return s

    def _init_search_session(self, session: requests.Session, keyword: str, area_code: str) -> bool:
        """
        Step 1: GET 搜尋頁面，讓 server 把條件存進 PHPSESSID cookie
        """
        params = {"ro": keyword, "ab": area_code}
        try:
            r = session.get(f"{self.BASE_URL}/job-index.html", params=params, timeout=20)
            r.raise_for_status()
            session.headers.update({
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": r.url,
            })
            return True
        except Exception as e:
            print(f"[518] 初始化 session 失敗: {e}")
            return False

    def _fetch_page(self, session: requests.Session, page: int) -> List[Dict]:
        """
        Step 2: POST /ajax/ 取得指定頁的職缺 JSON
        """
        data = {
            "module": "job",
            "action": "ajaxLoader_jobList",
            "page": str(page),
        }
        try:
            time.sleep(self.delay + random.uniform(0, 1.5))
            r = session.post(f"{self.BASE_URL}/ajax/", data=data, timeout=20)
            r.raise_for_status()
            result = r.json()
            dataset = result.get("dataset", {})
            if not dataset.get("haveData", False):
                return []
            return dataset.get("jobList", [])
        except Exception as e:
            print(f"[518] 第 {page} 頁請求失敗: {e}")
            return []

    def _parse_job(self, raw: Dict, keyword: str, area: str) -> Dict[str, Any]:
        """將 518 API 職缺格式轉成標準格式"""
        ji = raw.get("jobInfo", {})
        co = raw.get("company", {})
        req = ji.get("required", {})

        salary_text = ji.get("salary", "面議")
        salary_min, salary_max = self._parse_salary(salary_text)

        return {
            "source": "518",
            "job_id": ji.get("id", ""),
            "title": ji.get("name", ""),
            "company": co.get("name", "") if isinstance(co, dict) else str(co),
            "company_industry": "",
            "location": ji.get("area", ""),
            "salary": salary_text,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "experience": req.get("experience", ""),
            "education": req.get("education", ""),
            "job_description": ji.get("description", ""),
            "job_category": "",
            "search_keyword": keyword,
            "area": area,
            "url": ji.get("url", ""),
            "posted_date": ji.get("date", ""),
            "scraped_at": datetime.now().isoformat(),
        }

    def _parse_salary(self, text: str):
        """解析薪資字串，回傳 (min, max)"""
        if not text or "面議" in text or "待遇面議" in text:
            return None, None
        numbers = re.findall(r"[\d,]+", text.replace(",", ""))
        if len(numbers) >= 2:
            return int(numbers[0]), int(numbers[1])
        if len(numbers) == 1:
            v = int(numbers[0])
            return v, v
        return None, None

    def search_jobs(self, keyword: str, area: str, max_pages: int = 5) -> List[Dict[str, Any]]:
        """
        搜尋 518 職缺

        Args:
            keyword:   搜尋關鍵字
            area:      地區名稱 ("taichung"/"changhua"/"nantou") 或直接帶代碼
            max_pages: 最多抓幾頁（每頁約 32 筆）

        Returns:
            標準化職缺列表
        """
        area_code = self.AREA_CODES.get(area, area)
        print(f"[518] 開始搜尋: {keyword} @ {area} (area_code={area_code})")

        session = self._make_session()
        if not self._init_search_session(session, keyword, area_code):
            print(f"[518] session 建立失敗，跳過 {keyword}@{area}")
            return []

        all_jobs: List[Dict[str, Any]] = []
        for page in range(1, max_pages + 1):
            raw_list = self._fetch_page(session, page)
            if not raw_list:
                print(f"[518] 第 {page} 頁無資料，結束")
                break
            for raw in raw_list:
                try:
                    all_jobs.append(self._parse_job(raw, keyword, area))
                except Exception:
                    continue
            print(f"[518] 第 {page} 頁取得 {len(raw_list)} 筆")

        # 去重
        seen = set()
        unique = []
        for j in all_jobs:
            if j["job_id"] not in seen:
                seen.add(j["job_id"])
                unique.append(j)

        print(f"[518] 搜尋完成: {keyword} @ {area}，共 {len(unique)} 筆")
        return unique
