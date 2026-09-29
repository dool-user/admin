from leadgen import tabelog
from leadgen.contacts import Contact, ContactFinder, find_ng, instagram_url, parse_page
from leadgen.models import Shop
from leadgen.pipeline import read_csv, write_csv

TOP = """<html><body>
<a href="/menu/">メニュー</a><a href="/contact/">お問い合わせ</a>
<a href="https://www.instagram.com/menya_kouki/?hl=ja">Instagram</a>
<form action="/search"><input name="q"></form></body></html>"""
CONTACT = """<html><body><p>営業目的のお問い合わせはご遠慮ください。</p>
<form method="post"><input name="name"><textarea name="body"></textarea></form></body></html>"""
CONTACT_OK = """<html><body><form method="post"><input name="email"><textarea name="body"></textarea></form></body></html>"""


def test_instagram_url():
    assert instagram_url('https://instagram.com/menya_kouki?igsh=x') == 'https://www.instagram.com/menya_kouki/'
    assert instagram_url('https://www.instagram.com/p/Cxyz123/') == ''
    assert instagram_url('https://example.com/menya') == ''


def test_find_ng():
    assert find_ng('営業目的のお問い合わせはご遠慮ください') .startswith('営業')
    assert find_ng('セールスのお電話はお断りしております') != ''
    assert find_ng('ご予約・お問い合わせはこちら') == ''


def test_parse_page_top():
    p = parse_page(TOP, 'https://kouki.example/')
    assert p['instagram'] == 'https://www.instagram.com/menya_kouki/'
    assert p['contact_links'] == ['https://kouki.example/contact/']
    assert p['form'] is False  # 検索窓だけのフォームは問い合わせフォームではない


class FakeResp:
    def __init__(self, text, status=200):
        self.text, self.status_code = text, status
        self.headers = {'Content-Type': 'text/html; charset=utf-8'}
        self.encoding = 'utf-8'


class FakeSession:
    def __init__(self, pages):
        self.pages, self.headers, self.calls = pages, {}, []

    def get(self, url, timeout=None):
        self.calls.append(url)
        if url.endswith('/robots.txt'):
            return FakeResp('User-agent: *\nDisallow: /private/\n')
        return FakeResp(self.pages[url]) if url in self.pages else FakeResp('', 404)


def finder(pages):
    return ContactFinder(delay=0, session=FakeSession(pages), log=lambda *a: None)


def test_find_form_and_ng():
    c = finder({'https://kouki.example/': TOP, 'https://kouki.example/contact/': CONTACT}).find('https://kouki.example/')
    assert c.form_url == 'https://kouki.example/contact/'
    assert c.instagram == 'https://www.instagram.com/menya_kouki/'
    assert c.contact_ng and c.channel == ''  # お断り表記があれば送らない


def test_find_form_ok():
    c = finder({'https://kouki.example/': TOP, 'https://kouki.example/contact/': CONTACT_OK}).find('https://kouki.example/')
    assert c.channel == 'フォーム'


def test_instagram_only_and_robots():
    f = finder({})
    assert f.find('https://www.instagram.com/sakura_cafe/').channel == 'Instagram DM'
    assert f.find('https://kouki.example/private/').note == '公式サイトを読めなかった'
    assert Contact().channel == ''


def test_tabelog_detail_homepage_and_instagram():
    html = """<table class="rstinfo-table__table">
    <tr><th>店名</th><td>麺屋 こうき</td></tr>
    <tr><th>住所</th><td>東京都新宿区西新宿1-1-1</td></tr>
    <tr><th>ホームページ</th><td><a href="https://kouki.example/" rel="nofollow">https://kouki.example/</a></td></tr>
    <tr><th>公式アカウント</th><td><a href="https://www.instagram.com/menya_kouki/">instagram</a></td></tr>
    </table>"""
    d = tabelog.parse_detail(html, 'https://tabelog.com/tokyo/A1304/A130401/13000001/')
    assert d['website'] == 'https://kouki.example/'
    assert d['instagram'] == 'https://www.instagram.com/menya_kouki/'


def test_csv_roundtrip(tmp_path):
    s = Shop(source='食べログ', name='麺屋 こうき', website='https://kouki.example/', form_url='https://kouki.example/contact/', channel='フォーム')
    path = write_csv([s], tmp_path / 'a.csv')
    back = read_csv(path)[0]
    assert (back.name, back.form_url, back.channel) == ('麺屋 こうき', 'https://kouki.example/contact/', 'フォーム')
