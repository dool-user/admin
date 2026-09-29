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
