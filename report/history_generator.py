"""
歷史報告與趨勢分析生成器 - Oliver 溫暖風格版
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


class HistoryGenerator:
    def __init__(self, report_dir: str = "report", data_dir: str = "data"):
        self.report_dir = Path(report_dir)
        self.data_dir = Path(data_dir)

    def generate_history_page(self) -> str:
        reports = self._build_reports()
        trend_data = self._analyze_trends(reports)
        html = self._render_html(reports, trend_data)

        out = self.report_dir / "history.html"
        with open(out, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"[History] 歷史報告索引已生成: {out}")
        return str(out)

    # ------------------------------------------------------------------ #
    # 資料讀取：analysis JSON 按時間排序，依序對應週次
    # ------------------------------------------------------------------ #
    def _build_reports(self) -> List[Dict]:
        """
        Week <10 = 測試期（對應 104-only 舊檔）
        Week 10+ = 正式期（各週對應各自的完整分析檔）
        """
        # 取得所有分析 JSON，過濾掉中間除錯產生的備份（215115, 215309）
        all_files = sorted(self.data_dir.glob("analysis_*.json"))
        analysis_files = [
            f for f in all_files
            if '215115' not in f.name and '215309' not in f.name
        ]

        # 分離測試期檔案（02/26 之前）和正式期檔案（02/26 及之後）
        test_files = [f for f in analysis_files if f.name < 'analysis_20260226']
        official_files = [f for f in analysis_files if f.name >= 'analysis_20260226']

        # 取得所有週報告 HTML
        week_pattern = re.compile(r'taichung_job_market_week(\d+)\.html')
        week_files: Dict[int, str] = {}
        for f in self.report_dir.glob("taichung_job_market_week*.html"):
            m = week_pattern.match(f.name)
            if m:
                week_files[int(m.group(1))] = f.name
        sorted_weeks = sorted(week_files.keys())

        # 分離測試週和正式週
        test_weeks = [w for w in sorted_weeks if w < 10]
        official_weeks = [w for w in sorted_weeks if w >= 10]

        reports = []
        for i, week_num in enumerate(sorted_weeks):
            is_test = week_num < 10

            # 週次對應分析檔：測試期用舊檔，正式期各週對應各自的檔案
            if is_test:
                test_idx = test_weeks.index(week_num)
                af = test_files[test_idx] if test_idx < len(test_files) else (test_files[-1] if test_files else None)
            else:
                official_idx = official_weeks.index(week_num)
                af = official_files[official_idx] if official_idx < len(official_files) else (official_files[-1] if official_files else None)

            analysis: Dict = {}
            if af:
                try:
                    with open(af, 'r', encoding='utf-8') as fp:
                        raw = json.load(fp)
                    summary = raw.get('summary', {})
                    top_skills = raw.get('skill_analysis', {}).get('top_skills', [])
                    top_skill = top_skills[0].get('skill', 'N/A') if top_skills else 'N/A'
                    median_salary = raw.get('salary_analysis', {}).get('median_salary')

                    date_str = af.name.split('_')[1]
                    try:
                        report_date = datetime.strptime(date_str, '%Y%m%d').strftime('%Y/%m/%d')
                    except Exception:
                        report_date = date_str

                    analysis = {
                        'total_jobs': summary.get('total_jobs', 0),
                        'top_skill': top_skill,
                        'median_salary': median_salary,
                        'report_date': report_date,
                        'sources': summary.get('sources_distribution', {}),
                        'is_test': is_test,
                    }
                except Exception:
                    pass

            reports.append({
                'week': week_num,
                'file': week_files[week_num],
                'date': analysis.get('report_date', '待更新'),
                'total_jobs': analysis.get('total_jobs', 0),
                'top_skill': analysis.get('top_skill', 'N/A'),
                'median_salary': analysis.get('median_salary', 'N/A'),
                'sources': analysis.get('sources', {}),
                'is_test': analysis.get('is_test', is_test),
            })

        # 最新的排在前面
        reports.sort(key=lambda x: x['week'], reverse=True)
        return reports

    def _analyze_trends(self, reports: List[Dict]) -> Dict:
        sorted_r = sorted(reports, key=lambda x: x['week'])
        counts = [r['total_jobs'] for r in sorted_r]
        weeks = [r['week'] for r in sorted_r]
        dates = [r['date'] for r in sorted_r]

        if len(sorted_r) < 2:
            return {
                'has_trend': False,
                'weeks': weeks,
                'job_counts': counts,
                'dates': dates,
            }

        change = counts[-1] - counts[0]
        change_pct = round((change / counts[0] * 100), 1) if counts[0] > 0 else 0

        return {
            'has_trend': True,
            'weeks': weeks,
            'job_counts': counts,
            'dates': dates,
            'job_change': change,
            'job_change_pct': change_pct,
            'latest_week': sorted_r[-1]['week'],
            'latest_jobs': sorted_r[-1]['total_jobs'],
        }

    # ------------------------------------------------------------------ #
    # HTML 渲染 — Oliver 溫暖風格
    # ------------------------------------------------------------------ #
    def _render_html(self, reports: List[Dict], trend: Dict) -> str:
        rows_html = ""
        for r in reports:
            salary_disp = f"{r['median_salary']:,}" if isinstance(r['median_salary'], (int, float)) else (r['median_salary'] or '—')
            total_jobs_disp = f"{r['total_jobs']:,}" if r['total_jobs'] else '0'
            is_test = r.get('is_test', r['week'] < 10)
            period_badge = (
                '<span style="background:#FEF3C7;color:#92400E;padding:2px 8px;border-radius:8px;'
                'font-size:0.75rem;font-weight:700;margin-left:6px;">測試期</span>'
                if is_test else
                '<span style="background:#D1FAE5;color:#065F46;padding:2px 8px;border-radius:8px;'
                'font-size:0.75rem;font-weight:700;margin-left:6px;">正式</span>'
            )
            # 測試期薪資顯示為不適用
            if is_test:
                salary_disp = '<span style="color:var(--text-muted);font-size:0.85rem;">僅104，無薪資</span>'
            rows_html += f"""
                <tr {'style="opacity:0.7;"' if is_test else ''}>
                    <td><span class="week-badge">第 {r['week']} 週</span>{period_badge}</td>
                    <td>{r['date']}</td>
                    <td class="num">{total_jobs_disp}</td>
                    <td><span class="skill-tag">{r['top_skill']}</span></td>
                    <td class="num">{salary_disp}</td>
                    <td><a href="{r['file']}" class="btn-view" target="_blank">查看報告 →</a></td>
                </tr>"""

        latest_week = trend.get('latest_week', 'N/A')
        latest_jobs = f"{trend['latest_jobs']:,}" if trend.get('has_trend') else 'N/A'
        change_pct = f"{trend['job_change_pct']:+.1f}%" if trend.get('has_trend') else 'N/A'
        change_class = ''
        if trend.get('has_trend'):
            change_class = 'up' if trend['job_change'] > 0 else ('down' if trend['job_change'] < 0 else '')

        trend_json = json.dumps(trend)

        return f'''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>歷史趨勢 | 台中數位人才市場監控</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&family=Noto+Sans+TC:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary: #F07167;
            --primary-dark: #E05D53;
            --primary-light: #F8AD9D;
            --secondary: #F4A261;
            --accent: #2A9D8F;
            --danger: #E76F51;
            --success: #2A9D8F;
            --bg: #FFFDF9;
            --card: #ffffff;
            --text: #4A403A;
            --text-light: #8A7E78;
            --text-muted: #BDB5B1;
            --border: #F3EAE3;
            --border-light: #FAF5F0;
            --font: 'Nunito', 'Noto Sans TC', sans-serif;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: var(--font); background: var(--bg); color: var(--text); font-size: 15px; line-height: 1.6; }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 30px; }}

        /* Header */
        header {{
            background: linear-gradient(135deg, #FFDAB9 0%, #F8AD9D 100%);
            border-radius: 24px;
            padding: 40px 32px;
            margin-bottom: 40px;
            position: relative;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(240,113,103,.1);
        }}
        header::after {{
            content: '📈';
            position: absolute; top: -20px; right: 20px;
            font-size: 120px; opacity: .13; transform: rotate(10deg);
            pointer-events: none;
        }}
        header h1 {{ font-size: 2rem; font-weight: 800; color: #3D332D; margin-bottom: 8px; }}
        header .sub {{ font-size: 1rem; color: #5C4D45; font-weight: 500; margin-bottom: 20px; }}
        .nav-pills {{ display: flex; gap: 12px; flex-wrap: wrap; }}
        .nav-pill {{
            color: #5C4D45; text-decoration: none;
            padding: 8px 18px;
            background: rgba(255,255,255,.45); border-radius: 20px;
            font-weight: 700; font-size: 0.9rem;
            transition: background .2s;
        }}
        .nav-pill:hover {{ background: rgba(255,255,255,.7); }}

        /* KPI row */
        .kpi-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 36px; }}
        @media(max-width:900px) {{ .kpi-grid {{ grid-template-columns: repeat(2,1fr); }} }}
        @media(max-width:500px) {{ .kpi-grid {{ grid-template-columns: 1fr; }} }}

        .kpi-card {{
            background: var(--card); border-radius: 20px;
            border: 1px solid var(--border);
            padding: 24px; text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,.02);
            transition: transform .2s, box-shadow .2s;
        }}
        .kpi-card:hover {{ transform: translateY(-3px); box-shadow: 0 8px 25px rgba(240,113,103,.08); }}
        .kpi-icon {{ font-size: 2rem; margin-bottom: 10px; }}
        .kpi-value {{ font-size: 2.2rem; font-weight: 800; color: var(--text); margin-bottom: 4px; }}
        .kpi-value.up {{ color: var(--danger); }}
        .kpi-value.down {{ color: var(--accent); }}
        .kpi-label {{ font-size: 0.85rem; color: var(--text-light); font-weight: 600; }}

        /* Chart card */
        .card {{
            background: var(--card); border-radius: 20px;
            border: 1px solid var(--border);
            box-shadow: 0 4px 15px rgba(0,0,0,.02);
            overflow: hidden; margin-bottom: 28px;
        }}
        .card-header {{
            display: flex; align-items: center; justify-content: space-between;
            padding: 20px 26px; border-bottom: 1px dashed var(--border);
        }}
        .card-title {{ font-size: 1.05rem; font-weight: 700; color: var(--text); }}
        .badge {{
            font-size: 0.75rem; font-weight: 700; padding: 4px 12px;
            border-radius: 20px; background: var(--primary-light); color: #fff;
        }}
        .card-body {{ padding: 26px; }}
        .chart-wrap {{ height: 320px; position: relative; }}

        /* Table */
        .table-wrap {{ overflow-x: auto; }}
        table {{ width: 100%; border-collapse: separate; border-spacing: 0; font-size: .95rem; }}
        thead {{ background: var(--bg); }}
        th {{ padding: 16px 20px; font-weight: 700; color: var(--text-light); border-bottom: 2px solid var(--border); white-space: nowrap; text-align: left; }}
        td {{ padding: 16px 20px; border-bottom: 1px solid var(--border-light); }}
        tr:hover td {{ background: var(--bg); }}
        tr:last-child td {{ border-bottom: none; }}
        .num {{ text-align: right; font-weight: 700; }}
        .week-badge {{
            background: var(--primary); color: #fff;
            padding: 4px 12px; border-radius: 20px; font-size: .85rem; font-weight: 700;
        }}
        .skill-tag {{
            background: #FEF3C7; color: #D97706;
            padding: 4px 10px; border-radius: 12px; font-size: .85rem; font-weight: 600;
        }}
        .btn-view {{
            display: inline-block; padding: 6px 16px;
            background: var(--primary); color: #fff;
            text-decoration: none; border-radius: 12px;
            font-size: .85rem; font-weight: 700;
            transition: background .2s, transform .15s;
        }}
        .btn-view:hover {{ background: var(--primary-dark); transform: translateX(2px); }}

        /* Empty state */
        .empty-chart {{
            display: flex; justify-content: center; align-items: center;
            height: 320px; color: var(--text-muted); font-size: 1rem; font-weight: 600;
        }}

        footer {{ text-align: center; padding: 40px 0 20px; color: var(--text-muted); font-size: .88rem; }}
        footer p {{ margin: 4px 0; }}
    </style>
</head>
<body>
<div class="container">

    <header>
        <h1>歷史趨勢報告</h1>
        <div class="sub">台中中部數位人才就業市場 — 長期追蹤分析</div>
        <div class="nav-pills">
            <a href="index.html" class="nav-pill">← 回到最新報告</a>
            <a href="taichung_job_market_week{latest_week}.html" class="nav-pill">最新週報告</a>
        </div>
    </header>

    <!-- KPI -->
    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-icon">📅</div>
            <div class="kpi-value">{len(reports)}</div>
            <div class="kpi-label">累計週數</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">💼</div>
            <div class="kpi-value">{latest_jobs}</div>
            <div class="kpi-label">最新職缺數</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">📊</div>
            <div class="kpi-value {change_class}">{change_pct}</div>
            <div class="kpi-label">職缺數累計變化</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">🗓️</div>
            <div class="kpi-value">{latest_week}</div>
            <div class="kpi-label">當前週次</div>
        </div>
    </div>

    <!-- Trend Chart -->
    <div class="card">
        <div class="card-header">
            <div class="card-title">職缺數量週趨勢</div>
            <span class="badge">歷史對比</span>
        </div>
        <div class="card-body">
            <div class="chart-wrap">
                <canvas id="trendChart"></canvas>
            </div>
        </div>
    </div>

    <!-- History Table -->
    <div class="card">
        <div class="card-header">
            <div class="card-title">歷史報告列表</div>
            <span class="badge">{len(reports)} 週</span>
        </div>
        <div class="table-wrap">
            <table>
                <thead>
                    <tr>
                        <th>週次</th>
                        <th>報告日期</th>
                        <th class="num">職缺總數</th>
                        <th>熱門技能</th>
                        <th class="num">中位數薪資(元)</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>{rows_html}</tbody>
            </table>
        </div>
    </div>

    <footer>
        <p><strong>梵亞行銷 | 台中教育大學新尖兵計畫</strong></p>
        <p>本報告由自動化監控系統生成 | 資料來源：104、1111、518 人力銀行</p>
    </footer>
</div>

<script>
const trend = {trend_json};
const fontFamily = "'Nunito', 'Noto Sans TC', sans-serif";

if (trend.has_trend && trend.weeks && trend.weeks.length >= 2) {{
    new Chart(document.getElementById('trendChart'), {{
        type: 'line',
        data: {{
            labels: trend.weeks.map((w, i) => `第 ${{w}} 週\\n${{(trend.dates||[])[i]||''}}`),
            datasets: [{{
                label: '職缺數',
                data: trend.job_counts,
                borderColor: '#F07167',
                backgroundColor: 'rgba(240,113,103,.08)',
                borderWidth: 3,
                pointRadius: 7,
                pointBackgroundColor: '#F07167',
                pointBorderColor: '#fff',
                pointBorderWidth: 2.5,
                tension: 0.35,
                fill: true
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{ display: false }},
                tooltip: {{
                    backgroundColor: 'rgba(74,64,58,.9)',
                    padding: 14,
                    cornerRadius: 12,
                    titleFont: {{ family: fontFamily, size: 13, weight: 700 }},
                    bodyFont: {{ family: fontFamily, size: 13 }},
                    callbacks: {{
                        label: ctx => ` 職缺數：${{ctx.raw.toLocaleString()}} 筆`
                    }}
                }}
            }},
            scales: {{
                y: {{
                    beginAtZero: false,
                    grid: {{ color: '#F3EAE3' }},
                    ticks: {{
                        font: {{ family: fontFamily, size: 12 }},
                        callback: v => v.toLocaleString()
                    }}
                }},
                x: {{
                    grid: {{ display: false }},
                    ticks: {{ font: {{ family: fontFamily, size: 12, weight: 600 }} }}
                }}
            }}
        }}
    }});
}} else {{
    document.getElementById('trendChart').closest('.chart-wrap').innerHTML =
        '<div class="empty-chart">📊 需累積至少 2 週資料才能顯示趨勢圖（目前 ' + (trend.weeks ? trend.weeks.length : 0) + ' 週）</div>';
}}
</script>
</body>
</html>'''
