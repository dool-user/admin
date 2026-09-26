/**
 * LPフォーム受信用 Google Apps Script
 * 申込をスプレッドシートに1行ずつ保存し、メールと Slack に通知します。
 *
 * 使い方：
 *  1. 保存先のスプレッドシートを開き → 拡張機能 → Apps Script を開く
 *     （別のスプレッドシートに保存する場合は SPREADSHEET_ID を書き換える）
 *  2. このファイルの内容を貼り付け、NOTIFY_TO を通知先メールに変更
 *  3. Slack に通知する場合：プロジェクトの設定（歯車）→ スクリプト プロパティ に
 *     プロパティ SLACK_WEBHOOK_URL ／ 値 https://hooks.slack.com/services/… を追加
 *     （Webhook URL は秘密情報なので、このファイルやリポジトリには書かない）
 *     エディタ上部の関数選択で testNotify を選んで実行 → 承認 → Slack とメールにテスト通知が届けばOK
 *  4. デプロイ → 新しいデプロイ → 種類「ウェブアプリ」
 *     実行ユーザー：自分 / アクセスできるユーザー：全員
 *  5. 発行された URL を lp/assets/js/config.js の formEndpoint に設定
 */
var NOTIFY_TO = 'notify@example.com'; // ★要変更（空にするとメール通知なし）
var SHEET_NAME = '申込一覧';
// 保存先スプレッドシート（URL の /d/ と /edit の間）。空ならこのスクリプトを開いたスプレッドシートに保存
var SPREADSHEET_ID = '1MMPZ61RnZl-YzGezagqpquMz_jqVpj-hZSnM7SzDr6E';

var COLUMNS = [
  'submitted_at', 'name', 'kana', 'tel', 'email', 'zip', 'address', 'building_type', 'start_date',
  'services', 'contact_time', 'note', 'area', 'tel_mode',
  'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content', 'gclid', 'ttclid', 'landing_url', 'referrer',
];

function doPost(e) {
  var p = e.parameter || {};
  if (p.website) return json_({ ok: true }); // bot

  var row;
  var lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    var ss = book_();
    var sheet = ss.getSheetByName(SHEET_NAME) || ss.insertSheet(SHEET_NAME);
    if (sheet.getLastRow() === 0) sheet.appendRow(COLUMNS);
    // 先頭が = + - @ の値は数式として解釈されないよう ' を付ける
    sheet.appendRow(COLUMNS.map(function (k) {
      var v = String(p[k] || '');
      return /^[=+\-@]/.test(v) ? "'" + v : v;
    }));
    row = sheet.getLastRow();
  } finally {
    lock.releaseLock();
  }

  // 通知が失敗しても申込の保存は済んでいるので、エラーは記録だけして続ける
  try { notifyMail_(p); } catch (err) { console.error('mail', err); }
  try { notifySlack_(p, row); } catch (err) { console.error('slack', err); }

  return json_({ ok: true });
}

function notifyMail_(p) {
  if (!NOTIFY_TO) return;
  MailApp.sendEmail({
    to: NOTIFY_TO,
    subject: '【LP新規申込】' + (p.name || '') + ' 様（' + (p.area || '') + '）',
    body: COLUMNS.map(function (k) { return k + ': ' + (p[k] || ''); }).join('\n'),
  });
}

/**
 * Slack 通知。チャンネルには折り返しに必要な項目だけを載せ、
 * メール・住所・備考などの詳細はスプレッドシートのリンクから確認する。
 */
function notifySlack_(p, row) {
  var url = PropertiesService.getScriptProperties().getProperty('SLACK_WEBHOOK_URL');
  if (!url) return;

  var ss = book_();
  var sheet = ss.getSheetByName(SHEET_NAME);
  var link = sheet ? ss.getUrl() + '#gid=' + sheet.getSheetId() + '&range=A' + row : ss.getUrl();
  var source = [p.utm_source, p.utm_campaign].filter(Boolean).join(' / ') ||
    (p.gclid ? 'Google広告' : p.ttclid ? 'TikTok広告' : '不明');

  var fields = [
    ['お名前', (p.name || '') + ' 様'],
    ['電話番号', p.tel],
    ['エリア', p.area],
    ['建物', p.building_type],
    ['開始希望日', p.start_date],
    ['お申込み内容', p.services],
    ['連絡希望時間', p.contact_time],
    ['流入元', source],
  ].map(function (f) { return { type: 'mrkdwn', text: '*' + f[0] + '*\n' + esc_(f[1] || '—') }; });

  var payload = {
    text: '新しいお申込みがありました：' + esc_(p.name || '') + ' 様', // 通知バナー用
    blocks: [
      { type: 'header', text: { type: 'plain_text', text: '📩 新しいお申込み' } },
      { type: 'section', fields: fields },
      { type: 'actions', elements: [{ type: 'button', text: { type: 'plain_text', text: 'スプレッドシートで詳細を見る' }, url: link }] },
    ],
  };

  var res = UrlFetchApp.fetch(url, {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify(payload),
    muteHttpExceptions: true,
  });
  if (res.getResponseCode() !== 200) throw new Error('Slack ' + res.getResponseCode() + ': ' + res.getContentText());
}

/** 設定確認用：エディタから実行すると、テスト用の申込でメールと Slack に通知します（シートには保存しません） */
function testNotify() {
  var p = {
    name: 'テスト 太郎', tel: '09000000000', area: '東京都', building_type: '集合住宅',
    start_date: '2026-10-01', services: '電気,ガス', contact_time: '指定なし', utm_source: 'test',
  };
  notifyMail_(p);
  notifySlack_(p, 1);
}

// Slack の mrkdwn で特別な意味を持つ記号をエスケープ
function esc_(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function book_() {
  return SPREADSHEET_ID ? SpreadsheetApp.openById(SPREADSHEET_ID) : SpreadsheetApp.getActiveSpreadsheet();
}

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}
