"""
1111 人力銀行爬蟲模組

【修正說明 2026-02-25】
1111 是 Nuxt3 SSR 架構，頁面 HTML 內嵌了所有職缺資料在一個
<script type="application/json"> 標籤裡，格式是 Nuxt3 的「revive serialization」。

正確流程：
  GET /search/job?ks=keyword&c0=area_code&page=N
  -> 解析 <script type="application/json"> 裡的 JSON 陣列
  -> 用迭代式 deref 還原物件結構
  -> 取 data.apiJob.result.hits 為職缺列表

原始爬蟲失敗原因：
  a. SSL 憑證驗證失敗（Missing Subject Key Identifier）
  b. 嘗試用 BeautifulSoup 解析動態內容（CSS class 不存在）
  c. 沒有處理 Nuxt3 的 revive 格式，無法解析嵌入的資料
"""

import time
import random
import warnings
import re
import json
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

import requests
from bs4 import BeautifulSoup

warnings.filterwarnings('ignore', message='Unverified HTTPS request')


class Scraper1111:
    """
    1111 人力銀行職缺爬蟲
    解析 Nuxt3 SSR 頁面中的內嵌 JSON 資料
    """

    BASE_URL = "https://www.1111.com.tw"

    AREA_CODES = {
        "taichung": "100900",   # 台中市
        "changhua": "100910",   # 彰化縣
        "nantou": "100911",     # 南投縣
    }

    def __init__(self, delay: float = 3.0):
        self.delay = delay

    def _make_session(self) -> requests.Session:
        ua_list = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        ]
        s = requests.Session()
        s.verify = False  # 1111 也有 SSL 憑證問題
        s.headers.update({
            "User-Agent": random.choice(ua_list),
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })
        return s

    def _deref(self, payload: list, val: Any, depth: int = 0) -> Any:
        """
        Nuxt3 revive 格式的解構輔助函式。
        整數 = 對 payload[n] 的引用；["ShallowReactive"|..., n] 同理。
        最多追蹤 15 層引用，避免無限迴圈。
        """
        if depth > 15:
            return val
        # int reference
        if isinstance(val, int) and 0 < val < len(payload):
            return self._deref(payload, payload[val], depth + 1)
        # Nuxt3 marker: ["ShallowReactive", n]
        if (isinstance(val, list) and len(val) == 2
                and isinstance(val[0], str) and isinstance(val[1], int)):
            return self._deref(payload, payload[val[1]], depth + 1)
        return val

    def _deref_nuxt_payload(self, payload: list) -> Dict:
        """
        解構 Nuxt3 SSR payload，回傳根物件（dict）。
        結構：payload[0] = ['ShallowReactive', 1] -> root dict 在 payload[1]
        """
        root = self._deref(payload, payload[0])
        if not isinstance(root, dict):
            return {}
        return root

    def _fetch_page(self, session: requests.Session, keyword: str,
                    area_code: str, page: int) -> tuple:
        """
        GET 搜尋頁面並解析 Nuxt3 payload，回傳 (jobs_list, total_pages)
        """
        params = {
            "ks": keyword,
            "c0": area_code,
            "page": str(page),
            "col": "ab",
            "sort": "desc",
        }
        try:
            time.sleep(self.delay + random.uniform(0, 1.5))
            r = session.get(f"{self.BASE_URL}/search/job", params=params, timeout=25)
            r.raise_for_status()
        except Exception as e:
            print(f"[1111] 第 {page} 頁請求失敗: {e}")
            return [], 0

        soup = BeautifulSoup(r.content, "lxml")
        json_tag = soup.find("script", {"type": "application/json"})
        if not json_tag:
            print(f"[1111] 第 {page} 頁未找到 JSON payload")
            return [], 0

        try:
            payload = json.loads(json_tag.get_text())
            root = self._deref_nuxt_payload(payload)

            # 逐層 deref: root.data -> apiJob -> result -> hits
            data = self._deref(payload, root.get("data"))
            if not isinstance(data, dict):
                return [], 0

            api_job_ref = data.get("apiJob")
            api_job = self._deref(payload, api_job_ref)
            if not isinstance(api_job, dict):
                return [], 0

            result_ref = api_job.get("result")
            result = self._deref(payload, result_ref)
            if not isinstance(result, dict):
                return [], 0

            hits_ref = result.get("hits")
            hits_raw = self._deref(payload, hits_ref)
            pagination_ref = result.get("pagination")
            pagination = self._deref(payload, pagination_ref)
            total_pages = 0
            if isinstance(pagination, dict):
                # pagination dict: {'page': ref, 'limit': ref, 'totalCount': ref, 'totalPage': ref}
                # Each value is itself an index into the payload
                tp_ref = pagination.get("totalPage", 0)
                tp_val = self._deref(payload, tp_ref)
                if isinstance(tp_val, int):
                    total_pages = tp_val

            # hits_raw 是 index 列表，每個 index 指向一個 job dict
            hits = []
            if isinstance(hits_raw, list):
                for ref in hits_raw:
                    job_dict = self._deref(payload, ref)
                    if isinstance(job_dict, dict):
                        # 展開每個欄位的引用
                        resolved = {
                            k: self._deref(payload, v)
                            for k, v in job_dict.items()
                        }
                        # workCity 可能是一個 dict ref
                        wc = resolved.get("workCity")
                        if isinstance(wc, dict):
                            resolved["workCity"] = self._deref(payload, wc.get("name", wc))
                        hits.append(resolved)

            return hits, int(total_pages) if total_pages else 0

        except Exception as e:
            print(f"[1111] 解析 payload 失敗 (page {page}): {e}")
            return [], 0

    def _parse_job(self, raw: Dict, keyword: str, area: str) -> Dict[str, Any]:
        """將 1111 職缺物件轉為標準格式"""
        salary_text = raw.get("salary", "面議") or "面議"
        salary_min, salary_max = self._parse_salary(salary_text)

        # workCity 可能是 dict 或 string
        work_city = raw.get("workCity", "")
        if isinstance(work_city, dict):
            work_city = work_city.get("name", "")

        # industry 可能是 list 或 dict
        industry = raw.get("industry", "")
        if isinstance(industry, list) and industry:
            industry = industry[0].get("name", "") if isinstance(industry[0], dict) else str(industry[0])
        elif isinstance(industry, dict):
            industry = industry.get("name", "")

        job_id = str(raw.get("jobId", ""))

        return {
            "source": "1111",
            "job_id": job_id,
            "title": raw.get("title", ""),
            "company": raw.get("companyName", ""),
            "company_industry": industry,
            "location": work_city,
            "salary": salary_text,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "experience": str(raw.get("require", {}).get("workYear", "")) if isinstance(raw.get("require"), dict) else "",
            "education": str(raw.get("require", {}).get("edu", "")) if isinstance(raw.get("require"), dict) else "",
            "job_description": raw.get("description", ""),
            "job_category": raw.get("role", ""),
            "search_keyword": keyword,
            "area": area,
            "url": f"{self.BASE_URL}/job/{job_id}" if job_id else "",
            "posted_date": raw.get("updateAt", ""),
            "scraped_at": datetime.now().isoformat(),
        }

    def _parse_salary(self, text: str):
        """解析薪資字串，回傳 (min, max)"""
        if not text or "面議" in text:
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
        搜尋 1111 職缺

        Args:
            keyword:   搜尋關鍵字
            area:      地區名稱 ("taichung"/"changhua"/"nantou") 或直接帶代碼
            max_pages: 最多抓幾頁（每頁 30 筆）

        Returns:
            標準化職缺列表
        """
        area_code = self.AREA_CODES.get(area, area)
        print(f"[1111] 開始搜尋: {keyword} @ {area} (area_code={area_code})")

        session = self._make_session()
        all_jobs: List[Dict[str, Any]] = []

        for page in range(1, max_pages + 1):
            hits, total_pages = self._fetch_page(session, keyword, area_code, page)
            if not hits:
                print(f"[1111] 第 {page} 頁無資料，結束")
                break
            for raw in hits:
                try:
                    all_jobs.append(self._parse_job(raw, keyword, area))
                except Exception:
                    continue
            print(f"[1111] 第 {page} 頁取得 {len(hits)} 筆（共 {total_pages} 頁）")
            if page >= total_pages:
                break

        # 去重
        seen = set()
        unique = []
        for j in all_jobs:
            if j["job_id"] not in seen:
                seen.add(j["job_id"])
                unique.append(j)

        print(f"[1111] 搜尋完成: {keyword} @ {area}，共 {len(unique)} 筆")
        return unique
