# 公開手順書（Cloudflare Pages ＋ .com ドメイン）

このLPを本番公開して運用するまでの手順です。Cloudflare・Google の管理画面での操作とドメインの購入は、アカウントの持ち主（あなた）が行います。リポジトリ側の準備は完了しています。

**公開されるのは `lp/` フォルダの中身だけです。** 動画・台本（`marketing/`）、フォーム受信スクリプト（`gas/`）、この手順書（`docs/`）は公開されません。

## 費用の目安

| 項目 | 費用 |
|---|---|
| Cloudflare Pages（ホスティング） | 無料 |
| .com ドメイン（Cloudflare で購入） | 年 約1,600〜2,000円（原価販売・更新時も同額。WHOIS情報の非公開は無料） |
| Google Apps Script（フォーム受信）・Google タグマネージャー | 無料 |
| フリーダイヤル回線 | 別途（ご契約中の電話会社） |

## 事前に用意するもの

- [ ] フリーダイヤル番号（通常用・夜間用。夜間を分けない場合は1本）
- [ ] 申込通知を受け取るメールアドレス
- [ ] Google アカウント（フォーム受信・GTM用）
- [ ] ドメイン代を払うクレジットカード

---

## 1. Cloudflare アカウントを作る

1. https://dash.cloudflare.com/sign-up でアカウントを作成（メール認証まで）
2. 2段階認証をオンにする（右上のアカウント → My Profile → Authentication）

## 2. ドメインを購入する（Cloudflare Registrar）

1. ダッシュボード左メニュー **Domain Registration → Register Domains**
2. 希望のドメイン名を検索して、空いていれば購入
   - 候補例：`denki-kaitsu.com` / `denki-kaitsu-support.com` / `kaitsu-support.com` / `denki-hikkoshi.com`
   - **「tepco」「tokyo-denryoku」など電力会社の名前や、それを連想させる語は入れない**（誤認・商標トラブル防止）
3. 登録者情報を入力（WHOIS上は自動で非公開）

## 3. Cloudflare Pages でサイトを公開する

1. 左メニュー **Workers & Pages → Create → Pages → Connect to Git**
2. GitHub を連携し、リポジトリ **`dool-user/admin`** を選ぶ
3. 設定を次のとおり入力して **Save and Deploy**

| 項目 | 設定値 |
|---|---|
| Production branch | `main` |
| Framework preset | None |
| Build command | （空欄） |
| Build output directory | `lp` |

4. 数十秒で `https://（プロジェクト名）.pages.dev` に公開されます。ここで表示を確認してください。

> 以後、GitHub の本番ブランチに変更をプッシュすると自動で再公開されます。問題があれば、Pages の **Deployments** から1クリックで前の状態に戻せます。

## 4. 独自ドメインをつなぐ

1. Pages のプロジェクト → **Custom domains → Set up a custom domain**
2. 購入したドメイン（例 `denki-kaitsu-support.com`）を入力 → Activate
3. `www.denki-kaitsu.com` も同様に追加（どちらでも開けるように）
4. 数分〜数十分で `https://` 付きで開けるようになります（証明書は自動）

## 5. ドメインをLPに反映する

リポジトリで次を実行してコミット・プッシュします（Claude に「ドメインは○○.comに決まった」と伝えてもらえれば、こちらで行います）。

```
python3 scripts/set_domain.py denki-kaitsu.com
```

canonical・OGP・robots.txt・sitemap.xml の `example.com` が置き換わります。

## 6. フォームの受信を設定する（Google スプレッドシート＋メール・Slack 通知）

