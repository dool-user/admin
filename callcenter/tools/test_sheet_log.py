import json

import sheet_log


def test_row_to_record_maps_outbox_columns():
    r = {'ID': 'S1', '店名': 'さくら歯科', '区分': '医療', '状態': '送信済', '本文': '長い本文', 'AP': 'ユイ'}
    rec = sheet_log.row_to_record(r)
    assert rec['名称'] == 'さくら歯科' and rec['区分'] == '医療' and rec['状態'] == '送信済'
    assert '本文' not in rec and 'AP' not in rec  # 本文はシートに送らない


def test_log_without_webhook_does_nothing(tmp_path):
    pend = tmp_path / 'p.jsonl'
    assert sheet_log.log({}, {'ID': 'S1'}, pend, post=lambda *a: 1 / 0) is False
    assert not pend.exists()


def test_log_keeps_failed_and_flushes_later(tmp_path):
    pend = tmp_path / 'p.jsonl'
    sender = {'sheet_webhook': 'https://example.invalid/exec', 'sheet_token': 't'}
    sent = []

    def down(url, payload):
        raise OSError('offline')

    assert sheet_log.log(sender, {'ID': 'S1'}, pend, post=down) is False
    assert sheet_log.log(sender, {'ID': 'S2'}, pend, post=lambda u, p: {'ok': False, 'error': 'bad token'}) is False
    assert [json.loads(l)['ID'] for l in pend.read_text(encoding='utf-8').splitlines()] == ['S1', 'S2']

    def up(url, payload):
        sent.append(payload)
        return {'ok': True}

    assert sheet_log.log(sender, {'ID': 'S3'}, pend, post=up) is True
    assert [p['ID'] for p in sent] == ['S1', 'S2', 'S3']  # 残っていた分を先に送る
    assert all(p['token'] == 't' for p in sent)
    assert not pend.exists()
