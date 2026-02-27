import os
import sys
import json
from dotenv import load_dotenv

# 載入 .env 檔案
load_dotenv()

# 將當前目錄加入路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analyzer.llm_analyzer import GeminiAnalyzer
from utils.notifier import LineNotifier

def run_test():
    print("=== Patrick 的安全性與整合測試 ===")
    
    # 檢查環境變數
    google_key = os.environ.get("GOOGLE_API_KEY")
    line_token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    line_user = os.environ.get("LINE_USER_ID")
    
    if not google_key or not line_token or not line_user:
        print("❌ 錯誤：找不到環境變數。請確認您已在 taichung-job-monitor/.env 檔案中填入正確的金鑰。")
        print(f"GOOGLE_API_KEY: {'已設定' if google_key else '未設定'}")
        print(f"LINE_CHANNEL_ACCESS_TOKEN: {'已設定' if line_token else '未設定'}")
        print(f"LINE_USER_ID: {'已設定' if line_user else '未設定'}")
        return

    print("✅ 環境變數檢查通過。")

    # 構造一個假的分析結果
    dummy_analysis = {
        "summary": {
            "total_jobs": 3283
        },
        "salary_analysis": {
            "median_salary": 37500
        },
        "skill_analysis": {
            "top_skills": [{"skill": "Python", "count": 100}, {"skill": "GA4", "count": 80}]
        },
        "market_trends": {
            "social_volume": {
                "total_posts_analyzed": 50,
                "keyword_counts": {"待業": 10, "面試": 5, "焦慮": 3}
            }
        }
    }

    # 1. 測試 Gemini AI
    print("\n--- 測試 1: Gemini AI 呼叫 ---")
    try:
        gemini = GeminiAnalyzer()
        
        print("生成 CEO 戰略建議中...")
        strategy = gemini.generate_ceo_strategy(dummy_analysis)
        print("CEO 戰略建議結果：")
        print(json.dumps(strategy, ensure_ascii=False, indent=2))
        
        # 把策略放進 dummy_analysis 讓 LINE 通知用
        dummy_analysis["ceo_strategy"] = strategy
        print("✅ Gemini AI 測試成功。")
    except Exception as e:
        print(f"❌ Gemini AI 測試失敗: {e}")
        return

    # 2. 測試 LINE 通知
    print("\n--- 測試 2: LINE Messaging API 推播 ---")
    try:
        notifier = LineNotifier()
        # 測試推播 (Week 99 表示測試)
        notifier.send_report_notification(dummy_analysis, 99)
        print("✅ LINE 通知觸發完成（請檢查您的手機是否收到訊息）。")
    except Exception as e:
        print(f"❌ LINE 通知測試失敗: {e}")

if __name__ == "__main__":
    run_test()
