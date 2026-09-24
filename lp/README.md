# 電気開通手続き LP（でんき開通サポート）

引越し時の電気・ガス・水道・ネットの開通手続き代行サービスのLPです。
HTML・CSS・JSだけで動く静的サイトなので、どのサーバーにもそのまま置けます（WordPressテーマへの組み込みも可）。

## ファイル構成

```
lp/
├── index.html            … /tokyo/ へリダイレクト
├── tokyo/index.html      … 東京エリアLP（本体）
├── thanks.html           … 申込完了ページ（CV計測用）
├── privacy.html          … プライバシーポリシー（ひな形）
├── assets/css/style.css
├── assets/js/config.js   … ★電話番号・社名・フォーム送信先・エリアはここで管理
├── assets/js/main.js
└── gas/form-receiver.gs  … フォーム受信用（スプレッドシート保存＋メール通知）
```

## 公開前にやること

1. `assets/js/config.js` の「★要変更」をすべて差し替える（社名、電話番号＝通常／夜間、登録番号）
2. `tokyo/index.html` の `canonical`・`og:url`（example.com）を本番URLに変える
3. `gas/form-receiver.gs` をデプロイし、発行されたURLを `formEndpoint` に設定する
   （空欄のままだとデモモードになり、送信しても thanks.html に移動するだけ）
4. GTMのコメントアウトを外し、`GTM-XXXXXXX` を差し替える（`tokyo/index.html` と `thanks.html` の両方）
5. 「最短当日」「無料」などの表記が実際の運用と一致しているか確認する（景品表示法）。実際のお客様の声を載せる場合は、掲載許諾を取った本物の声だけを使う
6. `privacy.html` を自社の内容に合わせて修正し、専門家に確認してもらう

## 表示ルール（誤認防止・必ず守ること）

電力会社の公式窓口と誤認させる表示は、不正競争防止法（混同させる表示）、景品表示法・特定商取引法（事業者を誤認させる表示や勧誘）の問題になり、Google広告の審査でも停止の対象になります。改修や広告文の作成時は次を守ってください。

- 東京電力など実在する会社のロゴ、ロゴに似たマーク、ブランドカラー、キャッチコピーを使わない
- 会社名は「東京電力パワーグリッドのエリアの物件に対応」のような**事実の説明**としてだけ、普通の文字で書く
- 「東京電力の窓口」「公式」「東京電力から案内」など、提携・公式と受け取れる言い回しを使わない（広告文・電話の案内も同じ）
- よくある質問の「ここは東京電力の窓口ですか？」と、フッターの「各社の公式窓口ではありません」の注記は削除しない（ファーストビューの注記は運営判断で削除済み。誤認の申し出や広告審査で指摘があれば、ファーストビューに戻すことを検討する）
- 電話で特定の事業者のプランを勧めるときは、契約前に事業者名・料金・契約条件を伝える
- フッターの「取次先・登録」欄に、取次の根拠（契約先事業者名、登録・届出番号など）を正確に書く

## URLパラメータ（広告URLで表示を切り替え）

| パラメータ | 動作 |
|---|---|
| `tel=yakan` | 夜間用の電話番号・受付時間表示に切り替える（セッション中は保持） |
| `callhide` | 電話ボタンをすべて隠し、Web申込のみにする |
| `mvhide` | メインビジュアルを隠し、CTAから表示する |
| `hidemodal=1` | 離脱防止モーダルを出さない |
| `ctaorder=form` / `ctaorder=tel` | CTAボタンの並び順（未指定の場合、受付時間外は自動でフォームが先） |
| `utm_*` / `gclid` / `gbraid` / `wbraid` | フォームの hidden 項目に自動で入り、申込データと紐づく |

値の扱い：`callhide` のように値なしで付けると ON、`hidemodal=` のように空の値だと OFF、`0` / `false` も OFF。
広告テンプレートに空欄で入っているパラメータは、動作を変えません。

例）`/tokyo/?tel=yakan&callhide&mvhide&hidemodal=&ctaorder=&utm_source=google&utm_medium=cpc`

## エリア展開（例：神奈川）

1. `tokyo/` フォルダを `kanagawa/` として複製する
2. `kanagawa/index.html` の `<body data-area="tokyo">` を `kanagawa` に変え、title・description・FAQの文言を直す
3. `config.js` の `areas` に `kanagawa: { name, short, utility, cities }` を追加する

## 計測イベント（GTM dataLayer）

| event | タイミング |
|---|---|
| `tel_click` | 電話ボタンのタップ（`cta_id` で設置位置を識別） |
| `cta_click` | Web申込ボタンのクリック |
| `form_start` | フォームへの入力開始 |
| `generate_lead` | フォーム送信成功 |
| `thanks_view` | 完了ページの表示 |
| `modal_open` | 離脱防止モーダルの表示 |

Google広告のコンバージョンは `tel_click` と `generate_lead`（または `thanks_view`）に設定してください。
