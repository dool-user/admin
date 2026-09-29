"""承認済みの文面を、人が1件ずつ確認して送るための補助ツール

  python tools/send_assist.py            # 承認済みを上から順に
  python tools/send_assist.py --limit 5  # 5件だけ

- フォーム：ブラウザでフォームを開き、名前・会社名・メール・電話・件名・本文を入力して、送信ボタンに枠を付けて止まる
  **送信ボタンは押しません。** 内容を確かめて、人が押してください（同意のチェック・選択肢も人が選ぶ）
- Instagram DM：プロフィールを開き、文面を画面右下に出す（コピーして DM に貼り付け、人が送る）
- 送ったら Enter（s）で outbox.csv の状態を「送信済」にし、送信日時を入れる
- 1日の上限（sender.yaml の daily_limit）を超えたら止まる。営業お断り表記が見つかったフォームは開くだけで入力しない

準備：leadgen と同じ Python 環境（playwright, PyYAML）で動きます。sender.yaml.example を sender.yaml にコピーして書き換えてください。
Instagram は初回だけブラウザでログインしてください（ログイン状態は callcenter/.browser に残ります）。
"""
import argparse
import csv
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTBOX = ROOT / 'sales' / 'out' / 'outbox.csv'
SENDER = ROOT / 'sender.yaml'
JST = timezone(timedelta(hours=9))

# ラベル・name・placeholder から入力欄の種類を決める（上から順に判定）
FIELD_RULES = [
    ('skip', re.compile(r'確認用|再入力|confirm|郵便|zip|住所|address|url|ホームページ|年齢|生年', re.I)),
    ('email', re.compile(r'e-?mail|メール|mail', re.I)),
    ('phone', re.compile(r'tel|phone|電話|携帯', re.I)),
    ('kana', re.compile(r'kana|フリガナ|ふりがな|カナ|furigana', re.I)),
    ('company', re.compile(r'company|corp|organization|会社|法人|企業|団体|屋号|店舗名|貴社|御社', re.I)),
    ('subject', re.compile(r'subject|title|件名|タイトル|用件', re.I)),
    ('name', re.compile(r'name|名前|氏名|担当|お名前', re.I)),
]
NG_RE = re.compile(r'(営業|セールス|勧誘|売り込み)[^。\n]{0,20}(お断り|ご遠慮|禁止|控え|受け付けて(い|お)りません|お受けして(い|お)りません)')


def classify(label, tag='input', typ='text'):
    """入力欄 → 'email' / 'phone' / 'kana' / 'company' / 'subject' / 'name' / 'body' / ''（触らない）"""
    typ = (typ or 'text').lower()
    if tag == 'textarea':
        return 'body'
    if typ in ('hidden', 'submit', 'button', 'checkbox', 'radio', 'file', 'image', 'reset', 'password', 'search'):
        return ''
    if typ == 'email':
        return '' if re.search(r'確認|再入力|confirm', label or '', re.I) else 'email'
    if typ == 'tel':
        return 'phone'
    for kind, rx in FIELD_RULES:
        if rx.search(label or ''):
            return '' if kind == 'skip' else kind
    return ''


def values(sender, row):
    return {
        'name': sender.get('name', ''), 'kana': sender.get('name_kana', ''), 'company': sender.get('company', ''),
        'email': sender.get('email', ''), 'phone': sender.get('phone', ''),
        'subject': row.get('件名', ''), 'body': row.get('本文', ''),
    }


def load_outbox(path=OUTBOX):
    with Path(path).open(encoding='utf-8-sig', newline='') as f:
        r = csv.DictReader(f)
        return r.fieldnames, list(r)


def save_outbox(fields, rows, path=OUTBOX):
    with Path(path).open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def sent_today(rows, today):
    return sum(1 for r in rows if r.get('状態') == '送信済' and (r.get('送信日時') or '').startswith(today))


LABEL_JS = """els => els.map(el => {
  const id = el.id && document.querySelector('label[for="' + CSS.escape(el.id) + '"]');
  const wrap = el.closest('label, tr, dd, .form-group, p, li') || el.parentElement;
  let ctx = wrap ? wrap.innerText : '';
  if (wrap && wrap.tagName === 'DD' && wrap.previousElementSibling) ctx = wrap.previousElementSibling.innerText;
  const primary = [id && id.innerText, el.getAttribute('aria-label'), el.name, el.id, el.placeholder].filter(Boolean).join(' ');
  const vis = !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
  return {tag: el.tagName.toLowerCase(), type: el.type || '', label: primary, ctx: (ctx || '').slice(0, 40), visible: vis};
})"""

