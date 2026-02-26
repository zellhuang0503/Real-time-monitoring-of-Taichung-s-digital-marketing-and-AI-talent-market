"""
職缺分析主模組
整合所有分析功能，提供完整的就業市場分析
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import Counter, defaultdict
import os

from .skill_extractor import SkillExtractor
from .salary_analyzer import SalaryAnalyzer
from config import INDUSTRY_CODE_MAPPING


class JobAnalyzer:
    """
    職缺分析器
    整合多維度分析功能
    """
    
    def __init__(self):
        self.skill_extractor = SkillExtractor()
        self.salary_analyzer = SalaryAnalyzer()
    
    def analyze(self, jobs: List[Dict], previous_jobs: List[Dict] = None) -> Dict[str, Any]:
        """
        執行完整的職缺分析
        
        Args:
            jobs: 當前職缺列表
            previous_jobs: 前期職缺列表（用於趨勢比較）
            
        Returns:
            完整的分析結果
        """
        print("[Analyzer] 開始分析職缺數據...")
        
        result = {
            'analysis_date': datetime.now().isoformat(),
            'summary': self._analyze_summary(jobs),
            'job_distribution': self._analyze_job_distribution(jobs),
            'skill_analysis': self.skill_extractor.analyze_jobs_skills(jobs),
            'skill_combinations': self.skill_extractor.get_skill_combinations(jobs),
            'salary_analysis': self.salary_analyzer.analyze_salary_distribution(jobs),
            'salary_by_skill': self.salary_analyzer.analyze_salary_by_skill(jobs, self.skill_extractor),
            'company_analysis': self._analyze_companies(jobs),
            'experience_requirements': self._analyze_experience_requirements(jobs),
            'education_requirements': self._analyze_education_requirements(jobs),
            'trend_analysis': self._analyze_trends(jobs, previous_jobs) if previous_jobs else None,
            'emerging_jobs': self._detect_emerging_jobs(jobs, previous_jobs) if previous_jobs else [],
        }
        
        print(f"[Analyzer] 分析完成：共 {len(jobs)} 筆職缺")
        return result
    
    def _analyze_summary(self, jobs: List[Dict]) -> Dict:
        """分析摘要統計"""
        total_jobs = len(jobs)
        
        # 資料來源分布
        source_counter = Counter(job.get('source', 'unknown') for job in jobs)
        
        # 地區分布
        area_counter = Counter(job.get('area', 'unknown') for job in jobs)
        
        # 有薪資資訊的比例
        jobs_with_salary = sum(1 for job in jobs if job.get('salary_min') or job.get('salary_max'))
        
        # 日期範圍
        dates = [job.get('posted_date', '') for job in jobs if job.get('posted_date')]
        
        return {
            'total_jobs': total_jobs,
            'sources_distribution': dict(source_counter),
            'area_distribution': dict(area_counter),
            'salary_coverage': {
                'with_salary': jobs_with_salary,
                'without_salary': total_jobs - jobs_with_salary,
                'coverage_rate': round(jobs_with_salary / total_jobs * 100, 1) if total_jobs > 0 else 0
            },
            'date_range': {
                'earliest': min(dates) if dates else None,
                'latest': max(dates) if dates else None,
            } if dates else None
        }
    
    def _analyze_job_distribution(self, jobs: List[Dict]) -> Dict:
        """分析職缺類別分布"""
        # 按搜尋關鍵字分類
        keyword_counter = Counter(job.get('search_keyword', '其他') for job in jobs)
        
        # 按職務類別分類
        category_counter = Counter()
        for job in jobs:
            category = job.get('job_category', '未分類')
            # 處理 list 或其他非字串類型
            if isinstance(category, list):
                category = category[0] if category else '未分類'
            elif not isinstance(category, str):
                category = str(category) if category else '未分類'
            # 如果類別太長，取主要部分
            if len(category) > 30:
                category = category[:30] + '...'
            category_counter[category] += 1
        
        return {
            'by_search_keyword': [
                {'keyword': kw, 'count': count, 'percentage': round(count / len(jobs) * 100, 1)}
                for kw, count in keyword_counter.most_common(20)
            ],
            'by_job_category': [
                {'category': cat, 'count': count, 'percentage': round(count / len(jobs) * 100, 1)}
                for cat, count in category_counter.most_common(15)
            ]
        }
    
    def _analyze_companies(self, jobs: List[Dict]) -> Dict:
        """分析公司資訊"""
        # 產業別分布
        industry_counter = Counter()
        for job in jobs:
            industry = job.get('company_industry', '未註明')
            # 處理 list 或其他非字串類型
            if isinstance(industry, list):
                industry = industry[0] if industry else '未註明'
            elif not isinstance(industry, str):
                industry = str(industry) if industry else '未註明'
            if industry and industry != '未註明':
                industry_counter[industry] += 1
        
        # 轉譯產業別代碼為中文名稱
        def translate_industry(industry_code):
            """將產業代碼轉譯為中文名稱"""
            if not industry_code or industry_code == '未註明':
                return '未分類'
            # 轉為字串以確保類型一致
            code_str = str(industry_code)
            # 查詢對照表
            if code_str in INDUSTRY_CODE_MAPPING:
                return INDUSTRY_CODE_MAPPING[code_str]
            # 若無對照，顯示原始代碼
            return f"其他產業({code_str})"
        
        # 招聘最多的公司
        company_counter = Counter(job.get('company', '未知') for job in jobs)
        
        # 公司規模推估（依職缺數量）
        company_job_counts = list(company_counter.values())
        
        return {
            'total_companies': len(company_counter),
            'top_industries': [
                {
                    'industry': ind, 
                    'industry_name': translate_industry(ind),  # 新增：中文產業名稱
                    'count': count, 
                    'percentage': round(count / len(jobs) * 100, 1)
                }
                for ind, count in industry_counter.most_common(15)
            ],
            'top_hiring_companies': [
                {'company': comp, 'job_count': count}
                for comp, count in company_counter.most_common(20)
            ],
            'company_size_distribution': {
                'large_scale': sum(1 for c in company_job_counts if c >= 10),
                'medium_scale': sum(1 for c in company_job_counts if 3 <= c < 10),
                'small_scale': sum(1 for c in company_job_counts if c < 3),
            }
        }
    
    def _analyze_experience_requirements(self, jobs: List[Dict]) -> Dict:
        """分析經驗要求分布"""
        exp_counter = Counter()
        
        for job in jobs:
            exp = job.get('experience', '未註明')
            # 簡化分類
            if '不拘' in exp or '不限' in exp:
                exp_counter['經驗不拘'] += 1
            elif '1年' in exp or '1 年' in exp:
                exp_counter['1年以下'] += 1
            elif '3年' in exp or '3 年' in exp:
                exp_counter['1-3年'] += 1
            elif '5年' in exp or '5 年' in exp:
                exp_counter['3-5年'] += 1
            elif '10年' in exp or '10 年' in exp:
                exp_counter['5-10年'] += 1
            else:
                exp_counter['其他/未註明'] += 1
        
        # 計算對新鮮人友善的職缺比例
        entry_friendly = exp_counter.get('經驗不拘', 0) + exp_counter.get('1年以下', 0)
        
        return {
            'distribution': [
                {'experience': exp, 'count': count, 'percentage': round(count / len(jobs) * 100, 1)}
                for exp, count in exp_counter.most_common()
            ],
            'entry_level_friendly': {
                'count': entry_friendly,
                'percentage': round(entry_friendly / len(jobs) * 100, 1) if jobs else 0
            }
        }
    
    def _analyze_education_requirements(self, jobs: List[Dict]) -> Dict:
        """分析學歷要求分布"""
        edu_counter = Counter()
        
        for job in jobs:
            edu = job.get('education', '未註明')
            if '不拘' in edu or '不限' in edu:
                edu_counter['學歷不拘'] += 1
            elif '高中' in edu or '高職' in edu:
                edu_counter['高中/高職'] += 1
            elif '專科' in edu or '專校' in edu:
                edu_counter['專科'] += 1
            elif '大學' in edu or '學士' in edu:
                edu_counter['大學'] += 1
            elif '碩士' in edu or '研究所' in edu:
                edu_counter['碩士以上'] += 1
            else:
                edu_counter['其他/未註明'] += 1
        
        return {
            'distribution': [
                {'education': edu, 'count': count, 'percentage': round(count / len(jobs) * 100, 1)}
                for edu, count in edu_counter.most_common()
            ]
        }
    
    def _analyze_trends(self, current_jobs: List[Dict], previous_jobs: List[Dict]) -> Dict:
        """分析趨勢變化"""
        current_total = len(current_jobs)
        previous_total = len(previous_jobs)
        
        # 職缺數量變化
        job_change = current_total - previous_total
        job_change_pct = (job_change / previous_total * 100) if previous_total > 0 else 0
        
        # 技能趨勢
        skill_trends = self.skill_extractor.compare_skill_trends(current_jobs, previous_jobs)
        
        # 薪資趨勢
        salary_trends = self.salary_analyzer.compare_salary_trends(current_jobs, previous_jobs)
        
        return {
            'job_count_change': {
                'current': current_total,
                'previous': previous_total,
                'change': job_change,
                'change_percentage': round(job_change_pct, 1),
            },
            'skill_trends': skill_trends,
            'salary_trends': salary_trends,
        }
    
    def _detect_emerging_jobs(self, current_jobs: List[Dict], previous_jobs: List[Dict]) -> List[Dict]:
        """偵測新興職位"""
        # 提取兩個時期的職位名稱
        current_titles = {job.get('title', '') for job in current_jobs}
        previous_titles = {job.get('title', '') for job in previous_jobs}
        
        # 找出新出現的職位名稱關鍵詞
        # 這裡使用簡單的啟發式方法
        
        # 常見的職位關鍵詞
        job_keywords = [
            'AI', 'AIGC', '生成式', 'ChatGPT', 'Prompt', '提示工程',
            'SEO', 'SEM', 'GA4', '數據分析', '數位行銷', '社群經營',
            '電商', '電子商務', '網紅', 'KOL', '社群小編',
            '全端', '前端', '後端', 'Python', 'React', 'Vue',
            '數位轉型', '自動化', 'MarTech', '行銷科技'
        ]
        
        emerging = []
        
        # 統計當期各關鍵詞的出現頻率
        current_keywords = defaultdict(int)
        for job in current_jobs:
            title = job.get('title', '')
            for kw in job_keywords:
                if kw in title:
                    current_keywords[kw] += 1
        
        # 統計前期各關鍵詞的出現頻率
        previous_keywords = defaultdict(int)
        for job in previous_jobs:
            title = job.get('title', '')
            for kw in job_keywords:
                if kw in title:
                    previous_keywords[kw] += 1
        
        # 找出增長最快的關鍵詞
        for kw, current_count in current_keywords.items():
            previous_count = previous_keywords.get(kw, 0)
            
            # 如果前期幾乎沒有，但現在有不少
            if previous_count == 0 and current_count >= 3:
                emerging.append({
                    'keyword': kw,
                    'current_count': current_count,
                    'previous_count': previous_count,
                    'trend': 'new_emerging',
                    'description': f'"{kw}"類職缺本期新增 {current_count} 個'
                })
            # 如果前期有，但現在大幅增加
            elif previous_count > 0:
                growth_rate = (current_count - previous_count) / previous_count
                if growth_rate > 0.5 and current_count >= 5:  # 增長超過50%
                    emerging.append({
                        'keyword': kw,
                        'current_count': current_count,
                        'previous_count': previous_count,
                        'growth_rate': round(growth_rate * 100, 1),
                        'trend': 'fast_growing',
                        'description': f'"{kw}"類職缺增長 {round(growth_rate * 100)}%'
                    })
        
        # 按當期數量排序
        emerging.sort(key=lambda x: x['current_count'], reverse=True)
        
        return emerging[:10]
    
    def save_analysis(self, analysis_result: Dict, filepath: str):
        """儲存分析結果"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, ensure_ascii=False, indent=2)
        
        print(f"[Analyzer] 分析結果已儲存: {filepath}")
    
    def load_previous_analysis(self, filepath: str) -> Optional[Dict]:
        """載入前期分析結果"""
        if not os.path.exists(filepath):
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[Analyzer] 載入前期資料失敗: {e}")
            return None
