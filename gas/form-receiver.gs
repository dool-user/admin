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
 *  6. Meta 広告の計測（Conversions API）を使う場合：スクリプト プロパティに
 *     META_PIXEL_ID（ピクセルID）と META_CAPI_TOKEN（アクセストークン）を追加。
 *     テスト中だけ META_TEST_EVENT_CODE（イベントマネージャの「テストイベント」のコード）も追加し、
 *     testMetaLead を実行 → テストイベント画面に Lead が出ればOK（確認後は META_TEST_EVENT_CODE を削除）
 */
var NOTIFY_TO = 'notify@example.com'; // ★要変更（空にするとメール通知なし）
var SHEET_NAME = '申込一覧';
// 保存先スプレッドシート（URL の /d/ と /edit の間）。空ならこのスクリプトを開いたスプレッドシートに保存
var SPREADSHEET_ID = '1MMPZ61RnZl-YzGezagqpquMz_jqVpj-hZSnM7SzDr6E';
// Meta Graph API のバージョン（古くなったら Meta の開発者ドキュメントで最新に更新）
var META_API_VERSION = 'v24.0';

var COLUMNS = [
  'submitted_at', 'name', 'kana', 'tel', 'email', 'zip', 'address', 'building_type', 'start_date',
  'services', 'contact_time', 'note', 'area', 'tel_mode',
  'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content', 'gclid', 'ttclid', 'landing_url', 'referrer',
  'fbclid', 'event_id', // 既存のシートと列がずれないよう、追加の列は末尾に足す
];

function doPost(e) {
  // エディタから直接実行した場合（申込データなし）はテスト通知に切り替える
  if (!e || !e.parameter) {
    console.log('doPost はフォーム送信時に動く関数です。テスト通知を送ります。');
    testNotify();
    return json_({ ok: true, test: true });
  }
  var p = e.parameter;
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
  try { sendMetaLead_(p); } catch (err) { console.error('meta', err); }

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
    (p.gclid ? 'Google広告' : p.ttclid ? 'TikTok広告' : p.fbclid ? 'Meta広告' : '不明');

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

/**
 * Meta Conversions API に Lead を送る（ブラウザのピクセルと同じ event_id で重複を除く）。
 * 電話番号・メールアドレス等は Meta の仕様どおり SHA-256 でハッシュ化してから送る。
 */
function sendMetaLead_(p) {
  var props = PropertiesService.getScriptProperties();
  var pixelId = props.getProperty('META_PIXEL_ID');
  var token = props.getProperty('META_CAPI_TOKEN');
  if (!pixelId || !token) return;

  var userData = { country: [sha256_('jp')] };
  var tel = String(p.tel || '').replace(/\D/g, '');
  if (tel) userData.ph = [sha256_(tel.charAt(0) === '0' ? '81' + tel.slice(1) : tel)]; // 国番号付き・記号なし
  var email = String(p.email || '').trim().toLowerCase();
  if (email) userData.em = [sha256_(email)];
  var zip = String(p.zip || '').replace(/\D/g, '');
  if (zip) userData.zp = [sha256_(zip)];
  if (p.fbc) userData.fbc = p.fbc; // fbc・fbp・ユーザーエージェントはハッシュ化しない
  if (p.fbp) userData.fbp = p.fbp;
  if (p.user_agent) userData.client_user_agent = p.user_agent;

  var event = {
    event_name: 'Lead',
    event_time: Math.floor(Date.now() / 1000),
    action_source: 'website',
    event_source_url: p.landing_url || undefined,
    user_data: userData,
    custom_data: { content_name: 'entry_form' },
  };
  if (p.event_id) event.event_id = p.event_id;

  var body = { data: [event] };
  var testCode = props.getProperty('META_TEST_EVENT_CODE');
  if (testCode) body.test_event_code = testCode;

  var res = UrlFetchApp.fetch('https://graph.facebook.com/' + META_API_VERSION + '/' + pixelId + '/events?access_token=' + encodeURIComponent(token), {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify(body),
    muteHttpExceptions: true,
  });
  if (res.getResponseCode() !== 200) throw new Error('Meta ' + res.getResponseCode() + ': ' + res.getContentText());
}

/** 設定確認用：テスト用の Lead を Meta に送る（META_TEST_EVENT_CODE を設定してから実行） */
function testMetaLead() {
  if (!PropertiesService.getScriptProperties().getProperty('META_TEST_EVENT_CODE')) {
    throw new Error('先にスクリプト プロパティ META_TEST_EVENT_CODE を設定してください（本番の計測に混ざらないように）');
  }
  sendMetaLead_({ tel: '09000000000', email: 'test@example.com', zip: '1710022', event_id: 'test_' + Date.now(), landing_url: 'https://denki-kaitsu-support.com/tokyo/' });
  console.log('送信しました。イベントマネージャの「テストイベント」を確認してください。');
}

function sha256_(s) {
  return Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, s, Utilities.Charset.UTF_8)
    .map(function (b) { return ('0' + (b & 0xff).toString(16)).slice(-2); }).join('');
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
