"""食べログ 新規開店リスト（毎日の定期実行用）"""
import json
from pathlib import Path

import yaml

from . import master
from .models import UBER_FOUND, now_jst
from .pipeline import Criteria, _fill_area, _match_genre, _phone_ok, check_uber, post_webhook, write_csv
from .tabelog import TabelogClient, list_url


def load_config(path):
    cfg = yaml.safe_load(Path(path).read_text(encoding='utf-8')) or {}
    base = Path(path).resolve().parent.parent  # leadgen/ から見た相対パス
    for k in ('output_dir', 'state_file'):
        p = Path(cfg.get(k) or ('output' if k == 'output_dir' else 'state/tabelog_seen.json'))
        cfg[k] = p if p.is_absolute() else base / p
    return cfg


def load_seen(path):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except (FileNotFoundError, ValueError):
        return {}


def save_seen(path, seen):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(seen, ensure_ascii=False, indent=0), encoding='utf-8')


def run_daily(config_path, log=print, stop=lambda: False, dry_run=False):
    cfg = load_config(config_path)
    seen = load_seen(cfg['state_file'])
    first_run = not seen
    today = now_jst().strftime('%Y-%m-%d')
    items = master.genre_items(cfg.get('genre_large'), cfg.get('genre_small'))
    phone = cfg.get('phone') or 'any'
    client = TabelogClient(delay=float(cfg.get('tabelog_delay', 2.0)), log=log)
    shops = []
    for area in cfg.get('areas') or []:
        pref = master.prefecture(area['prefecture'])
        city = master.city(pref, area['city']) if area.get('city') else None
        first = list_url(pref['slug'], city['tabelog'] if city else None, new_open=True)
        log(f'食べログ 新規開店: {first}')
        for page, rows in client.iter_list(first, max_pages=int(cfg.get('max_pages', 5))):
            fresh = [r for r in rows if r['id'] not in seen]
            log(f'  {page}ページ目: {len(rows)}件中 新規 {len(fresh)}件')
            for row in fresh:
                if stop():
                    break
                seen[row['id']] = today
                if row['genre'] and not _match_genre(row['genre'], items):
                    continue
                shop = client.shop(row)
                if not shop:
                    continue
                _fill_area(shop)
                if not master.in_area(shop.address, pref, city) or not _phone_ok(shop, phone):
                    continue
                if not _match_genre(shop.genre, items):
                    continue
                shops.append(shop)
                log(f'    {shop.name} / {shop.genre} / オープン {shop.open_date or "不明"} / {shop.phone or "電話なし"}')
            # ニューオープン順なので、新しい店が1件もないページまで来たら終わり
            if not fresh or stop():
                break

    if cfg.get('check_uber', True) and shops:
        check_uber(shops, Criteria(screenshot_dir=str(cfg['output_dir'] / 'screenshots')), log, stop)
    if not cfg.get('include_found', False):
        shops = [s for s in shops if s.ubereats_status != UBER_FOUND]

    if cfg.get('find_contacts', False) and shops:
        from .contacts import fill_contacts
        fill_contacts(shops, log=log, stop=stop)

    out = write_csv(shops, cfg['output_dir'] / f'tabelog_new_{now_jst():%Y%m%d}.csv')
    log(f'出力: {out}（{len(shops)}件）' + ('　※初回のため、一覧に出ている店をまとめて取得しました' if first_run else ''))
    if not dry_run:
        save_seen(cfg['state_file'], seen)
        post_webhook(shops, f'食べログ新規開店 {today}', log=log)
    return shops, out
