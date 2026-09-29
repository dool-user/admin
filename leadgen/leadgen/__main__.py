"""コマンドラインから使う

  python -m leadgen search --source both --pref 東京都 --city 新宿区 --large ラーメン・麺類 --small ラーメン --phone yes
  python -m leadgen daily                       # 食べログ新規開店（config/daily.yaml）
  python -m leadgen contacts output/list.csv    # 問い合わせフォーム・Instagram を追加
  python -m leadgen areas --pref 東京都          # 市区町村の一覧
  python -m leadgen genres                      # 業種の一覧
  python -m leadgen check-genres                # 業種マスタの食べログURLが生きているか確認
  python -m leadgen check-uber --name 店名 --address 住所 --lat 35.69 --lng 139.70 --headed
"""
import argparse
import sys
from pathlib import Path

from . import master
from .models import Shop, now_jst

ROOT = Path(__file__).resolve().parent.parent


def main(argv=None):
    ap = argparse.ArgumentParser(prog='python -m leadgen')
    sub = ap.add_subparsers(dest='cmd', required=True)

    s = sub.add_parser('search', help='条件を指定してリストを作る')
    s.add_argument('--source', choices=['tabelog', 'google', 'both'], default='both')
    s.add_argument('--pref', required=True, help='都道府県（例：東京都）')
    s.add_argument('--city', help='市区町村（例：新宿区）。省略で都道府県全体')
    s.add_argument('--large', help='業種・大区分（例：和食）')
    s.add_argument('--small', help='業種・小区分（例：寿司）')
    s.add_argument('--phone', choices=['any', 'yes', 'no'], default='any', help='電話番号 any=指定なし yes=あり no=なし')
    s.add_argument('--limit', type=int, default=100, help='取得元ごとの最大件数')
    s.add_argument('--no-uber', action='store_true', help='Uber Eats の確認をしない')
    s.add_argument('--include-found', action='store_true', help='Uber Eats 掲載ありの店も出力する')
    s.add_argument('--headed', action='store_true', help='Uber Eats 確認のブラウザを表示する')
    s.add_argument('--contacts', action='store_true', help='公式サイトから問い合わせフォーム・Instagram・営業お断り表記を探す')
    s.add_argument('--out', help='出力CSV（省略時は output/list_日時.csv）')

    ct = sub.add_parser('contacts', help='作成済みのCSVに問い合わせフォーム・Instagramを追加する')
    ct.add_argument('csv', help='search / daily で出力したCSV')
    ct.add_argument('--out', help='出力CSV（省略時は元のファイル名_contacts.csv）')

    d = sub.add_parser('daily', help='食べログ新規開店リスト')
    d.add_argument('--config', default=str(ROOT / 'config' / 'daily.yaml'))
    d.add_argument('--dry-run', action='store_true', help='取得済みの記録と Webhook 送信をしない')

    a = sub.add_parser('areas', help='都道府県・市区町村の一覧')
    a.add_argument('--pref')
    sub.add_parser('genres', help='業種の一覧')
    sub.add_parser('check-genres', help='業種マスタの食べログURLを確認')

    u = sub.add_parser('check-uber', help='1店舗だけ Uber Eats を確認（動作確認用）')
    u.add_argument('--name', required=True)
    u.add_argument('--address', required=True)
    u.add_argument('--lat', type=float, required=True)
    u.add_argument('--lng', type=float, required=True)
    u.add_argument('--headed', action='store_true')

    args = ap.parse_args(argv)

    if args.cmd == 'search':
        from .pipeline import Criteria, run, write_csv
        c = Criteria(source=args.source, prefecture=args.pref, city=args.city, genre_large=args.large,
                     genre_small=args.small, phone=args.phone, limit=args.limit, check_uber=not args.no_uber,
                     include_found=args.include_found, uber_headed=args.headed,
                     screenshot_dir=str(ROOT / 'output' / 'screenshots'), find_contacts=args.contacts)
        shops = run(c)
        out = write_csv(shops, args.out or ROOT / 'output' / f'list_{now_jst():%Y%m%d_%H%M}.csv')
        print(f'出力: {out}（{len(shops)}件）')

    elif args.cmd == 'contacts':
        from .contacts import fill_contacts
        from .pipeline import read_csv, write_csv
        shops = fill_contacts(read_csv(args.csv))
        src = Path(args.csv)
        out = write_csv(shops, args.out or src.with_name(src.stem + '_contacts.csv'))
        n = sum(1 for s in shops if s.channel)
        print(f'出力: {out}（{len(shops)}件中、送れる店 {n}件）')

    elif args.cmd == 'daily':
        from .daily import run_daily
        run_daily(args.config, dry_run=args.dry_run)

    elif args.cmd == 'areas':
        for p in master.prefectures():
            if args.pref and args.pref not in (p['name'], p['code']):
                continue
            print(p['name'], '：', '、'.join(c['name'] for c in p['cities']) if args.pref else len(p['cities']))

    elif args.cmd == 'genres':
        for large, items in master.genres().items():
            print(large, '：', '、'.join(g['name'] for g in items))

    elif args.cmd == 'check-genres':
        from .tabelog import TabelogClient, list_url
        client = TabelogClient(delay=1.5)
        bad = 0
        for large, items in master.genres().items():
            for g in items:
                if not g.get('tabelog'):
                    continue
                url = list_url('tokyo', genre_slug=g['tabelog'])
                ok = client.get(url) is not None
                bad += not ok
                print(('OK ' if ok else 'NG ') + f'{large} / {g["name"]}: {url}')
        sys.exit(1 if bad else 0)

    elif args.cmd == 'check-uber':
        from .ubereats import UberEatsChecker
        shop = Shop(source='手入力', name=args.name, address=args.address, lat=args.lat, lng=args.lng)
        with UberEatsChecker(headed=args.headed, screenshot_dir=ROOT / 'output' / 'screenshots') as ch:
            print(ch.check(shop))
            if args.headed:
                input('ブラウザを確認したら Enter で終了します')


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, KeyError) as e:
        sys.exit(f'エラー: {e}')