PANEL_JS = """text => {
  const d = document.createElement('div');
  d.style.cssText = 'position:fixed;right:16px;bottom:16px;z-index:2147483647;width:340px;background:#fff;color:#111;'
    + 'border:2px solid #e8590c;border-radius:10px;padding:10px;font:13px sans-serif;box-shadow:0 6px 24px rgba(0,0,0,.25)';
  d.innerHTML = '<b>送る文面（コピーして貼り付け、人が送信）</b>';
  const t = document.createElement('textarea');
  t.value = text; t.style.cssText = 'width:100%;height:160px;margin-top:6px';
  d.appendChild(t); document.body.appendChild(d); t.focus(); t.select();
}"""


def fill_form(page, vals):
    """入力できた欄の種類を返す。送信ボタンは押さず、枠で示すだけ"""
    fields = page.locator('form input, form textarea')
    infos = fields.evaluate_all(LABEL_JS)
    done = []
    for i, info in enumerate(infos):
        kind = classify(info['label'], info['tag'], info['type']) or classify(info['ctx'], info['tag'], info['type'])
        if not kind or not info['visible'] or not vals.get(kind):
            continue
        if kind != 'body' and kind in done:
            continue
        try:
            fields.nth(i).fill(vals[kind])
            done.append(kind)
        except Exception:
            pass
    page.evaluate("""() => {
      const b = document.querySelector('form [type=submit], form button:not([type=button])');
      if (b) { b.style.outline = '4px solid #e8590c'; b.scrollIntoView({block: 'center'}); }
    }""")
    return done


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--limit', type=int, default=0, help='今回扱う件数（0で上限まで）')
    ap.add_argument('--outbox', default=str(OUTBOX))
    args = ap.parse_args(argv)

    import yaml
    from playwright.sync_api import sync_playwright

    if not SENDER.exists():
        sys.exit(f'{SENDER.name} がありません。sender.yaml.example をコピーして、送信者の情報を入れてください')
    sender = yaml.safe_load(SENDER.read_text(encoding='utf-8')) or {}
    if any('★' in str(v) for v in sender.values()):
        sys.exit('sender.yaml に「★要変更」が残っています')
    fields, rows = load_outbox(args.outbox)
    today = datetime.now(JST).strftime('%Y-%m-%d')
    limit = int(sender.get('daily_limit', 30))
    todo = [r for r in rows if r.get('状態') == '承認済']
    if args.limit:
        todo = todo[:args.limit]
    print(f'承認済 {len(todo)}件／本日の送信 {sent_today(rows, today)}件（上限 {limit}件）')

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(str(ROOT / '.browser'), headless=False, locale='ja-JP')
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        for r in todo:
            if sent_today(rows, today) >= limit:
                print('本日の上限に達したので止めます')
                break
            print(f"\n── {r['ID']} {r['店名']}（{r['送る手段']}）\n{r['送り先URL']}")
            page.goto(r['送り先URL'], wait_until='domcontentloaded')
            page.wait_for_timeout(1500)
            if r['送る手段'] == 'フォーム':
                ng = NG_RE.search(page.inner_text('body'))
                if ng:
                    print(f'  「{ng.group(0)}」の表記があります。入力しません → 見送りにします')
                    r['状態'], r['メモ'] = '見送り', (r.get('メモ', '') + f' 営業お断り表記：{ng.group(0)}').strip()
                    save_outbox(fields, rows, args.outbox)
                    continue
                done = fill_form(page, values(sender, r))
                print(f"  入力した欄：{'・'.join(done) or 'なし（手で入力してください）'}")
                print('  同意のチェック・選択肢を確かめ、内容を見直してから、ブラウザで送信ボタンを押してください')
            else:
                page.evaluate(PANEL_JS, r['本文'])
                print('  右下の文面をコピーし、「メッセージ」から貼り付けて送ってください')
            ans = input('  送った → Enter ／ 見送り → n ／ あとで → k ／ 終了 → q : ').strip().lower()
            if ans == 'q':
                break
            if ans == 'k':
                continue
            if ans == 'n':
                r['状態'] = '見送り'
            else:
                r['状態'], r['送信日時'] = '送信済', datetime.now(JST).strftime('%Y-%m-%d %H:%M')
            save_outbox(fields, rows, args.outbox)
        ctx.close()
    print(f'本日の送信 {sent_today(rows, today)}件')


if __name__ == '__main__':
    main()
