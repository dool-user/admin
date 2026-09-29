# リサーチメモ（ハヤト・逆張り派）2026-09-29

> 調べ方：WebSearch の検索結果の要約だけで判断した（WebFetch は使っていない／本文は未確認）。公開前に原文を確認すること。

## 今日の結論（1〜2行）
3分野とも「失敗・トラブル」の記事は**すでに多い**。ただし書き手の多くは業者（研修会社・ツール会社・MEO代行）で、結論が「だから当社へ」になりがち。空白は**「やめ方・止め方・自分で続ける方法」を、売る側ではなく使っている本人のログで書いた記事**（推測）。

## 見つけたこと
| アカウント | 見つけたこと | 事実／推測 | 出典 |
|---|---|---|---|
| A01 | Claude Code の高額請求の注意喚起が多い（「想定1万円が127万円のAPI課金」の事例紹介、支出上限・アラート設定のすすめ） | 事実（要約から読んだ。金額は各記事の主張で未検証） | https://saix.co.jp/claude-code-10-mistakes-to-avoid/ ・ https://note.com/emilia_lab/n/nd2a6d5531ef6 ・ https://library.libecity.com/articles/01KQG982GKBQJ79DHKRAWQCMKS |
| A01 | 料金体系の変更で請求が増えたという注意喚起がある（要約では日付が「2024年6月15日」とあり、年が怪しい） | 事実（日付は要確認） | https://x.com/beku_AI/article/2066383281470451818 |
| A01 | 中小企業の導入事故（データ消失・高額請求・名簿漏れ）を「10パターン」にまとめた記事は、相談を受ける会社のもの | 事実 | https://saix.co.jp/claude-code-10-mistakes-to-avoid/ ・ https://walker-s.co.jp/ai/claudecode-failure/ |
| A01 | 「非エンジニアの9割は挫折」「150時間使って別ツールに移った」という声がある。一方「挫折した後どう立て直したか」を書いた記事は検索上位に見えない | 事実（前半）／推測（後半） | https://x.com/IHayato/status/2022613193697423375 ・ https://www.sbbit.jp/article/cont1/185291 |
| A01 | 運用・保守・引き継ぎの記事は Zenn・開発会社に多く、エンジニア向け。「一人社長が作った仕組みを、作った本人がいなくても回す」向けは少なく見える | 事実（前半）／推測（後半） | https://zenn.dev/polarisai_blog/articles/72b0214231121f ・ https://nulab.com/ja/blog/nulab/claude-code-handover-skills/ |
| A02 | AIフォーム営業が受け手の業務妨害として報道されている（「これは営業じゃない！業務妨害だ！」） | 事実 | https://toyokeizai.net/articles/-/870844 ・ https://news.yahoo.co.jp/articles/4ea7668e9564fac831fd86bfef15f5ce187e17f9 |
| A02 | 受け手側の「AI営業を止める方法」の記事も出ている＝送る側の信用はすでに下がっている | 事実（前半）／推測（後半） | https://kurasaku.co.jp/tech-blog/block-ai-agent-sales |
| A02 | 「除外リスト」「送ってはいけないフォーム（営業お断り・採用フォーム）」の記事はあるが、ほぼフォーム営業ツールの会社のブログ | 事実 | https://uruteq.logly.co.jp/blog/btob%E3%83%9E%E3%83%BC%E3%82%B1%E3%83%86%E3%82%A3%E3%83%B3%E3%82%B0/form-outreach-exclusion-list-guide/ ・ https://www.formrea.ch/blog/formsales-forms-to-avoid |
| A02 | 自社の営業部には「営業お断りの店は入れない」「人が1件ずつ確認して送る」「1日の上限」のルールがすでにある（CLAUDE.md）＝「送らない設計」の実物がある | 事実（社内資料） | CLAUDE.md |
| A03 | MEO業者の契約トラブル（中途解約できない・違約金・Googleアカウント権限を返さない）の記事は多い | 事実 | https://salonica.jp/blog/meo-contract-trouble/ ・ https://gicp.co.jp/manegementnote/meo-content/cancel/ ・ https://webma.xscore.co.jp/study/meo-countermeasures-company/ |
| A03 | 「独自ツールに依存すると解約後に投稿・口コミ管理が止まり順位が下がる」「オーナー権限は自社で持つ」という指摘がある | 事実 | https://assist-all.co.jp/note/meo-diy-guide-limit-outsourcing/ ・ https://note.com/marketing_place/n/n90625bca6af1 |
| A03 | 口コミ返信の記事は「感情的に返すな・丁寧に」の型ばかり。低評価を受ける店主の負担・返信をどこまでやめてよいか、を扱う記事は見当たらない | 推測 | https://www.sogo-ad.jp/blog/meo-review-reply-template/ ・ https://coomil.co.jp/column/googlemap-bad-review/ |

## 自分の視点でしか言えないこと（1つ）
A03 は**MEOツールを売る側が「ツールをやめても困らない始め方（権限の持ち方・解約後に自分で続ける最低限）」を書く**のが一番の空白（推測）。業者の記事は「悪い業者に注意」で止まり、自社の解約後までは書かない。売る側が出口を先に見せると信頼になり、見込み客づくりにも効く可能性がある。ただしツール販売と競合しうるので、書いてよい範囲は**社長の確認が必要**。
A01・A02 も同じ型で「高額請求を止めた設定」「送らなかった店の数と理由」を、自社の実ログ（数字は社長確認後）で書けば、業者ブログと差がつく（推測）。

## データサイエンティストに検証してほしい仮説（3つまで）
1. A03：「MEOをやめても困らない権限の持ち方」系のタイトルは、「MEOで集客を増やす」系より表示→購入の割合が高い（見込み客が業者不信を持っているため）。公開後に同価格で比べる
2. A01：「Claude Code の請求を止めた設定（一人社長の実例）」は、「Claude Code で業務自動化」より購入が多い。ただし失敗記事は業者ブログで供給過多なので、差が出ないなら「実ログかどうか」は効いていない
3. A02：「送らない店の選び方（除外の型）」を前面に出した記事は、「返信率を上げる文面」より SNS での反応（保存・引用）が多い。フォーム営業への世間の反感が強いため
