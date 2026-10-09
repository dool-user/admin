import toss


def test_toss_text_follows_format_and_fills_blanks():
    t = toss.toss_text({'店舗名': '○○整骨院', '提案商材': 'MEO対策ツール', '商談日': '10/15', '商談時間': '14:00'})
    lines = t.split('\n')
    assert lines[0] == '【アポ登録】'
    assert lines[1:3] == ['▼店舗名', '○○整骨院']
    assert [l for l in lines if l.startswith('▼')] == ['▼' + k for k in toss.TOSS_FIELDS]
    assert lines[lines.index('▼料金提示') + 1] == '—'


def test_example_csv_has_all_toss_fields():
    head = toss.EXAMPLE.read_text(encoding='utf-8-sig').strip().split(',')
    assert all(k in head for k in toss.TOSS_FIELDS) and 'ID' in head
