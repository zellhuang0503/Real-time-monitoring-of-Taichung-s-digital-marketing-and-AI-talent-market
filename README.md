# 台中中部數位人才就業市場監控系統

> 為台中教育大學新尖兵計畫打造的即時就業市場分析工具

[![Weekly Monitor](https://github.com/[your-username]/taichung-job-monitor/actions/workflows/weekly-monitor.yml/badge.svg)](https://github.com/[your-username]/taichung-job-monitor/actions/workflows/weekly-monitor.yml)

---

## 系統概述

本系統自動監控台中、彰化、南投三地區的數位行銷與 AI 應用人才需求，為新尖兵計畫課程規劃提供數據驅動的決策支持。

### 核心功能

- **自動資料收集**: 每週自動從 104、1111、518 等人力銀行抓取職缺資料
- **智能分析引擎**: 萃取技能需求、分析薪資分布、識別趨勢變化
- **課程建議生成**: 基於市場數據自動產出課程調整建議
- **互動式報告**: 單一 HTML 檔案儀表板，內嵌 Chart.js 圖表
- **歷史趨勢追蹤**: 累積多週資料，支援跨期比較分析

---

## 監控範圍

### 地理區域
- 台中市
- 彰化縣
- 南投縣

### 人才類別
1. **數位行銷**: SEO、SEM、社群經營、內容行銷、電商營運
2. **AI 應用**: ChatGPT、Prompt Engineering、自動化、生成式 AI
3. **前端開發**: React、Vue、JavaScript、UI/UX
4. **後端開發**: Python、Node.js、資料庫、API
5. **數據分析**: Power BI、Google Analytics、SQL、商業分析
6. **設計影音**: Figma、Photoshop、影音剪輯

---

## 技術架構

```
┌─────────────────────────────────────────────────────────┐
│                    GitHub Actions                        │
│              (每週一早上 9 點自動執行)                    │
└─────────────────────────┬───────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
   ┌─────────┐      ┌──────────┐      ┌──────────┐
   │  104    │      │   1111   │      │   518    │
   │  API    │      │  爬蟲    │      │  爬蟲    │
   └────┬────┘      └────┬─────┘      └────┬─────┘
        │                │                 │
        └────────────────┼─────────────────┘
                         ▼
            ┌──────────────────────┐
            │    Python 分析引擎    │
            │  • 技能萃取 (NLP)     │
            │  • 薪資統計分析       │
            │  • 趨勢比較          │
            └──────────┬───────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │  課程建議引擎         │
            │  • 數據驅動建議      │
            │  • 課程比重調整      │
            └──────────┬───────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │  HTML 報告生成器      │
            │  • Chart.js 圖表     │
            │  • 互動式儀表板      │
            └──────────┬───────────┘
                       │
                       ▼
              ┌────────────────┐
              │  GitHub Pages  │
              │  自動部署報告   │
              └────────────────┘
```

---

## 安裝與使用

### 本地開發環境

```bash
# 1. 複製專案
git clone [repository-url]
cd taichung-job-monitor

# 2. 建立虛擬環境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安裝相依套件
pip install -r requirements.txt

# 4. 執行測試模式
python main.py --test

# 5. 執行完整收集
python main.py
```

### 參數說明

```bash
python main.py [options]

Options:
  --test          測試模式，只爬取少量資料
  --skip-scrape   跳過爬蟲，使用現有資料重新生成報告
```

---

## 輸出檔案

執行後會產生以下檔案：

```
taichung-job-monitor/
├── data/
│   ├── jobs_YYYYMMDD_HHMMSS.json       # 原始職缺資料
│   ├── analysis_YYYYMMDD_HHMMSS.json   # 分析結果
│   └── history/                        # 歷史資料備份
├── report/
│   ├── index.html                      # 最新報告
│   └── taichung_job_market_weekN.html  # 各週報告
└── .github/
    └── workflows/
        └── weekly-monitor.yml          # 自動化配置
```

---

## 報告內容

HTML 報告包含以下區塊：

### 📊 執行摘要
- 監控範圍內總職缺數
- 市場中位數薪資
- 接受新人職缺比例
- 本週核心洞察

### 💡 課程調整建議
- 高優先級調整項目
- 原因分析與行動建議

### 🔧 技能需求分析
- Top 15 熱門技能排行（長條圖）
- 必備技能清單
- 加分技能清單
- 技能組合分析

### 💰 薪資市場分析
- 薪資區間分布（甜甜圈圖）
- 經驗要求分布（圓餅圖）
- 高薪技能排行表格

### 📈 職缺類別分布
- 各領域職缺數量（長條圖）
- 熱門技能組合（橫條圖）
- 產業別分布表格

---

## 自動化部署

### GitHub Actions 配置

系統已配置 `.github/workflows/weekly-monitor.yml`，會：

1. **每週一早上 9 點自動執行**
2. **手動觸發**: 可在 Actions 頁面點擊 "Run workflow"
3. **自動部署**: 報告會自動部署到 GitHub Pages
4. **資料備份**: 所有資料會保存為 Artifact（保留 90 天）

### 啟用 GitHub Pages

1. 前往專案 Settings → Pages
2. Source 選擇 "Deploy from a branch"
3. Branch 選擇 "gh-pages"
4. 儲存後等待部署完成
5. 報告將顯示在: `https://[your-username].github.io/taichung-job-monitor/`

---

## 專案結構

```
taichung-job-monitor/
├── config.py                    # 配置文件
├── main.py                      # 主執行腳本
├── requirements.txt             # Python 相依套件
├── README.md                    # 本文件
│
├── scrapers/                    # 爬蟲模組
│   ├── __init__.py
│   ├── base_scraper.py         # 基礎爬蟲類別
│   ├── scraper_104.py          # 104 人力銀行
│   ├── scraper_1111.py         # 1111 人力銀行
│   └── scraper_518.py          # 518 人力銀行
│
├── analyzer/                    # 分析模組
│   ├── __init__.py
│   ├── job_analyzer.py         # 主分析器
│   ├── skill_extractor.py      # 技能萃取
│   ├── salary_analyzer.py      # 薪資分析
│   └── course_recommender.py   # 課程建議
│
├── report/                      # 報告生成
│   ├── __init__.py
│   └── html_report_generator.py # HTML 報告產生器
│
├── data/                        # 資料目錄（自動建立）
│   └── history/                # 歷史資料
│
├── report/                      # 報告輸出（自動建立）
│
└── .github/
    └── workflows/
        └── weekly-monitor.yml  # 自動化工作流
```

---

## 注意事項

### 爬蟲禮儀
- 所有爬蟲皆設定 2-3 秒請求間隔，避免對目標網站造成負擔
- 使用隨機 User-Agent 降低被封鎖風險
- 僅收集公開職缺資料，不收集個人資訊

### 資料限制
- 104 人力銀行有公開 API，資料最穩定
- 1111 與 518 使用網頁爬蟲，可能因網站改版失效
- 薪資資料約 60-70% 的職缺會標示，部分為「面議」

### 隱私聲明
- 本系統僅收集公開職缺資訊
- 不收集任何個人可識別資訊
- 資料僅用於課程規劃參考

---

## 開發者

**梵亞行銷** - 為台中教育大學新尖兵計畫開發

如有問題或建議，歡迎提交 Issue。

---

## License

MIT License

---

## 更新日誌

### v1.0.0 (2026-02-24)
- 初始版本發布
- 支援 104、1111、518 三大平台
- 自動化週報生成
- GitHub Actions 自動部署
