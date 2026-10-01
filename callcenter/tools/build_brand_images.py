"""note アカウントのアイコン（1000×1000）とヘッダー画像（1920×1006）を作る

  python tools/build_brand_images.py   # → note/brand/<屋号>/

- アイコンは note で円形に切り取られるので、大事なものは中央の円の中に置く
- ヘッダーはクリエイターページで中央の帯だけが見えるので、文字は縦の中央（上下およそ 25〜75% の間）に置く
- 屋号：まるっと窓口（引越し A11）／ツナグラボ（AI・営業・MEO：A01・A02・A03）
日本語フォントは環境変数 NOTE_FONT_CSS（「;」区切りの CSS ファイル）で渡す。Noto Sans JP と Zen Maru Gothic を想定。
"""
import html
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'note' / 'brand'


def fonts():
    css = os.environ.get('NOTE_FONT_CSS', '')
    if css:
        return ''.join(f'<link rel="stylesheet" href="file://{p}">' for p in css.split(';') if p)
    return '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@500;700;900&family=Zen+Maru+Gothic:wght@500;700;900&display=swap">'


def page(w, h, body, css):
    return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8">{fonts()}<style>
*{{box-sizing:border-box;margin:0}}body{{width:{w}px;height:{h}px;overflow:hidden;font-family:"Noto Sans JP","IPAGothic",sans-serif}}
{css}</style></head><body>{body}</body></html>'''


# ── まるっと窓口（引越し）──
M = {'main': '#C4622D', 'deep': '#8E3F17', 'cream': '#FBF3EA', 'sun': '#F2B544'}
HOUSE = '''<svg viewBox="0 0 400 400" style="width:100%;height:100%">
  <circle cx="200" cy="200" r="168" fill="none" stroke="{ring}" stroke-width="30"/>
  <path d="M110 205L200 125L290 205V290H110Z" fill="{fill}"/>
  <rect x="176" y="232" width="48" height="58" rx="6" fill="{door}"/>
  <circle cx="288" cy="112" r="26" fill="{sun}"/></svg>'''


def marutto_icon():
    svg = HOUSE.format(ring='#FFFFFF', fill='#FFFFFF', door=M['main'], sun=M['sun'])
    body = f'<div class="c"><div class="i">{svg}</div><p>まるっと窓口</p></div>'
    css = f'''.c{{width:1000px;height:1000px;background:{M['main']};display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px}}
