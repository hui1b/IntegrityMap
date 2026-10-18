import json, collections, re, io

new = json.load(open('data.json', encoding='utf-8'))['points']
old_idx = json.load(open('_src/map_index.json', encoding='utf-8'))
old_rank = json.load(open('_src/map_rank.json', encoding='utf-8'))
oldm = {str(p['ID']): p for p in old_idx['data']['map']['data']}
oldr = {str(r['ID']): r for r in old_rank['data']['data']}
old = []
for pid, mp in oldm.items():
    r = oldr.get(pid, {})
    old.append({'id': pid, 'title': mp.get('title',''), 'schoolName': mp.get('schoolName',''),
                'summary': (r.get('summary') or '').strip(), 'link': r.get('link') or ''})

def norm(s): return re.sub(r'[\s《》（）()、·—\-–,，。.；;:：“”"\'‘’]', '', s or '')
by_ts = {(p['title'], p['schoolName']): p for p in old}
by_t = collections.defaultdict(list)
for p in old: by_t[p['title']].append(p)
by_norm_t = collections.defaultdict(list)
for p in old: by_norm_t[norm(p['title'])].append(p)
by_school = collections.defaultdict(list)
for p in old: by_school[p['schoolName']].append(p)

matched_old_ids = set()
for p in new:
    if (p['title'], p['schoolName']) in by_ts:
        matched_old_ids.add(by_ts[(p['title'], p['schoolName'])]['id']); continue
    if p['title'] in by_t:
        matched_old_ids.add(by_t[p['title']][0]['id']); continue
    nt = norm(p['title'])
    if nt in by_norm_t:
        matched_old_ids.add(by_norm_t[nt][0]['id']); continue
    cands = by_school.get(p['schoolName'], [])
    hit = None
    for c in cands:
        nc = norm(c['title'])
        if nt and nc and (nt in nc or nc in nt): hit = c; break
    if hit: matched_old_ids.add(hit['id'])

out = io.StringIO()
def w(*a): print(*a, file=out)

w('=== LEFT-OVER OLD (not used by any new point): %d ===' % (len(old) - len(matched_old_ids)))
for p in old:
    if p['id'] not in matched_old_ids:
        w(p['id'], '|', p['schoolName'], '|', p['title'])
        w('     link:', p['link'])
        w('     summary:', p['summary'][:80])
w()

# For each unmatched new, show all old entries for the same school
unmatched = ['82','83','84','85','87','190','225']
w('=== ALL OLD ENTRIES FOR SCHOOLS OF UNMATCHED NEW ===')
for p in new:
    if p['id'] in unmatched:
        w('NEW', p['id'], '|', p['schoolName'], '|', p['title'])
        for c in by_school.get(p['schoolName'], []):
            w('    OLD', c['id'], '|', c['title'], '| link:', c['link'])
        w()

open('_src/unmatched_report.txt','w',encoding='utf-8').write(out.getvalue())
print('ok')
