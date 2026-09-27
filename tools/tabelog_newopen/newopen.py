"""
食べログの新規オープン店を抽出して CSV に保存する（毎朝8時に GitHub Actions で実行）

- 一覧は「ニューオープン」条件＋新着順で取得し、各店舗ページの「オープン日」で絞り込む
- 一度出力した店は seen.json に記録し、翌日以降は出さない（毎日「新しく見つかった店」だけが並ぶ）

実行: python3 newopen.py [--config config.json] [--out-dir ../../data/tabelog_newopen]
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import re
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

JST = timezone(timedelta(hours=9))
HERE = Path(__file__).resolve().parent
DEFAULT_OUT = HERE.parent.parent / "data" / "tabelog_newopen"

LIST_URL = "https://tabelog.com/{area}/rstLst/{page}/?SrtT=nod&ChkNewOpen=1"
RESTAURANT_URL_RE = re.compile(r"https://tabelog\.com/[a-z]+/A\d{4}/A\d{6}/(\d+)/")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/128.0 Safari/537.36",
    "Accept-Language": "ja,en;q=0.8",
}

CSV_COLUMNS = ["発見日", "オープン日", "店名", "ジャンル", "電話番号", "住所", "評価", "食べログURL"]


def parse_open_date(text: str) -> date | None:
    """「2026年9月20日」「2026年9月」などを日付にする（日が無ければ1日扱い）"""
    m = re.search(r"(\d{4})年\s*(\d{1,2})月(?:\s*(\d{1,2})日)?", text or "")
    if not m:
        return None
    return date(int(m.group(1)), int(m.group(2)), int(m.group(3) or 1))


def extract_restaurant_urls(html: str) -> list[str]:
    urls: list[str] = []
    for m in RESTAURANT_URL_RE.finditer(html):
        if m.group(0) not in urls:
            urls.append(m.group(0))
    return urls


def parse_restaurant(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    info: dict[str, str] = {}
    # 店舗基本情報の表（店名・ジャンル・予約・お問い合わせ・住所…）を見出し→値で読む
    for row in soup.select("table tr"):
        th, td = row.find("th"), row.find("td")
        if th and td:
            key = th.get_text(strip=True)
            info.setdefault(key, td.get_text(" ", strip=True))

    def pick(*selectors: str) -> str:
        for sel in selectors:
            el = soup.select_one(sel)
            if el and el.get_text(strip=True):
                return el.get_text(" ", strip=True)
        return ""

    phone = pick(".rstinfo-table__tel-num") or info.get("予約・お問い合わせ") or info.get("電話番号", "")
    phone_match = re.search(r"0\d{1,4}-?\d{1,4}-?\d{3,4}", phone)
    address = pick(".rstinfo-table__address") or info.get("住所", "")
    address = re.sub(r"\s*大きな地図を見る.*$", "", address)
    opened = pick(".rstinfo-opened-date") or info.get("オープン日", "")
    return {
        "name": info.get("店名") or pick("h2.display-name", "h1"),
        "genre": info.get("ジャンル", ""),
        "phone": phone_match.group(0) if phone_match else "",
        "address": address,
        "rating": pick(".rdheader-rating__score-val-dtl"),
        "open_date": parse_open_date(opened),
        "url": url,
    }


def is_target(shop: dict, today: date, days: int, phone: str) -> bool:
    opened = shop["open_date"]
    if opened is None or opened > today + timedelta(days=60) or opened < today - timedelta(days=days):
        return False
    if phone == "with" and not shop["phone"]:
        return False
    if phone == "without" and shop["phone"]:
        return False
    return True


class Fetcher:
    def __init__(self, delay: tuple[float, float] = (1.5, 3.0)) -> None:
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.delay = delay

    def get(self, url: str) -> str | None:
        time.sleep(random.uniform(*self.delay))
        try:
            res = self.session.get(url, timeout=20)
        except requests.RequestException as exc:
            print(f"  取得失敗 {url}: {exc.__class__.__name__}", file=sys.stderr)
            return None
        if res.status_code != 200:
            print(f"  取得失敗 {url}: HTTP {res.status_code}", file=sys.stderr)
            return None
        res.encoding = res.apparent_encoding or "utf-8"
        return res.text


def run(config: dict, out_dir: Path, fetcher: Fetcher | None = None, today: date | None = None) -> list[dict]:
    fetcher = fetcher or Fetcher()
    today = today or datetime.now(JST).date()
    out_dir.mkdir(parents=True, exist_ok=True)
    seen_path = out_dir / "seen.json"
    seen: dict[str, str] = json.loads(seen_path.read_text("utf-8")) if seen_path.exists() else {}

    found: list[dict] = []
    for area in config["areas"]:
        for page in range(1, config.get("pages", 3) + 1):
            html = fetcher.get(LIST_URL.format(area=area, page=page))
            if not html:
                break
            urls = extract_restaurant_urls(html)
            print(f"{area} {page}ページ目: {len(urls)}件")
            if not urls:
                break
            for url in urls:
                shop_id = RESTAURANT_URL_RE.match(url).group(1)
                if shop_id in seen:
                    continue
                detail = fetcher.get(url)
                if not detail:
                    continue
                shop = parse_restaurant(detail, url)
                # 対象外の店も記録して、翌日以降に同じページを取り直さない
                seen[shop_id] = today.isoformat()
                if is_target(shop, today, config.get("days", 30), config.get("phone", "any")):
                    print(f"  ◎ {shop['name']}（{shop['open_date']}）")
                    found.append(shop)

    found.sort(key=lambda s: s["open_date"], reverse=True)
    if found:
        out_path = out_dir / f"{today.isoformat()}.csv"
        with out_path.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_COLUMNS)
            for s in found:
                writer.writerow([today.isoformat(), s["open_date"].isoformat(), s["name"], s["genre"],
                                 s["phone"], s["address"], s["rating"], s["url"]])
        print(f"{len(found)}件を保存しました: {out_path}")
    else:
        print("新しいオープン店は見つかりませんでした")
    seen_path.write_text(json.dumps(seen, ensure_ascii=False, indent=0, sort_keys=True), "utf-8")
    return found


def main() -> None:
    parser = argparse.ArgumentParser(description="食べログの新規オープン店を抽出")
    parser.add_argument("--config", default=str(HERE / "config.json"))
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT))
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text("utf-8"))
    run(config, Path(args.out_dir))


if __name__ == "__main__":
    main()
