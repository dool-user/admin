"""営業文面の A/B テスト（10/12 社長の指示：何通かテストで送り、AB 検証で良いものに変えていく）

  python tools/ab_test.py assign          # 文面案が空の下書きに、区分ごとに A・B を交互に割り当てる
  python tools/ab_test.py report          # 文面案ごとの 送信数・返信数・アポ数・率 と判定

テストの中身・判定の決まりは sales/ab-tests.md。文面の型は sales/templates.md の「テスト中の文面案」。
- 送信数＝状態が 送信済・送信不明・返信あり・アポ（送った行）
- 返信数＝返信日時が入っている、または状態が 返信あり・アポ（断りの返信も入る）
- アポ数＝状態が アポ
判定は「両方の案が最低件数（初期値 各100通）を送ったあと」だけ。それまでは「途中」と出す（少ない数で決めない）。
"""
import argparse
import csv
import math
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTBOX = ROOT / 'sales' / 'out' / 'outbox.csv'
VARIANTS = ['A', 'B']
MIN_SENT = 100
SENT = {'送信済', '送信不明', '返信あり', 'アポ'}


def load(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as f:
        rd = csv.DictReader(f)
        return list(rd.fieldnames), list(rd)


def save(path, fields, rows):
    with Path(path).open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def assign(rows, variants=VARIANTS):
    """文面案が空の下書きに、区分ごとに交互に割り当てる（区分の偏りで差が出ないように）。割り当てた件数を返す"""
    count = defaultdict(int)
    for r in rows:
        if r.get('文面案'):
            count[r.get('区分', '')] += 1
    n = 0
    for r in rows:
        if r.get('状態') == '下書き' and not r.get('文面案'):
            k = r.get('区分', '')
            r['文面案'] = variants[count[k] % len(variants)]
            count[k] += 1
            n += 1
    return n


def tally(rows):
    t = {v: {'送信': 0, '返信': 0, 'アポ': 0} for v in sorted({r.get('文面案') for r in rows if r.get('文面案')})}
    for r in rows:
        v = r.get('文面案')
        if not v or r.get('状態') not in SENT and not r.get('返信日時'):
            continue
        t[v]['送信'] += 1
        if r.get('返信日時') or r.get('状態') in ('返信あり', 'アポ'):
            t[v]['返信'] += 1
        if r.get('状態') == 'アポ':
            t[v]['アポ'] += 1
    return t


def fisher_p(a, b, c, d):
    """2×2 表 [[a,b],[c,d]] のフィッシャーの正確検定（両側）の p 値"""
    n1, n2, k = a + b, c + d, a + c
    n = n1 + n2

    def pr(x):
        return math.comb(n1, x) * math.comb(n2, k - x) / math.comb(n, k)
    p0 = pr(a)
    lo, hi = max(0, k - n2), min(k, n1)
    return min(1.0, sum(pr(x) for x in range(lo, hi + 1) if pr(x) <= p0 * (1 + 1e-9)))


def judge(t, metric='返信', min_sent=MIN_SENT):
    vs = [v for v in VARIANTS if v in t]
    if len(vs) < 2:
        return '途中（案が2つそろっていない）'
    a, b = t[vs[0]], t[vs[1]]
    if a['送信'] < min_sent or b['送信'] < min_sent:
        return f'途中（各{min_sent}通まで：{vs[0]} {a["送信"]}通／{vs[1]} {b["送信"]}通）'
    p = fisher_p(a[metric], a['送信'] - a[metric], b[metric], b['送信'] - b[metric])
    ra, rb = a[metric] / a['送信'], b[metric] / b['送信']
    if p < 0.05:
        win = vs[0] if ra > rb else vs[1]
        return f'{win} の勝ち（{metric}率 {ra:.1%} 対 {rb:.1%}、p={p:.3f}）'
    return f'差は言えない（{metric}率 {ra:.1%} 対 {rb:.1%}、p={p:.3f}）。件数を増やすか、差の大きい案に変えて続ける'


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cmd', choices=['assign', 'report'])
    ap.add_argument('--outbox', default=str(OUTBOX))
    ap.add_argument('--min', type=int, default=MIN_SENT, help='判定に必要な各案の送信数')
    args = ap.parse_args(argv)
    fields, rows = load(args.outbox)
    if '文面案' not in fields:
        sys.exit('outbox.csv に「文面案」の列がありません')
    if args.cmd == 'assign':
        n = assign(rows)
        save(args.outbox, fields, rows)
        print(f'{n}件に文面案を割り当てました')
        return
    t = tally(rows)
    print('文面案  送信  返信  アポ  返信率  アポ率')
    for v, x in t.items():
        s = x['送信'] or 1
        print(f"{v:>4}  {x['送信']:>4}  {x['返信']:>4}  {x['アポ']:>4}  {x['返信']/s:>6.1%}  {x['アポ']/s:>6.1%}")
    st = defaultdict(int)
    for r in rows:
        st[r.get('状態', '')] += 1
    complaints = sum(1 for r in rows if '苦情' in r.get('メモ', ''))
    tried = sum(st[k] for k in ('送信済', '送信不明', '返信あり', 'アポ', '要手動'))
    bad = st['送信不明'] + st['要手動']
    print(f"送信の状態：送信済 {st['送信済']}／送信不明 {st['送信不明']}／要手動 {st['要手動']}／見送り {st['見送り']}／苦情 {complaints}"
          + (f"（送信不明＋要手動 {bad / tried:.0%}。2割以下で苦情0なら上限を1段上げてよいか社長に聞く）" if tried else ''))
    print('判定（返信率）：' + judge(t, '返信', args.min))
    print('判定（アポ率）：' + judge(t, 'アポ', args.min))


if __name__ == '__main__':
    main()
