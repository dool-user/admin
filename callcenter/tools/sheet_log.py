"""送付した案件を Google スプレッドシート（営業部 送付管理）に記録する（10/7 社長の指示）

送信ツール（send_assist.py）が送信済・送信不明・見送り・要手動のたびに自動で呼ぶ。
返信・アポは案件処理が、同じ ID で上書きする：

  python tools/sheet_log.py --test                                  # 設定の確認（「テスト」の行が入る）
  python tools/sheet_log.py --id S0012 --reply あり --reply-date 2026-10-09
  python tools/sheet_log.py --id S0012 --appt "2026-10-15 14:00" --owner ユイ
  python tools/sheet_log.py --flush                                 # 送れずに残った分を送り直す

設定：sender.yaml の sheet_webhook（Apps Script の …/exec）と sheet_token。受け側は gas/sales-log-receiver.gs。
送れなかった分は sales/out/sheet_pending.jsonl に残し、次に送るときに先に送り直す（記録が抜けないように）。
"""
import argparse
import json
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PENDING = ROOT / 'sales' / 'out' / 'sheet_pending.jsonl'
SENDER = ROOT / 'sender.yaml'
JST = timezone(timedelta(hours=9))
# outbox.csv の列 → シートの列
MAP = {'送信日時': '送信日時', 'ID': 'ID', '区分': '区分', '店名': '名称', '都道府県': '都道府県', '住所': '住所',
       '送り先URL': '送り先URL', '件名': '件名', '状態': '状態', 'メモ': 'メモ', 'リストの出典': 'リストの出典'}


def row_to_record(r):
    return {v: r.get(k, '') for k, v in MAP.items()}


def _post(url, payload, timeout=20):
    req = urllib.request.Request(url, data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as res:  # Apps Script は 302 で結果を返す（urllib が追う）
        return json.loads(res.read().decode('utf-8') or '{}')


def flush(sender, pending=PENDING, post=_post):
    """残っている分を送り直す。送れなかった件数を返す"""
    p = Path(pending)
    if not p.exists():
        return 0
    left = []
    for line in p.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        try:
            if not post(sender['sheet_webhook'], {**rec, 'token': sender.get('sheet_token', '')}).get('ok'):
                left.append(line)
        except Exception:
            left.append(line)
    if left:
        p.write_text('\n'.join(left) + '\n', encoding='utf-8')
    else:
        p.unlink()
    return len(left)


def log(sender, rec, pending=PENDING, post=_post):
    """1件を記録する。sheet_webhook がなければ何もしない。送れなければ pending に残す。成功で True"""
    url = (sender or {}).get('sheet_webhook')
    if not url:
        return False
    if Path(pending).exists():
        flush(sender, pending, post)
    try:
        res = post(url, {**rec, 'token': sender.get('sheet_token', '')})
        if res.get('ok'):
            return True
        print(f"  シートに書けませんでした：{res.get('error', '不明')}（あとで送り直します）")
    except Exception as e:
        print(f'  シートに書けませんでした：{type(e).__name__}（あとで送り直します）')
    Path(pending).parent.mkdir(parents=True, exist_ok=True)
    with Path(pending).open('a', encoding='utf-8') as f:
        f.write(json.dumps(rec, ensure_ascii=False) + '\n')
    return False


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--id')
    ap.add_argument('--reply', help='返信（例：あり／断り／なし）')
    ap.add_argument('--reply-date')
    ap.add_argument('--appt', help='アポ日時')
    ap.add_argument('--owner', help='担当')
    ap.add_argument('--memo')
    ap.add_argument('--test', action='store_true')
    ap.add_argument('--flush', action='store_true')
    args = ap.parse_args(argv)
    import yaml
    sender = yaml.safe_load(SENDER.read_text(encoding='utf-8')) if SENDER.exists() else {}
    if not (sender or {}).get('sheet_webhook'):
        sys.exit('sender.yaml に sheet_webhook（Apps Script の URL）と sheet_token を入れてください')
    if args.flush:
        left = flush(sender)
        print(f'送り直し：残り {left}件')
        return
    if args.test:
        rec = {'ID': 'TEST', '名称': 'テスト', '状態': 'テスト', '送信日時': datetime.now(JST).strftime('%Y-%m-%d %H:%M')}
    else:
        if not args.id:
            sys.exit('--id を指定してください')
        rec = {'ID': args.id, '返信': args.reply, '返信日': args.reply_date, 'アポ日時': args.appt, '担当': args.owner,
               'メモ': args.memo}
        rec = {k: v for k, v in rec.items() if v}
    print('記録しました' if log(sender, rec) else '記録できませんでした（sales/out/sheet_pending.jsonl に残しました）')


if __name__ == '__main__':
    main()
