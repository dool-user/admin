/**
 * LPフォーム受信用 Google Apps Script
 *
 * 使い方：
 *  1. Googleスプレッドシートを新規作成 → 拡張機能 → Apps Script を開く
 *  2. このファイルの内容を貼り付け、NOTIFY_TO を通知先メールに変更
 *  3. デプロイ → 新しいデプロイ → 種類「ウェブアプリ」
 *     実行ユーザー：自分 / アクセスできるユーザー：全員
 *  4. 発行された URL を assets/js/config.js の formEndpoint に設定
 */
var NOTIFY_TO = 'notify@example.com'; // ★要変更
var SHEET_NAME = '申込一覧';

var COLUMNS = [
  'submitted_at', 'name', 'kana', 'tel', 'email', 'zip', 'address', 'start_date',
  'services', 'contact_time', 'note', 'area', 'tel_mode',
  'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'gclid', 'landing_url', 'referrer',
];

function doPost(e) {
  var p = e.parameter || {};
  if (p.website) return json_({ ok: true }); // bot

  var lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getSheetByName(SHEET_NAME) || ss.insertSheet(SHEET_NAME);
    if (sheet.getLastRow() === 0) sheet.appendRow(COLUMNS);
    // 先頭が = + - @ の値は数式として解釈されないよう ' を付ける
    sheet.appendRow(COLUMNS.map(function (k) {
      var v = String(p[k] || '');
      return /^[=+\-@]/.test(v) ? "'" + v : v;
    }));
  } finally {
    lock.releaseLock();
  }

  MailApp.sendEmail({
    to: NOTIFY_TO,
    subject: '【LP新規申込】' + (p.name || '') + ' 様（' + (p.area || '') + '）',
    body: COLUMNS.map(function (k) { return k + ': ' + (p[k] || ''); }).join('\n'),
  });

  return json_({ ok: true });
}

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}
