"""送り先リスト（sales/data/leads.csv）に優先度を付ける（10/9 ユニシードの営業員・小寺さんの現場の知見。sales/knowledge.md「狙う先」）

  python tools/lead_score.py          # 優先度・狙う理由を入れ、優先度の高い順に並べ直す

狙うのは「すでに集客に取り組んでいるが、まだ伸ばせる店」。点数は目安（受注の実績が出たら重みを直す）。
人が見て入れる列（GBPの様子・昼夜営業・駅近）は、空なら点数に入れない。
"""
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEADS = ROOT / 'sales' / 'data' / 'leads.csv'

# 業種の重み（整骨院系は高単価になりやすい）
GENRE = [
    (re.compile(r'整骨|接骨|整体'), 3, '整骨院系（高単価になりやすい）'),
    (re.compile(r'エステ|脱毛|まつ(げ|エク)|ネイル'), 2, 'エステ関連'),
    (re.compile(r'美容|ヘア|hair|理容', re.I), 2, '美容院'),
    (re.compile(r'居酒屋|フレンチ|フランス料理|イタリア|ビストロ|トラットリア'), 2, '居酒屋・フレンチ・イタリアン'),
    (re.compile(r'クリニック|医院|歯科|診療所'), 2, '医療系'),
    (re.compile(r'飲食|レストラン|食堂|カフェ|ラーメン|焼肉|寿司|そば|うどん|中華|和食'), 1, '飲食店'),
]
# 店名に付いた余計な言葉（例：エステ○○／hair／まつエク【○○駅】）
NAME_STUFF = re.compile(r'[【】\[\]｜|/／]|駅|徒歩\d|(駅前|最寄)')
GBP_STALL = re.compile(r'止ま|途中|少し|放置')
GBP_DROP = re.compile(r'一時|急に|ぴたっと|ピタッと|業者')
YES = re.compile(r'^(1|あり|有|yes|y|○|◯)$', re.I)


def score(r):
    pts, why = 0, []
    text = ' '.join([r.get('業種', ''), r.get('店名', '')])
    for rx, p, label in GENRE:
        if rx.search(text):
            pts += p
            why.append(label)
            break
    if r.get('公式サイト'):
        pts += 1
        why.append('HPあり')
    if r.get('Instagram'):
        pts += 2
        why.append('Instagramあり（集客の意識が高い）')
    try:
        n = int(re.sub(r'\D', '', r.get('Google口コミ数', '')) or -1)
    except ValueError:
        n = -1
    if 10 <= n <= 200:  # 「ある程度ある」の仮の幅
        pts += 1
        why.append(f'口コミ{n}件')
    gbp = r.get('GBPの様子', '')
    if GBP_DROP.search(gbp):
        pts += 2
        why.append('更新が急に止まった（業者をやめた可能性）')
    elif GBP_STALL.search(gbp):
        pts += 2
        why.append('更新が途中で止まっている（やりたいが手が回らない）')
    if YES.match(r.get('昼夜営業', '').strip()):
        pts += 2
        why.append('ランチ＋ディナー')
    if YES.match(r.get('駅近', '').strip()):
        pts += 1
        why.append('駅近')
    if NAME_STUFF.search(r.get('店名', '')):
        pts += 1
        why.append('店名に余計な言葉（店名の整え方の話ができる）')
    if r.get('区分') == '医療':
        why = [w for w in why if not w.startswith('口コミ')]  # 医療では口コミの話をしない
    return pts, why


def main(path=LEADS):
    with Path(path).open(encoding='utf-8-sig', newline='') as f:
        rd = csv.DictReader(f)
        fields, rows = list(rd.fieldnames), list(rd)
    for c in ('優先度', '狙う理由'):
        if c not in fields:
            fields.append(c)
    for r in rows:
        p, why = score(r)
        r['優先度'], r['狙う理由'] = str(p), '・'.join(why)
    rows.sort(key=lambda r: (-int(r.get('反響') == '1'), -int(r['優先度'])))
    with Path(path).open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f'{len(rows)}件に優先度を付けました（反響→優先度の高い順）')


if __name__ == '__main__':
    main(*sys.argv[1:])
