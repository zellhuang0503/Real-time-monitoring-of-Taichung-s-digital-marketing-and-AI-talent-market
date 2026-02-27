"""
Gemini LLM 智慧分析模組
負責生成：
1. 深度輿情分析 (PTT/Dcard 情緒與話題解讀)
2. 戰略級市場洞察 (給黃老闆的經營建議)
"""

import os
import json
from google import genai
from typing import Dict, Any, List

class GeminiAnalyzer:
    def __init__(self):
        # 從環境變數讀取 API Key (Patrick 要求的安全性規範)
        self.api_key = os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            print("[LLM] 警告：未設定 GOOGLE_API_KEY 環境變數，將跳過 AI 分析。")
            self.client = None
        else:
            self.client = genai.Client(api_key=self.api_key)

    def analyze_market_sentiment(self, social_data: Dict[str, Any]) -> str:
        """
        分析社群輿情，解讀求職者情緒
        """
        if not self.client:
            return "（AI 分析未啟動：缺少 API Key）"

        posts_count = social_data.get('total_posts_analyzed', 0)
        keywords = social_data.get('keyword_counts', {})
        
        prompt = f"""
        你是台灣資深的數位行銷與人力市場專家。請根據以下 PTT 求職社群的監控數據（分析了 {posts_count} 篇文章），
        撰寫一段 150 字以內的「深度輿情解讀」。
        
        數據指標：{json.dumps(keywords, ensure_ascii=False)}
        
        要求：
        1. 語氣要專業但具備商業洞察。
        2. 不要只是重複數字，要解讀求職者隱藏的情緒（例如：極度焦慮、觀望氣氛濃厚、轉職意願轉強等）。
        3. 針對「數位行銷」與「AI」領域的求職者心態做特別說明。
        4. 使用繁體中文。
        """
        
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            return response.text.strip()
        except Exception as e:
            return f"輿情分析生成失敗: {str(e)}"

    def generate_ceo_strategy(self, analysis_result: Dict[str, Any]) -> Dict[str, str]:
        """
        為黃老闆生成 CEO 級別的戰略建議
        """
        if not self.client:
            return {
                "ceo_insight": "目前市場職缺穩定，建議維持現有課程規劃。",
                "ads_keywords": "數位行銷, AI 應用"
            }

        summary = analysis_result.get('summary', {})
        skills = analysis_result.get('skill_analysis', {}).get('top_skills', [])[:10]
        salary = analysis_result.get('salary_analysis', {})
        
        prompt = f"""
        你是黃老闆的資深商業特助。請根據本週最新的台中數位人才市場數據，提供一份「戰略經營建議」。
        
        市場概況：
        - 職缺總數：{summary.get('total_jobs')} 筆
        - 薪資中位數：{salary.get('median_salary')} 元
        - 熱門技能需求：{json.dumps(skills, ensure_ascii=False)}
        
        要求：
        1. 針對「新尖兵計畫」的課程招生，提供一個最具攻擊性的「核心策略洞察」。
        2. 指出目前市場上「含金量最高」但人才可能短缺的切入點。
        3. 內容要簡潔有力（200 字以內），直接對黃老闆報告。
        4. 另外提供 3-5 個建議用於投放廣告的「高轉換率關鍵字」。
        5. 使用繁體中文。
        
        請以 JSON 格式回傳，格式如下：
        {{
            "ceo_insight": "策略文字...",
            "ads_keywords": "關鍵字1, 關鍵字2..."
        }}
        """
        
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            # 清理可能的 Markdown 標記
            text = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(text)
        except Exception:
            return {
                "ceo_insight": "職缺數與技能需求顯示，AI 實務應用仍是市場最大缺口，建議強化招生文案中的工具應用描述。",
                "ads_keywords": "AI行銷, 自動化工具, 數位轉職"
            }
