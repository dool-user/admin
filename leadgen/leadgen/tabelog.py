"""食べログの一覧ページ・店舗ページの取得と解析

URL の形（2026年9月時点で確認）
  市区町村の一覧      https://tabelog.com/tokyo/C13104/rstLst/
  ジャンルで絞る      https://tabelog.com/tokyo/C13104/rstLst/ramen/
  ニューオープン順    https://tabelog.com/tokyo/C13104/rstLst/cond16-00-00/
  2ページ目以降       一覧の「次へ」リンクをたどる（無ければ末尾に <n>/ を付ける）
"""
import json
import re
import time

import requests
from bs4 import BeautifulSoup

from .models import Shop

BASE = 'https://tabelog.com'
NEW_OPEN = 'cond16-00-00'
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36')
# 店舗ページ：https://tabelog.com/tokyo/A1304/A130401/13012345/
DETAIL_RE = re.compile(r'^https://tabelog\.com/[a-z]+/A\d{4}/A\d{6}/(\d+)/?$')
CLOSED_RE = re.compile(r'閉店|休業|移転')


def list_url(pref_slug, city_code=None, genre_slug=None, new_open=False, page=1):
    url = f'{BASE}/{pref_slug}/'
    if city_code:
        url += f'{city_code}/'
    url += 'rstLst/'
    if genre_slug:
        url += f'{genre_slug}/'
    if new_open:
        url += f'{NEW_OPEN}/'
    if page > 1:
        url += f'{page}/'
    return url


def shop_id(url):
    m = DETAIL_RE.match(url.split('?')[0])
    return m.group(1) if m else ''


def _abs(url):
    url = (url or '').split('?')[0].split('#')[0]
    return BASE + url if url.startswith('/') else url


def _text(el):
    return re.sub(r'\s+', ' ', el.get_text(' ', strip=True)).strip() if el else ''


def parse_list(html):
    """一覧ページ → [{'url', 'id', 'name', 'genre', 'area', 'rating'}], 次ページURL"""
    soup = BeautifulSoup(html, 'lxml')
    items, seen = [], set()
    for box in soup.select('.list-rst'):
        a = box.select_one('a.list-rst__rst-name-target') or box.find('a', href=DETAIL_RE)
        url = _abs(box.get('data-detail-url') or (a.get('href') if a else ''))
        if not shop_id(url) or url in seen:
            continue
        seen.add(url)
        area_genre = _text(box.select_one('.list-rst__area-genre'))
        area, _, genre = area_genre.partition('/')
        items.append({
            'url': url, 'id': shop_id(url), 'name': _text(a), 'genre': genre.strip(), 'area': area.strip(),
            'rating': _text(box.select_one('.list-rst__rating-val')),
        })
    # 一覧の枠が変わっていた場合の保険：店舗ページへのリンクを全部拾う
    if not items:
        for a in soup.find_all('a', href=True):
            url = _abs(a['href'])
            if not shop_id(url):
                continue
            if url not in seen and _text(a):
                seen.add(url)
                items.append({'url': url, 'id': shop_id(url), 'name': _text(a), 'genre': '', 'area': '', 'rating': ''})
    nxt = soup.select_one('a.c-pagination__arrow--next, a[rel="next"]')
    return items, (_abs(nxt['href']) if nxt and nxt.get('href') else None)


def _jsonld_restaurant(soup):
    for s in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(s.string or '')
        except ValueError:
            continue
        for d in data if isinstance(data, list) else [data]:
            if isinstance(d, dict) and d.get('@type') in ('Restaurant', 'FoodEstablishment', 'LocalBusiness'):
                return d
    return {}


def _table(soup):
    """店舗基本情報の表 → {見出し: 値}"""
    rows = {}
    for tr in soup.select('table.rstinfo-table__table tr, table.c-table tr, .rstinfo-table tr'):
        th, td = tr.find('th'), tr.find('td')
        if th and td:
            rows.setdefault(_text(th), td)
    return rows


