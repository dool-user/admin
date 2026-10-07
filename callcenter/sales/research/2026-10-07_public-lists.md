# 公開リスト調査：MEO対策ツールの問い合わせフォーム営業（BtoB）向け

- 調査日：2026-10-07
- 対象：医療（クリニック・歯科・病院）／士業（税理士・行政書士・社労士・司法書士）／住まい（不動産・リフォーム）／店舗（飲食・美容・整骨院）、全国
- 目的：「ネットに公開されているリスト」から、HP の問い合わせフォームで案内する送り先リストを作る

## 0. 調べ方と確かさ（最初に読む）

- **この環境では、WebFetch も curl も、官公庁・業界団体のサイト（mhlw.go.jp、houjin-bangou.nta.go.jp、info.gbiz.go.jp、data.e-gov.go.jp、mlit.go.jp、soumu.go.jp、ppc.go.jp、zeirishikensaku.jp、gyosei.or.jp、shiho-shoshi.or.jp など）が通信制限で開けなかった。** このため、**下にある規約の文言はすべて「原文未確認」**。WebSearch の検索結果（検索エンジンの要約）に出た文言を載せている。使う前に、各 URL を自分のブラウザで開いて原文を確かめること。
- 例外：医療情報ネットのオープンデータの列については、そのデータを使っている公開リポジトリ（GitHub `nyampire/jp-healthcare-osm`、2026-06-01 時点のデータを使用）の中身を実際に読んで確かめた（二次情報）。
- 表の印：**◎**＝規約で商用利用可と（検索結果上）確認／**×**＝規約で商用利用・複製などが禁止と（検索結果上）確認／**？**＝確認できず／**（推測）**＝根拠が弱いもの。

## 1. 区分ごとの公開リスト（一覧表）

