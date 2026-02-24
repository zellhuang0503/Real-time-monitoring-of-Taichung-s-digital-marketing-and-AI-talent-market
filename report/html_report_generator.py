"""
HTML 報告生成器
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
        
        return charts
    
    def _get_html_template(self) -> Template:
        """取得 HTML 模板"""
        html = '''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>台中中部數位人才就業市場監控報告 - 第{{ week_number }}週</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        :root {
            --primary: #6366f1;
            --primary-dark: #4f46e5;
            --secondary: #10b981;
            --accent: #f59e0b;
            --danger: #ef4444;
            --bg: #f8fafc;
            --card: #ffffff;
            --text: #1e293b;
            --text-light: #64748b;
            --border: #e2e8f0;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            padding: 40px 20px;
            margin: -20px -20px 30px -20px;
            border-radius: 0 0 20px 20px;
            box-shadow: 0 4px 20px rgba(99, 102, 241, 0.3);
        }
        
        h1 {
            font-size: 2rem;
            margin-bottom: 10px;
            font-weight: 700;
        }
        
        .subtitle {
            font-size: 1.1rem;
            opacity: 0.9;
        }
        
        .meta {
            margin-top: 15px;
            font-size: 0.9rem;
            opacity: 0.8;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: var(--card);
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        
        .card h2 {
            font-size: 1.25rem;
            margin-bottom: 16px;
            color: var(--text);
            border-bottom: 2px solid var(--border);
            padding-bottom: 10px;
        }
        
        .metric {
            display: flex;
            align-items: baseline;
            gap: 8px;
            margin: 12px 0;
        }
        
        .metric-value {
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--primary);
        }
        
        .metric-label {
            color: var(--text-light);
            font-size: 0.95rem;
        }
        
        .chart-container {
            position: relative;
            height: 300px;
            margin: 20px 0;
        }
        
        .chart-container.large {
            height: 400px;
        }
        
        .insight-box {
            background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
            border-left: 4px solid var(--accent);
            padding: 16px 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
        
        .insight-box h3 {
            color: #92400e;
            margin-bottom: 8px;
            font-size: 1rem;
        }
        
        .insight-box p {
            color: #78350f;
            font-size: 0.95rem;
        }
        
        .recommendation {
            background: #eff6ff;
            border-left: 4px solid var(--primary);
            padding: 16px 20px;
            border-radius: 8px;
            margin: 12px 0;
        }
        
        .recommendation h4 {
            color: var(--primary-dark);
            margin-bottom: 8px;
            font-size: 1rem;
        }
        
        .priority-high {
            border-left-color: var(--danger);
            background: #fef2f2;
        }
        
        .priority-high h4 {
            color: var(--danger);
        }
        
        .skill-tag {
            display: inline-block;
            background: var(--primary);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            margin: 4px;
        }
        
        .skill-tag.secondary {
            background: var(--secondary);
        }
        
        .skill-tag.accent {
            background: var(--accent);
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 16px 0;
            font-size: 0.9rem;
        }
        
        th, td {
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid var(--border);
        }
        
        th {
            background: var(--bg);
            font-weight: 600;
            color: var(--text-light);
            text-transform: uppercase;
            font-size: 0.8rem;
            letter-spacing: 0.5px;
        }
        
        tr:hover {
            background: var(--bg);
        }
        
        .trend-up {
            color: var(--secondary);
        }
        
        .trend-down {
            color: var(--danger);
        }
        
        .section {
            margin-bottom: 40px;
        }
        
        .section-title {
            font-size: 1.5rem;
            margin-bottom: 20px;
            color: var(--text);
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .badge-primary {
            background: var(--primary);
            color: white;
        }
        
        .badge-secondary {
            background: var(--secondary);
            color: white;
        }
        
        .badge-accent {
            background: var(--accent);
            color: white;
        }
        
        footer {
            text-align: center;
            padding: 30px;
            color: var(--text-light);
            font-size: 0.85rem;
            border-top: 1px solid var(--border);
            margin-top: 40px;
        }
        
        @media (max-width: 768px) {
            .grid {
                grid-template-columns: 1fr;
            }
            
            h1 {
                font-size: 1.5rem;
            }
            
            .metric-value {
                font-size: 2rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>台中中部數位人才就業市場監控報告</h1>
            <div class="subtitle">新尖兵計畫課程規劃決策支持系統</div>
            <div class="meta">第 {{ week_number }} 週報告 | 資料日期: {{ report_date }}</div>
        </header>
        
        <!-- 執行摘要 -->
        <div class="section">
            <h2 class="section-title">
                <span>📊</span> 執行摘要
            </h2>
            <div class="insight-box">
                <h3>🎯 核心洞察</h3>
                <p>{{ recommendations.executive_summary.key_insight }}</p>
            </div>
            
            <div class="grid">
                <div class="card">
                    <div class="metric">
                        <span class="metric-value">{{ analysis.summary.total_jobs }}</span>
                        <span class="metric-label">相關職缺總數</span>
                    </div>
                    <p style="color: var(--text-light); font-size: 0.9rem;">
                        監控範圍：台中、彰化、南投三地區
                    </p>
                </div>
                
                <div class="card">
                    <div class="metric">
                        <span class="metric-value">{{ "{:,}".format(analysis.salary_analysis.median_salary) if analysis.salary_analysis.median_salary else "N/A" }}</span>
                        <span class="metric-label">中位數月薪 (元)</span>
                    </div>
                    <p style="color: var(--text-light); font-size: 0.9rem;">
                        基於 {{ analysis.salary_analysis.has_salary_info }} 個有薪資資訊的職缺
                    </p>
                </div>
                
                <div class="card">
                    <div class="metric">
                        <span class="metric-value">{{ "{:.0f}".format(analysis.experience_requirements.entry_level_friendly.percentage) }}%</span>
                        <span class="metric-label">接受新人職缺比例</span>
                    </div>
                    <p style="color: var(--text-light); font-size: 0.9rem;">
                        經驗不拘或1年以下經驗可
                    </p>
                </div>
            </div>
        </div>
        
        <!-- 優先建議 -->
        <div class="section">
            <h2 class="section-title">
                <span>💡</span> 課程調整優先建議
            </h2>
            {% for rec in recommendations.priority_recommendations %}
            <div class="recommendation {% if rec.priority == '高' %}priority-high{% endif %}">
                <h4>
                    {% if rec.priority == '高' %}🔴{% elif rec.priority == '中' %}🟡{% else %}🟢{% endif %}
                    [{{ rec.priority }}] {{ rec.title }}
                </h4>
                <p><strong>原因：</strong>{{ rec.reason }}</p>
                <p><strong>建議行動：</strong>{{ rec.action }}</p>
            </div>
            {% endfor %}
        </div>
        
        <!-- 技能需求分析 -->
        <div class="section">
            <h2 class="section-title">
                <span>🔧</span> 技能需求分析
            </h2>
            
            <div class="grid">
                <div class="card" style="grid-column: span 2;">
                    <h2>Top 15 熱門技能需求</h2>
                    <div class="chart-container">
                        <canvas id="skillsChart"></canvas>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2>必備技能清單</h2>
                <p style="margin-bottom: 15px; color: var(--text-light);">
                    以下技能在超過 30 個職缺中被提及，建議納入必修
                </p>
                {% for skill in recommendations.skill_focus.must_have_skills[:8] %}
                <span class="skill-tag">{{ skill.skill }}</span>
                {% endfor %}
            </div>
            
            <div class="card">
                <h2>加分技能清單</h2>
                <p style="margin-bottom: 15px; color: var(--text-light);">
                    掌握這些技能能提升競爭力
                </p>
                {% for skill in recommendations.skill_focus.nice_to_have_skills[:8] %}
                <span class="skill-tag secondary">{{ skill.skill }}</span>
                {% endfor %}
            </div>
        </div>
        
        <!-- 薪資分析 -->
        <div class="section">
            <h2 class="section-title">
                <span>💰</span> 薪資市場分析
            </h2>
            
            <div class="grid">
                <div class="card">
                    <h2>薪資區間分布</h2>
                    <div class="chart-container">
                        <canvas id="salaryChart"></canvas>
                    </div>
                </div>
                
                <div class="card">
                    <h2>經驗要求分布</h2>
                    <div class="chart-container">
                        <canvas id="experienceChart"></canvas>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2>高薪技能排行 (中位數薪資)</h2>
                <table>
                    <thead>
                        <tr>
                            <th>技能</th>
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
                            <td>{{ "{:,}".format(skill.median_salary) }} 元</td>
                            <td>{{ "{:,}".format(skill.mean_salary) }} 元</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- 職缺分布 -->
        <div class="section">
            <h2 class="section-title">
                <span>📈</span> 職缺類別分布
            </h2>
            
            <div class="grid">
                <div class="card">
                    <h2>各領域職缺數量</h2>
                    <div class="chart-container">
                        <canvas id="jobCategoriesChart"></canvas>
                    </div>
                </div>
                
                <div class="card">
                    <h2>熱門技能組合</h2>
                    <div class="chart-container">
                        <canvas id="skillComboChart"></canvas>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- 詳細數據表格 -->
        <div class="section">
            <h2 class="section-title">
                <span>📋</span> 詳細數據
            </h2>
            
            <div class="card">
                <h2>產業別分布</h2>
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
                            <td>{{ ind.industry }}</td>
                            <td>{{ ind.count }}</td>
                            <td>{{ ind.percentage }}%</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
        
        <footer>
            <p>© 梵亞行銷 | 台中教育大學新尖兵計畫</p>
            <p>本報告由自動化監控系統生成 | 資料來源：104人力銀行、1111人力銀行、518人力銀行</p>
        </footer>
    </div>
    
    <script>
        // 圖表資料
        const chartsData = {{ charts_data | tojson }};
        
        // 技能需求圖表
        new Chart(document.getElementById('skillsChart'), {
            type: 'bar',
            data: {
                labels: chartsData.skills.labels,
                datasets: [{
                    label: '職缺提及次數',
                    data: chartsData.skills.data,
                    backgroundColor: 'rgba(99, 102, 241, 0.8)',
                    borderColor: 'rgba(99, 102, 241, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: { beginAtZero: true }
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
                        '#ef4444',
                        '#f59e0b',
                        '#10b981',
                        '#3b82f6',
                        '#6366f1',
                        '#8b5cf6'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
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
                        '#10b981',
                        '#3b82f6',
                        '#f59e0b',
                        '#ef4444',
                        '#6366f1',
                        '#94a3b8'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
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
                    backgroundColor: 'rgba(16, 185, 129, 0.8)',
                    borderColor: 'rgba(16, 185, 129, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: { beginAtZero: true }
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
                    backgroundColor: 'rgba(245, 158, 11, 0.8)',
                    borderColor: 'rgba(245, 158, 11, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: { beginAtZero: true }
                }
            }
        });
    </script>
</body>
</html>'''
        return Template(html)
