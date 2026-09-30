"""note の下書きを、公開前に読み心地を確かめるためのプレビュー画面（1枚の HTML）にまとめる

  python tools/build_note_preview.py   # → note/preview/index.html

note/out/articles.csv と note/out/drafts/<ID>.md を読み込む。noteそのものではなく、社内確認用の簡易な再現。
"""
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOTE = ROOT / 'note'
ACCOUNTS = {r['ID']: r['分野'] for r in csv.DictReader((NOTE / 'accounts.csv').open(encoding='utf-8-sig'))}


def load():
    items = []
    for r in csv.DictReader((NOTE / 'out' / 'articles.csv').open(encoding='utf-8-sig')):
        path = NOTE / 'out' / 'drafts' / f"{r['ID']}.md"
        if not path.exists():
            continue
        text = path.read_text(encoding='utf-8')
        m = re.match(r'\s*<!--(.*?)-->\s*', text, re.S)
        memo = m.group(1).strip() if m else ''
        body = text[m.end():] if m else text
        title = ''
        t = re.match(r'#\s+(.+)\n', body)
        if t:
            title, body = t.group(1).strip(), body[t.end():]
        free, _, paid = body.partition('--- ここから有料 ---')
        items.append({
            'id': r['ID'], 'acc': r['アカウント'], 'accName': ACCOUNTS.get(r['アカウント'], ''),
            'title': title or r['タイトル'], 'price': int(str(r['価格'] or 0).replace(',', '')), 'status': r['状態'],
            'writer': r['担当'], 'memo': memo, 'free': free.strip(), 'paid': paid.strip(),
            'chars': len(re.sub(r'\s', '', body)), 'asks': len(re.findall(r'【社長確認', body)),
        })
    return items


def main():
    tpl = (Path(__file__).parent / 'note_preview_template.html').read_text(encoding='utf-8')
    data = json.dumps(load(), ensure_ascii=False).replace('</', '<\\/')
    out = NOTE / 'preview' / 'index.html'
    out.parent.mkdir(exist_ok=True)
    out.write_text(tpl.replace('/*__DATA__*/[]', data), encoding='utf-8')
    print(out)


if __name__ == '__main__':
    main()
