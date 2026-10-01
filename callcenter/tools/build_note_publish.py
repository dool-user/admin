"""ストックの下書きから、note に貼る「公開用」の本文を作る

  python tools/build_note_publish.py N016 N001 ...   # → note/out/publish/<ID>.md

- 先頭の社内メモ（<!-- -->）と、末尾の「公開前に消す」一覧を外す
- 【社長確認】が残る行は消す（N001 の「始めた時期」のように、タグだけ外せばよい箇所は KEEP_LINE に書く）
- 相談フォームの URL が未定の記事は、相談の案内の段落ごと外す（フォーム公開後に足す）
- 画像は note に別でアップロードするので「［画像：ファイル名］」の目印に置き換える
- note のエディタには表がないので、表は「見出し列：残りの列」の箇条書きに直す
- フォームの URL・「仲介手数料無料」を書いてよいかは note/launch/settings.json で決める。
  フォームの URL が入っていれば記事に入れ、その下に URL だけの行も置く（note でリンクのカードになる）
- 文として成り立つ確認（紹介料の書き方・提携先の名前など）は、タグだけ外して文を残す（STRIP_TAG）
- スマホで読みやすいように、ふつうの段落は1文ごとに改行し、2文ごとに段落を分ける（mobile_breaks。10/1 社長の指示）
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOTE = ROOT / 'note' / 'out'
KEEP_LINE = {'N001'}  # 【社長確認：…】のタグだけ外し、文は残す
STRIP_TAG = ('書き方', '紹介料の有無と書き方', '提携先の不動産会社名と宅建業の免許番号', '対応できる範囲',
             '紹介できるサービス', '提携業者の範囲')
SETTINGS = json.loads((NOTE.parent / 'launch' / 'settings.json').read_text(encoding='utf-8'))
FORM_TAGS = {'引越し相談フォームのURL': 'moving_form_url', 'フォームを公開したURL': 'meo_form_url'}
CHUKAI = '仲介手数料を無料にできる物件があります。条件は物件によって違うため、ご相談のときにご説明します。'


def cells(row):
    return [c.strip() for c in row.strip().strip('|').split('|')]


def tables_to_lists(text):
    out, block = [], []
    for line in text.split('\n') + ['']:
        if line.startswith('|'):
            block.append(line)
            continue
        if block:
            head = cells(block[0])
            body = [cells(b) for b in block[2:]] if len(block) > 1 and set(block[1]) <= set('|-: ') else [cells(b) for b in block[1:]]
            for row in body:
                rest = '／'.join(f'{h}：{v}' if h else v for h, v in zip(head[1:], row[1:]) if v)
                out.append(f'- **{row[0]}**' + (f'　{rest}' if rest else ''))
            block = []
        out.append(line)
    return '\n'.join(out[:-1])


OPEN, CLOSE = '「（『【', '」）』】'


def sentences(line):
    """「。」で文に分ける（かぎかっこ・かっこの中では分けない）"""
    out, cur, depth = [], '', 0
    for ch in line:
        cur += ch
        if ch in OPEN:
            depth += 1
        elif ch in CLOSE:
            depth = max(0, depth - 1)
        elif ch in '。！？' and depth == 0:
            out.append(cur.strip())
            cur = ''
    if cur.strip():
        if out and re.fullmatch(r'[）」』】\s]*', cur.strip()):
            out[-1] += cur.strip()
        else:
            out.append(cur.strip())
    return out


def mobile_breaks(text):
    out, code = [], False
    for line in text.split('\n'):
        if line.startswith('```'):
            code = not code
        plain = (not code and line.strip() and not re.match(r'\s*(-\s|\*\s|>|#|\||\d+\.\s|［画像|https?://|--- ここから有料)', line))
        ss = sentences(line) if plain else []
        if len(ss) <= 1:
            out.append(line)
            continue
        paras = ['\n'.join(ss[i:i + 2]) for i in range(0, len(ss), 2)]
        out.append('\n\n'.join(paras))
    return '\n'.join(out)


def build(aid):
    text = (NOTE / 'drafts' / f'{aid}.md').read_text(encoding='utf-8')
    text = re.sub(r'\A\s*<!--.*?-->\s*', '', text, flags=re.S)
    # 「公開前に消す」一覧・社長向けの確認欄（末尾の --- 以降に置いてある）
    text = re.split(r'\n---\n+(?=###? 社長に|\*\*【社長確認】\*\*|## 確認リスト|### 確認リスト)', text)[0]
    # 「難しいと思ったら」の相談の節は、フォーム URL が未定なら節ごと外す
    text = re.sub(r'\n## 「自分でやるのは難しい」と思ったら\n.*?(?=\n## |\n---|\Z)',
                  lambda m: '' if '【社長確認' in m.group(0) else m.group(0), text, flags=re.S)
    for tag, key in FORM_TAGS.items():
        if SETTINGS.get(key):
            url = SETTINGS[key].rstrip('?&')
            # リンクの行の下に、URL だけの行を足す（note の「埋め込み」でカードになる）
            text = re.sub(r'^(.*)https://【社長確認：' + tag + r'】\?src=(\w+)(.*)$',
                          lambda m: f'{m.group(1)}{url}?src={m.group(2)}{m.group(3)}\n\n{url}?src={m.group(2)}', text, flags=re.M)
    if not SETTINGS.get('chukai_free_ok'):
        text = text.replace(CHUKAI, '')
        text = re.sub(r'[^。\n]*仲介手数料を無料にできる[^。\n]*。', '', text)
    for tag in STRIP_TAG:
        text = text.replace(f'【社長確認：{tag}】', '')
    text = text.replace('お部屋探し（お部屋探しは、提携する不動産会社をご紹介します（物件のご案内・契約・仲介は提携先の不動産会社が行います））',
                        'お部屋探し（提携する不動産会社をご紹介します。物件のご案内・契約・仲介は提携先の不動産会社が行います）')
    lines = []
    for line in text.split('\n'):
        if '【社長確認' in line:
            if aid in KEEP_LINE:
                line = re.sub(r'【社長確認[^】]*】', '', line).rstrip()
            else:
                continue
        lines.append(line)
    text = '\n'.join(lines)
    text = tables_to_lists(text)
    # 冒頭の「**こんな人向け：** 本文」は、見出しと本文を分けて置く（スマホで読みやすく）
    text = re.sub(r'^\*\*([^*\n]{2,14})：\*\*\s*', r'**\1**\n', text, flags=re.M)
    text = mobile_breaks(text)
    text = re.sub(r'<!-- 画像：.*?-->\n', '', text)
    text = re.sub(r'!\[([^\]]*)\]\(\.\./images/[^/]+/([^)]+)\)', r'［画像：\2（\1）をここにアップロード］', text)
    text = re.sub(r'\n{3,}', '\n\n', text).strip() + '\n'
    left = text.count('【社長確認')
    out = NOTE / 'publish' / f'{aid}.md'
    out.parent.mkdir(exist_ok=True)
    out.write_text(text, encoding='utf-8')
    return out, left


def main():
    for aid in sys.argv[1:]:
        out, left = build(aid)
        print(f'{aid}: {out.relative_to(ROOT)}（残りの【社長確認】{left}）')


if __name__ == '__main__':
    main()
