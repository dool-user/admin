"""抽出の本体：条件 → 食べログ／Googleマップから取得 → 絞り込み → Uber Eats 確認 → CSV"""
import csv
import json
import os
from dataclasses import dataclass
from pathlib import Path

import requests

from . import master
from .matching import same_shop
from .models import COLUMNS, UBER_FOUND, to_row

SOURCES = {'tabelog': '食べログ', 'google': 'Googleマップ', 'both': 'どちらも'}
PHONES = {'any': '指定なし', 'yes': 'あり', 'no': 'なし'}


@dataclass
class Criteria:
    source: str = 'both'            # tabelog / google / both
    prefecture: str = '東京都'
    city: str | None = None         # None なら都道府県全体
    genre_large: str | None = None
    genre_small: str | None = None
    phone: str = 'any'              # any / yes / no
    limit: int = 100                # 取得元ごとの最大件数
    check_uber: bool = True
    include_found: bool = False     # True なら Uber Eats 掲載ありの店も出力する
    tabelog_delay: float = 2.0
    uber_headed: bool = False
    screenshot_dir: str | None = None


def _match_genre(genre_text, items):
    if not items:
        return True
    return any(w in (genre_text or '') for g in items for w in g['match'])


def _fill_area(shop):
    shop.prefecture, shop.city = master.split_address(shop.address)
    return shop


def _phone_ok(shop, phone):
    return phone == 'any' or (phone == 'yes') == shop.has_phone


def collect_tabelog(c, log=print, stop=lambda: False):
    from .tabelog import TabelogClient, list_url

    pref = master.prefecture(c.prefecture)
    city = master.city(pref, c.city) if c.city else None
    items = master.genre_items(c.genre_large, c.genre_small)
    client = TabelogClient(delay=c.tabelog_delay, log=log)
    # ジャンルURLがある小区分はそのURLで、ない場合は全ジャンルの一覧をジャンル表記で絞り込む
    slugs = [g['tabelog'] for g in items if g.get('tabelog')] if items else [None]
    if items and len(slugs) < len(items):
        slugs.append(None)
    shops, seen = [], set()
    for slug in slugs:
        first = list_url(pref['slug'], city['tabelog'] if city else None, slug)
        log(f'食べログ: {first}')
        for page, rows in client.iter_list(first, max_pages=60):
            for row in rows:
                if stop() or len(shops) >= c.limit:
                    return shops
                if row['id'] in seen or (row['genre'] and not _match_genre(row['genre'], items)):
                    continue
                seen.add(row['id'])
                shop = client.shop(row)
                if not shop:
                    continue
                _fill_area(shop)
                if not master.in_area(shop.address, pref, city) or not _phone_ok(shop, c.phone):
                    continue
                if not _match_genre(shop.genre, items):
                    continue
                shops.append(shop)
                log(f'  [{len(shops)}] {shop.name} / {shop.genre} / {shop.phone or "電話なし"}')
    return shops


def collect_google(c, log=print, stop=lambda: False):
    from .google_places import PlacesClient

    pref = master.prefecture(c.prefecture)
    city = master.city(pref, c.city) if c.city else None
    items = master.genre_items(c.genre_large, c.genre_small)
    area = pref['name'] + (city['name'] if city else '')
    client = PlacesClient(log=log)
    queries = [f'{g["google"]} {area}' for g in items] or [f'飲食店 {area}']
    shops, seen = [], set()
    for q in queries:
        if stop() or len(shops) >= c.limit:
            break
        log(f'Googleマップ: 「{q}」')
        for shop in client.search(q):
            if shop.source_id in seen:
                continue
            seen.add(shop.source_id)
            _fill_area(shop)
            if not master.in_area(shop.address, pref, city) or not _phone_ok(shop, c.phone):
                continue
            shops.append(shop)
            log(f'  [{len(shops)}] {shop.name} / {shop.genre} / {shop.phone or "電話なし"}')
            if len(shops) >= c.limit:
                break
    return shops


def _digits(phone):
    return ''.join(ch for ch in phone if ch.isdigit())


def merge(tabelog, google):
    """両方で見つかった店は1行にまとめる（電話番号が同じ、または同じ市区町村で店名が一致）"""
    out = list(tabelog)
    for g in google:
        hit = next((t for t in tabelog if (_digits(g.phone) and _digits(g.phone) == _digits(t.phone))
                    or (g.city == t.city and same_shop(g.name, t.name))), None)
        if hit:
            hit.source = '両方'
            hit.other_url = g.url
            hit.phone = hit.phone or g.phone
            if hit.lat is None:
                hit.lat, hit.lng = g.lat, g.lng
        else:
            out.append(g)
    return out


def check_uber(shops, c, log=print, stop=lambda: False):
    from .ubereats import UberEatsChecker

    with UberEatsChecker(headed=c.uber_headed, screenshot_dir=c.screenshot_dir, log=log) as checker:
        for i, shop in enumerate(shops, 1):
            if stop():
                break
            shop.ubereats_status, shop.ubereats_hit, shop.ubereats_url = checker.check(shop)
            log(f'Uber Eats 確認 {i}/{len(shops)}: {shop.name} → {shop.ubereats_status} {shop.ubereats_hit}')
    return shops


def run(c, log=print, stop=lambda: False):
    tabelog, google = [], []
    if c.source in ('tabelog', 'both'):
        tabelog = collect_tabelog(c, log, stop)
    if c.source in ('google', 'both'):
        google = collect_google(c, log, stop)
    shops = merge(tabelog, google)
    if c.check_uber and shops:
        check_uber(shops, c, log, stop)
    if not c.include_found:
        shops = [s for s in shops if s.ubereats_status != UBER_FOUND]
    return shops


def write_csv(shops, path):
    """Excel でそのまま開けるよう BOM 付き UTF-8 で保存"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=[label for label, _ in COLUMNS])
        w.writeheader()
        for s in shops:
            w.writerow(to_row(s))
    return path


def post_webhook(shops, title, url=None, log=print):
    """Google スプレッドシート（gas/leadgen-receiver.gs）等へ送る。URL は環境変数 LEADGEN_WEBHOOK_URL"""
    url = url or os.environ.get('LEADGEN_WEBHOOK_URL', '')
    if not url:
        return False
    body = {'title': title, 'columns': [label for label, _ in COLUMNS], 'rows': [to_row(s) for s in shops]}
    r = requests.post(url, data=json.dumps(body, ensure_ascii=False).encode('utf-8'),
                      headers={'Content-Type': 'application/json'}, timeout=60)
    log(f'Webhook 送信: {r.status_code} {r.text[:200]}')
    return r.ok

