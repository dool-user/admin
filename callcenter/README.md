# Claude 営業センター

**Claude（Claude Code のサブエージェント）だけ**で組んだ組織です。部は2つあります。

- **営業部（DM・フォーム）**：Uber Eats に出店していない飲食店に、出店説明のアポを取る
- **note 販売部**：note の有料記事を企画・執筆し、Threads などで集客して売る

Claude は文面・原稿・点検・記録・集計までを担当します。**送信・投稿・公開は人が行います。**

## 組織

センター長（ソラ）は `CLAUDE.md`（メインのセッション）で、両方の部を統括します。

### 営業部（DM・フォーム）17名
| チーム | 人数 | エージェント定義 |
|---|---|---|
| A・B チーム | SV 2・AP 10（SV は5人に1人） | `.claude/agents/sv.md`・`appointer.md` |
| リスト抽出 | 1 | `list-extractor.md`（`../leadgen` で店と問い合わせフォーム・Instagram を探す） |
| マーケ | 1 | `marketer.md` |
| 案件処理（事務） | 3 | `case-admin.md`（返信対応・日程調整・案件票） |

### note 販売部 7名
| 担当 | 人数 | エージェント定義 |
|---|---|---|
| 編集長 | 1 | `note-editor.md` |
| リサーチ | 1 | `note-researcher.md` |
| ライター | 3 | `note-writer.md` |
| SNS 集客 | 1 | `note-promoter.md`（Threads・X の投稿案） |
| 分析 | 1 | `note-analyst.md` |

## ファイル構成
```
callcenter/
├── CLAUDE.md            毎回読む約束ごと（センター長の指示書）
├── sales/ ・ note/      部ごとのルールとナレッジ（同じ8ファイルの構成）
│   ├── character.md     人柄・文体
│   ├── templates.md     返信・販売につながった型
│   ├── hooks.md         効いた一言目
│   ├── knowledge.md     専門知識（数字は公式資料・社長の確認済みだけ）
│   ├── ng-words.md      使わない言葉
│   ├── review.md        出す前の点検
│   └── mistakes.md      直させたこと（Claude が作業の終わりに書く）
├── sales/data/leads.csv     送り先リスト
├── sales/out/outbox.csv     文面の台帳（下書き→承認済→送信済→返信あり→アポ）
├── note/out/articles.csv    記事の台帳（企画→執筆→校正待ち→公開待ち→公開済）
├── .claude/agents/      担当ごとのエージェント
├── tools/send_assist.py 承認済みの文面を人が送るための補助
└── dashboard/           いま何をしているかの可視化（index.html をブラウザで開く）
```

## 使い方
```bash
cd callcenter
claude
```
- 営業：「list-extractor で新宿区のラーメン店と連絡先を探して、AP 10人に割り振って文面を作って。SV の点検まで」
- note：「note-researcher で企画を5本出して、編集長が選んだ2本をライターに書かせて」

### 送る（人の作業）
```bash
cp sender.yaml.example sender.yaml     # 会社名・名前・連絡先・1日の上限を書く
python tools/send_assist.py            # leadgen と同じ Python 環境で
```
- フォーム：自動で入力し、**送信ボタンは押さずに止まります。** 内容・同意チェックを確かめて人が押す
- Instagram DM：プロフィールを開いて文面を表示。人がコピーして送る（Instagram は API で最初のDMを送れず、自動送信は規約違反のおそれがあるため）
- 「営業お断り」表記のあるフォームは入力せず「見送り」にします

## 守ること（法令・規約）
- 「営業お断り」「セールスご遠慮」の表記がある店には送らない。同じ店に30日以内に再送しない
- 名乗り・連絡先・「連絡が不要な場合の伝え方」を必ず書く
- note・SNS では、根拠のない収益の約束や事実でない期限を書かない（景品表示法）。実績は社長が確認した本物だけ

## 育て方
最初は `CLAUDE.md` と各部の `review.md` だけ守らせ、作業の終わりに「今回直させたところを mistakes.md に足して。何を・なぜ・次からどうするかの3行で」と送る。
返信・販売につながった型は `templates.md`、効いた一言目は `hooks.md`、言い回しの直しは `ng-words.md` に移していく。

## いまの状態
- `dashboard/` の動き・数字は**デモ（シミュレーション）**です。台帳（`outbox.csv`・`articles.csv`）とつなげれば実データで動かせます
- 台帳はまだ空です（実際の送信・販売はしていません）
