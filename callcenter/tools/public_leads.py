"""ネットに公開されている公的なリストから、送り先リスト（sales/data/leads.csv）を作る（10/7 社長の指示）

使ってよいリストと理由は sales/research/2026-10-07_public-lists.md。規約で営業利用・複製を禁じているリスト
（税理士・行政書士・司法書士の会員検索など）は使わない。ここで読むのは、社長が自分の PC にダウンロードした CSV だけ
（サイトを機械的に巡回して名簿を集めることはしない）。

  # 1) 医療：医療情報ネットのオープンデータ（厚労省・公共データ利用規約で商用可・出典の記載が条件）
  python tools/public_leads.py import 診療所_施設票.csv --kubun 医療 --gyoshu 診療所 --pref 東京都 --pref 大阪府 \\
      --source "医療情報ネット オープンデータ 2026-06-01時点（厚生労働省）"
  # 2) gBizINFO（企業ホームページ列）や自治体のオープンデータも同じ import で読める（列名は自動で探す。--url-col で指定も可）
  # 3) 法人番号の全件データ（国税庁・商用可）：HP がないので「HP を人が探す」リスト sales/data/hp_search.csv に出す
  python tools/public_leads.py houjin 13_tokyo_all.csv --kubun 士業 --source "法人番号公表サイト 全件データ 2026-09末（国税庁）"
  # 4) 公式 HP から問い合わせフォームを探す（robots.txt を守り1秒以上あける。営業お断り・画像認証は外す）
  python tools/public_leads.py forms --limit 200

決まり：
- 取り込むのは名称・区分・業種・都道府県・住所・公式サイトだけ。院長名・代表者名などの氏名は取り込まない
- 「リストの出典」に使ったリストの名前と時点を必ず入れる（送付管理シートにも出る）
- leads.csv・outbox.csv にすでにある先（同じドメイン、または名称＋住所が同じ）は足さない
"""
import argparse
import csv
import io
import re
import sys
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEADS = ROOT / 'sales' / 'data' / 'leads.csv'
HP_SEARCH = ROOT / 'sales' / 'data' / 'hp_search.csv'
OUTBOX = ROOT / 'sales' / 'out' / 'outbox.csv'
JST = timezone(timedelta(hours=9))
LEAD_FIELDS = ['店名', '区分', '業種', '都道府県', '住所', 'Google口コミ数', '送る手段', '問い合わせフォーム', '公式サイト',
               'Instagram', 'GBPの様子', '昼夜営業', '駅近', 'リストの出典', '取得元', '反響', '追加日', '優先度', '狙う理由']
HP_FIELDS = ['名称', '区分', '都道府県', '住所', '法人番号', 'リストの出典', '公式サイト', '確認者', 'メモ']
PREFS = re.compile(r'^(北海道|東京都|大阪府|京都府|.{2,3}県)')
COLS = {
    'name': ['正式名称', '医療機関名称', '名称', '施設名', '施設名称', '営業施設名称', '法人名', '商号', '事業者名'],
    'pref': ['都道府県名', '都道府県'],
    'addr': ['所在地', '住所', '営業施設所在地', '本社所在地', '所在地（住所）'],
    'url': ['案内用ホームページアドレス', 'ホームページアドレス', '薬局のホームページアドレス', '企業ホームページ', 'ホームページ',
            '公式サイト', 'URL', 'url', 'Webサイト', 'ウェブサイト'],
}
# 法人番号の名称で区分を決める（士業は「○○法人」だけ。個人の事務所は法人番号に載らない）
HOUJIN_RULES = {
    '医療': re.compile(r'医療法人|歯科'),
    '士業': re.compile(r'税理士法人|行政書士法人|司法書士法人|社会保険労務士法人|弁護士法人|特許業務法人|土地家屋調査士法人'),
    '住まい': re.compile(r'不動産|リフォーム|工務店|住宅|ハウス|ホーム(?!ページ)|建築|リノベ'),
}


def domain(url):
    m = re.match(r'https?://([^/]+)', url or '')
    return m.group(1).lower().removeprefix('www.') if m else ''


def norm_url(u):
    u = (u or '').strip().replace('：', ':').replace('／', '/')
    if not u or ' ' in u or '.' not in u:
        return ''
    if not re.match(r'https?://', u, re.I):
        u = 'http://' + u.lstrip('/')
    return u


