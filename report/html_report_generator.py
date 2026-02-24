"""
HTML 報告生成器 - UiUX Max Pro 設計優化版
生成單一 HTML 檔案的互動式儀表板
"""

import json
from datetime import datetime
from typing import Dict, Any, List
from jinja2 import Template


class HTMLReportGenerator:
    """
    HTML 報告生成器
    生成內嵌所有資源的單一 HTML 檔案
    """
    
    def __init__(self):
        self.template = self._get_html_template()
    
    def generate(self, analysis_result: Dict, course_recommendations: Dict, 
                 output_path: str, week_number: int = 1):
        """
        生成 HTML 報告
        
        Args:
            analysis_result: 分析結果
            course_recommendations: 課程建議
            output_path: 輸出檔案路徑
            week_number: 第幾週報告
        """
        # 準備模板資料
        template_data = self._prepare_template_data(
            analysis_result, course_recommendations, week_number
        )
        
        # 渲染 HTML
        html_content = self.template.render(**template_data)
        
        # 寫入檔案
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"[Report] HTML 報告已生成: {output_path}")
        return output_path
    
    def _prepare_template_data(self, analysis: Dict, recommendations: Dict, 
                               week_number: int) -> Dict:
        """準備模板所需的資料"""
        return {
            'week_number': week_number,
            'report_date': datetime.now().strftime('%Y年%m月%d日'),
            'analysis': analysis,
            'recommendations': recommendations,
            'charts_data': self._prepare_charts_data(analysis),
        }
    
    def _prepare_charts_data(self, analysis: Dict) -> Dict:
        """準備圖表資料（轉為 JSON 格式）"""
        charts = {}
        
        # 1. 技能需求排行
        skill_analysis = analysis.get('skill_analysis', {})
        top_skills = skill_analysis.get('top_skills', [])[:15]
        charts['skills'] = {
            'labels': [s['skill'] for s in top_skills],
            'data': [s['count'] for s in top_skills],
        }
        
        # 2. 薪資分布
        salary_analysis = analysis.get('salary_analysis', {})
        range_dist = salary_analysis.get('range_distribution', [])
        charts['salary'] = {
            'labels': [r['range'] for r in range_dist],
            'data': [r['count'] for r in range_dist],
        }
        
        # 3. 經驗要求
        exp_req = analysis.get('experience_requirements', {})
        exp_dist = exp_req.get('distribution', [])
        charts['experience'] = {
            'labels': [e['experience'] for e in exp_dist],
            'data': [e['count'] for e in exp_dist],
        }
        
        # 4. 職缺類別分布
        job_dist = analysis.get('job_distribution', {})
        keyword_dist = job_dist.get('by_search_keyword', [])[:10]
        charts['job_categories'] = {
            'labels': [k['keyword'] for k in keyword_dist],
            'data': [k['count'] for k in keyword_dist],
        }
        
        # 5. 技能組合
        skill_combos = analysis.get('skill_combinations', [])[:8]
        charts['skill_combinations'] = {
            'labels': [c['description'] for c in skill_combos],
            'data': [c['count'] for c in skill_combos],
        }
        
        # 6. 產業別分布 - 為進度條準備
        company_analysis = analysis.get('company_analysis', {})
        industries = company_analysis.get('top_industries', [])[:10]
        charts['industries'] = {
            'labels': [i.get('industry_name', i['industry']) for i in industries],
            'data': [i['count'] for i in industries],
            'percentages': [i['percentage'] for i in industries],
        }
        
        return charts
    
    def _get_html_template(self) -> Template:
        """取得 HTML 模板 - Data-Dense Dashboard Style"""
        html = '''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>台中中部數位人才就業市場監控報告 - 第{{ week_number }}週</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&family=Fira+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
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
            --border-light: #f1f5f9;
            --font-sans: 'Fira Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            --font-mono: 'Fira Code', 'Consolas', 'Monaco', monospace;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: var(--font-sans);
            background: var(--bg);
            color: var(--text);
            line-height: 1.5;
            font-size: 14px;
        }
        
        .container {
            max-width: 1600px;
            margin: 0 auto;
            padding: 24px;
        }
        
        /* Header - Data Dense Style */
        header {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            padding: 32px 28px;
            margin: -24px -24px 32px -24px;
            position: relative;
            overflow: hidden;
        }
        
        header::before {
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            width: 400px;
            height: 100%;
            background: linear-gradient(135deg, transparent 0%, rgba(255,255,255,0.05) 100%);
            pointer-events: none;
        }
        
        .header-content {
            max-width: 1600px;
            margin: 0 auto;
            position: relative;
            z-index: 1;
        }
        
        h1 {
            font-size: 1.75rem;
            font-weight: 600;
            margin-bottom: 8px;
            letter-spacing: -0.5px;
        }
        
        .subtitle {
            font-size: 1rem;
            opacity: 0.85;
            font-weight: 400;
            margin-bottom: 16px;
        }
        
        .header-meta {
            display: flex;
            gap: 24px;
            font-size: 0.85rem;
            opacity: 0.7;
            font-family: var(--font-mono);
        }
        
        .header-meta span {
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        /* Section Layout */
        .section {
            margin-bottom: 32px;
        }
        
        .section-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 2px solid var(--border);
        }
        
        .section-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--text);
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .section-title .icon {
            width: 32px;
            height: 32px;
            background: var(--primary);
            color: white;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1rem;
        }
        
        /* Grid System */
        .grid {
            display: grid;
            grid-template-columns: repeat(12, 1fr);
            gap: 20px;
        }
        
        .col-3 { grid-column: span 3; }
        .col-4 { grid-column: span 4; }
        .col-6 { grid-column: span 6; }
        .col-8 { grid-column: span 8; }
        .col-12 { grid-column: span 12; }
        
        @media (max-width: 1200px) {
            .col-3 { grid-column: span 6; }
        }
        
        @media (max-width: 768px) {
            .col-3, .col-4, .col-6, .col-8 { grid-column: span 12; }
        }
        
        /* Cards */
        .card {
            background: var(--card);
            border-radius: 8px;
            border: 1px solid var(--border);
            overflow: hidden;
        }
        
        .card-header {
            padding: 16px 20px;
            border-bottom: 1px solid var(--border-light);
            background: linear-gradient(to bottom, #fafbfc, var(--card));
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .card-title {
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--text);
            letter-spacing: 0.3px;
        }
        
        .card-badge {
            font-size: 0.7rem;
            font-weight: 600;
            padding: 3px 8px;
            border-radius: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .card-badge.primary { background: rgba(30, 64, 175, 0.1); color: var(--primary); }
        .card-badge.accent { background: rgba(245, 158, 11, 0.1); color: var(--accent); }
        .card-badge.success { background: rgba(16, 185, 129, 0.1); color: var(--success); }
        
        .card-body {
            padding: 20px;
        }
        
        /* KPI Cards */
        .kpi-card {
            background: var(--card);
            border-radius: 8px;
            border: 1px solid var(--border);
            padding: 20px;
            position: relative;
            transition: all 0.2s ease;
        }
        
        .kpi-card:hover {
            border-color: var(--primary-light);
            box-shadow: 0 4px 20px rgba(30, 64, 175, 0.08);
        }
        
        .kpi-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: var(--primary);
        }
        
        .kpi-card.accent::before { background: var(--accent); }
        .kpi-card.success::before { background: var(--success); }
        
        .kpi-label {
            font-size: 0.75rem;
            color: var(--text-light);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 500;
            margin-bottom: 8px;
        }
        
        .kpi-value {
            font-family: var(--font-mono);
            font-size: 2rem;
            font-weight: 600;
            color: var(--text);
            margin-bottom: 6px;
        }
        
        .kpi-subtext {
            font-size: 0.8rem;
            color: var(--text-muted);
        }
        
        .kpi-trend {
            font-size: 0.75rem;
            font-weight: 600;
            margin-top: 8px;
            display: flex;
            align-items: center;
            gap: 4px;
        }
        
        .kpi-trend.up { color: var(--success); }
        .kpi-trend.down { color: var(--danger); }
        
        /* Charts */
        .chart-container {
            position: relative;
            height: 280px;
        }
        
        .chart-container.large {
            height: 360px;
        }
        
        /* Insight Box */
        .insight-box {
            background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
            border: 1px solid rgba(245, 158, 11, 0.3);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            position: relative;
        }
        
        .insight-box::before {
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            width: 4px;
            height: 100%;
            background: var(--accent);
            border-radius: 8px 0 0 8px;
        }
        
        .insight-box h3 {
            font-size: 0.8rem;
            color: #92400e;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        
        .insight-box p {
            color: #78350f;
            font-size: 0.95rem;
            line-height: 1.6;
        }
        
        /* Recommendations */
        .recommendation {
            background: #eff6ff;
            border: 1px solid rgba(30, 64, 175, 0.15);
            border-radius: 8px;
            padding: 16px 20px;
            margin-bottom: 12px;
            position: relative;
            transition: all 0.2s ease;
        }
        
        .recommendation:hover {
            border-color: var(--primary);
            box-shadow: 0 2px 12px rgba(30, 64, 175, 0.08);
        }
        
        .recommendation::before {
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            width: 4px;
            height: 100%;
            background: var(--primary);
            border-radius: 8px 0 0 8px;
        }
        
        .recommendation.priority-high {
            background: #fef2f2;
            border-color: rgba(239, 68, 68, 0.2);
        }
        
        .recommendation.priority-high::before {
            background: var(--danger);
        }
        
        .recommendation-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 10px;
        }
        
        .priority-badge {
            font-size: 0.65rem;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .priority-badge.high {
            background: var(--danger);
            color: white;
        }
        
        .priority-badge.medium {
            background: var(--accent);
            color: white;
        }
        
        .priority-badge.low {
            background: var(--success);
            color: white;
        }
        
        .recommendation h4 {
            font-size: 0.95rem;
            color: var(--text);
            font-weight: 600;
        }
        
        .recommendation p {
            font-size: 0.85rem;
            color: var(--text-light);
            margin: 6px 0;
            line-height: 1.5;
        }
        
        .recommendation p strong {
            color: var(--text);
        }
        
        /* Skill Tags */
        .skill-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }
        
        .skill-tag {
            font-family: var(--font-mono);
            font-size: 0.8rem;
            padding: 6px 12px;
            border-radius: 4px;
            font-weight: 500;
            background: rgba(30, 64, 175, 0.08);
            color: var(--primary);
            border: 1px solid rgba(30, 64, 175, 0.15);
        }
        
        .skill-tag.secondary {
            background: rgba(16, 185, 129, 0.08);
            color: var(--success);
            border-color: rgba(16, 185, 129, 0.15);
        }
        
        .skill-tag.accent {
            background: rgba(245, 158, 11, 0.08);
            color: var(--accent);
            border-color: rgba(245, 158, 11, 0.15);
        }
        
        /* Tables */
        .table-container {
            overflow-x: auto;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85rem;
        }
        
        thead {
            background: var(--bg);
        }
        
        th {
            text-align: left;
            padding: 12px 16px;
            font-weight: 600;
            color: var(--text-light);
            text-transform: uppercase;
            font-size: 0.7rem;
            letter-spacing: 0.5px;
            border-bottom: 1px solid var(--border);
            white-space: nowrap;
        }
        
        td {
            padding: 14px 16px;
            border-bottom: 1px solid var(--border-light);
            color: var(--text);
        }
        
        tr:hover {
            background: var(--bg);
        }
        
        tr:last-child td {
            border-bottom: none;
        }
        
        /* Progress Bars for Industries */
        .progress-cell {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .progress-bar {
            flex: 1;
            height: 8px;
            background: var(--border-light);
            border-radius: 4px;
            overflow: hidden;
            min-width: 80px;
        }
        
        .progress-fill {
            height: 100%;
            border-radius: 4px;
            transition: width 0.5s ease;
        }
        
        .progress-fill.primary { background: linear-gradient(90deg, var(--primary), var(--primary-light)); }
        .progress-fill.accent { background: linear-gradient(90deg, var(--accent), var(--accent-light)); }
        .progress-fill.secondary { background: linear-gradient(90deg, var(--secondary), #60a5fa); }
        
        .progress-value {
            font-family: var(--font-mono);
            font-size: 0.8rem;
            font-weight: 600;
            color: var(--text-light);
            min-width: 45px;
            text-align: right;
        }
        
        .industry-code {
            font-family: var(--font-mono);
            font-size: 0.75rem;
            color: var(--text-muted);
            background: var(--bg);
            padding: 2px 6px;
            border-radius: 4px;
        }
        
        .industry-name {
            font-weight: 500;
        }
        
        /* Salary values */
        .salary-value {
            font-family: var(--font-mono);
            font-weight: 600;
            color: var(--text);
        }
        
        .salary-unit {
            font-size: 0.8rem;
            color: var(--text-muted);
            margin-left: 2px;
        }
        
        /* Footer */
        footer {
            text-align: center;
            padding: 32px;
            color: var(--text-muted);
            font-size: 0.8rem;
            border-top: 1px solid var(--border);
            margin-top: 40px;
        }
        
        footer p {
            margin: 4px 0;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .container {
                padding: 16px;
            }
            
            header {
                margin: -16px -16px 24px -16px;
                padding: 24px 20px;
            }
            
            h1 {
                font-size: 1.4rem;
            }
            
            .header-meta {
                flex-direction: column;
                gap: 8px;
            }
            
            .kpi-value {
                font-size: 1.5rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header>
            <div class="header-content">
                <h1>台中中部數位人才就業市場監控報告</h1>
                <div class="subtitle">新尖兵計畫課程規劃決策支持系統</div>
                <div class="header-meta">
                    <span>📅 第 {{ week_number }} 週報告</span>
                    <span>🕐 資料日期: {{ report_date }}</span>
                    <span>📍 監控範圍: 台中、彰化、南投</span>
                </div>
            </div>
        </header>
        
        <!-- Executive Summary -->
        <div class="section">
            <div class="section-header">
                <div class="section-title">
                    <div class="icon">📊</div>
                    執行摘要
                </div>
            </div>
            
            <div class="insight-box">
                <h3>🎯 核心洞察</h3>
                <p>{{ recommendations.executive_summary.key_insight }}</p>
            </div>
            
            <div class="grid">
                <div class="col-4">
                    <div class="kpi-card">
                        <div class="kpi-label">相關職缺總數</div>
                        <div class="kpi-value">{{ "{:,}".format(analysis.summary.total_jobs) }}</div>
                        <div class="kpi-subtext">台中、彰化、南投三地區</div>
                    </div>
                </div>
                
                <div class="col-4">
                    <div class="kpi-card accent">
                        <div class="kpi-label">中位數月薪</div>
                        <div class="kpi-value">{{ "{:,}".format(analysis.salary_analysis.median_salary) if analysis.salary_analysis.median_salary else "N/A" }}</div>
                        <div class="kpi-subtext">基於 {{ analysis.salary_analysis.has_salary_info }} 個職缺</div>
                    </div>
                </div>
                
                <div class="col-4">
                    <div class="kpi-card success">
                        <div class="kpi-label">接受新人比例</div>
                        <div class="kpi-value">{{ "{:.0f}".format(analysis.experience_requirements.entry_level_friendly.percentage) }}%</div>
                        <div class="kpi-subtext">經驗不拘或1年以下</div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Priority Recommendations -->
        <div class="section">
            <div class="section-header">
                <div class="section-title">
                    <div class="icon">💡</div>
                    課程調整優先建議
                </div>
            </div>
            
            {% for rec in recommendations.priority_recommendations %}
            <div class="recommendation {% if rec.priority == '高' %}priority-high{% endif %}">
                <div class="recommendation-header">
                    <span class="priority-badge {% if rec.priority == '高' %}high{% elif rec.priority == '中' %}medium{% else %}low{% endif %}">
                        {{ rec.priority }}
                    </span>
                    <h4>{{ rec.title }}</h4>
                </div>
                <p><strong>原因：</strong>{{ rec.reason }}</p>
                <p><strong>建議行動：</strong>{{ rec.action }}</p>
            </div>
            {% endfor %}
        </div>
        
        <!-- Skill Analysis -->
        <div class="section">
            <div class="section-header">
                <div class="section-title">
                    <div class="icon">🔧</div>
                    技能需求分析
                </div>
            </div>
            
            <div class="grid">
                <div class="col-8">
                    <div class="card">
                        <div class="card-header">
                            <div class="card-title">Top 15 熱門技能需求</div>
                            <span class="card-badge primary">需求排行</span>
                        </div>
                        <div class="card-body">
                            <div class="chart-container">
                                <canvas id="skillsChart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-4">
                    <div class="card" style="margin-bottom: 20px;">
                        <div class="card-header">
                            <div class="card-title">必備技能</div>
                            <span class="card-badge success">>30 職缺</span>
                        </div>
                        <div class="card-body">
                            <div class="skill-tags">
                                {% for skill in recommendations.skill_focus.must_have_skills[:8] %}
                                <span class="skill-tag">{{ skill.skill }}</span>
                                {% endfor %}
                            </div>
                        </div>
                    </div>
                    
                    <div class="card">
                        <div class="card-header">
                            <div class="card-title">加分技能</div>
                            <span class="card-badge accent">競爭力</span>
                        </div>
                        <div class="card-body">
                            <div class="skill-tags">
                                {% for skill in recommendations.skill_focus.nice_to_have_skills[:8] %}
                                <span class="skill-tag accent">{{ skill.skill }}</span>
                                {% endfor %}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Salary Analysis -->
        <div class="section">
            <div class="section-header">
                <div class="section-title">
                    <div class="icon">💰</div>
                    薪資市場分析
                </div>
            </div>
            
            <div class="grid">
                <div class="col-4">
                    <div class="card">
                        <div class="card-header">
                            <div class="card-title">薪資區間分布</div>
                        </div>
                        <div class="card-body">
                            <div class="chart-container">
                                <canvas id="salaryChart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-4">
                    <div class="card">
                        <div class="card-header">
                            <div class="card-title">經驗要求分布</div>
                        </div>
                        <div class="card-body">
                            <div class="chart-container">
                                <canvas id="experienceChart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-4">
                    <div class="card">
                        <div class="card-header">
                            <div class="card-title">職缺類別分布</div>
                        </div>
                        <div class="card-body">
                            <div class="chart-container">
                                <canvas id="jobCategoriesChart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="card" style="margin-top: 20px;">
                <div class="card-header">
                    <div class="card-title">高薪技能排行 (中位數薪資)</div>
                    <span class="card-badge accent">Top 10</span>
                </div>
                <div class="card-body">
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>技能名稱</th>
                                    <th>職缺數</th>
                                    <th>中位數薪資</th>
                                    <th>平均薪資</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for skill in analysis.salary_by_skill.top_paying_skills[:10] %}
                                <tr>
                                    <td><strong>{{ skill.skill }}</strong></td>
                                    <td>{{ skill.job_count }}</td>
                                    <td><span class="salary-value">{{ "{:,}".format(skill.median_salary) }}</span><span class="salary-unit">元</span></td>
                                    <td><span class="salary-value">{{ "{:,}".format(skill.mean_salary) }}</span><span class="salary-unit">元</span></td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Skill Combinations -->
        <div class="section">
            <div class="section-header">
                <div class="section-title">
                    <div class="icon">🔗</div>
                    技能組合分析
                </div>
            </div>
            
            <div class="grid">
                <div class="col-6">
                    <div class="card">
                        <div class="card-header">
                            <div class="card-title">熱門技能組合</div>
                            <span class="card-badge primary">出現頻率</span>
                        </div>
                        <div class="card-body">
                            <div class="chart-container large">
                                <canvas id="skillComboChart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-6">
                    <div class="card">
                        <div class="card-header">
                            <div class="card-title">產業別分布</div>
                            <span class="card-badge primary">Top 10</span>
                        </div>
                        <div class="card-body">
                            <div class="table-container">
                                <table>
                                    <thead>
                                        <tr>
                                            <th>產業別</th>
                                            <th>職缺數</th>
                                            <th>占比</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {% for ind in analysis.company_analysis.top_industries[:10] %}
                                        <tr>
                                            <td>
                                                <div>
                                                    <span class="industry-name">{{ ind.industry_name }}</span>
                                                    <br>
                                                    <span class="industry-code">{{ ind.industry }}</span>
                                                </div>
                                            </td>
                                            <td style="font-family: var(--font-mono);">{{ ind.count }}</td>
                                            <td>
                                                <div class="progress-cell">
                                                    <div class="progress-bar">
                                                        <div class="progress-fill {% if loop.index == 1 %}primary{% elif loop.index == 2 %}accent{% else %}secondary{% endif %}" 
                                                             style="width: {{ ind.percentage }}%"></div>
                                                    </div>
                                                    <span class="progress-value">{{ ind.percentage }}%</span>
                                                </div>
                                            </td>
                                        </tr>
                                        {% endfor %}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <footer>
            <p><strong>梵亞行銷 | 台中教育大學新尖兵計畫</strong></p>
            <p>本報告由自動化監控系統生成 | 資料來源：104人力銀行、1111人力銀行、518人力銀行</p>
        </footer>
    </div>
    
    <script>
        // 圖表資料
        const chartsData = {{ charts_data | tojson }};
        
        // 顏色配置
        const colors = {
            primary: '#1E40AF',
            primaryLight: '#3B82F6',
            accent: '#F59E0B',
            accentLight: '#fbbf24',
            success: '#10b981',
            danger: '#ef4444',
            secondary: '#64748b'
        };
        
        // 技能需求圖表
        new Chart(document.getElementById('skillsChart'), {
            type: 'bar',
            data: {
                labels: chartsData.skills.labels,
                datasets: [{
                    label: '職缺提及次數',
                    data: chartsData.skills.data,
                    backgroundColor: colors.primary,
                    borderColor: colors.primaryDark,
                    borderWidth: 0,
                    borderRadius: 4,
                    hoverBackgroundColor: colors.primaryLight
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(30, 41, 59, 0.95)',
                        padding: 12,
                        cornerRadius: 6,
                        titleFont: { family: 'Fira Sans', size: 13 },
                        bodyFont: { family: 'Fira Code', size: 12 }
                    }
                },
                scales: {
                    x: { 
                        beginAtZero: true,
                        grid: { color: '#f1f5f9' },
                        ticks: { font: { family: 'Fira Code', size: 11 } }
                    },
                    y: {
                        grid: { display: false },
                        ticks: { font: { family: 'Fira Sans', size: 12, weight: 500 } }
                    }
                }
            }
        });
        
        // 薪資分布圖表
        new Chart(document.getElementById('salaryChart'), {
            type: 'doughnut',
            data: {
                labels: chartsData.salary.labels,
                datasets: [{
                    data: chartsData.salary.data,
                    backgroundColor: [
                        colors.primary,
                        colors.primaryLight,
                        colors.accent,
                        colors.accentLight,
                        colors.success,
                        colors.secondary
                    ],
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '65%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 15,
                            font: { family: 'Fira Sans', size: 11 },
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(30, 41, 59, 0.95)',
                        padding: 12,
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.raw / total) * 100).toFixed(1);
                                return `${context.label}: ${context.raw} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
        
        // 經驗要求圖表
        new Chart(document.getElementById('experienceChart'), {
            type: 'pie',
            data: {
                labels: chartsData.experience.labels,
                datasets: [{
                    data: chartsData.experience.data,
                    backgroundColor: [
                        colors.success,
                        colors.primaryLight,
                        colors.accent,
                        colors.accentLight,
                        colors.primary,
                        colors.secondary
                    ],
                    borderWidth: 2,
                    borderColor: '#fff',
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            padding: 12,
                            font: { family: 'Fira Sans', size: 11 },
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(30, 41, 59, 0.95)',
                        padding: 12
                    }
                }
            }
        });
        
        // 職缺類別圖表
        new Chart(document.getElementById('jobCategoriesChart'), {
            type: 'bar',
            data: {
                labels: chartsData.job_categories.labels,
                datasets: [{
                    label: '職缺數',
                    data: chartsData.job_categories.data,
                    backgroundColor: colors.success,
                    borderRadius: 4,
                    hoverBackgroundColor: '#34d399'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(30, 41, 59, 0.95)',
                        padding: 12
                    }
                },
                scales: {
                    y: { 
                        beginAtZero: true,
                        grid: { color: '#f1f5f9' },
                        ticks: { font: { family: 'Fira Code', size: 11 } }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { 
                            font: { family: 'Fira Sans', size: 10 },
                            maxRotation: 45
                        }
                    }
                }
            }
        });
        
        // 技能組合圖表
        new Chart(document.getElementById('skillComboChart'), {
            type: 'bar',
            data: {
                labels: chartsData.skill_combinations.labels,
                datasets: [{
                    label: '出現次數',
                    data: chartsData.skill_combinations.data,
                    backgroundColor: colors.accent,
                    borderRadius: 4,
                    hoverBackgroundColor: colors.accentLight
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(30, 41, 59, 0.95)',
                        padding: 12
                    }
                },
                scales: {
                    x: { 
                        beginAtZero: true,
                        grid: { color: '#f1f5f9' },
                        ticks: { font: { family: 'Fira Code', size: 11 } }
                    },
                    y: {
                        grid: { display: false },
                        ticks: { 
                            font: { family: 'Fira Sans', size: 11 },
                            maxWidth: 150
                        }
                    }
                }
            }
        });
    </script>
</body>
</html>'''
        return Template(html)
