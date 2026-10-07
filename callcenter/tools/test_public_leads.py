import public_leads as pl


def test_import_medical_rows_skips_no_url_dupes_and_other_prefs():
    header = ['ID', '正式名称', '都道府県名', '所在地', '院長氏名', '案内用ホームページアドレス']
    rows = [
        ['1', 'さくら歯科', '東京都', '新宿区1-1', '山田', 'www.sakura-dental.jp'],
        ['2', 'URLなし医院', '東京都', '新宿区2-2', '佐藤', ''],
        ['3', 'もみじクリニック', '大阪府', '大阪市北区3-3', '鈴木', 'https://momiji.example.jp/'],
        ['4', 'さくら歯科 分院', '東京都', '渋谷区4-4', '田中', 'https://www.sakura-dental.jp/bun/'],
        ['5', 'すでにある医院', '東京都', '港区5-5', '', 'https://known.example.jp'],
    ]
    leads = [{'店名': 'x', '公式サイト': 'https://known.example.jp/'}]
    out = pl.import_rows(header, rows, '医療', '歯科', '医療情報ネット', prefs=['東京都'], leads=leads, today='2026-10-07')
    assert [r['店名'] for r in out] == ['さくら歯科']
    r = out[0]
    assert r['公式サイト'] == 'http://www.sakura-dental.jp' and r['住所'] == '東京都新宿区1-1'
    assert r['リストの出典'] == '医療情報ネット' and r['区分'] == '医療'
    assert '山田' not in r.values()  # 氏名は取り込まない


def test_houjin_rows_filters_by_name_and_closed():
    row = lambda no, name, pref, proc='01': ['1', no, proc, '0', '', '', name, '', '301', pref, '千代田区', '1-1']  # noqa: E731
    rows = [row('111', '税理士法人みらい', '東京都'), row('222', '株式会社みらい', '東京都'),
            row('333', '行政書士法人あおば', '東京都', '71'), row('444', '司法書士法人ひかり', '大阪府')]
    out = pl.houjin_rows(rows, '士業', '法人番号', prefs=['東京都'])
    assert [r['法人番号'] for r in out] == ['111'] and out[0]['住所'] == '東京都千代田区1-1'


def test_norm_url():
    assert pl.norm_url('example.jp') == 'http://example.jp'
    assert pl.norm_url('なし') == '' and pl.norm_url('') == ''
