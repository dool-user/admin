"""社長が note に「コピーして貼るだけ」で公開できる公開キット（1枚の HTML）を作る

  python tools/build_note_kit.py N016 N001 N018 N005 N006   # → note/launch/kit/index.html

本文は out/publish/<ID>.md（build_note_publish.py で作ったもの）を使い、無料部分と有料部分に分けてコピーできるようにする。
画像は kit/images/<ID>/ に写す（Artifact に出すときは files で渡す）。
"""
import csv
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOTE = ROOT / 'note'
MAGAZINE = {'A01': 'AIで営業チームを作る', 'A02': 'AIと人で回す店舗営業', 'A03': 'お店のGoogleマップ集客', 'A11': '（マガジンなし）'}
ACCOUNT = {'A01': 'ツナグラボ', 'A02': 'ツナグラボ', 'A03': 'ツナグラボ', 'A11': 'まるっと窓口'}
URL = {'ツナグラボ': 'https://note.com/tunagulab', 'まるっと窓口': 'https://note.com/maruttosupport'}
CHECKS = {
    'N016': ['Claude Code の機能名（権限・確認画面など）を公式ドキュメントで1回見る'],
    'N001': ['「始めた時期」は本文から外してある。書けるなら「筆者がやったこと」の最後に1文足す'],
    'N103': ['送信の仕組み（send_assist.py）の説明が今の設定と合っているか、ざっと見る'],
    'N104': ['Google ヘルプ「特別営業時間を設定する方法」を開いて、手順と「7日以上は臨時休業」の説明が合っているか見る（こちらでは原文を開けなかった）'],
    'N018': ['下の Google ヘルプを開いて、本文の説明と合っているか見る（こちらの環境では原文を開けなかった）',
             '相談フォームの案内は外してある。フォームを公開したら足す'],
}


def main(ids):
    rows = {r['ID']: r for r in csv.DictReader((NOTE / 'out' / 'articles.csv').open(encoding='utf-8-sig'))}
    out = NOTE / 'launch' / 'kit'
    items = []
    for aid in ids:
        r = rows[aid]
        text = (NOTE / 'out' / 'publish' / f'{aid}.md').read_text(encoding='utf-8')
        title = re.match(r'#\s+(.+)\n', text).group(1).strip()
        body = text.split('\n', 1)[1].strip()
        free, _, paid = body.partition('--- ここから有料 ---')
        tags = next((l for l in body.split('\n') if re.match(r'#[^\s#]', l)), '')
        draft = (NOTE / 'out' / 'drafts' / f'{aid}.md').read_text(encoding='utf-8')
        links = re.findall(r'^- (.+?)：(https://support\.google\.com/[^\s（]+)', draft.split('### 社長に原文を確認')[-1], re.M) if '### 社長に原文を確認' in draft else []
        imgs = sorted(p.name for p in (NOTE / 'out' / 'images' / aid).glob('*.png'))
        shutil.copytree(NOTE / 'out' / 'images' / aid, out / 'images' / aid, dirs_exist_ok=True)
        acc = ACCOUNT[r['アカウント']]
        items.append({'id': aid, 'title': title, 'price': int(r['価格'].replace(',', '') or 0), 'account': acc,
                      'accountUrl': URL[acc], 'magazine': MAGAZINE[r['アカウント']], 'free': free.strip(), 'paid': paid.strip(),
                      'images': imgs, 'checks': CHECKS.get(aid, []), 'links': [{'name': n, 'url': u} for n, u in links], 'tags': tags})
    tpl = (Path(__file__).parent / 'note_kit_template.html').read_text(encoding='utf-8')
    data = json.dumps(items, ensure_ascii=False).replace('</', '<\\/')
    (out / 'index.html').write_text(tpl.replace('/*__DATA__*/[]', data), encoding='utf-8')
    print(out / 'index.html')


if __name__ == '__main__':
    main(sys.argv[1:])
