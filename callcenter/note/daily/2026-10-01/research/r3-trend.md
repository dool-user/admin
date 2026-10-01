# リサーチメモ（レイ・トレンド派）2026-10-01

## 今日の結論（1〜2行）
この7日（9/24〜10/1）で新しく熱が上がったのは、A01 の「Opus 5.5 が Claude Code の既定モデルに」と「OpenAI DevDay（9/29）の常時稼働エージェント dots」。どちらも 9/23 のクラウドセッション正式版に続く「PCを閉じても動くAI」の競争で、A01 の業務記事の追い風になる（推測）。A11 は 10月の転勤引越しが「準繁忙期」と複数の業者記事で確認できた。

※ 調べ方：WebSearch の検索結果の要約だけ（WebFetch は対象サイトがすべて通信制限で読めなかった）。「どれくらい増えたか」は**未計測**。9/29 のメモと重なる話（クラウドセッション正式版・AGENTS.md・GBP 投稿閲覧数の復活・AI営業が嫌われている記事）は省いた。

## 見つけたこと
| アカウント | 見つけたこと | 事実／推測 | 出典 |
|---|---|---|---|
| A01 | Claude Code v2.1.280 で Opus 5.5 が既定の Opus モデルになり、Pro・Team Standard の既定も Sonnet から Opus に変わった。v2.1.280 の公開は 9/22、Opus 5.5 の解説記事は 9/25 | 事実（検索要約） | https://blog.serverworks.co.jp/2026/09/25/190000 ／ https://qiita.com/moha0918_/items/4d9f3ac4f27c7bac0aab（日付未確認） |
| A01 | 9月のアップデートをまとめた解説記事が note・企業メディアに出ている（「9月の総まとめ」「できること25選」など） | 事実（記事の存在）・日付未確認 | https://note.com/kawaidesign/n/ncecd4d2d5e91 ／ https://uravation.com/media/claude-code-features-20-2026/ |
| A01 | OpenAI DevDay（9/29 米国時間）で、専用のクラウドPCを持ち 4,000 以上のアプリとつながる常時稼働エージェント「dots」と、マネージドエージェント基盤が発表された。国内でも ITmedia（9/30）・Zenn がまとめ記事を出した | 事実（検索要約） | https://www.cnbc.com/2026/09/29/openai-devday-2026-live-updates.html ／ https://www.itmedia.co.jp/news/article/2609/30/2000001868/ ／ https://zenn.dev/galirage/articles/openai-dev-day-2026-keynote（日付未確認） |
| A02 | 9/25 に Emooove が営業AIエージェント「Sales Pilot」の有償プランを開始、9/28 に Onboard AI が営業の「トーク分析」機能を開始（検索要約による） | 事実（検索要約・原文未確認） | https://prtimes.jp/topics/keywords/%E5%96%B6%E6%A5%AD |
| A02 | 「対話するだけで営業リストができるAIエージェント」（URITAI）の発表がある | 事実（記事の存在）・日付未確認 | https://prtimes.jp/main/html/rd/p/000000003.000176534.html |
| A03 | 9/22 に GBP 管理画面から「閉業（永久）」の選択肢が消えた、9/23 に第三者の情報修正の提案は4日以内に却下しないと反映されると Google が文書で明確にした、とする週刊まとめがある | 事実（二次情報・Google 原文は未確認） | https://shinichi-miyazaki.website/seo-weekly-20260927/ |
| A03 | 訂正：9/29 のメモで「9/1 から」とした「マップに相談」は、Impress 等の要約では **8/7 発表**。7日の熱の話題ではない | 事実（検索要約） | https://www.ai-crew-school.jp/blog/google-map-ni-sodan/ ／ https://www.watch.impress.co.jp/docs/news/2131621.html |
| A11 | 10月1日付など下期の人事異動に合わせ、9月下旬〜10月初めは転勤の引越しが増え、2〜4月に次ぐ「準繁忙期」とする業者記事が複数ある | 事実（記事の主張）・日付未確認 | https://www.homes.co.jp/cont/press/feature/feature_00004/ ／ https://ka-center.jp/advice/season10.html ／ https://www.karugamo.co.jp/tips/32939/ |
| A11 | 一方で「10月は上旬が最も安い・旬ごとの差は小さい」とする料金記事もあり、混み具合の見方は割れている | 事実（記事の主張）・日付未確認 | https://hikkoshi-pedia.com/yen/2186/ |
| A11 | 転勤の内示から引越しまでの段取りを書いた「秋の人事異動で転勤決定の方へ」型の記事を、不動産会社も出している | 事実（記事の存在）・日付未確認 | https://www.rerent-naritafd.com/blog/entry-846027/ ／ https://www.rals.net/journal/residence/moving_due_to_job_transfer/ |

## 自分の視点でしか言えないこと（1つ）
9/23 クラウドセッション → 9/25 Opus 5.5 → 9/29 OpenAI dots と、「放っておいても動くAIエージェント」の発表が1週間に3つ続いた（日付は上の出典）。解説記事は「どれが強いか」の比較に流れると思うが（推測）、A01 が書けるのは「実際に営業部を放置で回したら何が起きたか」。比較記事が増える前の今週が出しどき（推測）。A11 は、10/1 付の異動は**もう内示が出た後**なので、今から出すなら「内示から2〜3週間で決める部屋・回線・電気」の急ぎ向けが刺さる（推測）。

## データサイエンティストに検証してほしい仮説（3つまで）
1. A01：題名に「放置で回す」「PCを閉じても」など常時稼働の言葉を入れた記事は、入れない記事よりクリック率が高い（今週の発表が続いた熱に乗れるか）
2. A11：「急な転勤（内示から短期間）」向けのコラムは、一般的な引越しコラムより相談フォームへの遷移が多い（10月前後の2週間で比べる）
3. A03：GBP の「第三者の修正提案は4日で反映」という話題は、店舗オーナーの不安（勝手に書き換えられる）に刺さり、投稿閲覧数の話題より反応が高い（ただし Google 原文を確認してから）
