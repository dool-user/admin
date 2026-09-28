import json
from pathlib import Path

import pytest

from leadgen import master, pipeline, tabelog
from leadgen.google_places import clean_address, to_shop
from leadgen.matching import core_name, same_shop
from leadgen.models import UBER_FOUND, UBER_NOT_FOUND, Shop
from leadgen.ubereats import place_param, store_names_from_json

FIX = Path(__file__).parent / 'fixtures'


def read(name):
    return (FIX / name).read_text(encoding='utf-8')


# ---- 地域・業種マスタ ----

def test_tabelog_city_codes_match_known_urls():
    # 食べログ上で確認できた URL と一致すること
    assert master.city(master.prefecture('東京都'), '新宿区')['tabelog'] == 'C13104'
    assert master.city(master.prefecture('北海道'), '札幌市')['tabelog'] == 'C1100'
    assert master.city(master.prefecture('神奈川県'), '川崎市')['tabelog'] == 'C14130'
    assert master.city(master.prefecture('大阪府'), '箕面市')['tabelog'] == 'C27220'
    # 政令指定都市の区は市のページを使う
    assert master.city(master.prefecture('兵庫県'), '神戸市中央区')['tabelog'] == 'C28100'


def test_split_address_and_area():
    assert master.split_address('東京都新宿区西新宿1-2-3') == ('東京都', '新宿区')
    assert master.split_address('神奈川県横浜市保土ヶ谷区岩間町1') == ('神奈川県', '横浜市保土ケ谷区')
    tokyo = master.prefecture('東京都')
    assert master.in_area('東京都中央区銀座1-1', tokyo, master.city(tokyo, '中央区'))
    assert not master.in_area('北海道札幌市中央区北1条', tokyo, master.city(tokyo, '中央区'))
    kana = master.prefecture('神奈川県')
    assert master.in_area('神奈川県横浜市中区山下町1', kana, master.city(kana, '横浜市'))


def test_genre_items():
    assert [g['name'] for g in master.genre_items('ラーメン・麺類', 'ラーメン')] == ['ラーメン']
    assert len(master.genre_items('和食')) > 5
    assert master.genre_items(None) == []


# ---- 食べログ ----

def test_list_url():
    assert tabelog.list_url('tokyo', 'C13104', 'ramen') == 'https://tabelog.com/tokyo/C13104/rstLst/ramen/'
    assert tabelog.list_url('tokyo', 'C13104', new_open=True) == 'https://tabelog.com/tokyo/C13104/rstLst/cond16-00-00/'
    assert tabelog.list_url('tokyo', page=3) == 'https://tabelog.com/tokyo/rstLst/3/'


def test_parse_list():
    items, nxt = tabelog.parse_list(read('tabelog_list.html'))
    assert [i['id'] for i in items] == ['13300001', '13300002']
    assert items[0]['name'] == '麺屋 テスト 新宿店'
    assert items[0]['genre'] == 'ラーメン、つけ麺'
    assert items[0]['rating'] == '3.45'
    assert nxt == 'https://tabelog.com/tokyo/C13104/rstLst/cond16-00-00/2/'


def test_parse_list_fallback_links():
    html = '<a href="/osaka/A2701/A270101/27000001/?lid=x">店A</a><a href="/osaka/rstLst/">一覧</a>'
    items, nxt = tabelog.parse_list(html)
    assert [(i['id'], i['name']) for i in items] == [('27000001', '店A')]
    assert nxt is None


def test_parse_detail_jsonld():
    d = tabelog.parse_detail(read('tabelog_detail.html'), '')
    assert d['name'] == '麺屋 テスト 新宿店'
    assert d['phone'] == '03-1234-5678'
    assert d['address'] == '東京都新宿区新宿3-1-1'
    assert (d['lat'], d['lng']) == (35.6905, 139.7049)
    assert d['open_date'] == '2026年9月20日'
    assert d['genre'] == 'ラーメン、つけ麺'
    assert not d['closed']


def test_parse_detail_table_only():
    d = tabelog.parse_detail(read('tabelog_detail_nold.html'), '')
    assert d['name'] == '鮨 さんぷる'
    assert d['phone'] == ''
    assert d['address'] == '東京都新宿区西新宿1-2-3'
    assert (d['lat'], d['lng']) == (35.6899, 139.6921)
    assert d['open_date'] == '2026年9月25日'


# ---- Googleマップ ----

def test_google_to_shop():
    s = to_shop({
        'id': 'ChIJxxx', 'displayName': {'text': 'カレー屋 サンプル'},
        'formattedAddress': '日本、〒160-0022 東京都新宿区新宿3丁目1-1',
        'nationalPhoneNumber': '03-0000-0000', 'location': {'latitude': 35.69, 'longitude': 139.70},
        'googleMapsUri': 'https://maps.google.com/?cid=1', 'primaryTypeDisplayName': {'text': 'カレー店'},
    })
    assert s.address == '東京都新宿区新宿3丁目1-1'
    assert s.phone == '03-0000-0000' and s.lat == 35.69
    assert clean_address('〒100-0001 東京都千代田区千代田1-1') == '東京都千代田区千代田1-1'


# ---- 店名の照合 ----

