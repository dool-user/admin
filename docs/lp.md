# 電気開通手続き LP（でんき開通サポート）

公開手順は `docs/deploy.md` を参照。公開されるのは `lp/` フォルダの中身だけです。

引越し時の電気・ガス・水道・ネットの開通手続き代行サービスのLPです。
HTML・CSS・JSだけで動く静的サイトなので、どのサーバーにもそのまま置けます（WordPressテーマへの組み込みも可）。

## ファイル構成

```
lp/
├── index.html            … LP本体（関東エリア：東京・神奈川・埼玉・千葉・茨城・群馬・栃木）
├── tokyo/index.html      … 旧URL /tokyo/ からトップへの転送（計測パラメータを引き継ぐ）
├── thanks.html           … 申込完了ページ（CV計測用）
├── privacy.html          … プライバシーポリシー（ひな形）
├── company.html          … 運営会社（フッターの「運営会社」からリンク）
├── assets/css/style.css
├── assets/js/config.js   … ★電話番号・社名・フォーム送信先・エリアはここで管理
├── assets/js/main.js
├── assets/js/meta.js     … Meta ピクセル
├── assets/zip/           … 郵便番号データ（scripts/build_zip.mjs で再生成）
├── _headers              … Cloudflare Pages 用の設定
├── robots.txt / sitemap.xml / 404.html

gas/form-receiver.gs      … フォーム受信用（スプレッドシート保存＋メール・Slack 通知）※公開フォルダの外
scripts/set_domain.py     … 本番ドメインの反映
marketing/tiktok/         … TikTok広告の動画・台本 ※公開フォルダの外
docs/deploy.md            … 公開手順書
```

## 公開前にやること

1. `lp/assets/js/config.js` の「★要変更」をすべて差し替える（電話番号＝通常／夜間。運営会社はグラハムコミュニケーションズ株式会社で設定済み）
2. 本番ドメインを `python3 scripts/set_domain.py ドメイン名` で反映する（canonical・og:url・robots.txt・sitemap.xml）
3. `gas/form-receiver.gs`（リポジトリ直下）をデプロイし、発行されたURLを `formEndpoint` に設定する
   （空欄のままだとデモモードになり、送信しても thanks.html に移動するだけ）
4. `lp/assets/js/config.js` の `gtmId` に Google タグマネージャーのID（GTM-XXXXXXX）を入れる（全ページで自動的に読み込まれる）
5. 「最短当日」「無料」などの表記が実際の運用と一致しているか確認する（景品表示法）。実際のお客様の声を載せる場合は、掲載許諾を取った本物の声だけを使う
6. `lp/privacy.html` を自社の内容に合わせて修正し、専門家に確認してもらう

## 表示ルール（誤認防止・必ず守ること）

電力会社の公式窓口と誤認させる表示は、不正競争防止法（混同させる表示）、景品表示法・特定商取引法（事業者を誤認させる表示や勧誘）の問題になり、Google広告の審査でも停止の対象になります。改修や広告文の作成時は次を守ってください。

- 東京電力など実在する会社のロゴ、ロゴに似たマーク、ブランドカラー、キャッチコピーを使わない
- 会社名は「東京電力パワーグリッドのエリアの物件に対応」のような**事実の説明**としてだけ、普通の文字で書く
- 「東京電力の窓口」「公式」「東京電力から案内」など、提携・公式と受け取れる言い回しを使わない（広告文・電話の案内も同じ）
- ヘッダー直下の運営者表示「このサイトは、〇〇が運営する…電力会社の公式サイトではありません。」、よくある質問の「ここは東京電力の窓口ですか？」、フッターの注記は削除しない
- 電話で特定の事業者のプランを勧めるときは、契約前に事業者名・料金・契約条件を伝える

## URLパラメータ（広告URLで表示を切り替え）

| パラメータ | 動作 |
|---|---|
| `tel=yakan` | 夜間用の電話番号・受付時間表示に切り替える（セッション中は保持） |
| `callhide` | 電話ボタンをすべて隠し、Web申込のみにする |
| `mvhide` | メインビジュアルを隠し、CTAから表示する |
| `hidemodal=1` | ページを開いた直後のポップアップ（アイコンタイル型）を出さない |
| `ctaorder=form` / `ctaorder=tel` | CTAボタンの並び順（未指定の場合、受付時間外は自動でフォームが先） |
| `utm_*` / `gclid` / `gbraid` / `wbraid` | フォームの hidden 項目に自動で入り、申込データと紐づく |

値の扱い：`callhide` のように値なしで付けると ON、`hidemodal=` のように空の値だと OFF、`0` / `false` も OFF。
広告テンプレートに空欄で入っているパラメータは、動作を変えません。

例）`/?tel=yakan&callhide&mvhide&hidemodal=&ctaorder=&utm_source=google&utm_medium=cpc`

## 対応エリアの変更

- 対応する都県は `config.js` の `serviceArea` で管理（ファーストビューと「ご依頼いただける地域」に反映）
- ファーストビューの「〇〇の新居に入居予定の方へ」は `config.js` の `areas.kanto.name`
- title・description・シェア時の表示（og:title）は `index.html` の `<head>` を直接編集
- 申込データの「area」には、入力された住所の都道府県（例：神奈川県）が入る

## 計測イベント（GTM dataLayer）

| event | タイミング |
|---|---|
| `tel_click` | 電話ボタンのタップ（`cta_id` で設置位置を識別） |
| `cta_click` | Web申込ボタンのクリック |
| `form_start` | フォームへの入力開始 |
| `generate_lead` | フォーム送信成功 |
| `thanks_view` | 完了ページの表示 |
| `popup_open` | ページを開いた直後のポップアップの表示（1セッション1回） |
| `popup_tile_select` | ポップアップのタイル選択（`tile` = power / movein / unknown） |

Google広告のコンバージョンは `tel_click` と `generate_lead`（または `thanks_view`）に設定してください。

Meta（Facebook・Instagram）は GTM を使わず、`assets/js/meta.js` で直接計測します（`config.js` の `metaPixelId` で有効化）。
`tel_click` → `Contact`、フォーム送信成功 → 完了ページで `Lead`。`Lead` はフォーム受信側（`gas/form-receiver.gs`）からも Conversions API で送り、フォームに付けた `event_id` で重複を除きます。
広告からの流入は `fbclid` としてスプレッドシートに記録されます。手順は `docs/deploy.md` の 8-2。