1. 保存先のスプレッドシート（設定済み：https://docs.google.com/spreadsheets/d/1MMPZ61RnZl-YzGezagqpquMz_jqVpj-hZSnM7SzDr6E/edit）を開く。申込は「申込一覧」シートに自動で追加されます
2. **拡張機能 → Apps Script** を開き、`gas/form-receiver.gs` の中身を貼り付ける
3. `NOTIFY_TO` を通知先メールアドレスに変更して保存
4. Slack に通知する（任意）
   1. Slack で通知用チャンネルを作る（例 `#lp-申込`。申込者の電話番号が流れるので、**担当者だけの非公開チャンネル**にする）
   2. https://api.slack.com/apps → **Create New App → From scratch** → ワークスペースを選ぶ
   3. **Incoming Webhooks** をオン → **Add New Webhook to Workspace** → 手順1のチャンネルを選ぶ → 表示された URL（`https://hooks.slack.com/services/…`）をコピー
   4. Apps Script の **プロジェクトの設定（歯車）→ スクリプト プロパティを追加**：プロパティ `SLACK_WEBHOOK_URL`、値に手順3の URL
      - Webhook URL を知っていれば誰でもそのチャンネルに投稿できるため、コードやチャットには貼らない
   5. エディタ上部の関数選択で `testNotify` を選んで **実行** → 承認 → Slack とメールにテスト通知が届けばOK
   - Slack には「お名前・電話番号・エリア・建物・開始希望日・申込内容・連絡希望時間・流入元」と、スプレッドシートの該当行を開くボタンが届きます。メールアドレス・住所・備考はスプレッドシートで確認します。
5. **デプロイ → 新しいデプロイ → 種類：ウェブアプリ**
   - 実行ユーザー：自分
   - アクセスできるユーザー：全員
6. 承認画面で許可 → 表示された「ウェブアプリのURL」（`https://script.google.com/macros/s/…/exec`）をコピー
7. `lp/assets/js/config.js` の `formEndpoint` に貼り付ける

> コードを貼り替えたあとは **デプロイ → デプロイを管理 → 編集（鉛筆）→ バージョン：新バージョン → デプロイ** で更新します（URL は変わりません）。

**スプレッドシートをチームに共有する**：スプレッドシート右上の **共有** → 担当者の Google アカウント（Gmail など）を追加 → 対応状況を書き込む人は「編集者」、見るだけの人は「閲覧者」にします。「リンクを知っている全員」には**しない**でください。

> スプレッドシートには申込者の個人情報が入ります。共有範囲は必要な担当者だけにしてください。

## 7. 設定ファイルを本番の値にする（`lp/assets/js/config.js`）

| 項目 | 入れるもの |
|---|---|
| `tel.default` / `tel.yakan` | 実際のフリーダイヤル（表示用とハイフンなし）、受付時間の表記 |
| `businessHours` | 通常番号の受付時間（「ただいま受付中」の表示に使う） |
| `formEndpoint` | 手順6のURL |
| `gtmId` | 手順8のGTMのID（例 `GTM-ABC1234`） |
| `metaPixelId` | 手順8-2のMetaピクセルID（数字のみ） |

## 8. 計測を設定する（Google タグマネージャー）

1. https://tagmanager.google.com でコンテナを作成（ウェブ）→ ID（GTM-XXXXXXX）を `gtmId` に入れる
2. GTM に次のタグを作成（トリガーはすべて「カスタムイベント」）

| タグ | トリガー（イベント名） |
|---|---|
| GA4 設定 | すべてのページ |
| Google 広告 コンバージョン（電話） | `tel_click` |
| Google 広告 コンバージョン（Web申込） | `generate_lead` |
| TikTok ピクセル（ページビュー） | すべてのページ |
| TikTok ピクセル（Contact） | `tel_click` |
| TikTok ピクセル（SubmitForm） | `generate_lead` |

3. プレビューで発火を確認してから **公開**

> Meta（Facebook・Instagram）のタグは GTM に**入れない**でください。LP に直接組み込み済みで、二重に計測されてしまいます（次の 8-2）。

## 8-2. Meta 広告の計測を設定する（Facebook・Instagram）

LP 側の仕組みは組み込み済みです。ID とトークンを入れるだけで動きます。

| 計測するもの | Meta のイベント | 送るタイミング |
|---|---|---|
| ページ表示 | `PageView` | 全ページ |
| 電話ボタンのタップ | `Contact` | タップしたとき |
| Web申込 | `Lead` | 完了ページ（ブラウザ）＋ フォーム受信時（サーバー：Conversions API）。同じ `event_id` で重複を除く |

1. **ピクセルを作る**：Meta ビジネスポートフォリオ → **イベントマネージャ** → 「データソースをリンク」→「ウェブ」→ 名前を付けて作成 → 表示された **ピクセルID（数字）** を控える
   - 「設定方法」を聞かれたら「コードを手動でインストール」を選び、そのまま閉じてOK（コードは LP に入っています）
