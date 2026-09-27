"""
コマンドラインから実行する場合の入口

例: python3 cli.py --pref 東京都 --city 豊島区 --category イタリア料理 --phone with
引数を省略すると、都道府県・業種などを番号で選ぶ対話モードになる。
"""
from __future__ import annotations

import argparse
from datetime import datetime

import scraper
from options import CATEGORIES, PREFECTURES, fetch_cities

PHONE_CHOICES = {"any": "指定なし", "with": "電話番号あり", "without": "電話番号なし"}
MODE_CHOICES = {
    scraper.MODE_ORDER_NO_UBER: "オンライン注文あり・Uber Eatsなし",
    scraper.MODE_NO_UBER: "Uber Eatsなし（注文ボタンが無い店も含む）",
}


def choose(title: str, items: list[str], allow_free: bool = False, allow_blank: bool = False) -> str:
    print(f"\n■ {title}")
    for i, item in enumerate(items, 1):
        print(f"  {i:>3}. {item}")
    hint = "番号" + ("または自由入力" if allow_free else "") + ("（空欄で指定なし）" if allow_blank else "")
    while True:
        answer = input(f"{hint} > ").strip()
        if not answer and allow_blank:
            return ""
        if answer.isdigit() and 1 <= int(answer) <= len(items):
            return items[int(answer) - 1]
        if answer and allow_free:
            return answer


def main() -> None:
    parser = argparse.ArgumentParser(description="Google マップから Uber Eats 未対応の店舗を抽出")
    parser.add_argument("--pref", choices=PREFECTURES, help="都道府県")
    parser.add_argument("--city", help="市区町村（例: 豊島区）")
    parser.add_argument("--category", help="業種（例: イタリア料理）")
    parser.add_argument("--phone", choices=PHONE_CHOICES, help="電話番号の有無")
    parser.add_argument("--mode", choices=MODE_CHOICES, default=scraper.MODE_ORDER_NO_UBER)
    parser.add_argument("--limit", type=int, default=100, help="調査する店舗数の上限（既定 100）")
    parser.add_argument("--no-strict-area", action="store_true", help="指定地域外の店も残す")
    parser.add_argument("--headed", action="store_true", help="ブラウザ画面を表示して実行")
    parser.add_argument("--out", help="出力CSVのパス")
    args = parser.parse_args()

    interactive = args.pref is None
    pref = args.pref or choose("都道府県", PREFECTURES)
    city = args.city
    if city is None and interactive:
        cities = fetch_cities(pref)
        city = choose("市区町村", cities, allow_free=True, allow_blank=True) if cities \
            else input("\n■ 市区町村（空欄で指定なし）> ").strip()
    category = args.category or (choose("業種", CATEGORIES, allow_free=True) if interactive else "飲食店")
    phone = args.phone or (
        {v: k for k, v in PHONE_CHOICES.items()}[choose("電話番号", list(PHONE_CHOICES.values()))]
        if interactive else "any"
    )

    cond = scraper.Condition(
        prefecture=pref, city=city or "", category=category, phone=phone, mode=args.mode,
        limit=args.limit, strict_area=not args.no_strict_area,
    )
    out = args.out or f"gmaps_{pref}{cond.city}_{category}_{datetime.now():%Y%m%d_%H%M}.csv"
    print(f"\n条件: {cond.query} / {PHONE_CHOICES[phone]} / {MODE_CHOICES[cond.mode]} / 上限{cond.limit}件\n")
    places = scraper.run(cond, headless=not args.headed)
    scraper.write_csv(places, out)
    print(f"CSVを保存しました: {out}")


if __name__ == "__main__":
    main()