def parse_detail(html, url):
    soup = BeautifulSoup(html, 'lxml')
    ld = _jsonld_restaurant(soup)
    table = _table(soup)

    def cell(*keys):
        for k in keys:
            for th, td in table.items():
                if th.startswith(k):
                    return td
        return None

    addr = ld.get('address') or {}
    address = ''.join(addr.get(k, '') for k in ('addressRegion', 'addressLocality', 'streetAddress')) if isinstance(addr, dict) else ''
    if not address:
        td = cell('住所')
        el = td.select_one('.rstinfo-table__address') if td else None
        address = _text(el or td).replace(' ', '')
    phone = ld.get('telephone', '')
    if not phone:
        td = cell('予約・お問い合わせ', 'お問い合わせ', '電話番号')
        el = td.select_one('.rstinfo-table__tel-num') if td else None
        m = re.search(r'0\d{1,4}-?\d{1,4}-?\d{3,4}', _text(el or td))
        phone = m.group(0) if m else ''
    geo = ld.get('geo') or {}
    lat, lng = geo.get('latitude'), geo.get('longitude')
    if lat is None:
        # 地図画像の URL に center=緯度,経度 が入っている
        img = soup.select_one('img.rstinfo-table__map-image, .rstinfo-table__map img, img[data-original*="center="]')
        m = re.search(r'center=([\d.]+),([\d.]+)', str(img) if img else html)
        if m:
            lat, lng = m.group(1), m.group(2)
    name = ld.get('name') or _text(cell('店名')) or _text(soup.select_one('.display-name'))
    genre = _text(cell('ジャンル'))
    if not genre and ld.get('servesCuisine'):
        c = ld['servesCuisine']
        genre = '、'.join(c) if isinstance(c, list) else str(c)
    opened = _text(cell('オープン日'))
    status = _text(soup.select_one('.rst-status-badge-large, .rdheader-rstname .rst-status, .rdheader-rst-status'))
    website, instagram = '', ''
    for td in filter(None, [cell('ホームページ'), cell('公式アカウント'), cell('公式サイト')]):
        for a in td.find_all('a', href=True):
            href = a['href']
            if 'instagram.com' in href:
                instagram = instagram or href
            elif href.startswith('http') and 'tabelog.com' not in href and not website:
                website = href
        if not website:
            m = re.search(r'https?://[^\s　]+', _text(td))
            if m and 'instagram.com' not in m.group(0):
                website = m.group(0)
    rating = ''
    agg = ld.get('aggregateRating') or {}
    if isinstance(agg, dict) and agg.get('ratingValue'):
        rating = str(agg['ratingValue'])
    return {
        'name': re.sub(r'\s+', ' ', name).strip(),
        'genre': genre,
        'address': address,
        'phone': phone.strip(),
        'lat': float(lat) if lat not in (None, '') else None,
        'lng': float(lng) if lng not in (None, '') else None,
        'open_date': opened,
        'rating': rating,
        'closed': bool(CLOSED_RE.search(status)),
        'website': website,
        'instagram': instagram,
    }


class TabelogClient:
    """一定の間隔（既定2秒）を空けて食べログにアクセスする"""

    def __init__(self, delay=2.0, session=None, log=print):
        self.delay = delay
        self.session = session or requests.Session()
        self.session.headers.update({'User-Agent': UA, 'Accept-Language': 'ja,en;q=0.8'})
        self.log = log
        self._last = 0.0

    def get(self, url):
        for attempt in range(3):
            wait = self._last + self.delay - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()
            try:
                r = self.session.get(url, timeout=30)
            except requests.RequestException as e:
                self.log(f'  食べログ接続エラー（{attempt + 1}回目）: {e}')
                time.sleep(5 * (attempt + 1))
                continue
            if r.status_code == 404:
                return None
            if r.status_code in (403, 429, 503):
                self.log(f'  食べログから {r.status_code} が返りました。{30 * (attempt + 1)}秒待って再試行します')
                time.sleep(30 * (attempt + 1))
                continue
            r.raise_for_status()
            r.encoding = r.encoding or 'utf-8'
            return r.text
        raise RuntimeError(f'食べログにアクセスできませんでした: {url}')

    def iter_list(self, first_url, max_pages):
        """一覧を max_pages ページまでたどる。1ページずつ (page, items) を返す"""
        url, page = first_url, 1
        while url and page <= max_pages:
            html = self.get(url)
            if html is None:
                return
            items, nxt = parse_list(html)
            if not items:
                return
            yield page, items
            page += 1
            url = nxt or first_url + f'{page}/'

    def shop(self, item, source='食べログ'):
        html = self.get(item['url'])
        if html is None:
            return None
        d = parse_detail(html, item['url'])
        if d['closed']:
            return None
        return Shop(
            source=source, name=d['name'] or item['name'], url=item['url'], genre=d['genre'] or item['genre'],
            address=d['address'], phone=d['phone'], lat=d['lat'], lng=d['lng'], open_date=d['open_date'],
            rating=d['rating'] or item.get('rating', ''), source_id=item['id'],
            website=d['website'], instagram=d['instagram'],
        )
