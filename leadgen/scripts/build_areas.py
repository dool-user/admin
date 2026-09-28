"""
都道府県・市区町村マスタ（leadgen/data/areas.json）を作り直す

元データ：総務省「全国地方公共団体コード」（令和6年1月1日現在）
  https://www.soumu.go.jp/denshijiti/code.html
この Excel を JSON 化した npm パッケージ @b4moss/jp-local-gov-id-data の prefectures/*.json を読み込みます。

使い方：
  npm pack @b4moss/jp-local-gov-id-data && tar xzf b4moss-jp-local-gov-id-data-*.tgz
  python3 scripts/build_areas.py package/prefectures

出力形式：
  [{"code": "13", "name": "東京都", "slug": "tokyo",
    "cities": [{"code": "13104", "name": "新宿区", "tabelog": "C13104"}, ...]}, ...]
  政令指定都市の区は "parent"（市の5桁コード）を持ち、食べログは市のページ＋住所の区名で絞り込む
"""
import json
import sys
from pathlib import Path

# 食べログの都道府県URL（https://tabelog.com/<slug>/）
SLUGS = [
    'hokkaido', 'aomori', 'iwate', 'miyagi', 'akita', 'yamagata', 'fukushima', 'ibaraki', 'tochigi', 'gunma',
    'saitama', 'chiba', 'tokyo', 'kanagawa', 'niigata', 'toyama', 'ishikawa', 'fukui', 'yamanashi', 'nagano',
    'gifu', 'shizuoka', 'aichi', 'mie', 'shiga', 'kyoto', 'osaka', 'hyogo', 'nara', 'wakayama',
    'tottori', 'shimane', 'okayama', 'hiroshima', 'yamaguchi', 'tokushima', 'kagawa', 'ehime', 'kochi', 'fukuoka',
    'saga', 'nagasaki', 'kumamoto', 'oita', 'miyazaki', 'kagoshima', 'okinawa',
]


def tabelog_code(code5):
    # 食べログは先頭の0を落とした団体コード（チェックディジットなし）：札幌市 01100 → C1100
    return 'C' + str(int(code5))


def main(src):
    out = []
    for i, slug in enumerate(SLUGS, start=1):
        data = json.loads((Path(src) / f'{i:02d}.json').read_text(encoding='utf-8'))
        muni = data['municipalities']
        # 政令指定都市＝後ろに「〇〇市〇〇区」が続く市
        names = {m['name'] for m in muni}
        designated = {n for n in names if n.endswith('市') and any(o.startswith(n) and o.endswith('区') and o != n for o in names)}
        city_code = {m['name']: m['code'][:5] for m in muni if m['name'] in designated}
        cities = []
        for m in muni:
            c = {'code': m['code'][:5], 'name': m['name']}
            parent = next((d for d in designated if m['name'].startswith(d) and m['name'] != d), None)
            if parent:
                c['parent'] = city_code[parent]
                c['tabelog'] = tabelog_code(city_code[parent])
            else:
                c['tabelog'] = tabelog_code(c['code'])
            cities.append(c)
        out.append({'code': f'{i:02d}', 'name': muni[0]['prefectureName'], 'slug': slug, 'cities': cities})
    dest = Path(__file__).resolve().parent.parent / 'leadgen' / 'data' / 'areas.json'
    dest.write_text(json.dumps(out, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print(dest, sum(len(p['cities']) for p in out), 'cities')


if __name__ == '__main__':
    main(sys.argv[1])