.i{{width:560px;height:560px}} p{{font-family:"Zen Maru Gothic",sans-serif;font-weight:900;color:#fff;font-size:108px;letter-spacing:.02em}}'''
    return page(1000, 1000, body, css)


def marutto_header():
    svg = HOUSE.format(ring=M['main'], fill=M['main'], door=M['cream'], sun=M['sun'])
    items = ['お部屋探し', '電気・ガス・水道', 'ネット回線', 'ウォーターサーバー', '引越し業者']
    chips = ''.join(f'<span>{html.escape(x)}</span>' for x in items)
    body = f'''<div class="h"><div class="blob b1"></div><div class="blob b2"></div>
<div class="row"><div class="i">{svg}</div><div class="t"><p class="k">関東の引越し相談</p><h1>まるっと窓口</h1>
<p class="s">引越しのこと、まるっとご相談ください</p><div class="chips">{chips}</div></div></div>
<p class="n">民間の相談窓口です（役所・電力会社などの公式窓口ではありません）</p></div>'''
    css = f'''.h{{width:1920px;height:1006px;background:{M['cream']};position:relative;overflow:hidden;display:flex;align-items:center;justify-content:center}}
.blob{{position:absolute;border-radius:50%;background:{M['main']};opacity:.09}} .b1{{width:620px;height:620px;left:-180px;top:-240px}} .b2{{width:520px;height:520px;right:-140px;bottom:-220px;background:{M['sun']};opacity:.18}}
.row{{display:flex;align-items:center;gap:64px;position:relative}}
.i{{width:330px;height:330px;flex:none}}
.k{{font-size:40px;font-weight:700;color:{M['deep']};letter-spacing:.08em}}
h1{{font-family:"Zen Maru Gothic",sans-serif;font-weight:900;font-size:156px;line-height:1.1;color:{M['main']};margin:6px 0 10px}}
.s{{font-size:44px;font-weight:700;color:#3A3029}}
.chips{{display:flex;flex-wrap:wrap;gap:12px;margin-top:26px;max-width:1080px}}
.chips span{{font-size:30px;font-weight:700;color:#fff;background:{M['main']};border-radius:999px;padding:8px 24px}}
.n{{position:absolute;bottom:40px;font-size:26px;color:#7A6A5E}}'''
    return page(1920, 1006, body, css)


# ── ツナグラボ（AI・営業・MEO）──
T = {'navy': '#1D2F5E', 'blue': '#2B4C9B', 'bg': '#F3F5FA'}
SUB = {
    'A01': ('AIで営業チームを作る', '#2B4C9B', ['Claude Code', '業務の自動化', 'AIへの仕事の渡し方']),
    'A02': ('AIと人で回す店舗営業', '#1E7A6E', ['フォーム営業', 'Instagram DM', '点検の仕組み']),
    'A03': ('お店のGoogleマップ集客', '#1F6F54', ['MEO', 'Googleビジネスプロフィール', '口コミのルール']),
    # 10/1：ツナグラボは1アカウント（A01〜A03 をマガジンで分ける）。アカウントのヘッダーはこれを使う
    'ALL': ('AIで営業と集客をつなぐ', '#2B4C9B', ['AIで営業チーム', 'フォーム・DM営業', 'Googleマップ集客']),
}
NODES = '''<svg viewBox="0 0 400 400" style="width:100%;height:100%">
  <path d="M120 130L280 130M120 130L200 280M280 130L200 280" stroke="{line}" stroke-width="26" stroke-linecap="round" fill="none"/>
  <circle cx="120" cy="130" r="54" fill="{a}"/><circle cx="280" cy="130" r="54" fill="{b}"/><circle cx="200" cy="280" r="54" fill="{c}"/></svg>'''


def tsunagu_icon():
    svg = NODES.format(line='#FFFFFF', a='#FFFFFF', b='#8FD3B8', c='#F2B544')
    body = f'<div class="c"><div class="i">{svg}</div><p>ツナグラボ</p></div>'
    css = f'''.c{{width:1000px;height:1000px;background:{T['navy']};display:flex;flex-direction:column;align-items:center;justify-content:center;gap:0}}
.i{{width:520px;height:520px}} p{{font-weight:900;color:#fff;font-size:112px;letter-spacing:.04em;margin-top:-10px}}'''
    return page(1000, 1000, body, css)


def tsunagu_header(acc):
    label, color, tags = SUB[acc]
    svg = NODES.format(line=T['navy'], a=T['navy'], b=color, c='#F2B544')
    chips = ''.join(f'<span>{html.escape(x)}</span>' for x in tags)
    body = f'''<div class="h"><div class="grid"></div>
<div class="row"><div class="i">{svg}</div><div class="t"><p class="k">TSUNAGU LAB</p><h1>ツナグラボ</h1>
<p class="s"><b>｜</b>{html.escape(label)}</p><div class="chips">{chips}</div></div></div></div>'''
    css = f'''.h{{width:1920px;height:1006px;background:{T['bg']};position:relative;overflow:hidden;display:flex;align-items:center;justify-content:center}}
.grid{{position:absolute;inset:0;background-image:linear-gradient(#DCE2EF 2px,transparent 2px),linear-gradient(90deg,#DCE2EF 2px,transparent 2px);background-size:64px 64px;opacity:.7}}
.row{{display:flex;align-items:center;gap:70px;position:relative}}
.i{{width:320px;height:320px;flex:none}}
.k{{font-size:34px;font-weight:900;color:{color};letter-spacing:.3em}}
h1{{font-weight:900;font-size:160px;line-height:1.05;color:{T['navy']};letter-spacing:.03em}}
.s{{font-size:52px;font-weight:900;color:{T['navy']};margin-top:8px}} .s b{{color:{color}}}
.chips{{display:flex;flex-wrap:wrap;gap:12px;margin-top:26px}}
.chips span{{font-size:30px;font-weight:700;color:{color};background:#fff;border:3px solid {color};border-radius:999px;padding:6px 22px}}'''
    return page(1920, 1006, body, css)


def check_sheet(icon, header, crop_h=486):
    """見え方の確認用：アイコンを円形に、ヘッダーを中央の帯だけで表示"""
    body = f'''<div class="w"><div class="a"><img src="{icon}"><p>アイコン（円形に表示）</p></div>
<div class="b"><div class="crop"><img src="{header}"></div><p>ヘッダー（クリエイターページで見える中央の帯のイメージ）</p></div></div>'''
    css = f'''.w{{width:1900px;height:760px;background:#fff;display:flex;gap:50px;padding:50px;align-items:flex-start}}
.a img{{width:300px;height:300px;border-radius:50%;display:block;box-shadow:0 0 0 6px #eee}} p{{font-size:24px;color:#555;margin-top:14px}}
.crop{{width:1450px;height:{int(crop_h * 1450 / 1920)}px;overflow:hidden;border-radius:14px;position:relative;box-shadow:0 0 0 2px #ddd}}
.crop img{{width:1450px;position:absolute;top:50%;transform:translateY(-50%)}}'''
    return page(1900, 760, body, css)


def render(jobs):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        for html_text, out, w, h in jobs:
            out.parent.mkdir(parents=True, exist_ok=True)
            pg = b.new_page(viewport={'width': w, 'height': h})
            tmp = out.with_suffix('.html')
            tmp.write_text(html_text, encoding='utf-8')
            pg.goto(tmp.as_uri())
            pg.wait_for_timeout(500)
            pg.screenshot(path=str(out))
            tmp.unlink()
            pg.close()
        b.close()


def main():
    m, t = OUT / 'marutto', OUT / 'tsunagulab'
    jobs = [(marutto_icon(), m / 'icon.png', 1000, 1000), (marutto_header(), m / 'header.png', 1920, 1006),
            (tsunagu_icon(), t / 'icon.png', 1000, 1000)]
    jobs += [(tsunagu_header(a), t / f'header_{a}.png', 1920, 1006) for a in SUB]
    render(jobs)
    checks = [(check_sheet((m / 'icon.png').as_uri(), (m / 'header.png').as_uri()), m / 'check.png', 1900, 760)]
    checks += [(check_sheet((t / 'icon.png').as_uri(), (t / f'header_{a}.png').as_uri()), t / f'check_{a}.png', 1900, 760) for a in SUB]
    render(checks)
    print(OUT)


if __name__ == '__main__':
    main()
