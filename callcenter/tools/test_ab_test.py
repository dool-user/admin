import ab_test as ab


def test_assign_alternates_within_each_kubun_and_skips_filled():
    rows = [{'状態': '下書き', '区分': '店舗'} for _ in range(3)] + [{'状態': '下書き', '区分': '医療'} for _ in range(2)]
    rows.append({'状態': '承認済', '区分': '店舗'})
    assert ab.assign(rows) == 5
    assert [r['文面案'] for r in rows[:5]] == ['A', 'B', 'A', 'A', 'B']
    assert not rows[5].get('文面案')
    rows.append({'状態': '下書き', '区分': '店舗'})
    ab.assign(rows)
    assert rows[-1]['文面案'] == 'B'  # 店舗はすでに A2・B1 なので次は B


def test_tally_counts_sent_reply_and_appt():
    rows = [{'文面案': 'A', '状態': '送信済'}, {'文面案': 'A', '状態': 'アポ', '返信日時': 'x'},
            {'文面案': 'A', '状態': '見送り', '返信日時': 'x'}, {'文面案': 'A', '状態': '承認済'},
            {'文面案': 'B', '状態': '返信あり'}]
    t = ab.tally(rows)
    assert t['A'] == {'送信': 3, '返信': 2, 'アポ': 1} and t['B'] == {'送信': 1, '返信': 1, 'アポ': 0}


def test_judge_waits_for_min_and_detects_clear_difference():
    small = {'A': {'送信': 10, '返信': 5, 'アポ': 0}, 'B': {'送信': 10, '返信': 0, 'アポ': 0}}
    assert ab.judge(small).startswith('途中')
    big = {'A': {'送信': 100, '返信': 20, 'アポ': 5}, 'B': {'送信': 100, '返信': 3, 'アポ': 1}}
    assert ab.judge(big).startswith('A の勝ち')
    same = {'A': {'送信': 100, '返信': 5, 'アポ': 1}, 'B': {'送信': 100, '返信': 4, 'アポ': 1}}
    assert ab.judge(same).startswith('差は言えない')


def test_fisher_p_symmetric_and_bounded():
    p = ab.fisher_p(3, 1, 1, 3)
    assert 0 < p <= 1 and abs(p - ab.fisher_p(1, 3, 3, 1)) < 1e-12
