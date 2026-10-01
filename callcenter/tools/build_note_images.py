"""note 記事の画像（見出し画像・ポイント図・チェックリスト図・図解）を作り、下書きに差し込む

  python tools/build_note_images.py            # 全記事
  python tools/build_note_images.py N010 N013  # 指定の記事だけ

出力：note/out/images/<ID>/header.png（1920×1006。note の見出し画像の推奨 1280×670 と同じ比率）
      note/out/images/<ID>/points.png・checklist.png・diagram.png（本文用）
下書きには `![...](../images/<ID>/...png)` の行を差し込む（何度実行しても1回分だけ）。
note に貼るときは、この画像を同じ位置にアップロードする。

日本語フォント：環境変数 NOTE_FONT_CSS に Noto Sans JP の CSS（fontsource の 700.css など）を
いくつか「;」区切りで渡すと使う。なければ Google Fonts、読めなければ端末の日本語フォント。
Playwright（Python）と Chromium が必要。
"""
import csv
import html
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from note_scenes import SCENES, pick  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
NOTE = ROOT / 'note'
DRAFTS = NOTE / 'out' / 'drafts'
IMAGES = NOTE / 'out' / 'images'

THEME = {  # アカウントごとの色と絵
    'A01': {'soft': '#C9D6F2', 'accent': '#2B4C9B', 'tint': '#EEF2FB', 'icon': 'network'},
    'A02': {'soft': '#BFE0D8', 'accent': '#1E7A6E', 'tint': '#EAF5F2', 'icon': 'mail'},
    'A03': {'soft': '#C2DFCC', 'accent': '#1F6F54', 'tint': '#EBF4EE', 'icon': 'pin'},
    'A11': {'soft': '#F3CFB8', 'accent': '#C4622D', 'tint': '#FBF0E8', 'icon': 'house'},
}
DEFAULT_THEME = {'accent': '#3A4656', 'tint': '#F1F2F4', 'icon': 'network'}

ICONS = {
    'network': '''<circle cx="210" cy="120" r="46"/><circle cx="90" cy="300" r="46"/><circle cx="330" cy="300" r="46"/>
      <circle cx="210" cy="430" r="46"/><path d="M210 166V384M178 150L118 262M242 150L302 262M125 330L180 400M295 330L240 400" fill="none" stroke-width="18"/>''',
    'mail': '''<rect x="30" y="120" width="360" height="250" rx="28"/><path d="M50 145L210 270L370 145" fill="none" stroke-width="22"/>
      <circle cx="350" cy="120" r="48" class="acc2"/>''',
    'pin': '''<path d="M210 40C126 40 70 104 70 182C70 290 210 440 210 440S350 290 350 182C350 104 294 40 210 40Z"/>
      <circle cx="210" cy="180" r="56" class="hole"/>''',
    'house': '''<path d="M40 230L210 80L380 230V420H40Z"/><rect x="170" y="300" width="80" height="120" class="hole"/>
      <rect x="250" y="330" width="150" height="110" rx="10" class="acc2"/><path d="M250 370H400" stroke-width="10" fill="none"/>''',
}


def load_articles():
    acc_names = {r['ID']: r['分野'] for r in csv.DictReader((NOTE / 'accounts.csv').open(encoding='utf-8-sig'))}
    out = []
    for r in csv.DictReader((NOTE / 'out' / 'articles.csv').open(encoding='utf-8-sig')):
        p = DRAFTS / f"{r['ID']}.md"
        if p.exists():
            out.append({'id': r['ID'], 'acc': r['アカウント'], 'accName': re.sub(r'（.*?）', '', acc_names.get(r['アカウント'], '')),
                        'price': r['価格'], 'path': p})
    return out


def title_of(text):
    m = re.search(r'^#\s+(.+)$', text, re.M)
    return m.group(1).strip() if m else ''


