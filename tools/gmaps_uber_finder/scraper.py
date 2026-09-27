"""
Google マップから店舗を集め、「オンラインで注文」に Uber Eats が無い店を抽出する。

Google マップの画面構成は予告なく変わるため、要素の特定は文言（「オンラインで注文」
「注文可能プロバイダ」など）を優先し、クラス名は補助的にだけ使っている。
"""
from __future__ import annotations

import csv
import os
import random
import re
import time
import urllib.parse
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Callable, Iterator

ORDER_LABELS = ("オンラインで注文", "オンライン注文", "Order online")
PROVIDER_MARKERS = ("注文可能プロバイダ", "Order with")
MODE_CHIPS = ("宅配", "受け取り", "Delivery", "Pickup")
END_OF_LIST = ("リストの最後に到達しました", "You've reached the end of the list")

UBER_RE = re.compile(r"uber\s*eats|ウーバー\s*イーツ", re.I)
# プロバイダ名の行ではないもの（手数料・お届け時間・見出しなど）
PROVIDER_NOISE_RE = re.compile(
    r"手数料|分後|お届け|予定|受け取り|宅配|配達|注文|プロバイダ|営業|閉店|fee|deliver|pickup|min\b|order",
    re.I,
)

PHONE_ANY, PHONE_WITH, PHONE_WITHOUT = "any", "with", "without"
MODE_ORDER_NO_UBER = "order_no_uber"  # 注文ボタンあり、かつ Uber Eats なし
MODE_NO_UBER = "no_uber"              # Uber Eats なし（注文ボタン自体が無い店も含む）

CSV_COLUMNS = [
    ("name", "店名"),
    ("category", "業種"),
    ("address", "住所"),
    ("phone", "電話番号"),
    ("website", "ウェブサイト"),
    ("rating", "評価"),
    ("reviews", "口コミ数"),
    ("has_online_order", "オンライン注文"),
    ("providers", "注文可能プロバイダ"),
    ("url", "GoogleマップURL"),
]


@dataclass
class Condition:
    prefecture: str
    city: str = ""
    category: str = "飲食店"
    phone: str = PHONE_ANY
    mode: str = MODE_ORDER_NO_UBER
    limit: int = 100          # 調査する店舗数の上限
    strict_area: bool = True  # 住所が指定の都道府県・市区町村に一致する店だけ残す

    @property
    def query(self) -> str:
        return f"{self.category} {self.prefecture}{self.city}".strip()


@dataclass
class Place:
    url: str = ""
    name: str = ""
    category: str = ""
    address: str = ""
    phone: str = ""
    website: str = ""
    rating: str = ""
    reviews: str = ""
    has_online_order: bool = False
    providers: list[str] = field(default_factory=list)
    has_uber_eats: bool = False

    def to_row(self) -> dict:
        row = {key: getattr(self, key) for key, _ in CSV_COLUMNS}
        row["has_online_order"] = "あり" if self.has_online_order else "なし"
        row["providers"] = " / ".join(self.providers)
        return row


# ---------------------------------------------------------------- 判定ロジック

def search_url(query: str) -> str:
    return "https://www.google.com/maps/search/" + urllib.parse.quote(query) + "?hl=ja"


def _compact(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def area_matches(address: str, prefecture: str, city: str) -> bool:
    addr = _compact(address)
    if not addr:
        return False
    if city:
        return _compact(city) in addr
    return _compact(prefecture) in addr


def phone_matches(phone: str, wanted: str) -> bool:
    if wanted == PHONE_WITH:
        return bool(phone)
    if wanted == PHONE_WITHOUT:
        return not phone
    return True


def uber_matches(place: Place, mode: str) -> bool:
    if place.has_uber_eats:
        return False
    if mode == MODE_ORDER_NO_UBER:
        return place.has_online_order
    return True


def matches(place: Place, cond: Condition) -> bool:
    if cond.strict_area and not area_matches(place.address, cond.prefecture, cond.city):
        return False
    return phone_matches(place.phone, cond.phone) and uber_matches(place, cond.mode)


def strip_label(text: str) -> str:
    """「住所: 東京都…」「電話番号: 03-…」のような先頭ラベルを外す"""
    return re.sub(r"^[^:：]{1,10}[:：]\s*", "", (text or "").strip())


def parse_rating(text: str) -> tuple[str, str]:
    rating = re.search(r"\d\.\d", text or "")
    reviews = re.search(r"\(([\d,]+)\)", text or "")
    return (rating.group(0) if rating else "", reviews.group(1).replace(",", "") if reviews else "")


def extract_providers(text: str) -> list[str]:
    """「注文可能プロバイダ:」以降の行からプロバイダ名だけを取り出す"""
    start = -1
    for marker in PROVIDER_MARKERS:
        idx = text.find(marker)
        if idx >= 0:
            start = text.find("\n", idx)
            break
    if start < 0:
        return []
    providers: list[str] = []
    for line in text[start:].splitlines():
        line = line.strip().strip("›>").strip()
        if not line or len(line) > 40 or PROVIDER_NOISE_RE.search(line):
            continue
        if re.fullmatch(r"[\d\s〜~\-:：分円¥￥,.]+", line):
            continue
        if line not in providers:
            providers.append(line)
    return providers


def provider_from_url(href: str) -> str:
    host = urllib.parse.urlparse(href).hostname or ""
    return host.removeprefix("www.")


# ---------------------------------------------------------------- ブラウザ操作

@contextmanager
def open_browser(headless: bool = True) -> Iterator:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=headless,
            args=["--lang=ja-JP"],
            # 既に入っている Chromium を使いたい場合は環境変数でパスを指定できる
            executable_path=os.environ.get("CHROMIUM_PATH") or None,
        )
        context = browser.new_context(
            locale="ja-JP",
            timezone_id="Asia/Tokyo",
            viewport={"width": 1400, "height": 900},
        )
        try:
            yield context.new_page()
        finally:
            browser.close()


