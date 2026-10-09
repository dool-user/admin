"""アポのトス（商談担当への引き継ぎ）を、決まったフォーマットで出す（10/9 ユニシードのトスフォーマット）

  python tools/toss.py S0012          # sales/out/appointments.csv の ID=S0012 をトスの文面にして表示
  python tools/toss.py S0012 --log    # あわせて送付管理シートの同じ ID の行に アポ日時・担当 を入れる

appointments.csv には携帯番号が入るので Git に入れない（.gitignore 済み。列の見本は appointments.example.csv）。
項目が当てはまらないときは空のままでよい（トスでは「—」と出す）。項目を足すときは TOSS_FIELDS と見本の CSV を両方直す。
"""
import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APPTS = ROOT / 'sales' / 'out' / 'appointments.csv'
EXAMPLE = ROOT / 'sales' / 'out' / 'appointments.example.csv'
TOSS_FIELDS = ['店舗名', '提案商材', '料金提示', '名前/役職', '携帯番号', 'URL', '前確認日/時間', '商談日', '商談時間', 'リンク',
               'アポインター名', 'リコール取得者', '備考/懸念点']


def toss_text(r):
    lines = ['【アポ登録】']
    for k in TOSS_FIELDS:
        lines += [f'▼{k}', (r.get(k) or '').strip() or '—']
    return '\n'.join(lines)


def load(path=APPTS):
    p = Path(path)
    if not p.exists():
        p.write_text(EXAMPLE.read_text(encoding='utf-8-sig'), encoding='utf-8-sig')
    with p.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('id', help='outbox の ID')
    ap.add_argument('--log', action='store_true', help='送付管理シートにも アポ日時・担当 を入れる')
    args = ap.parse_args(argv)
    row = next((r for r in load() if r.get('ID') == args.id), None)
    if not row:
        sys.exit(f'{APPTS.name} に ID={args.id} がありません')
    print(toss_text(row))
    if args.log:
        sys.path.insert(0, str(Path(__file__).parent))
        import yaml
        import sheet_log
        sender = yaml.safe_load((ROOT / 'sender.yaml').read_text(encoding='utf-8')) or {}
        rec = {'ID': args.id, 'アポ日時': f"{row.get('商談日', '')} {row.get('商談時間', '')}".strip(),
               '担当': row.get('アポインター名', ''), '状態': 'アポ'}
        print('\nシート：' + ('記録しました' if sheet_log.log(sender, rec) else '記録できませんでした（あとで送り直します）'))


if __name__ == '__main__':
    main()
