"""
本番ドメインを LP の各ファイルに反映する
使い方: python3 scripts/set_domain.py denki-kaitsu.com
（canonical / og:url / robots.txt / sitemap.xml の https://example.com を置き換え）
"""
import re
import sys
from pathlib import Path

if len(sys.argv) != 2 or not re.fullmatch(r'[a-z0-9.-]+\.[a-z]{2,}', sys.argv[1]):
    sys.exit('使い方: python3 scripts/set_domain.py your-domain.com')
domain = sys.argv[1]
root = Path(__file__).resolve().parent.parent / 'lp'
targets = [root / 'tokyo' / 'index.html', root / 'robots.txt', root / 'sitemap.xml']
pattern = re.compile(r'https://(?:example\.com|[a-z0-9.-]+\.[a-z]{2,})(?=/)')
for path in targets:
    text = path.read_text(encoding='utf-8')
    if path.name == 'index.html':
        new = re.sub(r'(<link rel="canonical" href=")https://[^/"]+', r'\g<1>https://' + domain, text)
        new = re.sub(r'(<meta property="og:url" content=")https://[^/"]+', r'\g<1>https://' + domain, new)
    else:
        new = pattern.sub('https://' + domain, text)
    path.write_text(new, encoding='utf-8')
    print(('更新' if new != text else '変更なし'), path.relative_to(root.parent))
