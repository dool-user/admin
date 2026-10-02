# 依頼：引越し相談フォームを Google Apps Script で公開し、note の記事に入れる

あなた（作業する AI）へ。以下の手順で、引越し相談フォームを公開してください。コードは下にすべて載せてあります。コードの中身は**書き換えないでください**（書き換えてよいのは、手順で指定した1か所だけ）。

## 前提
- 運営：まるっと窓口（関東の引越し・お部屋探しの民間の相談窓口）
- フォームは「相談したいこと・引越しの時期・エリア・お名前・連絡先」を受け取り、Google スプレッドシートの「引越し相談」シートに1行ずつ保存し、メールで通知します
- サーバーは使いません。Google Apps Script のウェブアプリとして公開します
- 会社の HP・プライバシーポリシーへのリンクは載せません（社長の指示）
- フォームの「紹介料を受け取る場合があります」の表示は、景品表示法（ステマ規制）のために必ず残します

## 必ず止まって社長に確認すること
- Google の権限の承認（「このアプリは確認されていません」と出たら、社長が「詳細」→「（安全ではないページ）に移動」を押す）
- デプロイ
- note の下書き保存・公開
- パスワードの入力（社長が行う）

## 手順

### A. フォームを公開する
1. https://sheets.new で新しいスプレッドシートを作り、名前を「まるっと窓口 相談」にする
2. メニュー「拡張機能」→「Apps Script」。プロジェクト名を「まるっと窓口 相談フォーム」にする
3. 「コード.gs」の中身を全部消して、下の【コード1】を全部貼る
4. 【コード1】の21行目あたり `var NOTIFY_TO = 'notify@example.com';` の `notify@example.com` だけを、社長に聞いた通知先メールアドレスに変える（**書き換えてよいのはここだけ**）
5. 左の「ファイル」の「＋」→「HTML」。名前は **moving-form**（拡張子は自動で付く）。中身を全部消して、下の【コード2】を全部貼る
6. 保存する
7. 動作の確認：上の関数の選択で `testNotify` を選んで「実行」→ 権限の承認（社長）→ 通知先にテストのメールが2通届けば OK
8. 「デプロイ」→「新しいデプロイ」→ 種類「ウェブアプリ」
   - 説明：引越し相談フォーム
   - 次のユーザーとして実行：自分
   - アクセスできるユーザー：全員
   → 社長に確認してから「デプロイ」
9. 表示された「ウェブアプリの URL」（`https://script.google.com/macros/s/…/exec`）を控え、社長に伝える
10. その URL をスマホとパソコンで開き、フォームが表示されることを確かめる。社長の了承を得てテスト送信を1件 → スプレッドシートに「引越し相談」シートができて1行入り、メールが届けば完了

### B. note の下書きにフォームを入れる
1. https://editor.note.com/notes/n3107470e7243/edit/ を開く
2. 本文のいちばん最後（ハッシュタグ #〜 の行があればその上）に、次を入れる（〈URL〉は A-9 の URL）
   - 大見出し：引越しのこと、まとめて相談できます
   - 本文：お部屋探し・電気ガス水道・ネット回線・ウォーターサーバー・引越し業者まで、まとめて無料でご相談いただけます。
   - 本文：※紹介するサービスによって、当社が紹介料を受け取る場合があります。
   - 本文：▼ 引越しの無料相談フォーム（2分ほどで送れます）
   - URL だけの行：〈URL〉?src=n3107470e7243 （貼ったあと Enter で、リンクのカードになるか確かめる）
3. 下書き保存して止まり、社長に画面を見せる

### C. 終わったら
- ウェブアプリの URL を社長に渡す（社長が Claude Code に貼って、ほかの引越し記事にも入れます。記事ごとに `?src=記事ID` を付けるので、どの記事から相談が来たか分かります）
- コードを直したくなったら：Apps Script で直して保存 →「デプロイ」→「デプロイを管理」→ 鉛筆 → バージョン「新しいバージョン」→ デプロイ（URL は変わりません）

## うまくいかないとき
| 症状 | 直し方 |
|---|---|
| URL を開くと「ファイル moving-form が見つかりません」 | HTML ファイルの名前が moving-form になっているか（moving-form.html と表示されれば正しい） |
| 送信しても行が増えない | スプレッドシートから開いた Apps Script か（拡張機能 → Apps Script で作ったもの）。別に作ったプロジェクトだと保存先がない |
| 「承認が必要です」が毎回出る | 実行ユーザーが「自分」になっているか |
| メールが来ない | NOTIFY_TO のアドレス。example.com のままだと送らない設定 |

---