def _accept_consent(page) -> None:
    if "consent." not in page.url:
        return
    for label in ("すべて同意", "Accept all", "同意する"):
        button = page.get_by_role("button", name=label)
        if button.count():
            button.first.click()
            page.wait_for_load_state("domcontentloaded")
            return


_COLLECT_JS = """
() => Array.from(document.querySelectorAll('div[role="feed"] a[href*="/maps/place/"]'))
  .map(a => a.href)
"""


def collect_place_urls(page, cond: Condition, log: Callable[[str], None],
                       should_stop: Callable[[], bool]) -> list[str]:
    page.goto(search_url(cond.query), wait_until="domcontentloaded")
    _accept_consent(page)
    try:
        page.wait_for_selector('div[role="feed"], div[role="main"] h1', timeout=20000)
    except Exception:
        log("検索結果を読み込めませんでした")
        return []
    if not page.query_selector('div[role="feed"]'):
        # 1件しかヒットしないと店舗ページへ直接移動する
        return [page.url] if "/maps/place/" in page.url else []

    urls: list[str] = []
    stagnant = 0
    while len(urls) < cond.limit and stagnant < 6 and not should_stop():
        found = page.evaluate(_COLLECT_JS)
        before = len(urls)
        for href in found:
            if href not in urls:
                urls.append(href)
        log(f"検索結果を読み込み中… {len(urls)}件")
        feed_text = page.inner_text('div[role="feed"]')
        if any(marker in feed_text for marker in END_OF_LIST):
            break
        stagnant = stagnant + 1 if len(urls) == before else 0
        page.eval_on_selector('div[role="feed"]', "el => el.scrollTo(0, el.scrollHeight)")
        page.wait_for_timeout(1500)
    return urls[: cond.limit]


_DETAIL_JS = """
() => {
  const main = document.querySelector('div[role="main"]') || document.body;
  const text = el => el ? (el.innerText || el.textContent || '').trim() : '';
  const phone = main.querySelector('[data-item-id^="phone:tel:"]');
  const address = main.querySelector('[data-item-id="address"]');
  const website = main.querySelector('a[data-item-id="authority"]');
  return {
    name: text(main.querySelector('h1')),
    category: text(main.querySelector('button.DkEaL')),
    address: address ? (address.getAttribute('aria-label') || text(address)) : '',
    phoneLabel: phone ? (phone.getAttribute('aria-label') || text(phone)) : '',
    phoneId: phone ? phone.getAttribute('data-item-id') : '',
    website: website ? website.href : '',
    rating: text(main.querySelector('div.F7nice')),
  };
}
"""

# 「オンラインで注文」ボタンを探して目印を付ける
_FIND_ORDER_JS = """
(labels) => {
  const main = document.querySelector('div[role="main"]') || document.body;
  for (const el of main.querySelectorAll('a, button, [role="button"]')) {
    const label = (el.getAttribute('aria-label') || '') + ' ' + (el.innerText || '');
    if (labels.some(l => label.includes(l))) {
      el.setAttribute('data-gm-order', '1');
      return {found: true, href: el.tagName === 'A' ? el.href : ''};
    }
  }
  return {found: false, href: ''};
}
"""

