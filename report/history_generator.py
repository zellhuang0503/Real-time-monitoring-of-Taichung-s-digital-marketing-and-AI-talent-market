"""
歷史報告與趨勢分析生成器
生成歷史報告索引頁面與趨勢分析
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


class HistoryGenerator:
    """
    歷史報告生成器
    生成歷史報告索引與趨勢分析頁面
    """
    
    def __init__(self, report_dir: str = "report", data_dir: str = "data"):
        self.report_dir = Path(report_dir)
        self.data_dir = Path(data_dir)
    
    def generate_history_page(self) -> str:
        """
        生成歷史報告索引頁面
        
        Returns:
            HTML 檔案路徑
        """
        # 掃描所有週報告
        weekly_reports = self._scan_weekly_reports()
        
        # 讀取趨勢資料
        trend_data = self._analyze_trends(weekly_reports)
        
        # 生成 HTML
        html_content = self._generate_history_html(weekly_reports, trend_data)
        
        # 儲存檔案
        output_path = self.report_dir / "history.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"[History] 歷史報告索引已生成: {output_path}")
        return str(output_path)
    
    def _scan_weekly_reports(self) -> List[Dict]:
        """掃描所有週報告"""
        reports = []
        
        # 掃描 report 資料夾中的週報告
        pattern = re.compile(r'taichung_job_market_week(\d+)\.html')
        
        for file in self.report_dir.glob("taichung_job_market_week*.html"):
            match = pattern.match(file.name)
            if match:
                week_num = int(match.group(1))
                
                # 嘗試讀取對應的分析資料
                analysis_data = self._load_analysis_for_week(week_num)
                
                reports.append({
                    'week': week_num,
                    'file': file.name,
                    'date': analysis_data.get('report_date', 'Unknown'),
                    'total_jobs': analysis_data.get('total_jobs', 0),
                    'top_skill': analysis_data.get('top_skill', 'N/A'),
                    'median_salary': analysis_data.get('median_salary', 'N/A')
                })
        
        # 按週數排序
        reports.sort(key=lambda x: x['week'], reverse=True)
        return reports
    
    def _load_analysis_for_week(self, week_num: int) -> Dict:
        """載入特定週的分析資料"""
        # 尋找對應的分析檔案
        for file in self.data_dir.glob(f"analysis_*.json"):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data.get('summary', {}).get('week_number') == week_num:
                        return {
                            'report_date': data.get('summary', {}).get('report_date', 'Unknown'),
                            'total_jobs': data.get('summary', {}).get('total_jobs', 0),
                            'top_skill': data.get('skill_analysis', {}).get('top_skills', [{}])[0].get('skill', 'N/A'),
                            'median_salary': data.get('salary_analysis', {}).get('median_salary', 'N/A')
                        }
            except:
                continue
        return {}
    
    def _analyze_trends(self, reports: List[Dict]) -> Dict:
        """分析趨勢資料"""
        if len(reports) < 2:
            return {'has_trend': False}
        
        # 按週數排序（舊到新）
        sorted_reports = sorted(reports, key=lambda x: x['week'])
        
        # 計算職缺數趨勢
        job_counts = [r['total_jobs'] for r in sorted_reports]
        
        trend = {
            'has_trend': True,
            'weeks': [r['week'] for r in sorted_reports],
            'job_counts': job_counts,
            'job_change': job_counts[-1] - job_counts[0] if len(job_counts) >= 2 else 0,
            'job_change_percent': round(((job_counts[-1] - job_counts[0]) / job_counts[0] * 100), 1) if job_counts[0] > 0 else 0,
            'latest_week': sorted_reports[-1]['week'],
            'latest_jobs': sorted_reports[-1]['total_jobs']
        }
        
        return trend
    
    def _generate_history_html(self, reports: List[Dict], trend: Dict) -> str:
        """生成歷史報告 HTML"""
        
        # 生成報告列表 HTML
        reports_html = ""
        for report in reports:
            salary_display = f"{report['median_salary']:,}" if isinstance(report['median_salary'], int) else report['median_salary']
            
            reports_html += f"""
                <tr>
                    <td><span class="week-badge">第 {report['week']} 週</span></td>
                    <td>{report['date']}</td>
                    <td class="numeric">{report['total_jobs']:,}</td>
                    <td><span class="skill-tag">{report['top_skill']}</span></td>
                    <td class="numeric">{salary_display}</td>
                    <td>
                        <a href="{report['file']}" class="btn-view" target="_blank">
                            查看報告 →
                        </a>
                    </td>
                </tr>
            """
        
        # 生成趨勢圖表資料
        trend_chart_data = json.dumps(trend) if trend['has_trend'] else '{}'
        
        html = f'''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>歷史報告與趨勢分析 | 台中中部數位人才就業市場監控</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&family=Fira+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary: #1E40AF;
            --primary-dark: #1e3a8a;
            --primary-light: #3B82F6;
            --secondary: #3B82F6;
            --accent: #F59E0B;
            --accent-light: #fbbf24;
            --danger: #ef4444;
            --success: #10b981;
            --bg: #F8FAFC;
            --card: #ffffff;
            --text: #1e293b;
            --text-light: #64748b;
            --text-muted: #94a3b8;
            --border: #e2e8f0;
            --font-sans: 'Fira Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            --font-mono: 'Fira Code', 'Consolas', 'Monaco', monospace;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: var(--font-sans);
            background: var(--bg);
            color: var(--text);
            line-height: 1.5;
            font-size: 14px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 24px;
        }}
        
        /* Header */
        header {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            padding: 32px 28px;
            margin: -24px -24px 32px -24px;
            position: relative;
            overflow: hidden;
        }}
        
        header::before {{
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            width: 400px;
            height: 100%;
            background: linear-gradient(135deg, transparent 0%, rgba(255,255,255,0.05) 100%);
            pointer-events: none;
        }}
        
        .header-content {{
            max-width: 1400px;
            margin: 0 auto;
            position: relative;
            z-index: 1;
        }}
        
        h1 {{
            font-size: 1.75rem;
            font-weight: 600;
            margin-bottom: 8px;
            letter-spacing: -0.5px;
        }}
        
        .subtitle {{
            font-size: 1rem;
            opacity: 0.85;
            font-weight: 400;
        }}
        
        .nav-links {{
            margin-top: 20px;
            display: flex;
            gap: 16px;
        }}
        
        .nav-link {{
            color: white;
            text-decoration: none;
            padding: 8px 16px;
            background: rgba(255,255,255,0.15);
            border-radius: 6px;
            font-size: 0.9rem;
            transition: background 0.2s;
        }}
        
        .nav-link:hover {{
            background: rgba(255,255,255,0.25);
        }}
        
        /* Stats Grid */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 32px;
        }}
        
        @media (max-width: 992px) {{
            .stats-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
        
        @media (max-width: 576px) {{
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
        }}
        
        .stat-card {{
            background: var(--card);
            border-radius: 8px;
            border: 1px solid var(--border);
            padding: 20px;
            text-align: center;
        }}
        
        .stat-value {{
            font-family: var(--font-mono);
            font-size: 2rem;
            font-weight: 600;
            color: var(--primary);
            margin-bottom: 4px;
        }}
        
        .stat-value.trend-up {{
            color: var(--success);
        }}
        
        .stat-value.trend-down {{
            color: var(--danger);
        }}
        
        .stat-label {{
            font-size: 0.85rem;
            color: var(--text-light);
        }}
        
        /* Chart Section */
        .chart-section {{
            background: var(--card);
            border-radius: 8px;
            border: 1px solid var(--border);
            padding: 24px;
            margin-bottom: 32px;
        }}
        
        .chart-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }}
        
        .chart-title {{
            font-size: 1.1rem;
            font-weight: 600;
        }}
        
        .chart-container {{
            height: 350px;
            position: relative;
        }}
        
        /* Table Section */
        .table-section {{
            background: var(--card);
            border-radius: 8px;
            border: 1px solid var(--border);
            overflow: hidden;
        }}
        
        .table-header {{
            padding: 20px 24px;
            border-bottom: 1px solid var(--border);
            background: linear-gradient(to bottom, #fafbfc, var(--card));
        }}
        
        .table-title {{
            font-size: 1.1rem;
            font-weight: 600;
        }}
        
        .table-container {{
            overflow-x: auto;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }}
        
        thead {{
            background: var(--bg);
        }}
        
        th {{
            text-align: left;
            padding: 14px 24px;
            font-weight: 600;
            color: var(--text-light);
            text-transform: uppercase;
            font-size: 0.7rem;
            letter-spacing: 0.5px;
            border-bottom: 1px solid var(--border);
            white-space: nowrap;
        }}
        
        td {{
            padding: 16px 24px;
            border-bottom: 1px solid var(--border-light);
        }}
        
        tr:hover {{
            background: var(--bg);
        }}
        
        tr:last-child td {{
            border-bottom: none;
        }}
        
        .numeric {{
            font-family: var(--font-mono);
            text-align: right;
        }}
        
        .week-badge {{
            background: var(--primary);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
        }}
        
        .skill-tag {{
            font-family: var(--font-mono);
            font-size: 0.8rem;
            padding: 4px 10px;
            border-radius: 4px;
            background: rgba(30, 64, 175, 0.08);
            color: var(--primary);
        }}
        
        .btn-view {{
            display: inline-block;
            padding: 6px 16px;
            background: var(--primary);
            color: white;
            text-decoration: none;
            border-radius: 4px;
            font-size: 0.85rem;
            transition: background 0.2s;
        }}
        
        .btn-view:hover {{
            background: var(--primary-dark);
        }}
        
        /* Footer */
        footer {{
            text-align: center;
            padding: 32px;
            color: var(--text-muted);
            font-size: 0.8rem;
            border-top: 1px solid var(--border);
            margin-top: 40px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="header-content">
                <h1>📈 歷史報告與趨勢分析</h1>
                <div class="subtitle">台中中部數位人才就業市場長期追蹤</div>
                <div class="nav-links">
                    <a href="index.html" class="nav-link">← 回到最新報告</a>
                    <a href="taichung_job_market_week{trend['latest_week'] if trend['has_trend'] else '1'}.html" class="nav-link">最新週報告</a>
                </div>
            </div>
        </header>
        
        <!-- Stats Summary -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{len(reports)}</div>
                <div class="stat-label">累計週數</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{trend['latest_jobs']:, if trend['has_trend'] else 'N/A'}</div>
                <div class="stat-label">最新職缺數</div>
            </div>
            <div class="stat-card">
                <div class="stat-value {'trend-up' if trend['job_change'] > 0 else 'trend-down' if trend['job_change'] < 0 else ''}">{trend['job_change_percent']:+}% if trend['has_trend'] else 'N/A'</div>
                <div class="stat-label">職缺數變化（累計）</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{trend['latest_week'] if trend['has_trend'] else 'N/A'}</div>
                <div class="stat-label">當前週次</div>
            </div>
        </div>
        
        <!-- Trend Chart -->
        <div class="chart-section">
            <div class="chart-header">
                <div class="chart-title">📊 職缺數量趨勢</div>
            </div>
            <div class="chart-container">
                <canvas id="trendChart"></canvas>
            </div>
        </div>
        
        <!-- History Table -->
        <div class="table-section">
            <div class="table-header">
                <div class="table-title">📋 歷史報告列表</div>
            </div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>週次</th>
                            <th>報告日期</th>
                            <th class="numeric">職缺總數</th>
                            <th>熱門技能</th>
                            <th class="numeric">中位數薪資</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody>
                        {reports_html}
                    </tbody>
                </table>
            </div>
        </div>
        
        <footer>
            <p><strong>梵亞行銷 | 台中教育大學新尖兵計畫</strong></p>
            <p>本報告由自動化監控系統生成 | 資料來源：104人力銀行、1111人力銀行、518人力銀行</p>
        </footer>
    </div>
    
    <script>
        // 趨勢圖表
        const trendData = {trend_chart_data};
        
        if (trendData.has_trend && trendData.weeks.length > 1) {{
            new Chart(document.getElementById('trendChart'), {{
                type: 'line',
                data: {{
                    labels: trendData.weeks.map(w => `第 ${{w}} 週`),
                    datasets: [{{
                        label: '職缺總數',
                        data: trendData.job_counts,
                        borderColor: '#1E40AF',
                        backgroundColor: 'rgba(30, 64, 175, 0.1)',
                        borderWidth: 3,
                        pointRadius: 6,
                        pointBackgroundColor: '#1E40AF',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2,
                        tension: 0.3,
                        fill: true
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{ display: false }},
                        tooltip: {{
                            backgroundColor: 'rgba(30, 41, 59, 0.95)',
                            padding: 12,
                            callbacks: {{
                                label: function(context) {{
                                    return `職缺數: ${{context.raw.toLocaleString()}}`;
                                }}
                            }}
                        }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            grid: {{ color: '#f1f5f9' }},
                            ticks: {{
                                font: {{ family: 'Fira Code', size: 11 }},
                                callback: function(value) {{
                                    return value.toLocaleString();
                                }}
                            }}
                        }},
                        x: {{
                            grid: {{ display: false }},
                            ticks: {{
                                font: {{ family: 'Fira Sans', size: 12 }}
                            }}
                        }}
                    }}
                }}
            }});
        }} else {{
            document.getElementById('trendChart').parentElement.innerHTML = 
                '<div style="display: flex; justify-content: center; align-items: center; height: 100%; color: var(--text-muted);">
                    <p>📊 資料累積中，需要至少 2 週數據才能顯示趨勢圖</p>
                </div>';
        }}
    </script>
</body>
</html>'''
        
        return html


if __name__ == "__main__":
    # 測試生成
    generator = HistoryGenerator()
    generator.generate_history_page()