| 区分 | リスト名（運営） | URL | 一括DL | 載っている項目／HPのURL | 営業利用の可否（規約・検索結果の文言。すべて原文未確認） | 更新頻度 | 注意 |
|---|---|---|---|---|---|---|---|
| 医療（病院・診療所・歯科） | 医療情報ネット（ナビイ）のオープンデータ（厚生労働省） | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryou/newpage_43373.html ／ e-Gov：https://data.e-gov.go.jp/data/dataset/iryou_teikyouseido_mhlw | **あり**（ZIP 内に CSV。業態ごとに施設票と診療科・診療時間票） | 名称・住所・座標・診療科・診療時間など。**HP の URL あり**（施設票の列「案内用ホームページアドレス」。薬局は「薬局のホームページアドレス」）。2026-06-01 版で病院 7,715／診療所 80,155／歯科 54,637 施設、URL が入っているのは全業態で約 12.2 万件（二次情報）。電話番号の列は**未確認** | ◎ 検索結果：「公共データ利用規約（第1.0版）」で公開（e-Gov 上は「CC BY」と表示）。商用可、出典の記載が条件。営業目的・DM の禁止文言は**見つからず** | **半年ごと**（6/1 時点・12/1 時点。2025-06、2025-12、2026-06 版を確認） | 院長名は今回の調べでは列に見当たらない（未確認）。URL の書式の揺れ（http/https の欠け等）あり |
| 医療（保険医療機関） | コード内容別医療機関一覧表（各地方厚生局） | 例：関東信越 https://kouseikyoku.mhlw.go.jp/kantoshinetsu/chousa/shitei.html ／東北 https://kouseikyoku.mhlw.go.jp/tohoku/gyomu/gyomu/hoken_kikan/itiran.html | 局ごとにファイルあり（主に PDF。Excel の有無は未確認） | 医療機関名・所在地・電話（推測）・開設者・管理者名（推測）。**HP の URL なし**（推測） | ？ 規約未確認 | 毎月（2026-09-01、2026-10-01 時点版を確認） | 8 局に分かれ形式もばらばら。上の医療情報ネットで足りるなら不要 |
| 全業種（法人） | 法人番号公表サイト 全件データ（国税庁） | https://www.houjin-bangou.nta.go.jp/download/zenken/index.html | **あり**（CSV／XML、都道府県別・全国） | 法人番号・商号・本店所在地（基本3情報）のみ。**電話・HP・業種なし** | ◎ 検索結果：「公共データ利用規約（第1.0版）に準拠した利用条件の下で利用することができます」「どなたでも複製、公衆送信、翻訳・変形等の翻案等を自由に利用でき、商用利用も可能」 | 全件は**毎月**（前月末時点）、差分は日次 | 業種がないので、医療法人・税理士法人・○○不動産などを**名称で絞る**使い方になる。個人事業主（多くのクリニック・士業）は載らない |
| 全業種（法人） | gBizINFO（経済産業省・デジタル庁） | https://info.gbiz.go.jp/ ／ 規約：https://help.info.gbiz.go.jp/hc/ja/articles/4999421139102 | **あり**（CSV。法人基本情報＋活動情報7種。API・ダウンロードは事前申請とトークンが要る） | 法人番号・名称・所在地・代表者名・資本金・従業員数・業種・**企業ホームページ（項目はある。入っている割合は不明）**。電話番号なし（二次情報） | ◎（条件つき）検索結果：コンテンツは政府標準利用規約（第2.0版）準拠で商用可。ただし API・DL は「**申請時に申告した目的の範囲内に限られます**」。制限回避のための複数トークン取得は禁止 | 未確認（推測：月次程度） | 申請時の「利用目的」に**営業リスト作成と書くこと**。代表者名は個人情報 |
| 住まい（不動産・リフォーム＝建設業） | 建設業者・宅建業者等企業情報検索システム（国土交通省） | https://etsuran2.mlit.go.jp/ （案内：https://www.mlit.go.jp/totikensangyo/const/sosei_const_tk3_000037.html） | **なし**（画面検索のみ。一括DLは確認できず） | 免許・許可番号、商号、代表者名、所在地、**電話番号**（検索結果）。**HP の URL なし** | △ 検索結果：「本システムにおいて提供する電子情報の複写、再配布、加工については特に制限はありませんが、…二次情報であることを明らかにする必要があります」。営業目的の禁止文言は**見つからず** | **毎月**（過去データは残らない） | 一括DLがないので大量取得は**機械的な取得（スクレイピング）になる → 規約・サーバ負荷の面で非推奨**。代表者名は個人情報 |
| 住まい（リフォーム） | 住宅リフォーム事業者団体登録制度の登録事業者検索（国交省制度、(一社)住宅リフォーム推進協議会） | https://www.j-reform.com/reform-dantai/kensaku.php | 未確認（推測：なし） | 事業者名・所在地など（推測） | ？ 規約未確認 | 未確認 | 件数が少なく網羅性は低い（推測） |
| 店舗（飲食） | 食品衛生申請等システムの公開データ（厚生労働省）＋各自治体のオープンデータ | 申請システム：https://ifas.mhlw.go.jp/ ／公開ページ：https://i2fas.mhlw.go.jp/ ／例：静岡県 https://opendata.pref.shizuoka.jp/dataset/12489.html 、神戸市 https://www.city.kobe.lg.jp/a99427/kenko/health/hygiene/dataset.html | **あり**（自治体別に DL。毎月15日に前月末分を作成） | 営業施設名称・所在地・座標・**営業施設の電話番号**・業種、申請者名（法人名／個人は氏名）。**HP の URL なし** | ？ IFAS の利用規約（https://ifas.mhlw.go.jp/termsofuse.htm）は開けず、二次利用・営業利用の条文は**未確認**。自治体のオープンデータ版は CC BY 等が多い（推測。サイトごとに要確認） | 毎月 | 2021年6月以降の許可・届出のみ。営業者が「公開しない」を選べる＝**網羅的ではない**。個人営業者の氏名が載る |
| 店舗（美容・理容） | 各自治体の生活衛生関係施設一覧（例：神戸市） | 例：https://www.city.kobe.lg.jp/a99427/kenko/health/hygiene/dataset.html | 自治体による（CSV あり） | 施設名・所在地など。HP なし（推測） | 自治体ごとに異なる（未確認） | 自治体ごと | **全国を一括で取れる公的リストは見つからなかった** |
| 店舗（整骨院） | 各自治体の施術所一覧（柔道整復・あはき） | 例：千葉県 https://www.pref.chiba.lg.jp/iryou/sezyutuichiran.html 、栃木県 https://www.pref.tochigi.lg.jp/e02/2020juusei.html 、仙台市 https://www.city.sendai.jp/imuyakumu/download/bunyabetsu/kenko/iryo/sefukushiho.html | 自治体による（CSV／Excel） | 施術所名・所在地、施術者名（推測）。HP なし | 自治体ごとに異なる（未確認） | 自治体ごと | **全国一括の公的リストは見つからなかった**（地方厚生局は申請様式のみ確認） |
| 士業（税理士） | 税理士情報検索サイト（日本税理士会連合会） | https://www.zeirishikensaku.jp/ | なし | 氏名・事務所名・所在地など（推測） | **× 禁止**。検索結果：「本サイトに掲載している情報の複製、転載、公衆送信その他一切の行為、並びに掲載情報の**商用利用を固く禁じます**」（要旨。原文未確認） | 随時（推測） | **リスト化に使わない** |
| 士業（行政書士） | 行政書士会員検索（日本行政書士会連合会） | https://www.gyosei.or.jp/members-search ／注意：https://www.gyosei.or.jp/members-search/search-notes | なし | 氏名・事務所名・所在地など | **× 禁止**。検索結果：登録情報の著作権は連合会に帰属し「**複製、転載、公衆送信等を行うことはできません**」（要旨。原文未確認）。各県会（富山・和歌山・福井など）も同様 | 随時（推測） | **リスト化に使わない** |
| 士業（司法書士） | 司法書士検索（日本司法書士会連合会） | https://www.shiho-shoshi.or.jp/other/doui/ ／サイト利用条件：https://www.shiho-shoshi.or.jp/other/terms_and_conditions/ | なし | 氏名・事務所名・所在地など | **× 禁止**。検索結果：「司法書士検索に掲載されている司法書士情報の著作権は、日本司法書士会連合会に帰属しており、**複製、転載、公衆送信等一切の行為を行うことはできません**」（要旨。原文未確認） | 随時（推測） | **リスト化に使わない**（検索前に同意画面あり） |
| 士業（社労士） | 都道府県社労士会の会員検索（全国社会保険労務士会連合会からリンク） | https://www.shakaihokenroumushi.jp/consult/tabid/527/Default.aspx | なし | 会ごとに異なる | ？ 利用条件は確認できず。連合会の規則で、会員情報の第三者提供は会報・名簿作成などの目的に限ると検索結果に出た | 会ごと | 他の士業と同じく**禁止と見なして扱うのが安全（推測）** |
| 士業（法人化しているもの） | 法人番号全件データ／gBizINFO で「税理士法人」「行政書士法人」「社会保険労務士法人」「司法書士法人」を名称検索 | 上記 | あり | 名称・所在地（＋gBizINFO なら HP の項目） | ◎（上記の規約どおり） | 上記 | **士業で使えるのは実質これだけ**。個人事務所は拾えない |