# 「注文可能プロバイダ」を含む注文パネルを特定し、テキストとリンクを返す。
# 宅配／受け取りのチップには目印を付けておく
_READ_ORDER_PANEL_JS = """
([markers, titles, chips]) => {
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let node = null;
  while (walker.nextNode()) {
    if (markers.some(m => walker.currentNode.textContent.includes(m))) { node = walker.currentNode.parentElement; break; }
  }
  if (!node) return null;
  let panel = node;
  for (let i = 0; i < 15 && panel.parentElement && panel !== document.body; i++) {
    if (panel.getAttribute('role') === 'dialog' || titles.some(t => (panel.innerText || '').includes(t))) break;
    panel = panel.parentElement;
  }
  let n = 0;
  for (const el of panel.querySelectorAll('button, [role="button"]')) {
    const label = (el.innerText || '').replace(/[×✕\\s]/g, '');
    if (chips.includes(label) && !el.disabled && el.getAttribute('aria-disabled') !== 'true') {
      el.setAttribute('data-gm-chip', String(n++));
    }
  }
  return {
    text: panel.innerText || '',
    links: Array.from(panel.querySelectorAll('a[href]')).map(a => a.href),
    chips: n,
  };
}
"""


def _read_order_panel(page) -> dict | None:
    return page.evaluate(_READ_ORDER_PANEL_JS, [list(PROVIDER_MARKERS), list(ORDER_LABELS), list(MODE_CHIPS)])


def read_order_providers(page) -> tuple[bool, list[str], bool]:
    """(オンライン注文の有無, プロバイダ一覧, Uber Eats の有無) を返す"""
    info = page.evaluate(_FIND_ORDER_JS, list(ORDER_LABELS))
    if not info["found"]:
        return False, [], False

    href = info["href"]
    if href and "google." not in (urllib.parse.urlparse(href).hostname or ""):
        # プロバイダが1社だけだと外部サイトへの直リンクになっていることがある
        return True, [provider_from_url(href)], bool(UBER_RE.search(href.replace("-", "")))

    page.click('[data-gm-order="1"]', timeout=5000)
    try:
        page.wait_for_function(
            "markers => markers.some(m => document.body.innerText.includes(m))",
            arg=list(PROVIDER_MARKERS), timeout=8000,
        )
    except Exception:
        return True, [], False

    texts: list[str] = []
    links: list[str] = []
    panel = _read_order_panel(page)
    chip_count = panel["chips"] if panel else 0
    if panel:
        texts.append(panel["text"])
        links += panel["links"]
    # 宅配／受け取りで表示されるプロバイダが変わるので両方を開く
    for i in range(chip_count):
        try:
            page.click(f'[data-gm-chip="{i}"]', timeout=3000)
            page.wait_for_timeout(800)
        except Exception:
            continue
        panel = _read_order_panel(page)
        if panel:
            texts.append(panel["text"])
            links += panel["links"]

    providers: list[str] = []
    for text in texts:
        for name in extract_providers(text):
            if name not in providers:
                providers.append(name)
    joined = "\n".join(texts + links)
    has_uber = bool(UBER_RE.search(joined) or "ubereats.com" in joined)
    return True, providers, has_uber


def inspect_place(page, url: str) -> Place:
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_selector('div[role="main"] h1', timeout=20000)
    page.wait_for_timeout(1200)
    raw = page.evaluate(_DETAIL_JS)
    rating, reviews = parse_rating(raw["rating"])
    phone = strip_label(raw["phoneLabel"]) or raw["phoneId"].removeprefix("phone:tel:")
    place = Place(
        url=url,
        name=raw["name"],
        category=raw["category"],
        address=strip_label(raw["address"]),
        phone=phone,
        website=raw["website"],
        rating=rating,
        reviews=reviews,
    )
    place.has_online_order, place.providers, place.has_uber_eats = read_order_providers(page)
    return place


def run(cond: Condition,
        on_log: Callable[[str], None] = print,
        on_match: Callable[[Place], None] = lambda p: None,
        should_stop: Callable[[], bool] = lambda: False,
        headless: bool = True) -> list[Place]:
    results: list[Place] = []
    with open_browser(headless) as page:
        on_log(f"検索: {cond.query}")
        urls = collect_place_urls(page, cond, on_log, should_stop)
        on_log(f"{len(urls)}件の店舗を調査します")
        for i, url in enumerate(urls, 1):
            if should_stop():
                on_log("中止しました")
                break
            try:
                place = inspect_place(page, url)
            except Exception as exc:  # 1店舗の失敗で全体を止めない
                on_log(f"[{i}/{len(urls)}] 取得失敗: {exc.__class__.__name__}")
                continue
            hit = matches(place, cond)
            uber = "Uber Eatsあり" if place.has_uber_eats else ("注文ボタンなし" if not place.has_online_order else "Uber Eatsなし")
            on_log(f"[{i}/{len(urls)}] {'◎' if hit else '　'} {place.name}（{uber}）")
            if hit:
                results.append(place)
                on_match(place)
            time.sleep(random.uniform(1.0, 2.5))
    on_log(f"完了: {len(results)}件が条件に一致しました")
    return results


def write_csv(places: list[Place], path: str) -> None:
    # Excel で文字化けしないよう BOM 付き UTF-8
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([label for _, label in CSV_COLUMNS])
        for place in places:
            row = place.to_row()
            writer.writerow([row[key] for key, _ in CSV_COLUMNS])
