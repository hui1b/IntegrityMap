import json, collections, re, io, sys
sys.path.insert(0, '_src')
from restore_summaries import load_old, match_points, norm

obj = json.load(open('data.json', encoding='utf-8'))
new_points = obj['points']
old = load_old()
result = match_points(new_points, old)

# discover slug -> category from old data using categoryId via map_index
idx = json.load(open('_src/map_index.json', encoding='utf-8'))
cat_by_id = {}
# category membership from cat files
CATS = {'110865':'历史遗迹','110866':'纪念场馆','110867':'教育基地','110868':'艺术作品','110869':'文化品牌','110870':'学科课程'}
id_to_cat = {}
for cid in CATS:
    c = json.load(open(f'_src/cat_{cid}.json', encoding='utf-8'))
    for p in c['data']['map']['data']:
        id_to_cat[str(p['ID'])] = CATS[cid]

slug_by_cat = collections.defaultdict(collections.Counter)
for o in old:
    m = re.search(r'/a/([a-z]+)/', o['link'])
    if m and o['id'] in id_to_cat:
        slug_by_cat[m.group(1)][id_to_cat[o['id']]] += 1
print('slug -> category evidence:', dict(slug_by_cat), file=sys.stderr)
slug_to_cat = {s: c.most_common(1)[0][0] for s, c in slug_by_cat.items()}

out = io.StringIO()
def w(*a): print(*a, file=out)
w('slug map:', slug_to_cat)
w()
mism = 0
miss = 0
for p in new_points:
    kind, o = result[p['id']]
    if not o:
        continue
    m = re.search(r'/a/([a-z]+)/', o['link'])
    oldcat = slug_to_cat.get(m.group(1)) if m else None
    if oldcat is None:
        miss += 1
        w('UNKNOWN SLUG:', p['id'], p['title'], '| link', o['link'])
    elif oldcat != p['category']:
        mism += 1
        w('MISMATCH', p['id'], '| new:', p['category'], '| old:', oldcat)
        w('    NEW', p['schoolName'], '|', p['title'])
        w('    OLD', o['schoolName'], '|', o['title'], '|', o['link'])
w()
w('category mismatches:', mism, '| unknown slugs:', miss)
open('_src/category_validation.txt', 'w', encoding='utf-8').write(out.getvalue())
print('done')