## 2. 使ってよい順のおすすめ

1. **医療情報ネットのオープンデータ（厚労省）** … 医療（病院・診療所・歯科）はこれ一本でよい。一括 CSV、HP の URL つき（約6割の施設に URL）、公共データ利用規約で商用可。出典を書く。半年ごと更新なので送る前に HP の生存確認をする。
2. **法人番号公表サイト 全件データ（国税庁）** … 全業種の法人の土台。業種がないので名称（「医療法人」「税理士法人」「不動産」「ホーム」「リフォーム」「工務店」など）で絞る。商用可。電話・HP なし → 3 で補う。
3. **gBizINFO（経産省）** … 2 に「企業ホームページ」「業種」「代表者名」を足す用途。商用可だが **API・DL の申請時に「営業先リストの作成」と目的を書く**こと（目的外利用は規約違反）。
4. **食品衛生申請等システムの公開データ・自治体のオープンデータ（飲食・美容・整骨院）** … 店舗系はここしかない。ただし全国一括は飲食のみ、美容・整骨院は自治体ごと。IFAS の規約は未確認なので**使う前に termsofuse を自分で読む**。個人営業者の氏名が入るので、氏名列は取り込まない。
5. **国交省の企業情報検索システム（不動産・建設）** … 規約上の制限は弱い（出典明示が条件）が、一括 DL がない。**件数を絞って手作業で使う程度**にとどめ、機械的な大量取得はしない。不動産・リフォームは 2＋3 で名称から拾う方を主にする。
6. **使わない**：日税連・日行連・日司連の会員検索、社労士会の会員検索（複製・商用利用が禁止、または禁止と見なすべき）。士業は 2・3 の「○○法人」だけを対象にする。

