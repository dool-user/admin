"""Uber Eats に店舗が載っているかをブラウザ（Playwright）で確認する

手順（1店舗ごと）
  1. 最初に https://www.ubereats.com/jp/near-me を開いて Cookie 等を受け取る
  2. 店舗の住所・緯度経度を配達先にして、Uber Eats の検索で店名を検索
     https://www.ubereats.com/jp/search?pl=<配達先>&q=<店名>
  3. 検索結果（画面の店舗カードと、画面が裏で受け取る検索結果データの両方）に同じ店名があれば「掲載あり」、
     検索結果が出たのに見つからなければ「未掲載」、画面が読めなかったときは「要確認」

Uber Eats は画面の作りを予告なく変えます。「要確認」ばかりになったら
  python -m leadgen check-uber --name 店名 --address 住所 --lat 緯度 --lng 経度 --headed
で実際の画面を見て、下の SELECTORS / API_HINTS を直してください。
"""
import base64
import json
import os
import re
import time
from pathlib import Path
from urllib.parse import quote

from .matching import same_shop
from .models import UBER_FOUND, UBER_NOT_FOUND, UBER_UNKNOWN

HOME = 'https://www.ubereats.com/jp/near-me'
SEARCH = 'https://www.ubereats.com/jp/search?pl={pl}&q={q}'
# 店舗カード（店舗ページへのリンク）
SELECTORS = ['a[href*="/store/"]']
# 検索結果データを返す通信の URL に含まれる文字列
API_HINTS = ['/_p/api/getSearchFeed', '/_p/api/getFeed', '/_p/api/getSearchSuggestions']


def place_param(address, lat, lng, place_id=''):
    """Uber Eats の配達先パラメータ pl（JSON を base64 にしたもの）"""
    data = {
        'address': address, 'reference': place_id, 'referenceType': 'google_places',
        'latitude': float(lat), 'longitude': float(lng),
    }
    raw = json.dumps(data, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    return base64.b64encode(raw).decode('ascii')


def store_names_from_json(obj, out=None):
    """検索結果データの中から店舗名（と店舗URL）を集める"""
    out = [] if out is None else out
    if isinstance(obj, dict):
        if any(k in obj for k in ('storeUuid', 'storeUUID', 'storeInfo')):
            title = obj.get('title') or (obj.get('storeInfo') or {}).get('title') or obj.get('name')
            if isinstance(title, dict):
                title = title.get('text') or title.get('richText', {}).get('text')
            url = obj.get('actionUrl') or obj.get('url') or ''
            if isinstance(title, str) and title:
                out.append((title, url if isinstance(url, str) else ''))
        for v in obj.values():
            store_names_from_json(v, out)
    elif isinstance(obj, list):
        for v in obj:
            store_names_from_json(v, out)
    return out


class UberEatsChecker:
    def __init__(self, headed=False, wait=6.0, delay=2.0, screenshot_dir=None, log=print):
        self.headed = headed
        self.wait = wait
        self.delay = delay
        self.screenshot_dir = Path(screenshot_dir) if screenshot_dir else None
        self.log = log

    def __enter__(self):
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        # 手元の Chrome/Chromium を使う場合は LEADGEN_CHROMIUM にパスを入れる（通常は不要）
        self._browser = self._pw.chromium.launch(headless=not self.headed,
                                                 executable_path=os.environ.get('LEADGEN_CHROMIUM') or None)
        self._ctx = self._browser.new_context(locale='ja-JP', timezone_id='Asia/Tokyo',
                                              viewport={'width': 1280, 'height': 900})
        self.page = self._ctx.new_page()
        self._responses = []
        self.page.on('response', self._on_response)
        try:
            self.page.goto(HOME, wait_until='domcontentloaded', timeout=45000)
            time.sleep(2)
        except Exception as e:  # noqa: BLE001 - 最初の画面が開けなくても検索は試す
            self.log(f'  Uber Eats のトップを開けませんでした: {e}')
        return self

    def __exit__(self, *exc):
        self._browser.close()
        self._pw.stop()

    def _on_response(self, res):
        if any(h in res.url for h in API_HINTS):
            try:
                self._responses.append(res.json())
            except Exception:  # noqa: BLE001 - JSON 以外は無視
                self._responses.append(None)

    def check(self, shop):
        """(判定, 該当した店名, 該当した店のURL) を返す"""
        if shop.lat is None or shop.lng is None:
            return UBER_UNKNOWN, '位置情報なし', ''
        place_id = shop.source_id if shop.source == 'Googleマップ' else ''
        url = SEARCH.format(pl=quote(place_param(shop.address, shop.lat, shop.lng, place_id)), q=quote(shop.name))
        self._responses = []
        try:
            self.page.goto(url, wait_until='domcontentloaded', timeout=45000)
            try:
                self.page.wait_for_load_state('networkidle', timeout=self.wait * 1000)
            except Exception:  # noqa: BLE001 - 通信が続くページもあるので時間で打ち切る
                pass
            time.sleep(1.5)
            cards = []
            for sel in SELECTORS:
                for a in self.page.query_selector_all(sel):
                    text = (a.inner_text() or '').strip().split('\n')[0]
                    href = a.get_attribute('href') or ''
                    if text:
                        cards.append((text, href))
            api_names = []
            for data in self._responses:
                if data:
                    store_names_from_json(data, api_names)
        except Exception as e:  # noqa: BLE001
            self._shot(shop)
            return UBER_UNKNOWN, f'画面エラー: {str(e)[:80]}', ''
        finally:
            time.sleep(self.delay)

        for name, href in cards + api_names:
            if same_shop(shop.name, name):
                if href.startswith('/'):
                    href = 'https://www.ubereats.com' + href
                return UBER_FOUND, name, href
        if cards or self._responses:
            return UBER_NOT_FOUND, '', ''
        # 検索結果が0件のときの表示（「一致する結果がありません」等）が出ていれば未掲載とみなす
        body = self.page.inner_text('body') if self.page else ''
        if re.search(r'見つかりません|結果はありません|一致する.*ありません|No results', body):
            return UBER_NOT_FOUND, '', ''
        self._shot(shop)
        return UBER_UNKNOWN, '検索結果を読み取れませんでした', ''

    def _shot(self, shop):
        if not self.screenshot_dir:
            return
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        safe = re.sub(r'[\\/:*?"<>|\s]+', '_', shop.name)[:40]
        try:
            self.page.screenshot(path=str(self.screenshot_dir / f'{safe}.png'))
        except Exception:  # noqa: BLE001
            pass
