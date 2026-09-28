"""都道府県・市区町村マスタと業種マスタ"""
import json
import unicodedata
from functools import lru_cache
from pathlib import Path

import yaml

DATA = Path(__file__).resolve().parent / 'data'


@lru_cache
def prefectures():
    return json.loads((DATA / 'areas.json').read_text(encoding='utf-8'))


def prefecture(name_or_code):
    for p in prefectures():
        if name_or_code in (p['name'], p['code'], p['slug']):
            return p
    raise KeyError(f'都道府県が見つかりません: {name_or_code}')


def city(pref, name_or_code):
    for c in pref['cities']:
        if name_or_code in (c['name'], c['code']):
            return c
    raise KeyError(f'{pref["name"]} に市区町村が見つかりません: {name_or_code}')


@lru_cache
def genres():
    """{大区分: [{name, tabelog, google, match}, ...]}"""
    return yaml.safe_load((DATA / 'genres.yaml').read_text(encoding='utf-8'))


def genre_items(large=None, small=None):
    """選択された大区分・小区分に当てはまる小区分のリスト（未指定なら空リスト＝業種指定なし）"""
    if not large:
        return []
    items = genres()[large]
    if small:
        return [g for g in items if g['name'] == small]
    return items


def _norm_addr(s):
    s = unicodedata.normalize('NFKC', s or '')
    return s.replace('ヶ', 'ケ').replace('ヵ', 'カ').replace(' ', '')


def split_address(address):
    """住所から (都道府県名, 市区町村名) を取り出す。政令指定都市は区まで返す（例：横浜市中区）"""
    a = _norm_addr(address)
    for p in prefectures():
        if not a.startswith(p['name']):
            continue
        rest = a[len(p['name']):]
        best = None
        for c in p['cities']:
            n = _norm_addr(c['name'])
            if rest.startswith(n) and (best is None or len(n) > len(_norm_addr(best['name']))):
                best = c
        return p['name'], best['name'] if best else ''
    return '', ''


def in_area(address, pref, city_row=None):
    """住所が指定の都道府県・市区町村内か（政令指定都市を選んだ場合は配下の区も含む）"""
    p, c = split_address(address)
    if p != pref['name']:
        return False
    return city_row is None or c == city_row['name'] or c.startswith(city_row['name'])