## 3. 公式 HP の URL が無いときに HP と問い合わせフォームを見つける方法

| 方法 | 状況（2026-10 時点） | 規約上の注意 |
|---|---|---|
| Google Custom Search JSON API | **新規受付は終了済み**。既存利用者も **2027-01-01 で終了**（検索結果・複数の二次情報）。後継として Google は Vertex AI Search を案内（最大50ドメイン内の検索向けで、ウェブ全体検索の代わりにはならない） | 新しく始めるには使えない |
| Bing Search API | **2025-08-11 に終了**（Microsoft の告知 https://learn.microsoft.com/en-us/lifecycle/announcements/bing-search-api-retirement ）。後継の Grounding with Bing は AI エージェント経由で、生の検索結果を受け取れない | 使えない |
| Google Places API（Place Details の websiteUri） | 使える（有料） | Google Maps Platform 規約 3.2.3 は「スクレイピング禁止」で、**商号・住所などを複製して保存することを禁止**。保存してよいのは place_id（無期限）と緯度経度（30日まで）だけ（検索結果。原文未確認）。→ **取得した URL を自社リストに保存するのは規約違反になりうる**。使うなら place_id だけ保存し、送信時にその都度取得する形にする（推測） |
| Brave Search API | 使える（有料） | 検索結果の要約：通常プランは**結果の保存不可**、保存するには「storage rights」付きプランが必要（二次情報。料金は未確認） |
| Google マップ・検索結果のスクレイピング | — | Google の規約で禁止。**やらない** |
| 現実的なやり方（推測を含む） | ①医療はオープンデータの URL を使う ②gBizINFO の「企業ホームページ」を使う ③残りは人が検索して確認（1件ずつ） ④ HP が分かったら、トップページや「お問い合わせ」「contact」のリンクを人または軽いクローラで探す（相手サイトの robots.txt と負荷に配慮） | 相手サイトのフォームに「営業目的の送信はお断り」と書かれていたら**送らない**ルールにする |

## 4. 法律面の注意

