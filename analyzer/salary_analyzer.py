"""
薪資分析模組
分析職缺薪資分布與趨勢
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from collections import defaultdict


class SalaryAnalyzer:
    """
    薪資分析器
    """
    
    def __init__(self):
        self.salary_ranges = {
            'below_30k': {'min': 0, 'max': 30000, 'label': '30K 以下'},
            '30k_40k': {'min': 30000, 'max': 40000, 'label': '30K - 40K'},
            '40k_50k': {'min': 40000, 'max': 50000, 'label': '40K - 50K'},
            '50k_60k': {'min': 50000, 'max': 60000, 'label': '50K - 60K'},
            '60k_80k': {'min': 60000, 'max': 80000, 'label': '60K - 80K'},
            'above_80k': {'min': 80000, 'max': float('inf'), 'label': '80K 以上'},
        }
    
    def analyze_salary_distribution(self, jobs: List[Dict]) -> Dict:
        """
        分析薪資分布
        
        Args:
            jobs: 職缺列表
            
        Returns:
            薪資分析結果
        """
        salaries = []
        salary_by_category = defaultdict(list)
        salary_by_experience = defaultdict(list)
        
        for job in jobs:
            salary_min = job.get('salary_min')
            salary_max = job.get('salary_max')
            
            # 計算平均薪資（若有範圍則取中位數）
            if salary_min and salary_max:
                avg_salary = (salary_min + salary_max) / 2
            elif salary_min:
                avg_salary = salary_min
            elif salary_max:
                avg_salary = salary_max
            else:
                continue
            
            salaries.append(avg_salary)
            
            # 按類別分組
            category = job.get('job_category', '未分類')
            salary_by_category[category].append(avg_salary)
            
            # 按經驗分組
            experience = job.get('experience', '未註明')
            salary_by_experience[experience].append(avg_salary)
        
        if not salaries:
            return {
                'total_analyzed': 0,
                'has_salary_info': 0,
                'message': '無法解析薪資資訊'
            }
        
        # 整體統計
        stats = {
            'total_analyzed': len(jobs),
            'has_salary_info': len(salaries),
            'salary_coverage_rate': round(len(salaries) / len(jobs) * 100, 1) if jobs else 0,
            'median_salary': int(np.median(salaries)),
            'mean_salary': int(np.mean(salaries)),
            'min_salary': int(np.min(salaries)),
            'max_salary': int(np.max(salaries)),
            'p25': int(np.percentile(salaries, 25)),
            'p75': int(np.percentile(salaries, 75)),
        }
        
        # 薪資區間分布
        range_distribution = defaultdict(int)
        for salary in salaries:
            for range_key, range_info in self.salary_ranges.items():
                if range_info['min'] <= salary < range_info['max']:
                    range_distribution[range_info['label']] += 1
                    break
        
        stats['range_distribution'] = [
            {'range': label, 'count': count, 'percentage': round(count / len(salaries) * 100, 1)}
            for label, count in sorted(range_distribution.items())
        ]
        
        # 各類別薪資
        stats['salary_by_category'] = []
        for category, cat_salaries in sorted(salary_by_category.items(), 
                                             key=lambda x: len(x[1]), reverse=True)[:10]:
            if len(cat_salaries) >= 5:  # 至少5筆才統計
                stats['salary_by_category'].append({
                    'category': category,
                    'count': len(cat_salaries),
                    'median': int(np.median(cat_salaries)),
                    'mean': int(np.mean(cat_salaries)),
                })
        
        # 各經驗薪資
        stats['salary_by_experience'] = []
        for exp, exp_salaries in sorted(salary_by_experience.items()):
            if len(exp_salaries) >= 5:
                stats['salary_by_experience'].append({
                    'experience': exp,
                    'count': len(exp_salaries),
                    'median': int(np.median(exp_salaries)),
                    'mean': int(np.mean(exp_salaries)),
                })
        
        return stats
    
    def analyze_salary_by_skill(self, jobs: List[Dict], skill_extractor) -> Dict:
        """
        分析各技能的薪資水平
        
        Args:
            jobs: 職缺列表
            skill_extractor: 技能萃取器實例
            
        Returns:
            技能薪資分析
        """
        skill_salaries = defaultdict(list)
        
        for job in jobs:
            # 取得薪資
            salary_min = job.get('salary_min')
            salary_max = job.get('salary_max')
            
            if salary_min and salary_max:
                avg_salary = (salary_min + salary_max) / 2
            elif salary_min:
                avg_salary = salary_min
            elif salary_max:
                avg_salary = salary_max
            else:
                continue
            
            # 提取技能
            skills = skill_extractor.extract_skills(
                job.get('job_description', ''),
                job.get('title', '')
            )
            
            # 累積各技能的薪資
            for skill in skills:
                skill_salaries[skill].append(avg_salary)
        
        # 計算各技能的薪資統計
        skill_salary_stats = []
        for skill, salaries in skill_salaries.items():
            if len(salaries) >= 3:  # 至少3筆
                skill_salary_stats.append({
                    'skill': skill,
                    'job_count': len(salaries),
                    'median_salary': int(np.median(salaries)),
                    'mean_salary': int(np.mean(salaries)),
                    'min_salary': int(np.min(salaries)),
                    'max_salary': int(np.max(salaries)),
                })
        
        # 按中位數薪資排序
        skill_salary_stats.sort(key=lambda x: x['median_salary'], reverse=True)
        
        return {
            'total_skills_analyzed': len(skill_salary_stats),
            'top_paying_skills': skill_salary_stats[:15],
            'skill_salary_details': skill_salary_stats
        }
    
    def compare_salary_trends(self, current_jobs: List[Dict], previous_jobs: List[Dict]) -> Dict:
        """
        比較兩個時期的薪資變化
        
        Args:
            current_jobs: 當期職缺
            previous_jobs: 前期職缺
            
        Returns:
            薪資趨勢比較
        """
        def get_salaries(jobs):
            salaries = []
            for job in jobs:
                salary_min = job.get('salary_min')
                salary_max = job.get('salary_max')
                if salary_min and salary_max:
                    salaries.append((salary_min + salary_max) / 2)
                elif salary_min:
                    salaries.append(salary_min)
                elif salary_max:
                    salaries.append(salary_max)
            return salaries
        
        current_salaries = get_salaries(current_jobs)
        previous_salaries = get_salaries(previous_jobs)
        
        if not current_salaries or not previous_salaries:
            return {
                'has_data': False,
                'message': '資料不足以比較薪資趨勢'
            }
        
        current_median = np.median(current_salaries)
        previous_median = np.median(previous_salaries)
        
        change = current_median - previous_median
        change_pct = (change / previous_median) * 100 if previous_median > 0 else 0
        
        return {
            'has_data': True,
            'current_median': int(current_median),
            'previous_median': int(previous_median),
            'change': int(change),
            'change_percentage': round(change_pct, 1),
            'trend': 'up' if change_pct > 5 else ('down' if change_pct < -5 else 'stable'),
            'current_mean': int(np.mean(current_salaries)),
            'previous_mean': int(np.mean(previous_salaries)),
        }
