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
        """取得 HTML 模板 - 溫暖舒適、充滿活力的設計大師 Oliver 風格"""
        html = '''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>台中中部數位人才就業市場監控報告 - 第{{ week_number }}週</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700&family=Noto+Sans+TC:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #F07167;      /* 溫暖珊瑚紅 */
            --primary-dark: #E05D53;
            --primary-light: #F8AD9D;
            --secondary: #F4A261;    /* 溫暖橙色 */
            --accent: #2A9D8F;       /* 舒服的藍綠色，用來點綴 */
            --accent-light: #8ABEB7;
            --danger: #E76F51;
            --success: #2A9D8F;
            --bg: #FFFDF9;           /* 非常淺的暖白底色 */
            --card: #ffffff;
            --text: #4A403A;         /* 暖深灰色，比純黑柔和 */
            --text-light: #8A7E78;
            --text-muted: #BDB5B1;
            --border: #F3EAE3;
            --border-light: #FAF5F0;
            --font-sans: 'Nunito', 'Noto Sans TC', sans-serif;
            --font-mono: 'Nunito', monospace; /* Keep it soft */
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
            line-height: 1.6;
            font-size: 15px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 30px;
        }
        
        /* Header - Warm & Soft Style */
        header {
            background: linear-gradient(135deg, #FFDAB9 0%, #F8AD9D 100%);
            border-radius: 24px;
            color: var(--text);
            padding: 40px 32px;
            margin-bottom: 40px;
            position: relative;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(240, 113, 103, 0.1);
        }
        
        header::after {
            content: '✨';
            position: absolute;
            top: -20px;
            right: 20px;
            font-size: 120px;
            opacity: 0.15;
            transform: rotate(15deg);
            pointer-events: none;
        }
        
        .header-content {
            position: relative;
            z-index: 1;
        }
        
        h1 {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 12px;
            letter-spacing: -0.5px;
            color: #3D332D;
        }
        
        .subtitle {
            font-size: 1.1rem;
            opacity: 0.85;
            font-weight: 500;
            margin-bottom: 20px;
        }
        
        .header-meta {
            display: flex;
            gap: 20px;
            font-size: 0.95rem;
            font-weight: 600;
            color: #5C4D45;
            background: rgba(255, 255, 255, 0.4);
            padding: 10px 20px;
            border-radius: 12px;
            display: inline-flex;
            flex-wrap: wrap;
        }
        
        .header-meta span {
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        /* Section Layout */
        .section {
            margin-bottom: 40px;
        }
        
        .section-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 24px;
        }
        
        .section-title {
            font-size: 1.3rem;
            font-weight: 700;
            color: var(--text);
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .section-title .icon {
            width: 36px;
            height: 36px;
            background: var(--primary-light);
            color: white;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
            box-shadow: 0 4px 10px rgba(248, 173, 157, 0.4);
        }
        
        /* Grid System */
        .grid {
            display: grid;
            grid-template-columns: repeat(12, 1fr);
            gap: 24px;
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
            border-radius: 20px;
            border: 1px solid var(--border);
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.02);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        
        .card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.05);
        }
        
        .card-header {
            padding: 20px 24px;
            border-bottom: 1px dashed var(--border);
            background: var(--card);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .card-title {
            font-size: 1.05rem;
            font-weight: 700;
            color: var(--text);
        }
        
        .card-badge {
            font-size: 0.75rem;
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 20px;
            letter-spacing: 0.5px;
        }
        
        .card-badge.primary { background: var(--primary-light); color: #fff; }
        .card-badge.accent { background: var(--secondary); color: #fff; }
        .card-badge.success { background: var(--success); color: #fff; }
        
        .card-body {
            padding: 24px;
        }
        
        /* KPI Cards */
        .kpi-card {
            background: var(--card);
            border-radius: 20px;
            border: 1px solid var(--border);
            padding: 24px;
            position: relative;
            transition: all 0.3s ease;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.02);
        }
        
        .kpi-card:hover {
            border-color: var(--primary-light);
            box-shadow: 0 8px 30px rgba(240, 113, 103, 0.1);
            transform: translateY(-3px);
        }
        
        .kpi-icon {
            font-size: 2rem;
            margin-bottom: 12px;
        }
        
        .kpi-label {
            font-size: 0.9rem;
            color: var(--text-light);
            font-weight: 600;
            margin-bottom: 8px;
        }
        
        .kpi-value {
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--text);
            margin-bottom: 4px;
        }
        
        .kpi-subtext {
            font-size: 0.85rem;
            color: var(--text-muted);
            background: var(--bg);
            padding: 4px 12px;
            border-radius: 12px;
            display: inline-block;
        }
        
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
            background: #FFF5F3;
            border: none;
            border-radius: 20px;
            padding: 24px 30px;
            margin-bottom: 24px;
            position: relative;
            box-shadow: inset 0 0 0 2px var(--primary-light);
        }
        
        .insight-box h3 {
            font-size: 1rem;
            color: var(--primary-dark);
            font-weight: 700;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .insight-box p {
            color: var(--text);
            font-size: 1.05rem;
            line-height: 1.6;
        }
        
        /* Recommendations */
        .recommendation {
            background: #fff;
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 20px 24px;
            margin-bottom: 16px;
            position: relative;
            transition: all 0.2s ease;
            box-shadow: 0 2px 8px rgba(0,0,0,0.02);
        }
        
        .recommendation:hover {
            border-color: var(--primary-light);
            box-shadow: 0 6px 20px rgba(240, 113, 103, 0.08);
            transform: translateX(4px);
        }
        
        .recommendation.priority-high {
            background: #FFF0ED;
            border-color: #FFD2C9;
        }
        
        .recommendation-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 12px;
        }
        
        .priority-badge {
            font-size: 0.75rem;
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 12px;
            letter-spacing: 0.5px;
        }
        
        .priority-badge.high { background: var(--danger); color: white; }
        .priority-badge.medium { background: var(--secondary); color: white; }
        .priority-badge.low { background: var(--success); color: white; }
        
        .recommendation h4 {
            font-size: 1.05rem;
            color: var(--text);
            font-weight: 700;
        }
        
        .recommendation p {
            font-size: 0.95rem;
            color: var(--text-light);
            margin: 6px 0;
            line-height: 1.6;
        }
        
        .recommendation p strong {
            color: var(--text);
            font-weight: 600;
        }
        
        /* Skill Tags */
        .skill-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }
        
        .skill-tag {
            font-size: 0.9rem;
            padding: 6px 14px;
            border-radius: 20px;
            font-weight: 600;
            background: #F3F4F6;
            color: var(--text);
            transition: all 0.2s ease;
            display: inline-block;
        }
        
        .skill-tag:hover {
            background: var(--primary-light);
            color: white;
            transform: scale(1.05);
        }
        
        .skill-tag.accent {
            background: #FEF3C7;
            color: #D97706;
        }
        
        /* Tables */
        .table-container {
            overflow-x: auto;
        }
        
        table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            font-size: 0.95rem;
        }
        
        thead {
            background: var(--bg);
        }
        
        th {
            text-align: left;
            padding: 16px;
            font-weight: 700;
            color: var(--text-light);
            border-bottom: 2px solid var(--border);
            white-space: nowrap;
        }
        
        td {
            padding: 16px;
            border-bottom: 1px solid var(--border-light);
            color: var(--text);
        }
        
        tr:hover td {
            background: var(--bg);
        }
        
        tr:last-child td {
            border-bottom: none;
        }
        
        /* Progress Bars */
        .progress-cell {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .progress-bar {
            flex: 1;
            height: 10px;
            background: var(--border);
            border-radius: 5px;
            overflow: hidden;
            min-width: 80px;
        }
        
        .progress-fill {
            height: 100%;
            border-radius: 5px;
            transition: width 0.5s ease;
        }
        
        .progress-fill.primary { background: var(--primary); }
        .progress-fill.accent { background: var(--secondary); }
        .progress-fill.secondary { background: var(--accent); }
        
        .progress-value {
            font-size: 0.85rem;
            font-weight: 700;
            color: var(--text-light);
            min-width: 45px;
            text-align: right;
        }
        
        .industry-code {
            font-size: 0.8rem;
            color: var(--text-muted);
            background: var(--bg);
            padding: 2px 8px;
            border-radius: 10px;
            margin-top: 4px;
            display: inline-block;
        }
        
        .industry-name {
            font-weight: 600;
        }
        
        /* Salary values */
        .salary-value {
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--primary-dark);
        }
        
        .salary-unit {
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-left: 4px;
        }
        
        /* Footer */
        footer {
            text-align: center;
            padding: 40px;
            color: var(--text-light);
            font-size: 0.9rem;
            margin-top: 40px;
        }
        
        footer p {
            margin: 6px 0;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .container { padding: 20px; }
            header { padding: 30px 20px; border-radius: 20px; }
            h1 { font-size: 1.6rem; }
            .kpi-value { font-size: 2rem; }
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
                    <span>🗓️ 第 {{ week_number }} 週報告</span>
                    <span>🕐 更新時間: {{ report_date }}</span>
                    <span>📍 監控範圍: 台中、彰化、南投</span>
                    <span style="margin-left: auto; background: rgba(0,0,0,0.05); border-radius: 12px; padding: 4px 12px;">
                        <a href="history.html" style="color: var(--text); text-decoration: none; font-weight: 700;">📈 查看歷史趨勢 →</a>
                    </span>
                </div>
            </div>
        </header>
        
        <!-- Executive Summary -->
        <div class="section">
            <div class="section-header">
                <div class="section-title">
                    <div class="icon">✨</div>
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
                        <div class="kpi-icon">💼</div>
                        <div class="kpi-label">相關職缺總數</div>
                        <div class="kpi-value">{{ "{:,}".format(analysis.summary.total_jobs) }}</div>
                        <div class="kpi-subtext">台中、彰化、南投三地區</div>
                    </div>
                </div>
                
                <div class="col-4">
                    <div class="kpi-card">
                        <div class="kpi-icon">💰</div>
                        <div class="kpi-label">中位數月薪</div>
                        <div class="kpi-value">{{ "{:,}".format(analysis.salary_analysis.median_salary) if analysis.salary_analysis.median_salary else "N/A" }}</div>
                        <div class="kpi-subtext">基於 {{ analysis.salary_analysis.has_salary_info }} 個職缺</div>
                    </div>
                </div>
                
                <div class="col-4">
                    <div class="kpi-card">
                        <div class="kpi-icon">🌱</div>
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
                <p><strong>🤔 原因：</strong>{{ rec.reason }}</p>
                <p><strong>🎯 建議行動：</strong>{{ rec.action }}</p>
            </div>
            {% endfor %}
        </div>
        
        <!-- Skill Analysis -->
        <div class="section">
            <div class="section-header">
                <div class="section-title">
                    <div class="icon">🛠️</div>
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
                    <div class="card" style="margin-bottom: 24px;">
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
                    <div class="icon">📈</div>
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
            
            <div class="card" style="margin-top: 24px;">
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
                    <div class="icon">🧩</div>
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
                                            <td><strong>{{ ind.count }}</strong></td>
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
            <p><strong>🎨 設計提供：Oliver (UI/UX 體驗優化版)</strong></p>
            <p>梵亞行銷 | 台中教育大學新尖兵計畫</p>
            <p>本報告由自動化監控系統生成 | 資料來源：104、1111、518 人力銀行</p>
        </footer>
    </div>
    
    <script>
        // 圖表資料
        const chartsData = {{ charts_data | tojson }};
        
        // 溫暖色系配置
        const colors = {
            primary: '#F07167',
            primaryLight: '#F8AD9D',
            accent: '#F4A261',
            accentLight: '#E7C8A0',
            success: '#2A9D8F',
            danger: '#E76F51',
            secondary: '#A8DADC'
        };
        
        // 字體配置
        const fontConfig = {
            family: "'Nunito', 'Noto Sans TC', sans-serif"
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
                    borderRadius: 8,
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
                        backgroundColor: 'rgba(74, 64, 58, 0.9)',
                        padding: 12,
                        cornerRadius: 10,
                        titleFont: { family: fontConfig.family, size: 14, weight: 700 },
                        bodyFont: { family: fontConfig.family, size: 13 }
                    }
                },
                scales: {
                    x: { 
                        beginAtZero: true,
                        grid: { color: '#F3EAE3' },
                        ticks: { font: { family: fontConfig.family, size: 12 } }
                    },
                    y: {
                        grid: { display: false },
                        ticks: { font: { family: fontConfig.family, size: 13, weight: 600 } }
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
                        colors.accent,
                        colors.success,
                        colors.primaryLight,
                        colors.secondary,
                        '#E9C46A'
                    ],
                    borderWidth: 0,
                    hoverOffset: 6
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
                            padding: 16,
                            font: { family: fontConfig.family, size: 12, weight: 600 },
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(74, 64, 58, 0.9)',
                        padding: 12,
                        cornerRadius: 10,
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.raw / total) * 100).toFixed(1);
                                return ` ${context.label}: ${context.raw} (${percentage}%)`;
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
                        colors.secondary,
                        colors.primary,
                        '#E9C46A'
                    ],
                    borderWidth: 3,
                    borderColor: '#ffffff',
                    hoverOffset: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            padding: 16,
                            font: { family: fontConfig.family, size: 12, weight: 600 },
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(74, 64, 58, 0.9)',
                        padding: 12,
                        cornerRadius: 10
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
                    borderRadius: 8,
                    hoverBackgroundColor: '#45B6A8'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(74, 64, 58, 0.9)',
                        padding: 12,
                        cornerRadius: 10
                    }
                },
                scales: {
                    y: { 
                        beginAtZero: true,
                        grid: { color: '#F3EAE3' },
                        ticks: { font: { family: fontConfig.family, size: 12 } }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { 
                            font: { family: fontConfig.family, size: 11, weight: 600 },
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
                    borderRadius: 8,
                    hoverBackgroundColor: '#FFB870'
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(74, 64, 58, 0.9)',
                        padding: 12,
                        cornerRadius: 10
                    }
                },
                scales: {
                    x: { 
                        beginAtZero: true,
                        grid: { color: '#F3EAE3' },
                        ticks: { font: { family: fontConfig.family, size: 12 } }
                    },
                    y: {
                        grid: { display: false },
                        ticks: { 
                            font: { family: fontConfig.family, size: 12, weight: 600 },
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