### 4-1. 個人情報保護法（個人情報保護委員会 Q&A。原文未確認）
- **公開情報でも個人情報**。ネット上で公開されている情報を「ファイルをダウンロードしてデータベース化する」ことは「個人情報を取得」したことになる（Q&A 1-4-4 の要旨。https://www.ppc.go.jp/all_faq_index/faq1-q4-4/ ）。
- **法人の代表者の氏名も個人情報**。氏名で検索できるデータベースなら「個人データ」になる。法人情報だけで検索できる作りなら「個人データ」には当たらない（Q&A 2-6 の要旨。https://www.ppc.go.jp/all_faq_index/faq2-q2-6/ ）。
- 個人事業主の士業・クリニックの院長名、飲食店の個人営業者名は個人情報。→ **対応**：
  - 取得前に、自社のプライバシーポリシーで利用目的（例：「当社サービスのご案内のため」）を公表しておく（法21条の通知・公表。一般的な理解）。
  - **氏名の列は取り込まない**（施設名・住所・URL だけで足りる）。取り込むなら名前で検索できない形にする。
  - 公開情報から作った名簿を**他人に配る・売ることはしない**（第三者提供。Q&A 1-49 の論点）。
  - 「今後案内不要」と言われたら止める（停止リストを持つ）。

### 4-2. 特定電子メール法（迷惑メール防止法）
- 法の「電子メール」は、施行規則で **SMTP を使う通信と SMS** に限られる（総務省資料・施行規則の検索結果）。ウェブの問い合わせフォームへの入力・送信（HTTP）はこの方式に当たらないので、**フォーム送信は法の対象外とする理解が一般的**。
- ただし、**総務省が「問い合わせフォームからの営業送信は対象外」と明言した文書は、今回見つけられなかった**（ガイドライン https://www.soumu.go.jp/main_sosiki/joho_tsusin/d_syohi/pdf/m_mail_081114_1.pdf は開けず原文未確認）。「フォームを持つ会社は法3条4項の『アドレスを公表している者』に当たる」という説明は民間サイトの見解にとどまる。
- 次は**法の対象になりうるので注意**（推測を含む）：フォームではなく、HP に載っているメールアドレスへ直接メールすること（公表アドレスへの送信はオプトイン規制の例外だが、「広告メールお断り」と書いてあれば例外にならない）。この場合も送信者表示・配信停止の方法の表示は必要。
- 対象外でも、**相手が「営業お断り」と書いたフォームへの送信、同じ相手への繰り返し送信、大量の自動送信**は、苦情・業務妨害の主張・相手サイトの規約違反につながりうる（推測）。

### 4-3. その他
- **特定商取引法**：事業者向けの勧誘（BtoB）は適用除外とされるのが一般的（未確認）。ただし個人営業の小さな店舗は「営業のため」の取引かで争いになる余地あり（推測）。
- **各リストの規約**：公共データ利用規約・政府標準利用規約は**出典の記載**と「加工した場合はその旨」の記載が条件。社内リストでも出典を残しておく。
- **医療**：医療機関への営業そのものを禁じる法律は見つからなかった。ただし MEO ツールの案内で「口コミ」を扱う場合、医療広告ガイドライン（体験談の扱い）に触れる可能性がある（推測。今回未調査）。

## 5. 未確認のまま残っていること（作業前に人が確認する）

1. 医療情報ネット オープンデータの**電話番号の列の有無**（定義書：https://www.mhlw.go.jp/content/11121000/001306376.xlsx ）
2. 法人番号公表サイト「利用規約」（https://www.houjin-bangou.nta.go.jp/riyokiyaku/index.html ）の原文
3. gBizINFO「API・データダウンロード利用規約」の原文と、「企業ホームページ」の入力率
4. 食品衛生申請等システムの利用規約（https://ifas.mhlw.go.jp/termsofuse.htm ）での公開データの二次利用・営業利用の扱い
5. 税理士・行政書士・司法書士の各検索サイトの禁止文言の原文（今回は検索結果の要約のみ）
6. 国交省 企業情報検索システムの「利用上の注意」原文
7. 総務省の特定電子メール法ガイドラインで、ウェブフォームについての記述があるか