def summary_points(text):
    """「まとめ」「ポイント」の見出し・太字の直後にある箇条書き（最大4つ）"""
    m = re.search(r'(?:まとめ|ポイント)[^\n]*\n+((?:\s*[-・]\s+.+\n?){2,})', text)
    if not m:
        return []
    items = [re.sub(r'^\s*[-・]\s+', '', x).strip() for x in m.group(1).strip().splitlines() if x.strip()]
    return [re.sub(r'\*\*|`', '', x) for x in items][:4]


def checklist_items(text):
    """最初のチェックリスト（- [ ] の並び。コードブロックの中でも外でも）"""
    for block in re.findall(r'```[^\n]*\n(.*?)```', text, re.S) + [text]:
        items = re.findall(r'^\s*-\s*\[\s?\]\s*(.+)$', block, re.M)
        if len(items) >= 3:
            return [re.sub(r'\*\*|`', '', x).strip() for x in items][:14]
    return []


def font_css():
    local = os.environ.get('NOTE_FONT_CSS', '')
    if local:
        return ''.join(f'<link rel="stylesheet" href="file://{p}">' for p in local.split(';') if p)
    return '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700;900&display=swap">'


BASE_CSS = '''*{box-sizing:border-box;margin:0}body{font-family:"Noto Sans JP","IPAGothic","IPAPGothic",sans-serif;color:#1E2227}
.acc{color:var(--a)}'''


def page(body, w, h, theme, extra=''):
    return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8">{font_css()}<style>{BASE_CSS}
:root{{--a:{theme['accent']};--t:{theme['tint']};--s:{theme.get('soft', theme['tint'])}}}{extra}</style></head>
<body style="width:{w}px;{'height:%dpx;' % h if h else ''}">{body}</body></html>'''


def header_html(a, title, theme):
    """見出し画像：左にタイトル、右に本題の絵（note_scenes.py。タイトルの言葉で選ぶ）"""
    scene = SCENES[pick(title, a['acc'])]
    size = 84 if len(title) <= 28 else 72 if len(title) <= 40 else 62
    free = a['price'] in ('0', '')
    css = f'''.hd{{width:1920px;height:1006px;background:var(--t);position:relative;overflow:hidden;padding:0 0 0 130px;display:flex;align-items:center}}
