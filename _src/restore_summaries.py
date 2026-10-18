"""Restore `summary` and `link` on the new dataset from the original website data.

Usage:
    python restore_summaries.py --dry-run     # write audit report only
    python restore_summaries.py --apply       # write data.json + data.js
"""
import argparse
import collections
import io
import json
import re
from difflib import SequenceMatcher

ROOT = __file__.rsplit('\\', 2)[0] if '\\' in __file__ else '.'
DATA_JSON = 'data.json'
DATA_JS = 'data.js'

# Manually confirmed equivalences: new point id -> original website ID
MANUAL = {
    '87': '2276619',   # 浙江工业大学 于谦清廉史迹与思想 == 《风孰与高——于谦传》
    '190': '2274750',  # 重庆邮电大学 长波楼与重庆邮电大学档案馆 == 重庆邮电大学的长波楼与档案馆
    '225': '2274983',  # 丽江师范学院 《桂梅赞》（歌剧） == 民族歌剧《桂梅赞》
}


def norm(s):
    return re.sub(r'[\s《》（）()、·—\-–,，。.；;:：“”"\'‘’]', '', s or '')


def load_old():
    idx = json.load(open('_src/map_index.json', encoding='utf-8'))
    rank = json.load(open('_src/map_rank.json', encoding='utf-8'))
    oldm = {str(p['ID']): p for p in idx['data']['map']['data']}
    oldr = {str(r['ID']): r for r in rank['data']['data']}
    old = []
    for pid, mp in oldm.items():
        r = oldr.get(pid, {})
        old.append({
            'id': pid,
            'title': (mp.get('title') or '').strip(),
            'schoolName': (mp.get('schoolName') or '').strip(),
            'summary': (r.get('summary') or '').strip(),
            'link': (r.get('link') or '').strip(),
        })
    return old


def match_points(new_points, old):
    by_id = {p['id']: p for p in old}
    by_school = collections.defaultdict(list)
    for p in old:
        by_school[p['schoolName']].append(p)

    result = {}
    for np in new_points:
        pid = np['id']
        if pid in MANUAL and MANUAL[pid] in by_id:
            result[pid] = ('manual', by_id[MANUAL[pid]])
            continue

        nt = norm(np['title'])
        cands = by_school.get(np['schoolName'], [])

        # 1. exact title within the same school
        hit = next((c for c in cands if c['title'] == np['title']), None)
        if hit:
            result[pid] = ('exact_ts', hit); continue

        # 2. punctuation/whitespace-insensitive title within the same school
        hit = next((c for c in cands if norm(c['title']) == nt), None)
        if hit:
            result[pid] = ('norm_title', hit); continue

        # 3. one title contained in the other within the same school.
        #    When several candidates contain the new title, take the one with
        #    the closest length (i.e. the least extra wording).
        contained = []
        for c in cands:
            nc = norm(c['title'])
            if nt and nc and (nt in nc or nc in nt):
                contained.append((abs(len(nc) - len(nt)), c))
        if contained:
            contained.sort(key=lambda x: x[0])
            result[pid] = ('containment', contained[0][1]); continue

        # 4. fuzzy match, same school only
        best, bestr = None, 0.0
        for c in cands:
            r = SequenceMatcher(None, nt, norm(c['title'])).ratio()
            if r > bestr:
                bestr, best = r, c
        if best and bestr >= 0.80:
            result[pid] = ('fuzzy_%.2f' % bestr, best); continue

        result[pid] = ('none', None)
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args()

    obj = json.load(open(DATA_JSON, encoding='utf-8'))
    new_points = obj['points']
    old = load_old()
    result = match_points(new_points, old)

    # duplicate target audit
    usage = collections.defaultdict(list)
    for pid, (kind, o) in result.items():
        if o:
            usage[o['id']].append(pid)

    out = io.StringIO()
    def w(*a): print(*a, file=out)

    kinds = collections.Counter(k for k, _ in result.values())
    w('NEW TOTAL:', len(new_points), '| OLD TOTAL:', len(old))
    w('MATCH KINDS:', dict(sorted(kinds.items())))
    w()
    w('=== UNMATCHED NEW POINTS (%d) ===' % kinds.get('none', 0))
    for pid, (kind, o) in result.items():
        if kind == 'none':
            np = next(x for x in new_points if x['id'] == pid)
            w(pid, '|', np['schoolName'], '|', np['title'], '|', np['category'])
    w()
    w('=== OLD ENTRIES USED BY MULTIPLE NEW POINTS ===')
    for oid, pids in usage.items():
        if len(pids) > 1:
            o = next(p for p in old if p['id'] == oid)
            w('OLD', oid, '|', o['schoolName'], '|', o['title'])
            for pid in pids:
                np = next(x for x in new_points if x['id'] == pid)
                w('    <- NEW', pid, '|', np['schoolName'], '|', np['title'], '|', result[pid][0])
    w()
    w('=== OLD ENTRIES NOT USED (%d) ===' % sum(1 for p in old if p['id'] not in usage))
    for p in old:
        if p['id'] not in usage:
            w(p['id'], '|', p['schoolName'], '|', p['title'])
    w()
    w('=== ALL CONTAINMENT / FUZZY MATCHES (review) ===')
    for pid, (kind, o) in result.items():
        if kind.startswith('contain') or kind.startswith('fuzzy'):
            np = next(x for x in new_points if x['id'] == pid)
            w('[%s] NEW %s | %s | %s' % (kind, pid, np['schoolName'], np['title']))
            w('           OLD %s | %s | %s' % (o['id'], o['schoolName'], o['title']))

    open('_src/restore_report.txt', 'w', encoding='utf-8').write(out.getvalue())
    print('report written: _src/restore_report.txt')

    if not args.apply:
        print('dry run only; pass --apply to write files')
        return

    restored = 0
    for p in new_points:
        kind, o = result[p['id']]
        if o:
            p['summary'] = o['summary']
            p['link'] = o['link']
            restored += 1
    with open(DATA_JSON, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write('\n')
    with open(DATA_JS, 'w', encoding='utf-8') as f:
        f.write('window.MAP_DATA = ' + json.dumps(obj, ensure_ascii=False, indent=1) + ';\n')
    print('restored summary+link on', restored, 'points; wrote data.json and data.js')


if __name__ == '__main__':
    main()
