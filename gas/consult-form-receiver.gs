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
