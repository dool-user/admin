# 店舗リスト抽出（Uber Eats 未掲載の飲食店）

Googleマップ・食べログから飲食店を抽出し、**Uber Eats に載っていない店だけ**を CSV（とスプレッドシート）に出力します。

| 機能 | 内容 |
|---|---|
| 条件を指定して抽出（画面） | 抽出元（Googleマップ／食べログ／どちらも）、都道府県→市区町村のプルダウン、業種（大区分・小区分）、電話番号（指定なし／あり／なし）を選んで抽出 |
| 食べログ 新規開店リスト | 食べログの「ニューオープン順」から**前回以降に出た新しい店だけ**を毎日 7:00（日本時間）に抽出 |
| Uber Eats 確認 | 抽出した全店舗を Uber Eats（https://www.ubereats.com/jp/near-me を起点）で検索し、見つからない店だけを残す |

## 仕組み

1. **食べログ**：一覧ページ（例 `https://tabelog.com/tokyo/C13104/rstLst/ramen/`）→ 各店舗ページから店名・ジャンル・住所・電話番号・緯度経度・オープン日を取得（2秒間隔）
2. **Googleマップ**：公式の Google Places API（Text Search）で「業種 ＋ 市区町村」を検索（1検索最大60件）
3. 両方で見つかった店は1行にまとめます（電話番号が同じ、または同じ市区町村で店名が一致）→ 取得元が「両方」
4. **Uber Eats**：ブラウザ（Playwright）で、店の住所を配達先にして店名を検索し、判定を「Uber Eats」列に入れます

| 判定 | 意味 | 出力 |
|---|---|---|
| 未掲載 | 検索結果に同じ店名がない | ○ |
| 掲載あり | 同じ店名（支店違いの同じチェーンを含む）があった | ×（「掲載ありの店も表示する」をオンにすると出力） |
| 要確認 | 位置情報がない、画面を読み取れなかった等 | ○（手で確認してください） |

## セットアップ（初回のみ）

Python 3.11 以上が必要です。

```bash
cd leadgen
python -m venv .venv
# Windows: .venv\Scripts\activate ／ Mac: source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
```

Googleマップも使う場合は API キーを設定します（食べログだけなら不要）。

1. Google Cloud コンソールでプロジェクトを作り、課金を有効化
2. 「Places API (New)」を有効化 → 認証情報 → API キーを作成（キーの制限で Places API (New) のみに絞る）
3. 環境変数に設定
   - Mac：`export GOOGLE_MAPS_API_KEY=取得したキー`
   - Windows（PowerShell）：`$env:GOOGLE_MAPS_API_KEY="取得したキー"`

