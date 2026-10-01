"""ストックの下書きから、note に貼る「公開用」の本文を作る

  python tools/build_note_publish.py N016 N001 ...   # → note/out/publish/<ID>.md

- 先頭の社内メモ（<!-- -->）と、末尾の「公開前に消す」一覧を外す
- 【社長確認】が残る行は消す（N001 の「始めた時期」のように、タグだけ外せばよい箇所は KEEP_LINE に書く）
- 相談フォームの URL が未定の記事は、相談の案内の段落ごと外す（フォーム公開後に足す）
- 画像は note に別でアップロードするので「［画像：ファイル名］」の目印に置き換える
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOTE = ROOT / 'note' / 'out'
KEEP_LINE = {'N001'}  # 【社長確認：…】のタグだけ外し、文は残す


def build(aid):
    text = (NOTE / 'drafts' / f'{aid}.md').read_text(encoding='utf-8')
    text = re.sub(r'\A\s*<!--.*?-->\s*', '', text, flags=re.S)
    # 「公開前に消す」一覧・社長向けの確認欄（末尾の --- 以降に置いてある）
    text = re.split(r'\n---\n+(?=###? 社長に|\*\*【社長確認】\*\*|## 確認リスト|### 確認リスト)', text)[0]
    # 「難しいと思ったら」の相談の節は、フォーム URL が未定なら節ごと外す
    text = re.sub(r'\n## 「自分でやるのは難しい」と思ったら\n.*?(?=\n## |\n---|\Z)',
                  lambda m: '' if '【社長確認' in m.group(0) else m.group(0), text, flags=re.S)
    lines = []
    for line in text.split('\n'):
        if '【社長確認' in line:
            if aid in KEEP_LINE:
                line = re.sub(r'【社長確認[^】]*】', '', line).rstrip()
            else:
                continue
        lines.append(line)
    text = '\n'.join(lines)
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
