/**
 * MEO（Googleマップ集客）無料相談フォームの受信用 Google Apps Script
 * 相談をスプレッドシートに1行ずつ保存し、メールで通知します。フォーム本体は meo/index.html。
 *
 * 使い方：
 *  1. 保存先のスプレッドシートを新しく作り → 拡張機能 → Apps Script を開く
 *  2. このファイルの内容を貼り付け、NOTIFY_TO を通知先メールに変更
 *  3. エディタ上部の関数選択で testNotify を選んで実行 → 承認 → テスト通知が届けばOK
 *  4. デプロイ → 新しいデプロイ → 種類「ウェブアプリ」／実行ユーザー：自分／アクセスできるユーザー：全員
 *  5. 発行された URL を meo/index.html の CONFIG.endpoint に設定
 *
 * 列 src には、どの note 記事から来たか（例：N007）が入る。営業部のマーケ担当が反響リードとして取り込む。
 */
var NOTIFY_TO = 'notify@example.com'; // ★要変更（空にするとメール通知なし）
var SHEET_NAME = 'MEO相談';

var COLUMNS = [
  'submitted_at', 'shop', 'industry', 'area', 'gmap', 'topics', 'note', 'name', 'role', 'tel', 'email', 'contact',
  'src', 'landing_url', 'referrer',
];

function doPost(e) {
  if (!e || !e.parameter) {
    testNotify();
    return json_({ ok: true, test: true });
  }
  var p = e.parameter;
  if (p.website) return json_({ ok: true }); // bot

  var lock = LockService.getScriptLock();
  lock.waitLock(10000);
  var row;
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getSheetByName(SHEET_NAME) || ss.insertSheet(SHEET_NAME);
    if (sheet.getLastRow() === 0) sheet.appendRow(COLUMNS);
    var submittedAt = Utilities.formatDate(new Date(), 'Asia/Tokyo', 'yyyy-MM-dd HH:mm:ss') + ' JST';
    row = COLUMNS.map(function (k) {
      if (k === 'submitted_at') return submittedAt;
      var v = String(p[k] || '').slice(0, 2000);
      return /^[=+\-@]/.test(v) ? "'" + v : v; // 数式として解釈させない
    });
    sheet.appendRow(row);
  } finally {
    lock.releaseLock();
  }
  notify_(row);
  return json_({ ok: true });
}

function notify_(row) {
  if (!NOTIFY_TO || NOTIFY_TO.indexOf('example.com') > -1) return;
  var lines = COLUMNS.map(function (k, i) { return k + '：' + (row[i] || ''); });
  var shop = row[COLUMNS.indexOf('shop')];
  MailApp.sendEmail(NOTIFY_TO, '【MEO相談】' + shop, lines.join('\n'));
}

function testNotify() {
  notify_(COLUMNS.map(function (k) { return k === 'shop' ? 'テスト送信の店' : '（テスト）'; }));
}

function json_(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}
