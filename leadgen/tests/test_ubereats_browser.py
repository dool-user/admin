"""UberEatsChecker を実際のブラウザで動かすテスト（Uber Eats の代わりに手元の偽サーバーを使う）"""
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import pytest

from leadgen import ubereats
from leadgen.models import UBER_FOUND, UBER_NOT_FOUND, UBER_UNKNOWN, Shop

pytest.importorskip('playwright')

# 検索された店名 → 偽の検索結果画面
PAGES = {
    # 店舗カードが出る（掲載あり）
    '麺屋 テスト 新宿店': '<a href="/jp/store/menya-test/abc"><h3>麺屋 テスト 新宿店</h3><p>4.5</p></a>',
    # 裏の通信で検索結果を受け取るが、該当店はない（未掲載）
    '居酒屋 たろう': '<div id="r"></div><script>fetch("/_p/api/getSearchFeedV1",{method:"POST"}).then(r=>r.json())'
           '.then(d=>{document.getElementById("r").textContent=d.data.feedItems.length})</script>',
    # 0件表示（未掲載）
    '鮨 さんぷる': '<p>「鮨 さんぷる」に一致する結果はありません</p>',
    # 何も読めない（要確認）
    '読めない店': '<p>住所を入力してください</p>',
}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, body, ctype='text/html; charset=utf-8'):
        b = body.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == '/search':
            q = parse_qs(u.query)
            assert q.get('pl'), 'pl（配達先）が付いていない'
            self._send('<html><body>' + PAGES[q['q'][0]] + '</body></html>')
        else:
            self._send('<html><body>home</body></html>')

    def do_POST(self):
        body = {'data': {'feedItems': [{'store': {'storeUuid': 'x', 'title': {'text': '別の店 新宿店'}}}]}}
        self._send(json.dumps(body, ensure_ascii=False), 'application/json')


@pytest.fixture(scope='module')
def checker():
    srv = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{srv.server_port}'
    mp = pytest.MonkeyPatch()
    mp.setattr(ubereats, 'HOME', base + '/')
    mp.setattr(ubereats, 'SEARCH', base + '/search?pl={pl}&q={q}')
    try:
        with ubereats.UberEatsChecker(wait=1, delay=0, log=lambda *_: None) as ch:
            yield ch
    except Exception as e:  # noqa: BLE001 - ブラウザが無い環境ではスキップ
        pytest.skip(f'ブラウザを起動できません: {e}')
    finally:
        mp.undo()
        srv.shutdown()


def shop(name, lat=35.69):
    return Shop(source='食べログ', name=name, address='東京都新宿区新宿3-1-1', lat=lat, lng=139.70)


def test_found(checker):
    status, hit, url = checker.check(shop('麺屋 テスト 新宿店'))
    assert status == UBER_FOUND and hit == '麺屋 テスト 新宿店' and url.endswith('/jp/store/menya-test/abc')


def test_not_found_by_api(checker):
    # 検索結果データは届いたが「別の店 新宿店」しかない
    assert checker.check(shop('居酒屋 たろう'))[0] == UBER_NOT_FOUND


def test_not_found_by_message(checker):
    assert checker.check(shop('鮨 さんぷる'))[0] == UBER_NOT_FOUND


def test_unknown(checker):
    assert checker.check(shop('読めない店'))[0] == UBER_UNKNOWN


def test_no_location(checker):
    assert checker.check(shop('読めない店', lat=None))[0] == UBER_UNKNOWN