2. `lp/assets/js/config.js` の `metaPixelId` にピクセルIDを入れる（Claude に ID を伝えれば反映します）
3. **ドメイン認証**：ビジネス設定 → ブランドセーフティ → **ドメイン** →「追加」→ `denki-kaitsu-support.com` →「DNS TXT レコード」を選ぶ → 表示された値を Cloudflare の **DNS → レコードを追加**（タイプ TXT、名前 `@`）に貼る → Meta に戻って「認証」
4. **Conversions API のトークンを作る**：イベントマネージャ → 作ったピクセル → **設定** →「コンバージョンAPI」→「アクセストークンを生成」→ 表示された長い文字列をコピー（再表示できないので注意）
5. **Apps Script に登録**（手順6と同じスクリプト）：プロジェクトの設定（歯車）→ スクリプト プロパティを追加
   - `META_PIXEL_ID`：ピクセルID
   - `META_CAPI_TOKEN`：手順4のトークン（秘密情報。コードやチャットには貼らない）
6. **テスト**
   1. イベントマネージャ → ピクセル →「**テストイベント**」タブ → 「サーバーイベントのテスト」に表示される **テストコード**（`TEST12345` のような文字列）を控える
   2. スクリプト プロパティに `META_TEST_EVENT_CODE` としてテストコードを追加
   3. Apps Script のエディタで `testMetaLead` を選んで実行 → テストイベント画面に「Lead（サーバー）」が出ればOK
   4. 同じ画面の「ブラウザイベントのテスト」に LP の URL を入れて開き、電話ボタン・フォーム送信で `Contact` / `Lead` が出ることを確認
   5. 確認が終わったら **`META_TEST_EVENT_CODE` を削除**（残すと本番の申込がテスト扱いになり、広告の最適化に使われない）
7. コードを貼り替えた場合は、Apps Script を「デプロイを管理 → 新バージョン」で更新する
8. 広告を作るときは、キャンペーンの目的「**リード**」→ コンバージョンの場所「ウェブサイト」→ イベント「**リード（Lead）**」を選ぶ

## 9. 公開前の最終チェック

スマホ実機（iPhone・Android）とPCで確認します。

- [ ] `https://ドメイン/` を開くと `/tokyo/` に移動する
- [ ] 開いて約1秒でポップアップが出る／「×」で閉じる／再読み込みで再表示されない
- [ ] 電話ボタン（ヘッダー・申込ボタン・下部固定・ポップアップ・相談バナー）で発信画面が開き、正しい番号が入っている
- [ ] 受付時間内・外で「ただいま受付中」の表示が切り替わる
- [ ] フォームを送信 → 完了ページに移動 → スプレッドシートに1行追加 → 通知メールと Slack 通知が届く
- [ ] `?utm_source=test&gclid=TEST&ttclid=TEST` 付きで申込 → スプレッドシートに値が入る
- [ ] `?tel=yakan` で夜間番号、`?callhide` で電話ボタン非表示、`?hidemodal=1` でポップアップ非表示
- [ ] GTM のプレビューで `tel_click` / `generate_lead` / `popup_open` が発火する
- [ ] Meta のテストイベントで `PageView` / `Contact` / `Lead`（ブラウザ・サーバー両方）が出る。確認後に `META_TEST_EVENT_CODE` を削除した
- [ ] フッターの「運営会社」「プライバシーポリシー」が開く／存在しないURLで404ページが出る
- [ ] プライバシーポリシーを専門家に確認してもらった

## 10. 広告を出すとき

- 広告のリンク先URL・表示URLは、手順4で設定したドメインにする
- 表示名・広告文に「東京電力」「公式」など、公式窓口と誤認させる語を入れない（`docs/lp.md` の表示ルール）
- TikTok は `marketing/tiktok/README.md` の入稿設定を参照

## 運用中の変更

文言・電話番号・受付時間などの変更は、Claude に依頼するか `lp/` 内のファイルを編集して本番ブランチにプッシュすれば、1分ほどで自動反映されます。
