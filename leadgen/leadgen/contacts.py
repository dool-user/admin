"""店の連絡先（問い合わせフォーム・Instagram）を公式サイトから探す

- 店の公式サイトのトップと、問い合わせページらしいリンク（最大2ページ）だけを読む
- robots.txt で禁止されているページは読まない。1サイトあたり1秒以上の間隔を空ける
- 「営業お断り」「セールスはご遠慮ください」などの表記があれば contact_ng に入れる（その店には送らない）
- 見つけるだけで、フォームへの入力・送信やDMの送信はしない
"""
import re
import time
from dataclasses import dataclass
from urllib import robotparser
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36')

CONTACT_WORD = re.compile(r'お問い?合わ?せ|問合せ|ご相談|ご予約・お問|contact|inquiry|enquiry', re.I)
CONTACT_HREF = re.compile(r'contact|inquiry|enquiry|toiawase|otoiawase|form', re.I)
GOOGLE_FORM = re.compile(r'https://(docs\.google\.com/forms|forms\.gle)/[^\s"\'<>]+')
# 例：「営業目的のお問い合わせはご遠慮ください」「セールスお断り」「営業メール禁止」
NG_RE = re.compile(
    r'(営業|セールス|勧誘|売り込み)[^。\n]{0,20}(お断り|ご遠慮|禁止|控え|受け付けて(い|お)りません|お受けして(い|お)りません|返信(いた|し)しません)')
IG_SKIP = {'p', 'reel', 'reels', 'explore', 'stories', 'accounts', 'tv', 'about', 'legal', 'direct'}


@dataclass
class Contact:
    website: str = ''
    form_url: str = ''
    instagram: str = ''
    contact_ng: str = ''    # 営業お断りの表記（空なら表記なし）
    note: str = ''

    @property
    def channel(self):
        """送る手段。お断り表記があれば送らない"""
        if self.contact_ng:
            return ''
        if self.form_url:
            return 'フォーム'
        if self.instagram:
            return 'Instagram DM'
        return ''


def instagram_url(href):
    """https://www.instagram.com/<アカウント>/ の形にそろえる。投稿やリールのURLは空"""
    u = urlparse(href or '')
    if not u.netloc.lower().endswith('instagram.com'):
        return ''
    parts = [p for p in u.path.split('/') if p]
    if not parts or parts[0].lower() in IG_SKIP or not re.fullmatch(r'[A-Za-z0-9._]{1,30}', parts[0]):
        return ''
    return f'https://www.instagram.com/{parts[0]}/'


def _text(soup):
    return re.sub(r'\s+', ' ', soup.get_text(' ', strip=True))


def has_form(soup):
    """本文を書ける問い合わせフォームがあるか（検索窓・ログインだけのフォームは除く）"""
    for f in soup.find_all('form'):
        if f.find('textarea'):
            return True
    return bool(soup.find('iframe', src=GOOGLE_FORM))


def find_ng(text):
    m = NG_RE.search(text or '')
    return m.group(0) if m else ''


def parse_page(html, url):
    """1ページ分 → {'instagram', 'form', 'google_form', 'contact_links', 'ng'}"""
    soup = BeautifulSoup(html, 'lxml')
    host = urlparse(url).netloc
    ig, links = '', []
    for a in soup.find_all('a', href=True):
        href = urljoin(url, a['href'])
        ig = ig or instagram_url(href)
        u = urlparse(href)
        if u.scheme not in ('http', 'https') or u.netloc != host or href.split('#')[0] == url.split('#')[0]:
            continue
        label = a.get_text(' ', strip=True) + ' ' + (a.get('title') or '')
        if CONTACT_WORD.search(label) or CONTACT_HREF.search(u.path):
            if href not in links:
                links.append(href)
    gf = GOOGLE_FORM.search(html)
    return {
        'instagram': ig,
        'form': has_form(soup),
        'google_form': gf.group(0) if gf else '',
        'contact_links': links,
        'ng': find_ng(_text(soup)),
    }


class ContactFinder:
    def __init__(self, delay=1.0, session=None, log=print, max_pages=2):
        self.delay = delay
        self.max_pages = max_pages
        self.session = session or requests.Session()
        self.session.headers.update({'User-Agent': UA, 'Accept-Language': 'ja,en;q=0.8'})
        self.log = log
        self._robots = {}
        self._last = 0.0

    def allowed(self, url):
        u = urlparse(url)
        base = f'{u.scheme}://{u.netloc}'
        if base not in self._robots:
            rp = robotparser.RobotFileParser()
            try:
                r = self.session.get(base + '/robots.txt', timeout=10)
                rp.parse(r.text.splitlines() if r.status_code == 200 else [])
            except requests.RequestException:
                rp.parse([])
            self._robots[base] = rp
        return self._robots[base].can_fetch(UA, url)

    def get(self, url):
        if not self.allowed(url):
            return None
        wait = self._last + self.delay - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        self._last = time.monotonic()
        try:
            r = self.session.get(url, timeout=15)
        except requests.RequestException:
            return None
        if r.status_code != 200 or 'html' not in r.headers.get('Content-Type', 'text/html'):
            return None
        r.encoding = r.apparent_encoding if r.encoding in (None, 'ISO-8859-1') else r.encoding
        return r.text

    def find(self, website, instagram=''):
        c = Contact(website=website or '', instagram=instagram_url(instagram) or instagram_url(website))
        if not website or c.instagram and instagram_url(website):
            return c
        html = self.get(website)
        if html is None:
            c.note = '公式サイトを読めなかった'
            return c
        top = parse_page(html, website)
        c.instagram = c.instagram or top['instagram']
        c.contact_ng = top['ng']
        if top['form']:
            c.form_url = website
        c.form_url = c.form_url or top['google_form']
        for link in top['contact_links'][:self.max_pages]:
            if c.form_url and c.contact_ng:
                break
            page = self.get(link)
            if page is None:
                continue
            p = parse_page(page, link)
            c.contact_ng = c.contact_ng or p['ng']
            c.instagram = c.instagram or p['instagram']
            if not c.form_url:
                c.form_url = link if p['form'] else p['google_form']
        return c


def fill_contacts(shops, finder=None, log=print, stop=lambda: False):
    """Shop の website / instagram から連絡先を埋める"""
    finder = finder or ContactFinder(log=log)
    for i, s in enumerate(shops, 1):
        if stop():
            break
        c = finder.find(s.website, s.instagram)
        s.instagram, s.form_url, s.contact_ng = c.instagram, c.form_url, c.contact_ng
        s.channel = c.channel
        log(f'連絡先 {i}/{len(shops)}: {s.name} → {s.channel or ("送らない：" + c.contact_ng if c.contact_ng else "見つからない")}')
    return shops
