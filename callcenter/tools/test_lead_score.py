import csv

import lead_score as ls


def test_score_prefers_active_seikotsu_over_bare_shop():
    a = {'店名': '○○整骨院', '業種': '整骨院', '公式サイト': 'https://a.jp', 'Instagram': 'https://www.instagram.com/a/',
         'Google口コミ数': '45', 'GBPの様子': '写真を少し上げて止まっている'}
    b = {'店名': '△△食堂', '業種': '食堂', 'Google口コミ数': '3'}
    pa, wa = ls.score(a)
    pb, _ = ls.score(b)
    assert pa > pb
    assert '整骨院系（高単価になりやすい）' in wa and any('Instagram' in w for w in wa) and any('止まっている' in w for w in wa)


def test_name_stuffing_and_lunch_dinner():
    p, why = ls.score({'店名': 'まつエク Lumi【渋谷駅】', '業種': 'まつげエクステ', '昼夜営業': 'あり'})
    assert any('店名' in w for w in why) and 'ランチ＋ディナー' in why


def test_medical_hides_review_reason():
    _, why = ls.score({'店名': 'さくら歯科', '区分': '医療', '業種': '歯科', 'Google口コミ数': '50'})
    assert not any(w.startswith('口コミ') for w in why)


def test_main_sorts_with_inquiries_first(tmp_path):
    p = tmp_path / 'leads.csv'
    with p.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['店名', '業種', '反響'])
        w.writeheader()
        w.writerows([{'店名': '食堂', '業種': '食堂', '反響': '0'}, {'店名': '整骨院', '業種': '整骨院', '反響': '0'},
                     {'店名': '反響の店', '業種': '', '反響': '1'}])
    ls.main(p)
    rows = list(csv.DictReader(p.open(encoding='utf-8-sig')))
    assert [r['店名'] for r in rows] == ['反響の店', '整骨院', '食堂'] and rows[1]['優先度']
