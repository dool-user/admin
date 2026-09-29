# リサーチメモ（レイ・トレンド派）2026-09-29

## 今日の結論（1〜2行）
この7日（9/22〜9/29）でいちばん勢いがあるのは A01 の「Claude Code クラウドセッション正式版（9/23）」。国内の大手ニュースサイトと個人の解説記事（note・Zenn）が続けて出ている。A02 は「AI営業が迷惑がられている」という逆風の話題、A04 は Threads のインサイト刷新でリンククリック数がなくなった件が、書き手が拾うべき新しい話題。

※ 調べ方：WebSearch の検索結果の要約だけを使った（WebFetch で本文は読んでいない）。「どれくらい増えたか」は検索件数や投稿数を測れていないので**未計測**。日付は検索結果に出たものだけ書き、確かめられないものは「日付未確認」とした。

## 見つけたこと
| アカウント | 見つけたこと | 事実／推測 | 出典 |
|---|---|---|---|
| A01 | Claude Code の「クラウドセッション」が 9/23（米国時間）に正式版になった。PCを閉じても作業が続く。Pro・Max・Team などで使える。既存の契約者には1回限りのクレジット（Pro 100ドル・Max 250ドル） | 事実（検索要約） | https://pc.watch.impress.co.jp/docs/news/2143165.html ／ https://forest.watch.impress.co.jp/docs/news/2142708.html（2026-09-23前後・日付は要約から） |
| A01 | 正式版のあと、個人の解説記事（Zenn・note・企業ブログ）が続けて出ている。Serverworks のブログは 9/26 に「AGENTS.md 対応・クラウドセッション正式版」をまとめた | 事実（記事の存在）／「増えた」は推測 | https://blog.serverworks.co.jp/2026/09/26/190000 ／ https://zenn.dev/goat_eat_any/articles/claude-code-cloud-sessions（日付未確認）／ https://note.com/natty_toucan386/n/n6beecde1fe99（日付未確認） |
| A01 | Claude Code が AGENTS.md（Codex・Cursor などと共通の指示ファイル）を読めるようになった（v2.1.277） | 事実（検索要約・日付は 9/26 の記事より前） | https://blog.serverworks.co.jp/2026/09/26/190000 |
| A01 | 9/17 に Claude Code の「プロジェクト」機能が刷新（ベータ）。頼むと複数の「スレッド」に仕事を分けて並行で進め、最後にまとめる | 事実（7日より少し前） | https://pc.watch.impress.co.jp/docs/news/2142119.html |
| A02 | 「AI営業がお問い合わせフォームに大量に届き、中小企業の社長が『業務妨害だ』と怒っている」という記事と、AI営業をブロックする方法の記事が出ている | 事実（記事の存在）・日付未確認 | https://toyokeizai.net/articles/-/870844 ／ https://kurasaku.co.jp/tech-blog/block-ai-agent-sales ／ https://formok.com/new/ja/block |
| A02 | 9月上旬に、リスト作成〜DM〜AI架電まで自動化する営業サービスの発表が続いた（例：FanVoice AI開拓部 9/2） | 事実（検索要約）・7日より前 | https://prtimes.jp/topics/keywords/AI%E5%96%B6%E6%A5%AD |
| A03 | GBP の投稿の閲覧数レポートが復活すると、9/11 に公式ニュースレターで発表されたとする記事がある（2023年2月に廃止されていた） | 事実（二次情報。Google 公式の原文は未確認） | https://note.com/information_meo/n/naeeffb065200 |
| A03 | Google マップの会話型AI「マップに相談」が 9/1 から日本で順次提供 | 事実（プレスリリースの要約）・7日より前 | https://prtimes.jp/main/html/rd/p/000000619.000037205.html |
| A04 | Threads のインサイトが刷新（9/8）。Meta AI が「なぜ伸びた／伸びなかったか」を要約する。一方でリンククリック数はなくなった | 事実（海外記事の要約） | https://www.engadget.com/2251592/threads-is-overhauling-its-in-app-analytics-with-more-details-except-for-link-clicks/ |
| A04 | ポッドキャスト向けの新機能（9/16）。9月から Instagram なしで Threads 広告が出せる、という海外の要約がある。ただし国内記事は「Instagram 必須」と書いており、食い違う | 事実（要約）／広告の件は**未確認** | https://techcrunch.com/2026/09/16/threads-new-features-let-podcasters-promote-shows-and-reach-listeners/ ／ https://www.medix-inc.co.jp/webbu/threads-ads-11963 |

## 自分の視点でしか言えないこと（1つ）
「クラウドセッション正式版」の解説記事は、いまは**使い方・料金**ばかり（推測：検索に出た題名から判断）。A01 だけが書けるのは「PCを閉じている間に、営業部のリスト抽出や文面の下書きを回した」という**業務での使い方**。熱が高いのは正式版の直後の1〜2週間なので（推測）、10月上旬までに出すかどうかで差がつく。もう1つ、A02 は「AI営業が嫌われている」話題が出てきているので、「嫌われないAI営業（送信は人・1日の上限・お断りの店は入れない）」という書き方なら逆風を味方にできる（推測）。

## データサイエンティストに検証してほしい仮説（3つまで）
1. A01：「Claude Code クラウドセッションを業務で使った記事」を 10/6 までに出すと、同じ A01 のほかの記事よりビュー・購入が多い（正式版直後の熱に乗れるか）
2. A02：題名で「嫌われないAI営業」と逆風に触れた記事は、触れない記事よりクリック率が高い
3. A04：Threads でリンククリック数が見られなくなったので、note 側のアクセス元（Threads から来た数）を毎日記録しないと A04 の効果が測れない。まず計測の仕組みを作るのが先か（Threads 本体の数字だけで判断すると外れる）