.band{{position:absolute;left:0;top:0;width:28px;height:100%;background:var(--a)}}
.txt{{width:940px;display:flex;flex-direction:column;gap:44px;position:relative;z-index:1}}
.chip{{align-self:flex-start;font-size:32px;font-weight:700;color:#fff;background:var(--a);border-radius:999px;padding:10px 30px}}
h1{{font-size:{size}px;font-weight:900;line-height:1.38;letter-spacing:.01em;text-wrap:balance}}
.foot{{font-size:30px;font-weight:700;color:#4A5260}} .foot b{{color:var(--a)}}
.blob{{position:absolute;right:-120px;top:50%;transform:translateY(-50%);width:980px;height:980px;border-radius:50%;background:var(--a);opacity:.1}}
.blob2{{position:absolute;right:520px;bottom:-160px;width:300px;height:300px;border-radius:50%;background:#F2B544;opacity:.22}}
svg{{position:absolute;right:90px;top:50%;transform:translateY(-50%);width:640px;height:640px}}
svg .a{{fill:var(--a)}} svg .s{{fill:var(--s)}} svg .t{{fill:var(--t)}} svg .y{{fill:#F2B544}} svg .w{{fill:#fff}} svg .k{{fill:#2A2F38}}
svg .ln-a{{stroke:var(--a)}} svg .ln-s{{stroke:var(--s)}} svg .ln-y{{stroke:#F2B544}} svg .ln-w{{stroke:#fff}} svg .ln-k{{stroke:#2A2F38}}
svg [class^="ln-"]{{fill:none;stroke-linecap:round;stroke-linejoin:round}}'''
    body = f'''<div class="hd"><div class="band"></div><div class="blob"></div><div class="blob2"></div>
<svg viewBox="0 0 600 600" aria-hidden="true">{scene}</svg>
<div class="txt"><span class="chip">{html.escape(a['accName'])}</span><h1>{html.escape(title)}</h1>
<div class="foot"><b>{'無料で読めます' if free else '保存版'}</b></div></div></div>'''
    return page(body, 1920, 1006, theme, css)


def points_html(points, theme):
    css = '''.pt{width:1600px;background:#fff;border:6px solid var(--a);border-radius:40px;padding:80px 90px}
.pt h2{font-size:58px;font-weight:900;color:var(--a);margin-bottom:44px}
.pt li{list-style:none;display:flex;gap:30px;align-items:flex-start;font-size:44px;line-height:1.5;font-weight:700;padding:26px 0;border-top:3px dashed #E1DED6}
.pt li:first-child{border-top:0}
.pt .n{flex:none;width:76px;height:76px;border-radius:50%;background:var(--a);color:#fff;display:grid;place-items:center;font-size:40px;font-weight:900}'''
    lis = ''.join(f'<li><span class="n">{i + 1}</span><span>{html.escape(p)}</span></li>' for i, p in enumerate(points))
    return page(f'<div class="pt" id="shot"><h2>この記事のポイント</h2><ul style="padding:0">{lis}</ul></div>', 1600, 0, theme, css)


def checklist_html(items, theme):
    css = '''.ck{width:1600px;background:var(--t);border-radius:40px;padding:76px 90px}
.ck h2{font-size:56px;font-weight:900;margin-bottom:12px}.ck p{font-size:32px;color:#4A5260;margin-bottom:36px}
.ck li{list-style:none;display:flex;gap:28px;align-items:flex-start;font-size:38px;line-height:1.5;background:#fff;border-radius:18px;padding:22px 30px;margin-top:14px}
.ck .b{flex:none;width:46px;height:46px;border:5px solid var(--a);border-radius:10px;margin-top:5px}'''
    lis = ''.join(f'<li><span class="b"></span><span>{html.escape(x)}</span></li>' for x in items)
    return page(f'<div class="ck" id="shot"><h2>保存用チェックリスト</h2><p>スクリーンショットして使ってください</p><ul style="padding:0">{lis}</ul></div>', 1600, 0, theme, css)


def flow_html(title, steps, theme, note=''):
    """横に並ぶステップの図解（steps: [(見出し, 説明)]）"""
    css = f'''.fl{{width:1800px;background:#fff;border-radius:40px;padding:70px 70px 80px;border:4px solid #E4E1D9}}
.fl h2{{font-size:54px;font-weight:900;margin-bottom:50px}}
.row{{display:flex;gap:0;align-items:stretch}}
.st{{flex:1;background:var(--t);border-radius:28px;padding:36px 30px;position:relative}}
.st b{{display:block;font-size:40px;color:var(--a);font-weight:900;margin-bottom:14px}}
.st span{{font-size:32px;line-height:1.55;font-weight:500}}
.ar{{flex:none;width:56px;display:grid;place-items:center;font-size:52px;color:var(--a);font-weight:900}}
.nt{{font-size:30px;color:#4A5260;margin-top:36px}}'''
    cells = []
    for i, (h, d) in enumerate(steps):
        if i:
            cells.append('<div class="ar">›</div>')
        cells.append(f'<div class="st"><b>{html.escape(h)}</b><span>{html.escape(d)}</span></div>')
    nt = f'<p class="nt">{html.escape(note)}</p>' if note else ''
    return page(f'<div class="fl" id="shot"><h2>{html.escape(title)}</h2><div class="row">{"".join(cells)}</div>{nt}</div>', 1800, 0, theme, css)


# 記事ごとの図解（見出しの直前に差し込む）
DIAGRAMS = {
    'N001': ('## 1. 組織図', '17人の営業チームと仕事の流れ', [
        ('リスト抽出', '送り先と問い合わせフォーム・Instagram を探す'), ('AP 10人', '店ごとの文面を下書き'),
        ('SV 2人', '点検して承認か差し戻し'), ('人が送信', '内容を見て送信ボタンを押す'), ('事務 3人', '返信・日程調整・案件票')],
        'SV は AP 5人に1人。まとめ役のセンター長が全体を割り振る'),
    'N005': ('## ', '作る役・点検する役・送る役を分ける', [
        ('AP が作る', '店ごとの文面を下書き'), ('SV が点検', 'review.md で1件ずつ'), ('差し戻し', '理由を記録して直す'),
        ('人が送る', '送信ボタンは人が押す')], ''),
    'N010': ('## ', '引越しまでの流れ', [
        ('1か月前', '退去の連絡・業者の見積もり'), ('2週間前', 'ライフライン・ネットの申込'), ('1週間前', '転出届・郵便の転送'),
        ('当日', '立ち会い・鍵の受け渡し'), ('引越し後', '転入届は14日以内')], '期限や方法は自治体・各社の案内で確かめてください'),
    'N013': ('## ', '電気・ガス・水道の手続き', [
        ('旧居', '停止日を連絡（電気・ガス・水道）'), ('新居', '開始日を連絡'), ('ガス', '開栓は立ち会いが必要なことが多い'),
        ('当日', 'ブレーカー・水道を確認')], 'お客さま番号と、旧居・新居の住所を手元に用意'),
}


def render(pairs):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={'width': 1920, 'height': 1006}, device_scale_factor=1)
        for html_text, out, full in pairs:
            out.parent.mkdir(parents=True, exist_ok=True)
            tmp = out.with_suffix('.html')
            tmp.write_text(html_text, encoding='utf-8')
            pg.goto(tmp.as_uri())
            pg.wait_for_timeout(300)
            try:
                pg.evaluate('document.fonts.ready')
            except Exception:
                pass
            if full:
                pg.screenshot(path=str(out), clip={'x': 0, 'y': 0, 'width': 1920, 'height': 1006})
            else:
                pg.locator('#shot').screenshot(path=str(out), omit_background=True)
            tmp.unlink()
        b.close()


def insert(text, marker, line, before):
    """before（正規表現）の直前に画像の行を1回だけ入れる"""
    if marker in text:
        text = re.sub(r'\n*' + re.escape(marker) + r'\n!\[[^\n]*\n+', '\n\n', text)
    m = re.search(before, text, re.M)
    if not m:
        return text
    return text[:m.start()] + f'{marker}\n{line}\n\n' + text[m.start():]


def main(ids):
    arts = [a for a in load_articles() if not ids or a['id'] in ids]
    jobs, edits = [], []
    for a in arts:
        text = a['path'].read_text(encoding='utf-8')
        theme = THEME.get(a['acc'], DEFAULT_THEME)
        d = IMAGES / a['id']
        title = title_of(text)
        jobs.append((header_html(a, title, theme), d / 'header.png', True))
        pts = summary_points(text)
        if pts:
            jobs.append((points_html(pts, theme), d / 'points.png', False))
            text = insert(text, '<!-- 画像：ポイント -->', f'![この記事のポイント](../images/{a["id"]}/points.png)',
                          r'^(?:\*\*)?[^\n]*(?:まとめ|ポイント)[^\n]*\n+\s*[-・]\s')
        cl = checklist_items(text)
        if cl:
            jobs.append((checklist_html(cl, theme), d / 'checklist.png', False))
            first = re.search(r'^```[^\n]*\n(?:(?!```).)*?-\s*\[\s?\]', text, re.S | re.M)
            if first:
                text = insert(text, '<!-- 画像：チェックリスト -->', f'![保存用チェックリスト](../images/{a["id"]}/checklist.png)',
                              re.escape(text[first.start():first.start() + 12]))
        if a['id'] in DIAGRAMS:
            head, t, steps, note = DIAGRAMS[a['id']]
            jobs.append((flow_html(t, steps, theme, note), d / 'diagram.png', False))
            anchor = r'^' + re.escape(head) if head != '## ' else r'^## '
            text = insert(text, '<!-- 画像：図解 -->', f'![{t}](../images/{a["id"]}/diagram.png)', anchor)
        edits.append((a['path'], text))
    render(jobs)
    for p, t in edits:
        p.write_text(t, encoding='utf-8')
    print(f'{len(arts)}本・画像 {len(jobs)}枚 → {IMAGES}')


if __name__ == '__main__':
    main(sys.argv[1:])
