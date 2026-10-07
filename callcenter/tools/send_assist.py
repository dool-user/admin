"""承認済みの文面を送るためのツール（人が1件ずつ確認して送る／HP の問い合わせフォームを自動で送る）

  python tools/send_assist.py            # 承認済みを上から順に（人が確認して送る）
  python tools/send_assist.py --limit 5  # 5件だけ
  python tools/send_assist.py --auto --limit 10   # フォームを自動で送る（10/7 社長が承認。sender.yaml に auto_send: true が必要）

自動送信（--auto）の決まり：
- 送るのは「送る手段=フォーム」かつ SV が「承認済」にした行だけ。Instagram DM は使わない
- 営業お断りの表記があるページ、画像認証（reCAPTCHA・hCaptcha・Turnstile など）があるフォームは送らず「見送り」。認証を回避することはしない
- 同じサイト（ドメイン）に30日以内に送っていたら「見送り」
- 必須の欄を埋められないフォームは送らず「要手動」（人が送る）
- 送る時間は平日の send_hours（初期値 10〜17時）だけ。1件ごとに interval_sec（初期値 90〜240秒の間でランダム）あける。1日の上限 daily_limit を守る
- 送信後の画面を sales/out/screens/<ID>.png に残す。完了の表示が見えたら「送信済」、見えなければ「送信不明」（上限の数には入れる）

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
import random
import re
import sys
import time
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
CAPTCHA_RE = re.compile(r'recaptcha|hcaptcha|turnstile|captcha|画像認証|認証コード|表示されている文字', re.I)
DONE_RE = re.compile(r'ありがとうございま|送信(が|を)?完了|送信いたしました|送信しました|受け付けました|受付(が)?完了|thank you', re.I)
CONFIRM_BTN_RE = re.compile(r'送信|送る|submit|send|この内容で', re.I)
AGREE_RE = re.compile(r'同意|プライバシー|個人情報|privacy|agree', re.I)
NG_RE = re.compile(r'(営業|セールス|勧誘|売り込み)[^。\n]{0,20}(お断り|ご遠慮|禁止|控え|受け付けて(い|お)りません|お受けして(い|お)りません)')


def domain(url):
    m = re.match(r'https?://([^/]+)', url or '')
    return (m.group(1).lower().removeprefix('www.') if m else '')


def recently_sent(rows, url, now, days=30):
    """同じドメインに days 日以内に送っていれば True"""
    d = domain(url)
    for r in rows:
        if r.get('状態') in ('送信済', '送信不明') and domain(r.get('送り先URL')) == d and r.get('送信日時'):
            try:
                t = datetime.strptime(r['送信日時'][:16], '%Y-%m-%d %H:%M').replace(tzinfo=JST)
            except ValueError:
                continue
            if now - t < timedelta(days=days):
                return True
    return False


def in_send_hours(now, hours=(10, 17)):
    return now.weekday() < 5 and hours[0] <= now.hour < hours[1]


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
    return sum(1 for r in rows if r.get('状態') in ('送信済', '送信不明') and (r.get('送信日時') or '').startswith(today))


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


def has_captcha(page):
    return bool(CAPTCHA_RE.search(page.content()))


def prepare_extras(page):
    """同意のチェックを入れ、必須の選択肢は「その他／お問い合わせ」を選ぶ。埋められない必須欄があれば (False, 欄名)"""
    page.evaluate("""(agreeSrc) => {
      const agree = new RegExp(agreeSrc, 'i');
      document.querySelectorAll('form input[type=checkbox]').forEach(cb => {
        const wrap = cb.closest('label, p, li, div, dd, td') || cb.parentElement;
        if (agree.test((wrap && wrap.innerText) || cb.name || '')) cb.checked = true;
      });
      document.querySelectorAll('form select').forEach(s => {
        if (s.value) return;
        const o = [...s.options].find(o => /その他|お問い?合わ?せ|ご相談|ご提案/.test(o.text)) || [...s.options].find(o => o.value);
        if (o) { s.value = o.value; s.dispatchEvent(new Event('change', {bubbles: true})); }
      });
      document.querySelectorAll('form input[type=radio][required]').forEach(r => {
        const g = document.querySelectorAll('form input[type=radio][name="' + r.name + '"]');
        if (![...g].some(x => x.checked)) {
          const pick = [...g].find(x => /その他|お問い?合わ?せ|ご相談/.test((x.closest('label') || x.parentElement).innerText)) || g[g.length - 1];
          pick.checked = true;
        }
      });
    }""", AGREE_RE.pattern)
    empty = page.evaluate("""() => [...document.querySelectorAll('form [required]')]
      .filter(el => el.type !== 'hidden' && (el.offsetWidth || el.offsetHeight))
      .filter(el => (el.type === 'checkbox' || el.type === 'radio') ? !document.querySelector('form input[name="' + el.name + '"]:checked') : !el.value)
      .map(el => el.name || el.id || el.type)""")
    return not empty, empty


def auto_submit(page, shot):
    """送信ボタンを押し、確認画面があればもう一度押す。完了の表示が見えたら True"""
    page.locator('form [type=submit], form button:not([type=button])').first.click()
    page.wait_for_timeout(3000)
    for _ in range(2):
        if DONE_RE.search(page.inner_text('body')):
            break
        nxt = [b for b in page.locator('[type=submit], button').all()
               if b.is_visible() and CONFIRM_BTN_RE.search(b.inner_text() or b.get_attribute('value') or '')]
        if not nxt:
            break
        nxt[0].click()
        page.wait_for_timeout(3000)
    Path(shot).parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(shot), full_page=True)
    return bool(DONE_RE.search(page.inner_text('body')))


def run_auto(args, sender, fields, rows):
    from playwright.sync_api import sync_playwright
    if not sender.get('auto_send'):
        sys.exit('自動送信は sender.yaml に auto_send: true を書いたときだけ動きます')
    limit = int(sender.get('daily_limit', 30))
    lo, hi = sender.get('interval_sec', [90, 240])
    hours = tuple(sender.get('send_hours', [10, 17]))
    todo = [r for r in rows if r.get('状態') == '承認済' and r.get('送る手段') == 'フォーム']
    if args.limit:
        todo = todo[:args.limit]
    today = datetime.now(JST).strftime('%Y-%m-%d')
    print(f'自動送信：承認済のフォーム {len(todo)}件／本日の送信 {sent_today(rows, today)}件（上限 {limit}件）')
    if not args.yes and input('送り始めますか？（y で開始）: ').strip().lower() != 'y':
        return
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not args.show)
        page = browser.new_page(locale='ja-JP')
        for n, r in enumerate(todo):
            now = datetime.now(JST)
            if not in_send_hours(now, hours):
                print(f'送る時間（平日 {hours[0]}〜{hours[1]}時）の外なので止めます')
                break
            if sent_today(rows, now.strftime('%Y-%m-%d')) >= limit:
                print('本日の上限に達したので止めます')
                break

            def mark(state, memo=''):
                r['状態'] = state
                if memo:
                    r['メモ'] = (r.get('メモ', '') + ' ' + memo).strip()
                save_outbox(fields, rows, args.outbox)
                print(f"  {r['ID']} {r['店名']} → {state} {memo}")

            if recently_sent(rows, r['送り先URL'], now):
                mark('見送り', '30日以内に同じサイトへ送信済み')
                continue
            try:
                page.goto(r['送り先URL'], wait_until='domcontentloaded', timeout=30000)
                page.wait_for_timeout(2000)
                ng = NG_RE.search(page.inner_text('body'))
                if ng:
                    mark('見送り', f'営業お断り表記：{ng.group(0)}')
                    continue
                if has_captcha(page):
                    mark('見送り', '画像認証あり（自動では送らない）')
                    continue
                done = fill_form(page, values(sender, r))
                if 'body' not in done:
                    mark('要手動', '本文の欄が見つからない')
                    continue
                ok, empty = prepare_extras(page)
                if not ok:
                    mark('要手動', '埋められない必須欄：' + '・'.join(empty[:5]))
                    continue
                finished = auto_submit(page, ROOT / 'sales' / 'out' / 'screens' / f"{r['ID']}.png")
                r['送信日時'] = datetime.now(JST).strftime('%Y-%m-%d %H:%M')
                mark('送信済' if finished else '送信不明', '' if finished else '完了の表示が見えない（画面を確認）')
            except Exception as e:
                mark('要手動', f'エラー：{type(e).__name__}')
                continue
            if n < len(todo) - 1:
                time.sleep(random.uniform(lo, hi))
        browser.close()
    print(f"本日の送信 {sent_today(rows, datetime.now(JST).strftime('%Y-%m-%d'))}件")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--limit', type=int, default=0, help='今回扱う件数（0で上限まで）')
    ap.add_argument('--outbox', default=str(OUTBOX))
    ap.add_argument('--auto', action='store_true', help='フォームを自動で送る（sender.yaml の auto_send: true が必要）')
    ap.add_argument('--yes', action='store_true', help='--auto の開始確認を省く')
    ap.add_argument('--show', action='store_true', help='--auto でブラウザの画面を表示する')
    args = ap.parse_args(argv)

    import yaml
    from playwright.sync_api import sync_playwright

    if not SENDER.exists():
        sys.exit(f'{SENDER.name} がありません。sender.yaml.example をコピーして、送信者の情報を入れてください')
    sender = yaml.safe_load(SENDER.read_text(encoding='utf-8')) or {}
    if any('★' in str(v) for v in sender.values()):
        sys.exit('sender.yaml に「★要変更」が残っています')
    fields, rows = load_outbox(args.outbox)
    if args.auto:
        return run_auto(args, sender, fields, rows)
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
