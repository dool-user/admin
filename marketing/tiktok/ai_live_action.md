# 実写風AI動画 制作キット（20代女性・単身引越し）

動画生成AI（Sora / Veo / Kling / Runway など）で実写風の映像を作るための台本とプロンプトです。
**前半の「困っている場面」だけをAIで生成し、後半のサービス紹介は既存のイラスト動画のカットを使います。**

## 前提ルール（必ず守る）

- AIの女性は「困っている場面」を演じるだけ。**「使ってよかった」「頼んだら助かった」などの感想・体験談は言わせない**（架空の口コミになり、ステマ規制・景品表示法に抵触するため）
- AI生成の人物が映る間は、画面上部に小さく「※AIで生成したイメージ映像です」と入れる
- TikTok広告の入稿時に「AI生成コンテンツ」のラベルをオンにする
- 映像内に電力会社のロゴ・制服・社名・実在のアプリ画面を出さない

## 人物設定（全カット共通・毎回プロンプトに入れる）

- 日本人女性、25歳前後、一人暮らしを始めたばかり
- 肩までのダークブラウンの髪、ナチュラルメイク
- オーバーサイズのグレーのパーカー、黒のスウェットパンツ
- 部屋：日本の1K、白い壁、フローリング、ガムテープで閉じた段ボールが積まれている、カーテンのない窓から夜の街の明かり

**一貫性のコツ：** まず人物の静止画を1枚作り、それを参照画像（image-to-video）にして全カットを生成すると、顔と服装がそろいます。

## カット割り（約24秒）

| # | 秒 | 生成 | 映像 | セリフ（本人） | 画面の文字 |
|---|---|---|---|---|---|
| 1 | 0〜3 | AI | 夜。玄関横の壁スイッチを何度もカチカチ押す。部屋は真っ暗 | 「え、うそ…電気つかない」 | 引越し初日の夜、電気つかない… |
| 2 | 3〜7 | AI | スマホのライトで照らしながら分電盤のブレーカーを上げる。それでも暗い | 「ブレーカー上げたのに…」 | ブレーカー上げても真っ暗 |
| 3 | 7〜11 | AI | 段ボールの間に座り込み、スマホを見て「あっ」という顔 | 「…電気の申し込み、してなかった」 | 原因：使用開始の申し込み忘れ |
| 4 | 11〜15 | AI | 天井を見上げてため息。指を折って数える | 「ガスも水道もネットも、全部別に連絡するの…？」 | 連絡先、ぜんぶバラバラ… |
| 5 | 15〜20 | 既存 | イラスト動画の解決カット（ロゴ・最短即日開通※・相談無料・土日祝も受付） | ナレーション「まとめて頼めるところ、あります。相談無料、土日もOK」 | ※即日開通の条件注記を必ず入れる |
| 6 | 20〜24 | 既存 | イラスト動画の最終カット（対応エリア・下のボタンへ矢印） | ナレーション「引越し予定の人は、今のうちにチェック！」 | 詳しくは下のボタンから |

## 生成プロンプト（カット1〜4）

共通設定：縦型 9:16、1080×1920、4〜5秒、スマホの手持ち撮影風。ナレーション入りの台本を使う場合は、セリフ（日本語）もプロンプトに含めて口の動きを合わせる。

**共通の人物・場所の記述（各プロンプトの先頭に付ける）**
```
Vertical 9:16 smartphone footage, handheld, natural and slightly shaky, realistic lighting, no text, no logos.
A Japanese woman in her mid-20s with shoulder-length dark brown hair and natural makeup, wearing an oversized gray hoodie and black sweatpants,
in a small newly rented Japanese studio apartment (1K) with white walls, wooden flooring, and stacked taped cardboard moving boxes. Night, city lights through a bare window.
```

**カット1**
```
She stands by the entrance and flips the wall light switch several times, but the room stays completely dark. Confused expression, she whispers in Japanese: 「え、うそ…電気つかない」. Dim light only from the window.
```

**カット2**
```
Using her smartphone flashlight, she opens the small circuit breaker panel above the entrance and pushes the main breaker lever up. Nothing happens, the room stays dark. She says in Japanese, disappointed: 「ブレーカー上げたのに…」. Close-up on her face lit by the phone light.
```

**カット3**
```
She sits on the floor between cardboard boxes, scrolling on her phone; the screen glow lights her face. She suddenly realizes something and says quietly in Japanese: 「…電気の申し込み、してなかった」. Slow push-in on her face.
```

**カット4**
```
Still sitting on the floor, she looks up at the ceiling and sighs, then counts on her fingers while saying in Japanese: 「ガスも水道もネットも、全部別に連絡するの…？」. Tired but relatable expression, medium shot.
```

**ネガティブプロンプト（使えるツールのみ）**
```
text, subtitles, logos, brand names, company uniforms, power company, extra fingers, distorted face, cartoon, anime
```

## 編集（こちらで対応できます）

生成したカット1〜4の動画ファイルを共有いただければ、次をまとめて仕上げます。

- テロップ（TikTok風の白箱・縁取り文字）と「※AIで生成したイメージ映像です」の表記
- カット5・6（既存のイラスト動画のカット）とのつなぎ
- ナレーション（jf_alpha の音声）と音量調整
- 9:16 / H.264 のMP4書き出し