def norm_key(name, addr):
    return re.sub(r'[\s　]', '', (name or '') + '|' + (addr or ''))


def read_table(path):
    """CSV（ZIP の中の CSV も可）を読んで (列名, 行) を返す。文字コードは UTF-8 / Shift_JIS を自動で"""
    p = Path(path)
    if p.suffix.lower() == '.zip':
        with zipfile.ZipFile(p) as z:
            name = next(n for n in z.namelist() if n.lower().endswith('.csv'))
            raw = z.read(name)
    else:
        raw = p.read_bytes()
    for enc in ('utf-8-sig', 'cp932'):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise SystemExit(f'{p.name} の文字コードが分かりません')
    rows = list(csv.reader(io.StringIO(text)))
    return rows[0], rows[1:]


def pick(header, kind, given=None):
    if given:
        return header.index(given)
    for c in COLS[kind]:
        if c in header:
            return header.index(c)
    return None


def load(path, fields):
    p = Path(path)
    if not p.exists() or p.stat().st_size == 0:
        return []
    with p.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def save(path, fields, rows):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)


def known(leads, outbox):
    doms, keys = set(), set()
    for r in leads:
        doms |= {domain(r.get('公式サイト')), domain(r.get('問い合わせフォーム'))}
        keys.add(norm_key(r.get('店名'), r.get('住所')))
    for r in outbox:
        doms.add(domain(r.get('送り先URL')))
        keys.add(norm_key(r.get('店名'), r.get('住所')))
    doms.discard('')
    return doms, keys


def import_rows(header, rows, kubun, gyoshu, source, prefs=(), url_col=None, name_col=None, addr_col=None,
                leads=(), outbox=(), today=''):
    """公開リストの行 → leads.csv の行（HP の URL があるものだけ）"""
    i_name, i_url = pick(header, 'name', name_col), pick(header, 'url', url_col)
    i_pref, i_addr = pick(header, 'pref'), pick(header, 'addr', addr_col)
    if i_name is None or i_url is None:
        raise SystemExit(f'名称か HP の列が見つかりません（列：{"・".join(header[:30])}）。--name-col / --url-col で指定してください')
    doms, keys = known(leads, outbox)
    out = []
    for r in rows:
        get = lambda i: (r[i].strip() if i is not None and i < len(r) else '')  # noqa: E731
        name, addr, url = get(i_name), get(i_addr), norm_url(get(i_url))
        pref = get(i_pref) or (PREFS.match(addr).group(1) if PREFS.match(addr) else '')
        if pref and not addr.startswith(pref):
            addr = pref + addr
        if not name or not url or (prefs and pref not in prefs):
            continue
        d, k = domain(url), norm_key(name, addr)
        if d in doms or k in keys:
            continue
        doms.add(d)
        keys.add(k)
        out.append({'店名': name, '区分': kubun, '業種': gyoshu, '都道府県': pref, '住所': addr, '公式サイト': url,
                    'リストの出典': source, '取得元': 'public_leads', '反響': '0', '追加日': today})
    return out


def houjin_rows(rows, kubun, source, prefs=(), hp_known=()):
    """法人番号の全件データ（見出しなし。7列目=商号、10〜12列目=所在地）→ HP を人が探すリスト"""
    rx = HOUJIN_RULES[kubun]
    seen = {r.get('法人番号') for r in hp_known}
    out = []
    for r in rows:
        if len(r) < 12 or r[2] == '71':  # 71=登記記録の閉鎖等
            continue
        name, pref = r[6], r[9]
        if not rx.search(name) or (prefs and pref not in prefs) or r[1] in seen:
            continue
        seen.add(r[1])
        out.append({'名称': name, '区分': kubun, '都道府県': pref, '住所': pref + r[10] + r[11], '法人番号': r[1],
                    'リストの出典': source})
    return out


CAPTCHA_RE = re.compile(r'recaptcha|hcaptcha|turnstile|captcha', re.I)