## 出典（検索で確認したページ。すべて原文未確認）
- [医療情報ネットのオープンデータ｜厚生労働省](https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryou/newpage_43373.html)
- [医療情報ネットのオープンデータ - e-Govデータポータル](https://data.e-gov.go.jp/data/dataset/iryou_teikyouseido_mhlw)
- [nyampire/jp-healthcare-osm（GitHub、実際に読んだ二次情報）](https://github.com/nyampire/jp-healthcare-osm)
- [全件データのダウンロード｜国税庁法人番号公表サイト](https://www.houjin-bangou.nta.go.jp/download/zenken/index.html)
- [利用規約｜国税庁法人番号公表サイト](https://www.houjin-bangou.nta.go.jp/riyokiyaku/index.html)
- [法人番号システムWeb-API機能利用規約](https://www.houjin-bangou.nta.go.jp/webapi/riyokiyaku.html)
- [gBizINFO API・データダウンロード利用規約](https://help.info.gbiz.go.jp/hc/ja/articles/4999421139102-API-%E3%83%87%E3%83%BC%E3%82%BF%E3%83%80%E3%82%A6%E3%83%B3%E3%83%AD%E3%83%BC%E3%83%89%E5%88%A9%E7%94%A8%E8%A6%8F%E7%B4%84)
- [gBizINFO 利用規約（PDF）](https://info.gbiz.go.jp/common/docs/policy.pdf)
- [公共データ利用規約 - e-Govデータポータル](https://data.e-gov.go.jp/data/dataset/pulic_data_license)
- [建設業者・宅建業者等企業情報検索システム - 国土交通省](https://www.mlit.go.jp/totikensangyo/const/sosei_const_tk3_000037.html)
- [保険医療機関・保険薬局の指定等一覧／関東信越厚生局](https://kouseikyoku.mhlw.go.jp/kantoshinetsu/chousa/shitei.html)
- [食品衛生申請等システム 利用規約](https://ifas.mhlw.go.jp/termsofuse.htm) ／ [食品衛生公開ページ](https://i2fas.mhlw.go.jp/)
- [静岡県 食品衛生関係営業許可台帳](https://opendata.pref.shizuoka.jp/dataset/12489.html) ／ [神戸市 生活衛生関係許可施設等の情報提供](https://www.city.kobe.lg.jp/a99427/kenko/health/hygiene/dataset.html)
- [千葉県 施術所一覧](https://www.pref.chiba.lg.jp/iryou/sezyutuichiran.html)
- [住宅リフォーム事業者団体 登録事業者検索](https://www.j-reform.com/reform-dantai/kensaku.php)
- [税理士情報検索サイト](https://www.zeirishikensaku.jp/)
- [行政書士会員検索 ご利用上の注意](https://www.gyosei.or.jp/members-search/search-notes)
- [司法書士検索（日本司法書士会連合会）](https://www.shiho-shoshi.or.jp/other/doui/)
- [各都道府県の社労士会を探す](https://www.shakaihokenroumushi.jp/consult/tabid/527/Default.aspx)
- [個人情報保護委員会 Q&A 1-4-4](https://www.ppc.go.jp/all_faq_index/faq1-q4-4/) ／ [Q&A 2-6](https://www.ppc.go.jp/all_faq_index/faq2-q2-6/) ／ [Q&A 1-49](https://www.ppc.go.jp/all_faq_index/faq1-q1-49/)
- [特定電子メールの送信等に関するガイドライン（総務省）](https://www.soumu.go.jp/main_sosiki/joho_tsusin/d_syohi/pdf/m_mail_081114_1.pdf) ／ [省令で定める内容についての考え方（総務省）](https://www.soumu.go.jp/main_sosiki/joho_tsusin/policyreports/chousa/mail_ken/pdf/080604_2_5.pdf)
- [Bing Search API retirement（Microsoft）](https://learn.microsoft.com/en-us/lifecycle/announcements/bing-search-api-retirement)
- [Google Maps Platform Service Specific Terms](https://cloud.google.com/maps-platform/terms/maps-service-terms) ／ [Places API Policies](https://developers.google.com/maps/documentation/places/web-service/policies)
- [Brave Search API](https://api.search.brave.com)