@pytest.mark.parametrize('a,b,expected', [
    ('らーめん一蘭 新宿中央東口店', '一蘭 渋谷店', False),
    ('らーめん一蘭 新宿中央東口店', 'らーめん一蘭 新宿店', True),
    ('マクドナルド 新宿東口店', 'マクドナルド 新宿東口店 (McDonald\'s)', True),
    ('ＣＡＦＥ　ＳＡＭＰＬＥ', 'Cafe Sample', True),
    ('鮨 さんぷる', '焼肉 さんぷる', False),
    ('松屋', '松屋 新宿店', True),
    ('松', '松屋', False),
])
def test_same_shop(a, b, expected):
    assert same_shop(a, b) is expected


def test_core_name():
    assert core_name('麺屋 テスト 新宿店') == '麺屋テスト'
    assert core_name('テスト本店') == 'テスト本店'


# ---- 両方から取った店の統合 ----

def test_merge():
    t = Shop(source='食べログ', name='麺屋 テスト 新宿店', phone='03-1234-5678', city='新宿区', url='t')
    g1 = Shop(source='Googleマップ', name='麺屋テスト', phone='0312345678', city='新宿区', url='g1', lat=1, lng=2)
    g2 = Shop(source='Googleマップ', name='別の店', phone='', city='新宿区', url='g2')
    out = pipeline.merge([t], [g1, g2])
    assert [s.source for s in out] == ['両方', 'Googleマップ']
    assert out[0].other_url == 'g1' and out[0].lat == 1


# ---- Uber Eats ----

def test_place_param_roundtrip():
    import base64
    d = json.loads(base64.b64decode(place_param('東京都新宿区新宿3-1-1', 35.69, 139.70)))
    assert d['address'] == '東京都新宿区新宿3-1-1' and d['latitude'] == 35.69


def test_store_names_from_json():
    data = {'data': {'feedItems': [
        {'type': 'REGULAR_STORE', 'store': {'storeUuid': 'u1', 'title': {'text': 'テスト食堂 新宿店'},
                                            'actionUrl': '/jp/store/test/u1'}},
        {'type': 'REGULAR_STORE', 'store': {'storeUuid': 'u2', 'title': 'カフェ サンプル'}},
    ]}}
    assert store_names_from_json(data) == [('テスト食堂 新宿店', '/jp/store/test/u1'), ('カフェ サンプル', '')]


# ---- 抽出の流れ（食べログへの通信は差し替え） ----

class FakeTabelog(tabelog.TabelogClient):
    def __init__(self, *a, **kw):
        super().__init__(delay=0, log=lambda *_: None)

    def get(self, url):
        if '/rstLst/' in url:
            return read('tabelog_list.html') if not url.rstrip('/').endswith('/2') else '<html></html>'
        return {'13300001': read('tabelog_detail.html'), '13300002': read('tabelog_detail_nold.html')}[tabelog.shop_id(url)]


@pytest.fixture
def fake_tabelog(monkeypatch):
    monkeypatch.setattr(tabelog, 'TabelogClient', FakeTabelog)


def test_collect_tabelog_phone_and_genre(fake_tabelog):
    c = pipeline.Criteria(source='tabelog', prefecture='東京都', city='新宿区', phone='yes', check_uber=False)
    assert [s.name for s in pipeline.collect_tabelog(c, log=lambda *_: None)] == ['麺屋 テスト 新宿店']
    c = pipeline.Criteria(source='tabelog', prefecture='東京都', city='新宿区', phone='no', check_uber=False)
    assert [s.name for s in pipeline.collect_tabelog(c, log=lambda *_: None)] == ['鮨 さんぷる']
    c = pipeline.Criteria(source='tabelog', prefecture='東京都', genre_large='和食', genre_small='寿司', check_uber=False)
    shops = pipeline.collect_tabelog(c, log=lambda *_: None)
    assert [(s.name, s.city) for s in shops] == [('鮨 さんぷる', '新宿区')]
    # 別の市区町村を指定したら出ない
    c = pipeline.Criteria(source='tabelog', prefecture='東京都', city='渋谷区', check_uber=False)
    assert pipeline.collect_tabelog(c, log=lambda *_: None) == []


def test_daily_only_new_shops(fake_tabelog, monkeypatch, tmp_path):
    from leadgen import daily
    monkeypatch.setattr(daily, 'TabelogClient', FakeTabelog)

    def fake_check(shops, c, log, stop):
        for s in shops:
            s.ubereats_status = UBER_FOUND if 'テスト' in s.name else UBER_NOT_FOUND
    monkeypatch.setattr(daily, 'check_uber', fake_check)
    cfg = tmp_path / 'config' / 'daily.yaml'
    cfg.parent.mkdir()
    cfg.write_text('areas:\n  - {prefecture: 東京都}\nmax_pages: 3\ntabelog_delay: 0\n', encoding='utf-8')

    shops, out = daily.run_daily(cfg, log=lambda *_: None)
    assert [s.name for s in shops] == ['鮨 さんぷる']  # Uber Eats 掲載ありは除外
    text = out.read_text(encoding='utf-8-sig')
    assert text.splitlines()[0].startswith('取得元,店名,')
    assert '鮨 さんぷる' in text and '未掲載' in text
    seen = json.loads((tmp_path / 'state' / 'tabelog_seen.json').read_text(encoding='utf-8'))
    assert set(seen) == {'13300001', '13300002'}

    # 2回目は取得済みなので0件
    shops, _ = daily.run_daily(cfg, log=lambda *_: None)
    assert shops == []
