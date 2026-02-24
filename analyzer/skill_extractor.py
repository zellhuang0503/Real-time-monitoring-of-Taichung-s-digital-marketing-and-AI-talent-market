"""
技能萃取模組
從職缺描述中提取技能關鍵字
"""

import re
from collections import Counter
from typing import List, Dict, Tuple, Set
from config import SKILL_KEYWORDS


class SkillExtractor:
    """
    技能萃取器
    使用關鍵字比對從職缺資料中提取技能需求
    """
    
    def __init__(self):
        # 建立技能映射表（小寫 -> 標準名稱）
        self.skill_mapping = {}
        for standard_name, aliases in SKILL_KEYWORDS.items():
            for alias in aliases:
                self.skill_mapping[alias.lower()] = standard_name
                # 也加入標準名稱本身
                self.skill_mapping[standard_name.lower()] = standard_name
    
    def extract_skills(self, job_description: str = "", job_title: str = "") -> List[str]:
        """
        從職缺描述和標題中提取技能
        
        Args:
            job_description: 職缺描述文字（可選）
            job_title: 職缺標題
            
        Returns:
            技能列表
        """
        # 優先使用職缺描述，如果沒有則只用標題
        if job_description:
            text = f"{job_title} {job_description}".lower()
        else:
            text = job_title.lower() if job_title else ""
        
        if not text:
            return []
        
        found_skills = set()
        
        # 1. 直接關鍵字比對
        for alias, standard_name in self.skill_mapping.items():
            # 使用單詞邊界比對，避免部分匹配
            pattern = r'\b' + re.escape(alias.lower()) + r'\b'
            if re.search(pattern, text):
                found_skills.add(standard_name)
        
        # 2. 特殊模式比對（處理複合技能）
        # 例如 "Google Analytics 4" 應該被識別為 GA4
        if re.search(r'google\s*analytics\s*4|ga4', text):
            found_skills.add("GA4")
        
        if re.search(r'facebook\s*ads?|fb\s*ads?|meta\s*ads?', text):
            found_skills.add("Meta Ads")
        
        if re.search(r'instagram\s*ads?|ig\s*ads?', text):
            found_skills.add("Meta Ads")
        
        return list(found_skills)
    
    def analyze_jobs_skills(self, jobs: List[Dict]) -> Dict[str, Dict]:
        """
        分析所有職缺的技能需求
        
        Args:
            jobs: 職缺列表
            
        Returns:
            技能統計分析結果
        """
        skill_counter = Counter()
        skill_by_category = {}
        
        # 為每個職缺提取技能
        for job in jobs:
            description = job.get('job_description', '')
            title = job.get('title', '')
            category = job.get('job_category', '其他')
            
            # 從描述和標題萃取技能（如果描述為空，只用標題）
            skills = self.extract_skills(description or None, title)
            
            # 全域計數
            skill_counter.update(skills)
            
            # 按類別計數
            if category not in skill_by_category:
                skill_by_category[category] = Counter()
            skill_by_category[category].update(skills)
        
        # 整理結果
        total_jobs = len(jobs)
        
        skill_stats = []
        for skill, count in skill_counter.most_common(30):
            skill_stats.append({
                'skill': skill,
                'count': count,
                'percentage': round(count / total_jobs * 100, 1) if total_jobs > 0 else 0,
            })
        
        return {
            'total_jobs_analyzed': total_jobs,
            'unique_skills_found': len(skill_counter),
            'top_skills': skill_stats,
            'skill_by_category': {
                cat: [{'skill': s, 'count': c} for s, c in counter.most_common(10)]
                for cat, counter in skill_by_category.items()
            }
        }
    
    def get_skill_combinations(self, jobs: List[Dict], top_n: int = 20) -> List[Dict]:
        """
        分析常見的技能組合
        
        Args:
            jobs: 職缺列表
            top_n: 返回前 N 個組合
            
        Returns:
            技能組合列表
        """
        from itertools import combinations
        
        combination_counter = Counter()
        
        for job in jobs:
            description = job.get('job_description', '')
            title = job.get('title', '')
            skills = self.extract_skills(description, title)
            
            # 只考慮有 2-4 個技能的職缺
            if 2 <= len(skills) <= 4:
                # 產生所有可能的組合
                for r in range(2, min(len(skills) + 1, 4)):
                    for combo in combinations(sorted(skills), r):
                        combination_counter[combo] += 1
        
        # 返回最常見的組合
        result = []
        for combo, count in combination_counter.most_common(top_n):
            result.append({
                'skills': list(combo),
                'count': count,
                'description': ' + '.join(combo)
            })
        
        return result
    
    def compare_skill_trends(self, current_jobs: List[Dict], previous_jobs: List[Dict]) -> Dict:
        """
        比較兩個時期的技能需求變化
        
        Args:
            current_jobs: 當期職缺
            previous_jobs: 前期職缺
            
        Returns:
            技能趨勢比較結果
        """
        current_skills = Counter()
        previous_skills = Counter()
        
        # 統計當期技能
        for job in current_jobs:
            skills = self.extract_skills(
                job.get('job_description', ''),
                job.get('title', '')
            )
            current_skills.update(skills)
        
        # 統計前期技能
        for job in previous_jobs:
            skills = self.extract_skills(
                job.get('job_description', ''),
                job.get('title', '')
            )
            previous_skills.update(skills)
        
        # 計算變化
        all_skills = set(current_skills.keys()) | set(previous_skills.keys())
        
        trends = []
        for skill in all_skills:
            current_count = current_skills.get(skill, 0)
            previous_count = previous_skills.get(skill, 0)
            
            if previous_count > 0:
                change_pct = ((current_count - previous_count) / previous_count) * 100
            else:
                change_pct = float('inf') if current_count > 0 else 0
            
            trends.append({
                'skill': skill,
                'current_count': current_count,
                'previous_count': previous_count,
                'change': current_count - previous_count,
                'change_percentage': round(change_pct, 1) if change_pct != float('inf') else None,
                'trend': 'up' if change_pct > 10 else ('down' if change_pct < -10 else 'stable')
            })
        
        # 按變化幅度排序
        trends.sort(key=lambda x: abs(x['change']), reverse=True)
        
        return {
            'rising_skills': [t for t in trends if t['trend'] == 'up'][:10],
            'declining_skills': [t for t in trends if t['trend'] == 'down'][:10],
            'all_trends': trends[:30]
        }
