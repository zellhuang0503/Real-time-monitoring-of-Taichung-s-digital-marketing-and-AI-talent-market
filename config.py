# 台中中部就業市場監控系統 - 配置文件
# 作者：梵亞行銷

from datetime import datetime

# 版本資訊
VERSION = "1.0.0"
PROJECT_NAME = "台中中部數位人才就業市場監控系統"

# 監控地區設定（台中、彰化、南投）
MONITORING_AREAS = {
    "6001008000": "台中市",  # 104 地區代碼
    "6001010000": "彰化縣",
    "6001011000": "南投縣",
}

# 關鍵字矩陣 - 數位人才類別
JOB_KEYWORDS = {
    "數位行銷": [
        "數位行銷", "社群行銷", "社群媒體", "SEO", "SEM", "Google Ads", 
        "Meta 廣告", "Facebook 廣告", "內容行銷", "電商營運", "網路行銷",
        "KOL", "網紅行銷", "數位廣告", "品牌行銷"
    ],
    "AI應用": [
        "AI", "人工智慧", "ChatGPT", "Prompt", "LLM", "生成式 AI", 
        "AI 行銷", "機器學習", "自動化", "AI 工具", "AIGC", "No-Code"
    ],
    "前端開發": [
        "前端", "Frontend", "React", "Vue", "Angular", "JavaScript", 
        "TypeScript", "HTML", "CSS", "UI/UX", "網頁設計"
    ],
    "後端開發": [
        "後端", "Backend", "Python", "Node.js", "Java", "PHP", 
        "API", "資料庫", "SQL", "MySQL", "MongoDB"
    ],
    "數據分析": [
        "資料分析", "數據分析", "Power BI", "Google Analytics", 
        "GA4", "Excel", "SQL", "大數據", "商業分析", "Data Analyst"
    ],
    "設計影音": [
        "平面設計", "UI 設計", "UX 設計", "Figma", "Adobe", 
        "Photoshop", "Illustrator", "影音剪輯", "影片製作", "攝影"
    ]
}

# 技能關鍵字映射（用於從職缺描述中提取技能）
SKILL_KEYWORDS = {
    # 行銷工具
    "GA4": ["Google Analytics 4", "GA4", "Google Analytics"],
    "Google Ads": ["Google Ads", "Google AdWords", "關鍵字廣告"],
    "Meta Ads": ["Meta Ads", "Facebook Ads", "Instagram Ads", "FB 廣告", "IG 廣告"],
    "SEO": ["SEO", "搜尋引擎優化"],
    "WordPress": ["WordPress", "WP"],
    "Shopify": ["Shopify"],
    "蝦皮": ["蝦皮", "Shopee"],
    
    # AI 工具
    "ChatGPT": ["ChatGPT", "GPT", "OpenAI"],
    "Midjourney": ["Midjourney"],
    "Copilot": ["Copilot", "GitHub Copilot"],
    "Claude": ["Claude"],
    
    # 開發語言
    "Python": ["Python"],
    "JavaScript": ["JavaScript", "JS"],
    "TypeScript": ["TypeScript", "TS"],
    "HTML/CSS": ["HTML", "CSS"],
    "React": ["React", "React.js"],
    "Vue": ["Vue", "Vue.js"],
    "Node.js": ["Node.js", "Nodejs"],
    
    # 數據工具
    "Excel": ["Excel"],
    "Power BI": ["Power BI"],
    "SQL": ["SQL", "MySQL", "PostgreSQL"],
    
    # 設計工具
    "Figma": ["Figma"],
    "Photoshop": ["Photoshop", "PS"],
    "Illustrator": ["Illustrator", "AI", "Ai 繪圖"],
    "Canva": ["Canva"],
    "Premiere": ["Premiere", "PR"],
    "After Effects": ["After Effects", "AE"],
}

# 薪資解析規則
SALARY_PATTERNS = {
    "月薪": r"月薪\s*([\d,]+)\s*至?\s*([\d,]+)?",
    "年薪": r"年薪\s*([\d,]+)\s*至?\s*([\d,]+)?",
    "時薪": r"時薪\s*([\d,]+)\s*至?\s*([\d,]+)?",
    "面議": r"面議",
}

# 輸出設定
OUTPUT_CONFIG = {
    "report_filename": f"taichung_job_market_report_{datetime.now().strftime('%Y%m%d')}.html",
    "data_dir": "data",
    "history_dir": "data/history",
    "report_dir": "report",
}

# 爬蟲設定
SCRAPER_CONFIG = {
    "request_delay": 2,  # 請求間隔秒數
    "max_retries": 3,    # 最大重試次數
    "timeout": 30,       # 請求超時秒數
    "user_agent_rotation": True,
}

# 課程建議設定
COURSE_SUGGESTIONS = {
    "high_demand_threshold": 50,  # 職缺數超過此值視為高需求
    "skill_gap_threshold": 0.3,   # 技能缺口閾值
    "salary_premium_threshold": 35000,  # 高薪門檻
}

# 104 產業別代碼對照表（產業別代碼 → 中文產業名稱）
# 資料來源：104人力銀行產業分類
INDUSTRY_CODE_MAPPING = {
    # 資訊科技
    "1001001001": "電腦軟體",
    "1001001002": "網路相關",
    "1001001003": "電子商務",
    "1001001006": "電信相關",
    
    # 電子/半導體
    "1002001010": "半導體",
    "1002015002": "電子零組件",
    
    # 金融/保險
    "1003001015": "銀行",
    "1003002016": "投資理財",
    "1003003013": "保險",
    
    # 製造業
    "1006003001": "電子製造",
    "1008003001": "機械設備",
    
    # 服務業
    "1011004001": "百貨相關",
    "1012001001": "餐飲業",
    "1016001001": "教育服務",
    "1016002001": "醫療服務",
    
    # 其他常見
    "1001003003": "數位內容",
    "1001003005": "資訊服務",
    "1003001001": "金融控股",
}

# 目標受眾設定（新尖兵計畫學員特徵）
TARGET_AUDIENCE = {
    "typical_experience": "fresh_graduate",  # 應屆畢業生/轉職者
    "preferred_job_types": ["junior", "associate", "entry_level"],
    "focus_areas": ["數位行銷", "AI應用", "數據分析"],
}
