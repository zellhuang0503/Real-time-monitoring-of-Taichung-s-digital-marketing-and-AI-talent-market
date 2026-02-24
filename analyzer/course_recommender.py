"""
課程建議引擎
基於市場數據自動生成課程規劃建議
"""

from typing import List, Dict, Any
from datetime import datetime


class CourseRecommender:
    """
    課程建議引擎
    為新尖兵計畫提供數據驅動的課程調整建議
    """
    
    def __init__(self):
        # 門檻設定
        self.thresholds = {
            'high_demand': 30,      # 職缺數超過此值為高需求
            'skill_gap': 0.25,      # 技能缺口閾值
            'salary_premium': 35000, # 高薪門檻
            'trending_skill': 20,    # 熱門技能增長門檻
        }
    
    def generate_recommendations(self, analysis_result: Dict) -> Dict[str, Any]:
        """
        基於分析結果生成課程建議
        
        Args:
            analysis_result: 職缺分析結果
            
        Returns:
            課程建議報告
        """
        recommendations = {
            'generated_at': datetime.now().isoformat(),
            'executive_summary': self._generate_summary(analysis_result),
            'priority_recommendations': self._generate_priority_recommendations(analysis_result),
            'module_adjustments': self._generate_module_adjustments(analysis_result),
            'tool_recommendations': self._generate_tool_recommendations(analysis_result),
            'skill_focus': self._generate_skill_focus(analysis_result),
            'market_insights': self._generate_market_insights(analysis_result),
        }
        
        return recommendations
    
    def _generate_summary(self, analysis: Dict) -> Dict:
        """生成執行摘要"""
        summary = analysis.get('summary', {})
        skill_analysis = analysis.get('skill_analysis', {})
        salary_analysis = analysis.get('salary_analysis', {})
        
        total_jobs = summary.get('total_jobs', 0)
        top_skills = skill_analysis.get('top_skills', [])
        median_salary = salary_analysis.get('median_salary', 0)
        
        return {
            'market_size': f"本期監控範圍內共有 {total_jobs} 個相關職缺",
            'top_demand': f"需求最高的技能: {', '.join([s['skill'] for s in top_skills[:3]])}" if top_skills else "無法識別",
            'salary_benchmark': f"市場中位數薪資: {median_salary:,} 元/月" if median_salary else "薪資資訊不足",
            'key_insight': self._generate_key_insight(analysis),
        }
    
    def _generate_key_insight(self, analysis: Dict) -> str:
        """生成核心洞察"""
        skill_analysis = analysis.get('skill_analysis', {})
        trends = analysis.get('trend_analysis', {})
        emerging = analysis.get('emerging_jobs', [])
        
        insights = []
        
        # 檢查趨勢
        if trends and trends.get('job_count_change', {}).get('change_percentage', 0) > 20:
            change = trends['job_count_change']['change_percentage']
            insights.append(f"職缺數量大幅增長 {change}%，顯示市場需求旺盛")
        
        # 檢查新興職位
        if emerging:
            keywords = [e['keyword'] for e in emerging[:2]]
            insights.append(f"新興職位趨勢: {', '.join(keywords)}")
        
        # 檢查技能需求
        top_skills = skill_analysis.get('top_skills', [])
        ai_skills = [s for s in top_skills if s['skill'] in ['ChatGPT', 'AI', '生成式 AI']]
        if ai_skills:
            insights.append(f"AI相關技能需求顯著，建議強化AI工具應用課程")
        
        if not insights:
            return "市場狀況穩定，建議維持現有課程架構並持續觀察"
        
        return "；".join(insights)
    
    def _generate_priority_recommendations(self, analysis: Dict) -> List[Dict]:
        """生成優先建議"""
        recommendations = []
        
        # 分析技能需求缺口
        skill_analysis = analysis.get('skill_analysis', {})
        top_skills = skill_analysis.get('top_skills', [])
        
        # 找出高需求技能
        high_demand_skills = [
            s for s in top_skills 
            if s['count'] >= self.thresholds['high_demand']
        ]
        
        if high_demand_skills:
            skill_names = ', '.join([s['skill'] for s in high_demand_skills[:5]])
            recommendations.append({
                'priority': '高',
                'category': '核心技能強化',
                'title': f'優先教學: {skill_names}',
                'reason': f"這些技能在 {high_demand_skills[0]['count']} 個職缺中被提及，為市場剛需",
                'action': '調整課程比重，增加實作時數',
            })
        
        # 分析薪資溢價技能
        salary_by_skill = analysis.get('salary_by_skill', {})
        top_paying = salary_by_skill.get('top_paying_skills', [])
        
        premium_skills = [
            s for s in top_paying 
            if s.get('median_salary', 0) >= self.thresholds['salary_premium']
        ]
        
        if premium_skills:
            recommendations.append({
                'priority': '中',
                'category': '高薪技能培養',
                'title': f'重點技能: {premium_skills[0]["skill"]}',
                'reason': f"掌握此技能的職缺中位數薪資達 {premium_skills[0]['median_salary']:,} 元",
                'action': '納入進階課程或專題實作',
            })
        
        # 檢查新興趨勢
        emerging = analysis.get('emerging_jobs', [])
        if emerging:
            trend = emerging[0]
            recommendations.append({
                'priority': '中',
                'category': '前瞻技能導入',
                'title': f'關注趨勢: {trend["keyword"]}',
                'reason': trend['description'],
                'action': '開設工作坊或邀請業師分享',
            })
        
        return recommendations
    
    def _generate_module_adjustments(self, analysis: Dict) -> List[Dict]:
        """生成課程模組調整建議"""
        adjustments = []
        
        job_dist = analysis.get('job_distribution', {})
        keyword_dist = job_dist.get('by_search_keyword', [])
        
        # 根據職缺分布調整課程比重
        total_jobs = sum(k['count'] for k in keyword_dist)
        
        for keyword_data in keyword_dist[:6]:
            keyword = keyword_data['keyword']
            percentage = keyword_data['percentage']
            
            if percentage >= 25:
                adjustments.append({
                    'module': keyword,
                    'current_weight': '20%',
                    'recommended_weight': f'{max(25, int(percentage))}%',
                    'reason': f'市場需求占比 {percentage}%',
                    'suggestion': '增加實作專案與案例分析',
                })
            elif percentage <= 10:
                adjustments.append({
                    'module': keyword,
                    'current_weight': '15%',
                    'recommended_weight': f'{int(percentage)}%',
                    'reason': f'市場需求僅占 {percentage}%',
                    'suggestion': '維持基礎教學，或與其他模組整合',
                })
        
        return adjustments
    
    def _generate_tool_recommendations(self, analysis: Dict) -> List[Dict]:
        """生成工具教學建議"""
        tool_recommendations = []
        
        skill_analysis = analysis.get('skill_analysis', {})
        top_skills = skill_analysis.get('top_skills', [])
        
        # 工具對應課程建議
        tool_courses = {
            'GA4': {'course': 'Google Analytics 4 實務', 'hours': 12, 'level': '進階'},
            'Google Ads': {'course': 'Google Ads 認證班', 'hours': 16, 'level': '中階'},
            'Meta Ads': {'course': 'Meta 廣告投放實戰', 'hours': 12, 'level': '中階'},
            'SEO': {'course': 'SEO 搜尋引擎優化', 'hours': 8, 'level': '入門'},
            'ChatGPT': {'course': 'ChatGPT 職場應用', 'hours': 6, 'level': '入門'},
            'Python': {'course': 'Python 資料分析', 'hours': 20, 'level': '進階'},
            'Excel': {'course': 'Excel 商業分析', 'hours': 12, 'level': '入門'},
            'Power BI': {'course': 'Power BI 視覺化', 'hours': 16, 'level': '中階'},
            'Figma': {'course': 'Figma UI/UX 設計', 'hours': 12, 'level': '入門'},
            'WordPress': {'course': 'WordPress 網站建置', 'hours': 16, 'level': '入門'},
        }
        
        for skill_data in top_skills[:15]:
            skill_name = skill_data['skill']
            if skill_name in tool_courses:
                course_info = tool_courses[skill_name]
                tool_recommendations.append({
                    'tool': skill_name,
                    'market_demand': f"{skill_data['count']} 個職缺提及 ({skill_data['percentage']}%)",
                    'recommended_course': course_info['course'],
                    'suggested_hours': course_info['hours'],
                    'difficulty_level': course_info['level'],
                    'priority': '高' if skill_data['count'] >= 50 else ('中' if skill_data['count'] >= 20 else '低'),
                })
        
        return tool_recommendations
    
    def _generate_skill_focus(self, analysis: Dict) -> Dict:
        """生成技能重點建議"""
        return {
            'must_have_skills': self._identify_must_have_skills(analysis),
            'nice_to_have_skills': self._identify_nice_to_have_skills(analysis),
            'emerging_skills': self._identify_emerging_skills(analysis),
        }
    
    def _identify_must_have_skills(self, analysis: Dict) -> List[Dict]:
        """識別必備技能"""
        skill_analysis = analysis.get('skill_analysis', {})
        top_skills = skill_analysis.get('top_skills', [])
        
        must_have = []
        for skill in top_skills:
            if skill['count'] >= self.thresholds['high_demand']:
                must_have.append({
                    'skill': skill['skill'],
                    'demand_level': '高',
                    'prevalence': f"{skill['percentage']}% 的職缺要求",
                    'importance': '核心必備',
                })
        
        return must_have[:10]
    
    def _identify_nice_to_have_skills(self, analysis: Dict) -> List[Dict]:
        """識別加分技能"""
        skill_analysis = analysis.get('skill_analysis', {})
        top_skills = skill_analysis.get('top_skills', [])
        
        nice_to_have = []
        for skill in top_skills:
            if 10 <= skill['count'] < self.thresholds['high_demand']:
                nice_to_have.append({
                    'skill': skill['skill'],
                    'demand_level': '中',
                    'prevalence': f"{skill['percentage']}% 的職缺要求",
                    'importance': '加分項目',
                })
        
        return nice_to_have[:10]
    
    def _identify_emerging_skills(self, analysis: Dict) -> List[Dict]:
        """識別新興技能"""
        trends = analysis.get('trend_analysis', {})
        skill_trends = trends.get('skill_trends', {}) if trends else {}
        rising = skill_trends.get('rising_skills', [])
        
        emerging = []
        for skill_trend in rising[:5]:
            if skill_trend.get('change_percentage'):
                emerging.append({
                    'skill': skill_trend['skill'],
                    'growth_rate': f"+{skill_trend['change_percentage']}%",
                    'importance': '未來趨勢',
                    'suggestion': '開設選修或工作坊',
                })
        
        return emerging
    
    def _generate_market_insights(self, analysis: Dict) -> List[Dict]:
        """生成市場洞察"""
        insights = []
        
        # 經驗要求洞察
        exp_req = analysis.get('experience_requirements', {})
        entry_friendly = exp_req.get('entry_level_friendly', {})
        if entry_friendly.get('percentage', 0) > 60:
            insights.append({
                'topic': '新鮮人就業機會',
                'finding': f"{entry_friendly['percentage']}% 的職缺接受新人或經驗不拘",
                'implication': '新尖兵結訓學員就業機會良好',
                'recommendation': '強調作品集與實作能力培養',
            })
        
        # 產業分布洞察
        company_analysis = analysis.get('company_analysis', {})
        top_industries = company_analysis.get('top_industries', [])
        if top_industries:
            insights.append({
                'topic': '主要招聘產業',
                'finding': f"{top_industries[0]['industry']} 占比最高 ({top_industries[0]['percentage']}%)",
                'implication': '課程案例應該聚焦此產業',
                'recommendation': f'邀請{top_industries[0]["industry"]}業師授課',
            })
        
        # 薪資洞察
        salary_analysis = analysis.get('salary_analysis', {})
        median = salary_analysis.get('median_salary', 0)
        if median > 0:
            insights.append({
                'topic': '薪資行情',
                'finding': f"市場中位數薪資約 {median:,} 元",
                'implication': '學員可合理預期此薪資水平',
                'recommendation': '課程中可分享薪資談判技巧',
            })
        
        return insights
    
    def format_recommendation_text(self, recommendations: Dict) -> str:
        """將建議格式化為可讀文字"""
        lines = []
        lines.append("=" * 60)
        lines.append("新尖兵計畫 - 課程調整建議報告")
        lines.append("=" * 60)
        lines.append("")
        
        # 執行摘要
        summary = recommendations.get('executive_summary', {})
        lines.append("[執行摘要]")
        for key, value in summary.items():
            lines.append(f"  - {value}")
        lines.append("")
        
        # 優先建議
        lines.append("[優先調整建議]")
        for rec in recommendations.get('priority_recommendations', []):
            lines.append(f"\n[{rec['priority']}] {rec['title']}")
            lines.append(f"  原因: {rec['reason']}")
            lines.append(f"  行動: {rec['action']}")
        lines.append("")
        
        # 必備技能
        lines.append("[學員必備技能清單]")
        must_have = recommendations.get('skill_focus', {}).get('must_have_skills', [])
        for skill in must_have[:5]:
            lines.append(f"  [OK] {skill['skill']} - {skill['prevalence']}")
        lines.append("")
        
        return "\n".join(lines)