## 【コード1】コード.gs（gas/consult-form-receiver.gs）

```javascript
/**
 * 相談フォームの受信用 Google Apps Script（MEO 無料相談・引越しの相談の2つを1本で受ける）
 * 相談をスプレッドシートのフォーム別のシートに1行ずつ保存し、メールで通知します。
 * フォーム本体：meo/index.html（form=meo）、moving-form/index.html（form=moving）
 *
 * 使い方：
 *  1. 保存先のスプレッドシートを新しく作り → 拡張機能 → Apps Script を開く
 *  2. このファイルの内容を貼り付け、NOTIFY_TO を通知先メールに変更
 *  3. エディタ上部の関数選択で testNotify を選んで実行 → 承認 → テスト通知が届けばOK
 *  4. デプロイ → 新しいデプロイ → 種類「ウェブアプリ」／実行ユーザー：自分／アクセスできるユーザー：全員
 *  5. 発行された URL を、2つのフォームの CONFIG.endpoint に設定（同じ URL でよい）
 *
 * 引越しのフォームをこの Apps Script で公開する（サーバー不要。10/1〜）：
 *  - Apps Script の「ファイル +」→ HTML で「moving-form」という名前のファイルを作り、moving-form/index.html の中身を全部貼る
 *  - デプロイした URL（…/exec）がそのままフォームの URL になる。note の記事には「URL?src=記事ID」で入れる
 *
 * 列 src には、どの note 記事から来たか（例：N007）が入る。
 *  - MEO：営業部のマーケ担当が反響リードとして取り込む
 *  - 引越し：引越しチームの相談受付（モモ）が callcenter/moving/out/inquiries.csv に記録する
 */
var NOTIFY_TO = 'notify@example.com'; // ★要変更（空にするとメール通知なし）

var FORMS = {
  meo: {
    sheet: 'MEO相談', subject: '【MEO相談】', title: 'shop',
    columns: ['submitted_at', 'shop', 'industry', 'area', 'gmap', 'topics', 'note', 'name', 'role', 'tel', 'email', 'contact', 'src', 'landing_url', 'referrer'],
  },
  moving: {
    sheet: '引越し相談', subject: '【引越し相談】', title: 'name',
    columns: ['submitted_at', 'topics', 'when', 'area', 'from', 'note', 'name', 'tel', 'email', 'contact', 'src', 'landing_url', 'referrer'],
  },
};

// フォームのページを出す（引越し相談）。?src=N019 のように記事IDを受け取る
function doGet(e) {
  var src = String((e && e.parameter && e.parameter.src) || '').replace(/[^A-Za-z0-9_-]/g, '').slice(0, 20);
  var html = HtmlService.createHtmlOutputFromFile('moving-form').getContent()
    .replace('/*__GAS_SRC__*/null', JSON.stringify(src));
  return HtmlService.createHtmlOutput(html)
    .setTitle('引越しの無料相談｜まるっと窓口')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

// doGet で出したフォームから google.script.run で呼ばれる
function submitForm(p) {
  if (!p || p.website) return { ok: true }; // bot
  save_(p);
  return { ok: true };
}

function doPost(e) {
  if (!e || !e.parameter) {
    testNotify();
    return json_({ ok: true, test: true });
  }
  if (e.parameter.website) return json_({ ok: true }); // bot
  save_(e.parameter);
  return json_({ ok: true });
}

function save_(p) {
  var f = FORMS[p.form] || FORMS.meo;

  var lock = LockService.getScriptLock();
  lock.waitLock(10000);
  var row;
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getSheetByName(f.sheet) || ss.insertSheet(f.sheet);
    if (sheet.getLastRow() === 0) sheet.appendRow(f.columns);
    var submittedAt = Utilities.formatDate(new Date(), 'Asia/Tokyo', 'yyyy-MM-dd HH:mm:ss') + ' JST';
    row = f.columns.map(function (k) {
      if (k === 'submitted_at') return submittedAt;
      var v = String(p[k] || '').slice(0, 2000);
      return /^[=+\-@]/.test(v) ? "'" + v : v; // 数式として解釈させない
    });
    sheet.appendRow(row);
  } finally {
    lock.releaseLock();
  }
  notify_(f, row);
}

function notify_(f, row) {
  if (!NOTIFY_TO || NOTIFY_TO.indexOf('example.com') > -1) return;
  var lines = f.columns.map(function (k, i) { return k + '：' + (row[i] || ''); });
  MailApp.sendEmail(NOTIFY_TO, f.subject + row[f.columns.indexOf(f.title)], lines.join('\n'));
}

function testNotify() {
  Object.keys(FORMS).forEach(function (k) {
    var f = FORMS[k];
    notify_(f, f.columns.map(function (c) { return c === f.title ? 'テスト送信' : '（テスト）'; }));
  });
}

function json_(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}
```