def find_forms(leads, limit, log=print):
    """公式サイトから問い合わせフォームを探して leads を直す（../leadgen の ContactFinder を使う）"""
    sys.path.insert(0, str(ROOT.parent / 'leadgen'))
    from leadgen.contacts import ContactFinder
    finder = ContactFinder(log=log)
    keep, n = [], 0
    for r in leads:
        if r.get('問い合わせフォーム') or not r.get('公式サイト') or n >= limit:
            keep.append(r)
            continue
        n += 1
        c = finder.find(r['公式サイト'])
        if c.instagram and not r.get('Instagram'):
            r['Instagram'] = c.instagram  # 狙う目印（DM は送らない）
        if c.contact_ng:
            log(f"  外す（営業お断り：{c.contact_ng}）{r['店名']}")
            continue
        if c.form_url:
            html = finder.get(c.form_url) or ''
            if CAPTCHA_RE.search(html):
                log(f"  外す（画像認証あり）{r['店名']}")
                continue
            r['問い合わせフォーム'], r['送る手段'] = c.form_url, 'フォーム'
            log(f"  フォームあり {r['店名']} {c.form_url}")
        else:
            r['送る手段'] = ''
            log(f"  フォームなし {r['店名']}（{c.note or 'フォームが見つからない'}）")
        keep.append(r)
    return keep


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    im = sub.add_parser('import', help='HP の URL がある公開リスト（CSV/ZIP）を leads.csv に足す')
    im.add_argument('file')
    im.add_argument('--kubun', required=True, choices=['店舗', '医療', '士業', '住まい'])
    im.add_argument('--gyoshu', default='')
    im.add_argument('--source', required=True, help='リストの出典（名前と時点）')
    im.add_argument('--pref', action='append', default=[])
    im.add_argument('--url-col')
    im.add_argument('--name-col')
    im.add_argument('--addr-col')
    hj = sub.add_parser('houjin', help='法人番号の全件データから、HP を人が探すリストを作る')
    hj.add_argument('file')
    hj.add_argument('--kubun', required=True, choices=list(HOUJIN_RULES))
    hj.add_argument('--source', required=True)
    hj.add_argument('--pref', action='append', default=[])
    fm = sub.add_parser('forms', help='公式サイトから問い合わせフォームを探す')
    fm.add_argument('--limit', type=int, default=100)
    sub.add_parser('hp-done', help='hp_search.csv で公式サイトを入れた行を leads.csv に移す')
    args = ap.parse_args(argv)
    today = datetime.now(JST).strftime('%Y-%m-%d')
    leads, outbox = load(LEADS, LEAD_FIELDS), load(OUTBOX, None)

    if args.cmd == 'import':
        header, rows = read_table(args.file)
        new = import_rows(header, rows, args.kubun, args.gyoshu, args.source, args.pref, args.url_col, args.name_col,
                          args.addr_col, leads, outbox, today)
        save(LEADS, LEAD_FIELDS, leads + new)
        print(f'{len(rows)}行のうち HP あり・未登録 {len(new)}件を leads.csv に足しました。次：python tools/public_leads.py forms')
    elif args.cmd == 'houjin':
        _, rows = read_table(args.file)
        rows = [_] + rows  # 見出しなしの CSV
        hp = load(HP_SEARCH, HP_FIELDS)
        new = houjin_rows(rows, args.kubun, args.source, args.pref, hp)
        save(HP_SEARCH, HP_FIELDS, hp + new)
        print(f'{len(new)}件を hp_search.csv に足しました。公式サイト列を人が検索して埋め、python tools/public_leads.py hp-done')
    elif args.cmd == 'hp-done':
        hp = load(HP_SEARCH, HP_FIELDS)
        done = [r for r in hp if norm_url(r.get('公式サイト'))]
        header = ['名称', '都道府県', '住所', '公式サイト']
        new = import_rows(header, [[r['名称'], r['都道府県'], r['住所'], r['公式サイト']] for r in done], '', '', '',
                          leads=leads, outbox=outbox, today=today)
        src = {r['名称']: r for r in done}
        for n in new:
            n['区分'], n['リストの出典'] = src[n['店名']]['区分'], src[n['店名']]['リストの出典'] + '＋人が HP を確認'
        save(LEADS, LEAD_FIELDS, leads + new)
        save(HP_SEARCH, HP_FIELDS, [r for r in hp if r not in done])
        print(f'{len(new)}件を leads.csv に移しました')
    elif args.cmd == 'forms':
        leads = find_forms(leads, args.limit)
        save(LEADS, LEAD_FIELDS, leads)
        print(f"フォームあり：{sum(1 for r in leads if r.get('送る手段') == 'フォーム')}件（leads.csv 全体）")


if __name__ == '__main__':
    main()
