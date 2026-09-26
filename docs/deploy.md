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
- [ ] 取次の根拠になる情報（契約先の電力会社など事業者名、登録・届出番号）
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
| Production branch | `main`（まだ main に取り込んでいない場合は `claude/lp-denki-tetsuzuki-hs6x21`） |
| Framework preset | None |
| Build command | （空欄） |
| Build output directory | `lp` |

4. 数十秒で `https://（プロジェクト名）.pages.dev` に公開されます。ここで表示を確認してください。

> 以後、GitHub の本番ブランチに変更をプッシュすると自動で再公開されます。問題があれば、Pages の **Deployments** から1クリックで前の状態に戻せます。

## 4. 独自ドメインをつなぐ

1. Pages のプロジェクト → **Custom domains → Set up a custom domain**
2. 購入したドメイン（例 `denki-kaitsu.com`）を入力 → Activate
3. `www.denki-kaitsu.com` も同様に追加（どちらでも開けるように）
4. 数分〜数十分で `https://` 付きで開けるようになります（証明書は自動）

## 5. ドメインをLPに反映する

リポジトリで次を実行してコミット・プッシュします（Claude に「ドメインは○○.comに決まった」と伝えてもらえれば、こちらで行います）。

```
python3 scripts/set_domain.py denki-kaitsu.com
```

canonical・OGP・robots.txt・sitemap.xml の `example.com` が置き換わります。

## 6. フォームの受信を設定する（Google スプレッドシート＋メール通知）

1. Google ドライブで新しいスプレッドシートを作成（名前例：でんき開通サポート 申込一覧）
2. **拡張機能 → Apps Script** を開き、`gas/form-receiver.gs` の中身を貼り付ける
3. 11行目の `NOTIFY_TO` を通知先メールアドレスに変更して保存
4. **デプロイ → 新しいデプロイ → 種類：ウェブアプリ**
   - 実行ユーザー：自分
   - アクセスできるユーザー：全員
5. 承認画面で許可 → 表示された「ウェブアプリのURL」（`https://script.google.com/macros/s/…/exec`）をコピー
6. `lp/assets/js/config.js` の `formEndpoint` に貼り付ける

> スプレッドシートには申込者の個人情報が入ります。共有範囲は必要な担当者だけにしてください。

## 7. 設定ファイルを本番の値にする（`lp/assets/js/config.js`）

| 項目 | 入れるもの |
|---|---|
| `tel.default` / `tel.yakan` | 実際のフリーダイヤル（表示用とハイフンなし）、受付時間の表記 |
| `businessHours` | 通常番号の受付時間（「ただいま受付中」の表示に使う） |
| `brand.license` | 取次先の事業者名・登録/届出番号（運営会社ページに表示） |
| `formEndpoint` | 手順6のURL |
| `gtmId` | 手順8のGTMのID（例 `GTM-ABC1234`） |

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

## 9. 公開前の最終チェック

スマホ実機（iPhone・Android）とPCで確認します。

- [ ] `https://ドメイン/` を開くと `/tokyo/` に移動する
- [ ] 開いて約1秒でポップアップが出る／「×」で閉じる／再読み込みで再表示されない
- [ ] 電話ボタン（ヘッダー・申込ボタン・下部固定・ポップアップ・相談バナー）で発信画面が開き、正しい番号が入っている
- [ ] 受付時間内・外で「ただいま受付中」の表示が切り替わる
- [ ] フォームを送信 → 完了ページに移動 → スプレッドシートに1行追加 → 通知メールが届く
- [ ] `?utm_source=test&gclid=TEST&ttclid=TEST` 付きで申込 → スプレッドシートに値が入る
- [ ] `?tel=yakan` で夜間番号、`?callhide` で電話ボタン非表示、`?hidemodal=1` でポップアップ非表示
- [ ] GTM のプレビューで `tel_click` / `generate_lead` / `popup_open` が発火する
- [ ] フッターの「運営会社」「プライバシーポリシー」が開く／存在しないURLで404ページが出る
- [ ] 「取次先・登録」欄が「★要変更」のままになっていない
- [ ] プライバシーポリシーを専門家に確認してもらった

## 10. 広告を出すとき

- 広告のリンク先URL・表示URLは、手順4で設定したドメインにする
- 表示名・広告文に「東京電力」「公式」など、公式窓口と誤認させる語を入れない（`docs/lp.md` の表示ルール）
- TikTok は `marketing/tiktok/README.md` の入稿設定を参照

## 運用中の変更

文言・電話番号・受付時間などの変更は、Claude に依頼するか `lp/` 内のファイルを編集して本番ブランチにプッシュすれば、1分ほどで自動反映されます。
