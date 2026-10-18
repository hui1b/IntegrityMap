import json

def load(p):
    return json.load(open(p, encoding='utf-8'))

idx = load('_src/map_index.json')
rank = load('_src/map_rank.json')

CATS = [
    ('110865', '历史遗迹'),
    ('110866', '纪念场馆'),
    ('110867', '教育基地'),
    ('110868', '艺术作品'),
    ('110869', '文化品牌'),
    ('110870', '学科课程'),
]

# Build ID -> map point (lng/lat/subTitle) and ID -> rank row (address/summary/link)
map_by_id = {str(p['ID']): p for p in idx['data']['map']['data']}
rank_by_id = {str(r['ID']): r for r in rank['data']['data']}

# Build ID -> categoryId via category files
id_to_cat = {}
for cid, cname in CATS:
    c = load(f'_src/cat_{cid}.json')
    for p in c['data']['map']['data']:
        id_to_cat[str(p['ID'])] = cid

points = []
missing = []
for pid, mp in map_by_id.items():
    r = rank_by_id.get(pid, {})
    cat_id = id_to_cat.get(pid, '')
    cat_name = dict(CATS).get(cat_id, '')
    lng = mp.get('shortTitle', '')
    lat = mp.get('upTitle', '')
    try:
        lng_f = float(lng) if lng not in ('', None) else None
        lat_f = float(lat) if lat not in ('', None) else None
    except (ValueError, TypeError):
        lng_f = lat_f = None
    if lng_f is None or lat_f is None or lng_f == 0 or lat_f == 0:
        missing.append(pid)
    points.append({
        'id': pid,
        'title': mp.get('title', ''),
        'schoolName': mp.get('schoolName', ''),
        'categoryId': cat_id,
        'category': cat_name,
        'address': (r.get('address') or mp.get('subTitle') or '').strip(),
        'summary': (r.get('summary') or '').strip(),
        'link': r.get('link') or '',
        'lng': lng_f,
        'lat': lat_f,
    })

# provinces
prov = idx['data']['provinceMap']['data']
PROV_NAMES = {
    '110000': '北京', '120000': '天津', '130000': '河北', '140000': '山西',
    '150000': '内蒙古', '210000': '辽宁', '220000': '吉林', '230000': '黑龙江',
    '310000': '上海', '320000': '江苏', '330000': '浙江', '340000': '安徽',
    '350000': '福建', '360000': '江西', '370000': '山东', '410000': '河南',
    '420000': '湖北', '430000': '湖南', '440000': '广东', '450000': '广西',
    '460000': '海南', '500000': '重庆', '510000': '四川', '520000': '贵州',
    '530000': '云南', '540000': '西藏', '610000': '陕西', '620000': '甘肃',
    '630000': '青海', '640000': '宁夏', '650000': '新疆', '710000': '台湾',
    '810000': '香港', '820000': '澳门',
}
provinces = []
for code, val in prov.items():
    if code == '':
        continue
    provinces.append({'code': code, 'name': PROV_NAMES.get(code, code), 'total': val.get('total', 0)})
provinces.sort(key=lambda x: -x['total'])

total = idx['data']['total']
meta = {
    'title': '廉洁文化地图',
    'subtitle': '全国高校廉洁文化点位',
    'source': '全国高校思想政治工作网',
    'totalPoints': total['contentTotal'],
    'totalSchools': total['schoolTotal'],
    'categories': [{'id': '', 'name': '全部', 'count': total['contentTotal']}]
                 + [{'id': cid, 'name': cname, 'count': total['catalogContentTotal'].get(cid, 0)}
                    for cid, cname in CATS],
    'provinces': provinces,
}

data = {'meta': meta, 'points': points}

# sanity
cat_counts = {}
for p in points:
    cat_counts[p['category']] = cat_counts.get(p['category'], 0) + 1
print('points total:', len(points))
print('category counts:', cat_counts)
print('points with coords:', len(points) - len(missing))
print('missing coords IDs:', missing if missing else 'none')
print('points with summary:', sum(1 for p in points if p['summary']))
print('points with link:', sum(1 for p in points if p['link']))
print('schools unique:', len(set(p['schoolName'] for p in points)))
print('provinces:', len(provinces))

with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=1)

# Also emit data.js
js = 'window.MAP_DATA = ' + json.dumps(data, ensure_ascii=False, indent=1) + ';\n'
with open('data.js', 'w', encoding='utf-8') as f:
    f.write(js)
print('wrote data.json and data.js')
