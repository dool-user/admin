import pytest

from send_assist import classify, fill_form, sent_today, values


@pytest.mark.parametrize('label,tag,typ,expected', [
    ('your-name お名前', 'input', 'text', 'name'),
    ('フリガナ', 'input', 'text', 'kana'),
    ('会社名・店舗名', 'input', 'text', 'company'),
    ('email', 'input', 'email', 'email'),
    ('メールアドレス（確認用）', 'input', 'email', ''),
    ('電話番号', 'input', 'text', 'phone'),
    ('件名', 'input', 'text', 'subject'),
    ('your-message', 'textarea', '', 'body'),
    ('郵便番号', 'input', 'text', ''),
    ('プライバシーポリシーに同意', 'input', 'checkbox', ''),
    ('キーワード', 'input', 'search', ''),
])
def test_classify(label, tag, typ, expected):
    assert classify(label, tag, typ) == expected


def test_sent_today():
    rows = [{'状態': '送信済', '送信日時': '2026-09-29 10:00'}, {'状態': '送信済', '送信日時': '2026-09-28 10:00'},
            {'状態': '承認済', '送信日時': ''}]
    assert sent_today(rows, '2026-09-29') == 1


FORM = """<form action="/thanks" method="post">
<dl><dt>お名前</dt><dd><input name="f1"></dd>
<dt>会社名</dt><dd><input name="f2"></dd></dl>
<label>メール<input type="email" name="mail"></label>
<label>メール（確認用）<input type="email" name="mail2"></label>
<p>電話 <input type="tel" name="t"></p>
<input name="zip" placeholder="郵便番号">
<textarea name="msg"></textarea>
<label><input type="checkbox" name="agree">同意する</label>
<button type="submit">送信</button></form>"""


def test_fill_form_never_submits():
    pw = pytest.importorskip('playwright.sync_api')
    sender = {'name': '山田 太郎', 'company': '株式会社サンプル', 'email': 'taro@example.com', 'phone': '03-0000-0000'}
    with pw.sync_playwright() as p:
        try:
            b = p.chromium.launch()
        except Exception as e:
            pytest.skip(f'ブラウザを起動できない: {e}')
        page = b.new_page()
        page.set_content(FORM)
        done = fill_form(page, values(sender, {'件名': '', '本文': 'はじめまして'}))
        got = page.evaluate("() => Object.fromEntries([...document.querySelectorAll('input,textarea')].map(e => [e.name, e.type === 'checkbox' ? e.checked : e.value]))")
        assert got == {'f1': '山田 太郎', 'f2': '株式会社サンプル', 'mail': 'taro@example.com', 'mail2': '', 't': '03-0000-0000',
                       'zip': '', 'msg': 'はじめまして', 'agree': False}
        assert page.url == 'about:blank'  # 送信していない
        assert set(done) == {'name', 'company', 'email', 'phone', 'body'}
        b.close()


# ── 自動送信（--auto）の決まり ──
from datetime import datetime  # noqa: E402

from send_assist import (JST, auto_submit, domain, has_captcha, in_send_hours,  # noqa: E402
                         prepare_extras, recently_sent)


def test_domain_and_recently_sent():
    assert domain('https://www.example.com/contact/') == 'example.com'
    now = datetime(2026, 10, 8, 11, 0, tzinfo=JST)
    rows = [{'状態': '送信済', '送り先URL': 'https://example.com/form', '送信日時': '2026-09-20 10:00'},
            {'状態': '送信済', '送り先URL': 'https://old.jp/form', '送信日時': '2026-08-01 10:00'},
            {'状態': '見送り', '送り先URL': 'https://skip.jp/form', '送信日時': '2026-10-07 10:00'}]
    assert recently_sent(rows, 'https://www.example.com/contact', now)
    assert not recently_sent(rows, 'https://old.jp/contact', now)
    assert not recently_sent(rows, 'https://skip.jp/contact', now)


def test_in_send_hours():
    assert in_send_hours(datetime(2026, 10, 8, 10, 0, tzinfo=JST))       # 木 10時
    assert not in_send_hours(datetime(2026, 10, 8, 17, 0, tzinfo=JST))   # 17時は外
    assert not in_send_hours(datetime(2026, 10, 10, 11, 0, tzinfo=JST))  # 土曜


def _page(p):
    try:
        b = p.chromium.launch()
    except Exception as e:
        pytest.skip(f'ブラウザを起動できない: {e}')
    return b, b.new_page()


def test_auto_rules_on_local_forms(tmp_path):
    pw = pytest.importorskip('playwright.sync_api')
    sender = {'name': '山田 太郎', 'company': '株式会社サンプル', 'email': 'taro@example.com', 'phone': '03-0000-0000'}
    thanks = tmp_path / 'thanks.html'
    thanks.write_text('<p>お問い合わせありがとうございました。送信が完了しました。</p>', encoding='utf-8')
    confirm = tmp_path / 'confirm.html'
    confirm.write_text(f'<form action="{thanks.as_uri()}"><p>確認画面</p><button type="submit">この内容で送信する</button></form>', encoding='utf-8')
    ok_form = tmp_path / 'ok.html'
    ok_form.write_text(f'''<form action="{confirm.as_uri()}">
<label>お名前<input name="n" required></label><label>メール<input type="email" name="m" required></label>
<select name="kind" required><option value="">選択</option><option value="a">採用</option><option value="z">その他</option></select>
<textarea name="b" required></textarea><label><input type="checkbox" name="ag" required>個人情報の取り扱いに同意する</label>
<button type="submit">確認</button></form>''', encoding='utf-8')
    cap_form = tmp_path / 'cap.html'
    cap_form.write_text('<form><textarea name="b"></textarea><div class="g-recaptcha"></div><button>送信</button></form>', encoding='utf-8')
    with pw.sync_playwright() as p:
        b, page = _page(p)
        page.goto(cap_form.as_uri())
        assert has_captcha(page)
        page.goto(ok_form.as_uri())
        assert not has_captcha(page)
        done = fill_form(page, values(sender, {'件名': '', '本文': 'ご案内です'}))
        assert 'body' in done
        ok, empty = prepare_extras(page)
        assert ok, empty
        assert page.eval_on_selector('select', 'e => e.value') == 'z'
        assert auto_submit(page, tmp_path / 'shot.png')
        assert (tmp_path / 'shot.png').exists()
        b.close()
