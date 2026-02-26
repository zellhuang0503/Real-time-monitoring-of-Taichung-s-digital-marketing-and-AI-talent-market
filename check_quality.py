import sys, json, glob, os, re
sys.stdout.reconfigure(encoding='utf-8')

analysis_files = sorted(glob.glob('data/analysis_*.json'))

print(f'共 {len(analysis_files)} 個分析檔案:')
print()
print(f'{"#":<3} {"檔案":<40} {"職缺數":>7} {"來源":<35} {"薪資筆":>7} {"其他%":>8}')
print('-' * 105)

for i, af in enumerate(analysis_files):
    with open(af, 'r', encoding='utf-8') as f:
        d = json.load(f)
    fname = os.path.basename(af)
    total = d.get('summary', {}).get('total_jobs', 0)
    sources = d.get('summary', {}).get('sources_distribution', {})
    src_str = ' '.join(f'{k}:{v}' for k, v in sources.items())
    has_sal = d.get('salary_analysis', {}).get('has_salary_info', 0)
    exp_dist = d.get('experience_requirements', {}).get('distribution', [])
    pct_other = next((e['percentage'] for e in exp_dist if e['experience'] == '其他/未註明'), 0)
    print(f'{i+1:<3} {fname:<40} {total:>7,} {src_str:<35} {has_sal:>7} {pct_other:>7.1f}%')

# Week vs Analysis mapping
print()
print('=== 週次 vs 分析檔案對應 ===')
week_files_map = {}
for fp in glob.glob('report/taichung_job_market_week*.html'):
    m = re.search(r'week(\d+)', fp)
    if m:
        week_files_map[int(m.group(1))] = fp
sorted_weeks = sorted(week_files_map.keys())

print(f'週次 HTML 報告: {sorted_weeks}')
print(f'分析檔案數量: {len(analysis_files)}')
print()
print(f'{"週次":<8} {"對應分析檔":<40} {"職缺數":>8} {"來源":>30} {"薪資":>6} {"其他%":>8}  狀態')
print('-' * 115)

for i, wn in enumerate(sorted_weeks):
    af = analysis_files[i] if i < len(analysis_files) else None
    if not af:
        print(f'Week {wn}: 無對應分析檔案')
        continue
    with open(af, 'r', encoding='utf-8') as f:
        d = json.load(f)
    fname = os.path.basename(af)
    total = d.get('summary', {}).get('total_jobs', 0)
    sources = d.get('summary', {}).get('sources_distribution', {})
    src_str = ' '.join(f'{k}:{v}' for k, v in sources.items())
    has_sal = d.get('salary_analysis', {}).get('has_salary_info', 0)
    exp_dist = d.get('experience_requirements', {}).get('distribution', [])
    pct_other = next((e['percentage'] for e in exp_dist if e['experience'] == '其他/未註明'), 0)

    # 多來源 = 有 1111 或 518
    has_multi_src = len(sources) > 1
    # 有薪資資料
    has_salary = has_sal > 0
    # 經驗分布正常（其他<50%）
    exp_ok = pct_other < 50

    if has_multi_src and has_salary and exp_ok:
        status = 'COMPLETE'
    elif not has_multi_src and not has_salary:
        status = 'INCOMPLETE - 只有104，無薪資'
    elif not has_salary:
        status = 'PARTIAL - 無薪資'
    else:
        status = 'PARTIAL'

    print(f'Week {wn:<4} {fname:<40} {total:>8,} {src_str:>30} {has_sal:>6} {pct_other:>7.1f}%  {status}')