電話番号を取得するため、料金区分は **Text Search Enterprise** になります（単価・無料枠は [公式の料金表](https://developers.google.com/maps/billing-and-pricing/pricing) を確認してください）。

## 使い方

### 画面から（おすすめ）

```bash
cd leadgen
streamlit run app.py
```

ブラウザで http://localhost:8501 が開きます。条件を選んで「抽出する」→ 表で確認 →「CSV をダウンロード」。
CSV は `output/` にも保存されます（Excel でそのまま開けます）。

### コマンドから

```bash
# 新宿区のラーメン店（食べログ＋Googleマップ、電話番号ありのみ）
python -m leadgen search --source both --pref 東京都 --city 新宿区 --large ラーメン・麺類 --small ラーメン --phone yes

# 食べログだけ・横浜市全体・和食すべて・Uber Eats 確認なし
python -m leadgen search --source tabelog --pref 神奈川県 --city 横浜市 --large 和食 --no-uber

python -m leadgen genres            # 業種の一覧
python -m leadgen areas --pref 東京都 # 市区町村の一覧
python -m leadgen daily             # 新規開店リストを今すぐ作る
```

## 毎日 7:00 の新規開店リスト

対象エリア・業種・電話番号の条件は [`config/daily.yaml`](config/daily.yaml) で変えられます（初期値：東京・神奈川・埼玉・千葉の全業種）。

### A. GitHub Actions で自動実行（PC を起動しておく必要なし）

[`.github/workflows/leadgen-tabelog-daily.yml`](../.github/workflows/leadgen-tabelog-daily.yml) が毎日 UTC 22:00（＝日本時間 7:00）に動きます。

- 結果の CSV：GitHub の **Actions → leadgen-tabelog-daily → 各実行の Artifacts**（30日保存）
- スプレッドシートにも自動で追記する場合：
  1. [`gas/leadgen-receiver.gs`](../gas/leadgen-receiver.gs) の冒頭の手順でウェブアプリを公開
  2. GitHub の **Settings → Secrets and variables → Actions → New repository secret** に
     `LEADGEN_WEBHOOK_URL` ＝ `ウェブアプリのURL?token=合言葉` を登録
- 手動実行：Actions 画面の「Run workflow」
- 注意：GitHub の定期実行は混雑時に数分〜数十分遅れることがあります。また、この workflow はデフォルトブランチにマージされてから動き始めます

### B. 自分の PC で実行（GitHub のサーバーが食べログ／Uber Eats にブロックされる場合）

- Mac / Linux（cron）：`crontab -e` に
  `0 7 * * * cd /path/to/admin/leadgen && .venv/bin/python -m leadgen daily >> output/daily.log 2>&1`
- Windows（タスク スケジューラ）：「基本タスクの作成」→ 毎日 7:00 →
  プログラム `C:\path\to\admin\leadgen\.venv\Scripts\python.exe`、引数 `-m leadgen daily`、開始 `C:\path\to\admin\leadgen`

取得済みの店は `state/tabelog_seen.json` に記録され、翌日以降は新しく出た店だけが出力されます（初回は一覧に出ている分をまとめて取得）。

## 注意事項

- **利用規約**：食べログ・Uber Eats は、サイトの自動取得（スクレイピング）を利用規約で制限している可能性があります。運用前に各サービスの規約を確認し、アクセス間隔（`tabelog_delay`）を短くしすぎないでください。Googleマップは規約に沿うため公式 API を使っています（Googleマップの画面の「オンライン注文」欄は API で取れないため、Uber Eats 側を直接検索して判定しています）
- **画面構成の変更**：食べログ・Uber Eats のページ構成が変わると取得できなくなります。その場合の確認方法：
  - 業種マスタの食べログURL：`python -m leadgen check-genres`（`NG` の行を `leadgen/data/genres.yaml` で修正）
  - Uber Eats：`python -m leadgen check-uber --name 店名 --address 住所 --lat 緯度 --lng 経度 --headed` で実際の画面を表示。「要確認」の画面は `output/screenshots/` に保存されます
- **判定の限界**：店名の表記が Uber Eats と大きく違う店は「未掲載」と判定されることがあります。架電前に上位の店だけでも目視確認をおすすめします
- **食べログの電話番号**は「予約専用番号（050〜）」の場合があります

## データの出典

- 都道府県・市区町村：総務省「全国地方公共団体コード」（令和6年1月1日現在）https://www.soumu.go.jp/denshijiti/code.html
  （作り直し：`scripts/build_areas.py`）

## ファイル構成

| パス | 役割 |
|---|---|
| `app.py` | 画面（Streamlit） |
| `leadgen/tabelog.py` | 食べログの一覧・店舗ページの取得と解析 |
| `leadgen/google_places.py` | Google Places API |
| `leadgen/ubereats.py` | Uber Eats の掲載確認（Playwright） |
| `leadgen/matching.py` | 店名の表記ゆれ吸収・同一店判定 |
| `leadgen/pipeline.py` | 抽出条件 → 取得 → 絞り込み → 統合 → CSV |
| `leadgen/daily.py` | 新規開店リスト（毎日） |
| `leadgen/data/areas.json`・`genres.yaml` | 地域・業種マスタ |
| `config/daily.yaml` | 毎日の実行条件 |
| `tests/` | テスト（`python -m pytest tests`） |
