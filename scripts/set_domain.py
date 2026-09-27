"""
本番ドメインを LP の各ファイルに反映する
使い方: python3 scripts/set_domain.py denki-kaitsu-support.com
（sitemap.xml に書かれている今のドメインを、lp/ 内の HTML・robots.txt・sitemap.xml ですべて置き換える。
  canonical・og:url・og:image・構造化データ（JSON-LD）などが対象）
"""
import re
import sys
from pathlib import Path

if len(sys.argv) != 2 or not re.fullmatch(r'[a-z0-9.-]+\.[a-z]{2,}', sys.argv[1]):
    sys.exit('使い方: python3 scripts/set_domain.py your-domain.com')
domain = sys.argv[1]
root = Path(__file__).resolve().parent.parent / 'lp'

current = re.search(r'<loc>https://([^/<]+)/', (root / 'sitemap.xml').read_text(encoding='utf-8'))
if not current:
    sys.exit('sitemap.xml から今のドメインを読み取れませんでした')
old = current.group(1)
if old == domain:
    sys.exit(f'すでに {domain} になっています')

targets = sorted(root.glob('*.html')) + sorted(root.glob('*/index.html')) + [root / 'robots.txt', root / 'sitemap.xml']
for path in targets:
    text = path.read_text(encoding='utf-8')
    new = text.replace('https://' + old, 'https://' + domain)
    if new != text:
        path.write_text(new, encoding='utf-8')
        print('更新', path.relative_to(root.parent))