## 【コード2】moving-form.html（moving-form/index.html）

```html
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="robots" content="noindex">
<title>引越しの無料相談</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&family=Noto+Serif+JP:wght@700&display=swap">
<style>
/* Layout: 1列の相談フォーム。上に相談できること5つと約束、下にフォーム。引越し前の忙しい人がスマホで2分で送れる長さ */
:root{
  --bg:#F5F6F8; --surface:#FFFFFF; --ink:#1C2230; --body:#3A4540; --muted:#66716B; --line:#DDE2DC;
  --accent:#2A5CA8; --accent-ink:#FFFFFF; --soft:#E8EEF8; --err:#B3261E;
  --f-body:"Noto Sans JP","Hiragino Kaku Gothic ProN","Yu Gothic",system-ui,sans-serif;
  --f-title:"Noto Serif JP","Hiragino Mincho ProN","Yu Mincho",serif;
}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){
  --bg:#131815; --surface:#1B211E; --ink:#E9EEEB; --body:#CBD3CE; --muted:#96A19B; --line:#2E3632;
  --accent:#9DBAF0; --accent-ink:#0F1A15; --soft:#1E2638; --err:#F2B8B5; color-scheme:dark}}
:root[data-theme="dark"]{
  --bg:#131815; --surface:#1B211E; --ink:#E9EEEB; --body:#CBD3CE; --muted:#96A19B; --line:#2E3632;
  --accent:#9DBAF0; --accent-ink:#0F1A15; --soft:#1E2638; --err:#F2B8B5; color-scheme:dark}
*{box-sizing:border-box}
html,body{margin:0}
body{background:var(--bg);color:var(--body);font-family:var(--f-body);font-size:16px;line-height:1.8;padding-inline:16px;padding-block:32px 56px}
.wrap{max-width:640px;margin:0 auto;display:grid;gap:24px}
.eyebrow{font-size:13px;font-weight:700;color:var(--accent);letter-spacing:.08em;margin:0}
h1{font-family:var(--f-title);font-size:clamp(24px,5.4vw,32px);line-height:1.45;color:var(--ink);margin:6px 0 10px;text-wrap:balance}
.lead{margin:0}
.promise{list-style:none;margin:0;padding:0;display:grid;gap:8px}
.promise li{display:flex;gap:10px;align-items:baseline;background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:10px 14px}
.promise b{color:var(--ink)}
.promise span.n{flex:none;font-weight:700;color:var(--accent)}
form{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:24px clamp(16px,4vw,32px);display:grid;gap:20px}
.f{display:grid;gap:6px;min-width:0}
.f label,.f legend{font-weight:700;color:var(--ink);font-size:15px}
.req,.opt{font-size:11.5px;font-weight:700;border-radius:4px;padding:1px 6px;margin-left:6px;vertical-align:2px}
.req{background:var(--accent);color:var(--accent-ink)} .opt{background:var(--soft);color:var(--muted)}
.hint{font-size:13px;color:var(--muted);margin:0}
input[type=text],input[type=tel],input[type=email],input[type=url],select,textarea{width:100%;font:inherit;color:var(--ink);background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:10px 12px}
textarea{min-height:110px;resize:vertical}
input:focus,select:focus,textarea:focus{outline:2px solid var(--accent);outline-offset:1px;border-color:var(--accent)}
fieldset{border:0;margin:0;padding:0;display:grid;gap:6px;min-width:0}
.checks{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:6px}
.checks label,.radio label{font-weight:400;display:flex;gap:8px;align-items:flex-start;color:var(--body);background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:8px 10px;cursor:pointer}
.radio{display:flex;flex-wrap:wrap;gap:6px}
.row2{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media (max-width:520px){.row2{grid-template-columns:1fr}}
.privacy{font-size:13px;color:var(--muted);background:var(--bg);border-radius:8px;padding:10px 12px;margin:0}
.agree{display:flex;gap:8px;align-items:flex-start;font-weight:500;color:var(--ink)}
button[type=submit]{font:inherit;font-weight:700;font-size:17px;background:var(--accent);color:var(--accent-ink);border:0;border-radius:999px;padding:14px 20px;cursor:pointer}
button[type=submit]:disabled{opacity:.6;cursor:default}
button:focus-visible{outline:3px solid var(--ink);outline-offset:2px}
.error{color:var(--err);font-size:14px;margin:0}
.hp{position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden}
.done{background:var(--surface);border:1px solid var(--accent);border-radius:14px;padding:28px;text-align:center}
.done h2{font-family:var(--f-title);color:var(--ink);font-size:22px;margin:0 0 8px}
.foot{font-size:12.5px;color:var(--muted);text-align:center}
</style>
</head>
<body>
<main class="wrap">
  <header>
    <p class="eyebrow">引越し・新生活</p>
    <h1>引越しのこと、まとめてご相談ください</h1>
    <p class="lead">お部屋探しから、電気・ガス・水道、インターネット、ウォーターサーバー、引越し業者まで。必要なものだけ選んでください。</p>
  </header>

  <ul class="promise" aria-label="相談できること">
    <li><span class="n">1</span><span><b>お部屋探し</b>　仲介手数料を無料にできる物件があります<span id="c-fee"></span></span></li>
    <li><span class="n">2</span><span><b>電気・ガス・水道</b>　引越し先の手続きをまとめてご案内</span></li>
    <li><span class="n">3</span><span><b>インターネット回線</b>　引越し先で使える回線をご紹介</span></li>
    <li><span class="n">4</span><span><b>ウォーターサーバー</b>　新居に合わせてご紹介</span></li>
    <li><span class="n">5</span><span><b>引越し業者（関東）</b>　業者をご紹介</span></li>
  </ul>
  <p class="hint" id="partner"></p>
  <p class="hint" id="disclose"></p>

  <form id="form" novalidate>
    <fieldset class="f"><legend>相談したいこと<span class="req">必須</span></legend>
      <div class="checks">
        <label><input type="checkbox" name="topics" value="お部屋探し">お部屋探し（仲介手数料無料の物件）</label>
        <label><input type="checkbox" name="topics" value="電気・ガス・水道">電気・ガス・水道</label>
        <label><input type="checkbox" name="topics" value="インターネット回線">インターネット回線</label>
        <label><input type="checkbox" name="topics" value="ウォーターサーバー">ウォーターサーバー</label>
        <label><input type="checkbox" name="topics" value="引越し業者">引越し業者（関東）</label>
        <label><input type="checkbox" name="topics" value="まだ決めていない">何から始めればいいか相談したい</label>
      </div>
    </fieldset>
    <div class="row2">
      <div class="f"><label for="when">引越しの時期<span class="req">必須</span></label>
        <select id="when" name="when" required>
          <option value="">選んでください</option><option>1か月以内</option><option>1〜3か月後</option><option>3か月より先</option><option>まだ決まっていない</option>
        </select></div>
      <div class="f"><label for="area">引越し先のエリア<span class="req">必須</span></label><input id="area" name="area" type="text" placeholder="例：神奈川県 川崎市" required></div>
    </div>
    <div class="f"><label for="from">今のお住まいのエリア<span class="opt">任意</span></label><input id="from" name="from" type="text" placeholder="例：東京都 杉並区"></div>
    <div class="f"><label for="note">詳しく（任意）</label><textarea id="note" name="note" placeholder="例：3月に2人で引越し予定。駅から10分以内で探しています"></textarea></div>
    <div class="f"><label for="name">お名前<span class="req">必須</span></label><input id="name" name="name" type="text" autocomplete="name" required></div>
    <div class="row2">
      <div class="f"><label for="tel">電話番号</label><input id="tel" name="tel" type="tel" autocomplete="tel" inputmode="tel"></div>
      <div class="f"><label for="email">メールアドレス</label><input id="email" name="email" type="email" autocomplete="email" inputmode="email"></div>
    </div>
    <p class="hint">電話番号かメールアドレスの、どちらか1つは入れてください。</p>
    <fieldset class="f"><legend>ご希望の連絡方法</legend>
      <div class="radio">
        <label><input type="radio" name="contact" value="メール" checked>メール</label>
        <label><input type="radio" name="contact" value="電話">電話</label>
        <label><input type="radio" name="contact" value="どちらでも">どちらでも</label>
      </div>
    </fieldset>
    <div class="hp" aria-hidden="true"><label for="website">空欄のまま</label><input id="website" name="website" type="text" tabindex="-1" autocomplete="off"></div>
    <input type="hidden" name="form" value="moving"><input type="hidden" name="src" id="src"><input type="hidden" name="landing_url" id="landing_url"><input type="hidden" name="referrer" id="referrer">
    <p class="privacy" id="privacy"></p>
    <label class="agree"><input type="checkbox" id="agree" required>個人情報の取り扱いに同意して送信します</label>
    <p class="error" id="error" hidden></p>
    <button type="submit" id="submit">相談する</button>
  </form>

  <section class="done" id="done" hidden aria-live="polite">
    <h2>送信しました</h2>
    <p id="done-msg">内容を確認して、ご希望の方法でご連絡します。</p>
  </section>

  <p class="foot" id="foot"></p>
</main>

<script>
/* ★設定（公開前に書き換える）*/
var GAS_SRC = /*__GAS_SRC__*/null;  // Apps Script（doGet）で開いたとき、記事ID（?src=）がここに入る
var CONFIG = {
  endpoint: '',                       // 静的ページで使うときだけ：gas/consult-form-receiver.gs の URL。Apps Script の中で開くときは不要（自動で送る）
  company: 'まるっと窓口',
  privacyUrl: '',                     // 会社の HP・プライバシーポリシーへのリンクは載せない（10/1 社長）
  feeNote: '条件は物件によって違うため、ご相談のときにご説明します',
  partner: '★要変更 提携先の不動産会社名・宅建業の免許番号',
  disclose: '★要変更（紹介料を受け取る場合の書き方。例：ご紹介するサービスによって、当社が紹介料を受け取る場合があります）',
  replyDays: '2営業日以内'            // ★要変更 返信の目安
};

(function () {
  var $ = function (id) { return document.getElementById(id); };
  var params = new URLSearchParams(location.search);
  $('src').value = (GAS_SRC !== null ? GAS_SRC : params.get('src') || params.get('utm_content')) || '';
  $('landing_url').value = location.href.split('#')[0];
  $('referrer').value = document.referrer || '';
  $('c-fee').textContent = CONFIG.feeNote.indexOf('★') === 0 ? '' : '（' + CONFIG.feeNote + '）';
  $('partner').textContent = 'お部屋探しは、提携する不動産会社をご紹介します。物件のご案内・契約・仲介は提携先が行います' + (CONFIG.partner.indexOf('★') === 0 ? '。' : '（' + CONFIG.partner + '）。');
  $('disclose').textContent = CONFIG.disclose.indexOf('★') === 0 ? 'ご紹介するサービスによって、当社が紹介料を受け取る場合があります。' : CONFIG.disclose;
  $('privacy').innerHTML = 'いただいた情報は、このご相談への連絡と対応のためだけに使い、' +
    'ご本人の同意なく第三者に渡しません。運営：' + CONFIG.company.replace(/[<>&]/g, '') +
    (CONFIG.privacyUrl ? '　<a href="' + CONFIG.privacyUrl.replace(/"/g, '') + '" target="_blank" rel="noopener">プライバシーポリシー</a>' : '');
  $('foot').textContent = '© ' + CONFIG.company.replace(/^★要変更\s*/, '');

  var form = $('form');
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var err = [];
    if (!form.querySelectorAll('input[name=topics]:checked').length) err.push('相談したいこと');
    ['when', 'area', 'name'].forEach(function (id) { if (!$(id).value.trim()) err.push(form.querySelector('label[for="' + id + '"]').firstChild.textContent); });
    if (!$('tel').value.trim() && !$('email').value.trim()) err.push('電話番号かメールアドレス');
    if ($('email').value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test($('email').value)) err.push('メールアドレスの形');
    if (!$('agree').checked) err.push('個人情報の取り扱いへの同意');
    if (err.length) { $('error').textContent = '入力をご確認ください：' + err.join('・'); $('error').hidden = false; return; }
    $('error').hidden = true;

    var data = new FormData(form);
    data.set('topics', data.getAll('topics').join('、'));
    var finish = function (demo) {
      form.hidden = true; $('done').hidden = false;
      $('done-msg').textContent = demo
        ? '（確認用の画面のため、実際には送信されていません）'
        : '内容を確認して、' + CONFIG.replyDays + 'にご希望の方法でご連絡します。';
      window.scrollTo({ top: 0, behavior: 'smooth' });
    };
    var fail = function () {
      $('submit').disabled = false; $('submit').textContent = '相談する';
      $('error').textContent = '送信できませんでした。通信の状態を確かめて、もう一度お試しください。'; $('error').hidden = false;
    };
    var gas = window.google && google.script && google.script.run;
    if (!gas && !CONFIG.endpoint) { finish(true); return; }
    $('submit').disabled = true; $('submit').textContent = '送信しています…';
    if (gas) {
      var obj = {}; data.forEach(function (v, k) { obj[k] = v; });
      google.script.run.withSuccessHandler(function () { finish(false); }).withFailureHandler(fail).submitForm(obj);
      return;
    }
    fetch(CONFIG.endpoint, { method: 'POST', body: new URLSearchParams(data), mode: 'no-cors' })
      .then(function () { finish(false); })
      .catch(fail);
  });
})();
</script>
</body>
</html>
```
