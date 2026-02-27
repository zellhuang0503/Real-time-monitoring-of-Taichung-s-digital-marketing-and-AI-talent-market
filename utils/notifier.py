"""
LINE Messaging API 通知模組
負責將自動化監控結果推播至黃老闆的 LINE
"""

import os
import requests
import json
from typing import Dict, Any

class LineNotifier:
    def __init__(self):
        # 從環境變數讀取金鑰 (Patrick 安全規範)
        self.channel_access_token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
        self.user_id = os.environ.get("LINE_USER_ID")
        self.api_url = "https://api.line.me/v2/bot/message/push"

    def send_report_notification(self, analysis_result: Dict[str, Any], week_num: int):
        """
        發送本週監控摘要與報告連結
        """
        if not self.channel_access_token or not self.user_id:
            print("[LINE] 警告：未設定 LINE Token 或 User ID，跳過通知。")
            return

        summary = analysis_result.get('summary', {})
        salary = analysis_result.get('salary_analysis', {})
        ceo_insight = analysis_result.get('ceo_strategy', {}).get('ceo_insight', '市場趨勢已更新，請查看報告。')
        
        # 建立報告連結 (假設部署在 GitHub Pages)
        report_url = f"https://zellhuang0503.github.io/Real-time-monitoring-of-Taichung-s-digital-marketing-and-AI-talent-market/history.html"

        # 組合訊息文字
        message_text = (
            f"🔔 【第 {week_num} 週 市場監控報告已產出】\n\n"
            f"📊 數據概況：\n"
            f"• 職缺總數：{summary.get('total_jobs', 0):,} 筆\n"
            f"• 薪資中位數：{salary.get('median_salary', 0):,} 元\n\n"
            f"🧠 AI 戰略洞察：\n"
            f"{ceo_insight[:100]}...\n\n"
            f"🌐 完整報告連結：\n"
            f"{report_url}"
        )

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.channel_access_token}"
        }

        payload = {
            "to": self.user_id,
            "messages": [
                {
                    "type": "text",
                    "text": message_text
                }
            ]
        }

        try:
            r = requests.post(self.api_url, headers=headers, data=json.dumps(payload), timeout=10)
            if r.status_code == 200:
                print("[LINE] 通知發送成功！")
            else:
                print(f"[LINE] 通知發送失敗，狀態碼：{r.status_code}, 回傳內容：{r.text}")
        except Exception as e:
            print(f"[LINE] 通知發送發生例外：{e}")
