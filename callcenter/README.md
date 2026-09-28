# Claude 営業センター

Uber Eats 未出店の飲食店に、出店説明のアポを取る組織を **Claude（Claude Code のサブエージェント）だけ**で組んだものです。

| 部署 | 人数 | エージェント定義 |
|---|---|---|
| センター長 | 1 | `CLAUDE.md`（メインのセッション） |
| 架電 A・B チーム | SV 2・AP 10（SV は 5人に1人） | `.claude/agents/sv.md`・`appointer.md` |
| リスト抽出 | 1 | `.claude/agents/list-extractor.md`（`../leadgen` を使う） |
| マーケ | 1 | `.claude/agents/marketer.md` |
| 案件処理（事務） | 3 | `.claude/agents/case-admin.md` |

## ファイル構成
```
callcenter/
├── CLAUDE.md        毎回読む約束ごと（センター長の指示書）
├── character.md     人柄・口調
├── templates.md     アポが取れた型
├── hooks.md         効いた一言目
├── knowledge.md     専門知識（数字は公式資料で確認して記入）
├── ng-words.md      使わない言葉
├── review.md        出す前の点検
├── mistakes.md      直させたこと（Claude が作業の終わりに書く）
├── .claude/agents/  担当ごとのエージェント
├── data/leads.csv   架電リスト
├── out/             架電記録・アポ台帳・案件票
└── dashboard/       いま何をしているかの可視化（index.html をブラウザで開く）
```

## 使い方
```bash
cd callcenter
claude
```
例：「list-extractor で新宿区のラーメン店を抽出して、AP 10人に割り振って台本を作って」

育て方：最初は `CLAUDE.md` と `review.md` だけ守らせ、作業の終わりに「今回直させたところを mistakes.md に足して。何を・なぜ・次からどうするかの3行で」と送る。アポが取れた型は `templates.md`、効いた一言目は `hooks.md`、言い回しの直しは `ng-words.md` に移していく。

## できないこと
- Claude は電話を発信できません。台本・文面・記録・集計までを Claude が行い、発信は人か電話システム（音声AI・CTI）が行います
- `dashboard/` は今はデモの動き（シミュレーション）です。`out/` の記録とつなげれば実データで動かせます
