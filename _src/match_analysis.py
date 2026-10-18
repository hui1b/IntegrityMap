import json, collections, difflib, re, io, sys

new = json.load(open('data.json', encoding='utf-8'))['points']
old_idx = json.load(open('_src/map_index.json', encoding='utf-8'))
old_rank = json.load(open('_src/map_rank.json', encoding='utf-8'))
oldm = {str(p['ID']): p for p in old_idx['data']['map']['data']}
oldr = {str(r['ID']): r for r in old_rank['data']['data']}
old = []
for pid, mp in oldm.items():
    r = oldr.get(pid, {})
    old.append({
        'id': pid,
        'title': mp.get('title', ''),
        'schoolName': mp.get('schoolName', ''),
        'summary': (r.get('summary') or '').strip(),
        'link': r.get('link') or '',
        'address': (r.get('address') or mp.get('subTitle') or '').strip(),
        'categoryId': '',
    })

out = io.StringIO()
def w(*a): print(*a, file=out)

# 1) exact (title, school)
by_ts = collections.defaultdict(list)
for p in old: by_ts[(p['title'], p['schoolName'])].append(p)
by_t = collections.defaultdict(list)
for p in old: by_t[p['title']].append(p)
by_school = collections.defaultdict(list)
for p in old: by_school[p['schoolName']].append(p)

def norm(s):
    return re.sub(r'[\s《》（）()、·—\-–,，。.；;:：“”"\'‘’]', '', s or '')

by_norm_t = collections.defaultdict(list)
for p in old: by_norm_t[norm(p['title'])].append(p)

match = {}
unmatched = []
for p in new:
    if (p['title'], p['schoolName']) in by_ts:
        match[p['id']] = ('exact_title_school', by_ts[(p['title'], p['schoolName'])][0]); continue
    if p['title'] in by_t:
        match[p['id']] = ('exact_title', by_t[p['title']][0]); continue
    nt = norm(p['title'])
    if nt in by_norm_t:
        match[p['id']] = ('norm_title', by_norm_t[nt][0]); continue
    # containment within same school
    cands = by_school.get(p['schoolName'], [])
    hit = None
    for c in cands:
        nc = norm(c['title'])
        if nt and nc and (nt in nc or nc in nt):
            hit = c; break
    if hit:
        match[p['id']] = ('contains_same_school', hit); continue
    # fuzzy within same school
    best = None; bestr = 0
    for c in cands:
        r = difflib.SequenceMatcher(None, nt, norm(c['title'])).ratio()
        if r > bestr: bestr = r; best = c
    if best and bestr >= 0.75:
        match[p['id']] = ('fuzzy_same_school_%.2f' % bestr, best); continue
    unmatched.append(p)

w('NEW:', len(new), 'OLD:', len(old))
w('matched:', len(match), 'unmatched:', len(unmatched))
kinds = collections.Counter(v[0].split('_0')[0] for v in match.values())
for k, v in sorted(kinds.items()): w('  ', k, v)
w()
w('=== UNMATCHED NEW (no counterpart found) ===')
for p in unmatched:
    w(p['id'], '|', p['schoolName'], '|', p['title'], '|', p['category'])
    # show best fuzzy candidate overall
    best = None; bestr = 0
    for c in old:
        r = difflib.SequenceMatcher(None, norm(p['title']), norm(c['title'])).ratio()
        if r > bestr: bestr = r; best = c
    if best:
        w('     best global fuzzy %.2f: %s | %s' % (bestr, best['schoolName'], best['title']))
w()
w('=== MATCHED but summary/link missing in old? ===')
cnt_missing = 0
for pid, (kind, o) in match.items():
    if not o['summary'] or not o['link']:
        cnt_missing += 1
        w(pid, kind, 'summary_len', len(o['summary']), 'link', bool(o['link']))
w('count missing in old:', cnt_missing)

open('_src/match_report.txt', 'w', encoding='utf-8').write(out.getvalue())
print('wrote report')
