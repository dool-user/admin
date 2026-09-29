"""店舗リスト抽出（画面）

起動：  streamlit run app.py
"""
import io
from pathlib import Path

import pandas as pd
import streamlit as st

from leadgen import master
from leadgen.models import COLUMNS, now_jst, to_row
from leadgen.pipeline import PHONES, SOURCES, Criteria, run, write_csv

ROOT = Path(__file__).resolve().parent
ALL = '（すべて）'

st.set_page_config(page_title='店舗リスト抽出', page_icon='🍜', layout='wide')
st.title('店舗リスト抽出（Uber Eats 未掲載）')

tab_search, tab_daily = st.tabs(['条件を指定して抽出', '食べログ 新規開店（毎日7時）'])

with tab_search:
    c1, c2, c3 = st.columns(3)
    with c1:
        source = st.radio('抽出元', list(SOURCES), format_func=SOURCES.get, index=2, horizontal=True)
        pref_names = [p['name'] for p in master.prefectures()]
        pref_name = st.selectbox('都道府県', pref_names, index=pref_names.index('東京都'))
        pref = master.prefecture(pref_name)
        city_name = st.selectbox('市区町村', [ALL] + [c['name'] for c in pref['cities']])
    with c2:
        large = st.selectbox('業種（大区分）', [ALL] + list(master.genres()))
        smalls = [g['name'] for g in master.genres()[large]] if large != ALL else []
        small = st.selectbox('業種（小区分）', [ALL] + smalls, disabled=large == ALL)
        phone = st.radio('電話番号', list(PHONES), format_func=PHONES.get, horizontal=True)
    with c3:
        limit = st.number_input('取得元ごとの最大件数', 10, 1000, 100, step=10)
        check = st.checkbox('Uber Eats で掲載の有無を確認する', value=True)
        include_found = st.checkbox('Uber Eats 掲載ありの店も表示する', value=False)
        headed = st.checkbox('確認中のブラウザを表示する（動作確認用）', value=False)
        contacts = st.checkbox('問い合わせフォーム・Instagram を探す（DM・フォーム営業用）', value=True)

    if source in ('google', 'both'):
        st.caption('Googleマップは Google Places API を使います（環境変数 GOOGLE_MAPS_API_KEY が必要・従量課金）。')
    st.caption('食べログは1件ごとに2秒ほど間隔を空けて取得するため、100件で数分かかります。')

    if st.button('抽出する', type='primary'):
        crit = Criteria(
            source=source, prefecture=pref_name, city=None if city_name == ALL else city_name,
            genre_large=None if large == ALL else large, genre_small=None if small == ALL else small,
            phone=phone, limit=int(limit), check_uber=check, include_found=include_found, uber_headed=headed, find_contacts=contacts,
            screenshot_dir=str(ROOT / 'output' / 'screenshots'),
        )
        logs = []
        box = st.empty()

        def log(msg):
            logs.append(msg)
            box.code('\n'.join(logs[-15:]))

        try:
            with st.spinner('抽出中…'):
                shops = run(crit, log=log)
        except Exception as e:  # noqa: BLE001 - 画面にエラーを出す
            st.error(f'エラー: {e}')
            shops = None
        if shops is not None:
            out = write_csv(shops, ROOT / 'output' / f'list_{now_jst():%Y%m%d_%H%M}.csv')
            st.session_state['result'] = (shops, out)

    if 'result' in st.session_state:
        shops, out = st.session_state['result']
        st.success(f'{len(shops)}件（保存先: {out}）')
        df = pd.DataFrame([to_row(s) for s in shops], columns=[label for label, _ in COLUMNS])
        st.dataframe(df, use_container_width=True, hide_index=True,
                     column_config={'URL': st.column_config.LinkColumn(), 'URL（もう一方）': st.column_config.LinkColumn()})
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        st.download_button('CSV をダウンロード', buf.getvalue().encode('utf-8-sig'), file_name=out.name, mime='text/csv')

with tab_daily:
    st.write('毎日7時（日本時間）に GitHub Actions で自動実行され、結果は CSV とスプレッドシートに保存されます。'
             '対象エリア・業種は `config/daily.yaml` で変更できます。ここから手動で実行することもできます。')
    files = sorted((ROOT / 'output').glob('tabelog_new_*.csv'), reverse=True)
    if files:
        pick = st.selectbox('これまでの結果', files, format_func=lambda p: p.name)
        df = pd.read_csv(pick, encoding='utf-8-sig', dtype=str).fillna('')
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button('この CSV をダウンロード', pick.read_bytes(), file_name=pick.name, mime='text/csv')
    else:
        st.info('まだ結果がありません。')
    if st.button('今すぐ実行する'):
        from leadgen.daily import run_daily
        logs = []
        box = st.empty()

        def log(msg):
            logs.append(msg)
            box.code('\n'.join(logs[-15:]))

        try:
            shops, out = run_daily(ROOT / 'config' / 'daily.yaml', log=log)
            st.success(f'{len(shops)}件 → {out}')
        except Exception as e:  # noqa: BLE001
            st.error(f'エラー: {e}')
