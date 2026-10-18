import json, io, sys

def load(p):
    return json.load(open(p, encoding='utf-8'))

out = io.StringIO()
def w(*a):
    print(*a, file=out)

# Full field inventory
idx = load('_src/map_index.json')
md = idx['data']['map']['data']
pm = idx['data']['provinceMap']
w('=== map_index map.data: count =', len(md))
w('map point fields:', sorted(md[0].keys()))
w('sample point:', json.dumps(md[0], ensure_ascii=False))
w()
w('=== provinceMap type:', type(pm).__name__)
w('provinceMap keys:', list(pm.keys()) if isinstance(pm, dict) else 'n/a')
if isinstance(pm, dict) and 'data' in pm:
    pd = pm['data']
    w('provinceMap.data type:', type(pd).__name__, 'len:', len(pd) if hasattr(pd,'__len__') else 'n/a')
    if isinstance(pd, list):
        w('sample province:', json.dumps(pd[0], ensure_ascii=False))
    elif isinstance(pd, dict):
        k = list(pd.keys())
        w('province keys sample:', k[:5])
        w('sample province val:', json.dumps(pd[k[0]], ensure_ascii=False))
w()

rank = load('_src/map_rank.json')
rd = rank['data']
w('=== rank data keys:', list(rd.keys()))
w('rank total:', rd.get('total'))
rl = rd['data']
w('rank list count:', len(rl))
w('rank row fields:', sorted(rl[0].keys()))
w('sample rank row:', json.dumps(rl[0], ensure_ascii=False))
w()

# Join analysis: how many titles match between map points and rank rows
map_titles = set(p['title'] for p in md)
rank_titles = set(r['title'] for r in rl)
w('map titles:', len(map_titles), 'rank titles:', len(rank_titles))
w('titles in both:', len(map_titles & rank_titles))
w('map-only titles:', len(map_titles - rank_titles))
w('rank-only titles:', len(rank_titles - map_titles))

# map ID vs rank ID overlap
map_ids = set(str(p['ID']) for p in md)
rank_ids = set(str(r['ID']) for r in rl)
w('ID overlap:', len(map_ids & rank_ids))

# schoolName join
map_schools = set(p['schoolName'] for p in md)
rank_schools = set(r['schoolName'] for r in rl)
w('schoolName overlap:', len(map_schools & rank_schools), 'map schools:', len(map_schools), 'rank schools:', len(rank_schools))

# check title+school join
map_ts = set((p['title'], p['schoolName']) for p in md)
rank_ts = set((r['title'], r['schoolName']) for r in rl)
w('title+school in both:', len(map_ts & rank_ts))
w('map title+school count:', len(map_ts), 'rank title+school count:', len(rank_ts))

# category sizes
w()
w('=== category files ===')
catmap = {110865:'历史遗迹',110866:'纪念场馆',110867:'教育基地',110868:'艺术作品',110869:'文化品牌',110870:'学科课程'}
for cid, cname in catmap.items():
    c = load(f'_src/cat_{cid}.json')
    cm = c['data']['map']['data']
    w(f'{cid} {cname}: {len(cm)} points, fields={sorted(cm[0].keys()) if cm else "EMPTY"}')
    if cm:
        w('   sample:', json.dumps(cm[0], ensure_ascii=False))

open('_src/analysis.txt','w',encoding='utf-8').write(out.getvalue())
print('done')
