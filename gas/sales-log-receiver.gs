/**
 * 営業部の送付管理シートへの書き込み用 Google Apps Script（10/7 社長の指示：送付した案件はスプレッドシートで管理）
 * 送信ツール（callcenter/tools/send_assist.py）と callcenter/tools/sheet_log.py が、1件ごとに JSON を POST してくる。
 * 同じ ID の行があればその行を直し、なければ下に足す（返信・アポは案件処理が後から同じ ID で入れる）。
 *
 * 使い方：
 *  1. 送付管理のスプレッドシート「営業部 送付管理（HP問い合わせフォーム）」を開く → 拡張機能 → Apps Script
 *  2. このファイルの内容を貼り付け、TOKEN を長めの合言葉（英数字20文字以上）に変える
 *  3. デプロイ → 新しいデプロイ → 種類「ウェブアプリ」／実行ユーザー：自分／アクセスできるユーザー：全員
 *  4. 発行された URL（…/exec）と TOKEN を callcenter/sender.yaml の sheet_webhook・sheet_token に入れる
 *  5. python tools/sheet_log.py --test で「テスト」の行が1行入ればOK（確かめたら行は消してよい）
 */
var TOKEN = 'change-me'; // ★要変更（sender.yaml の sheet_token と同じにする）
var SHEET = '送付管理';
var COLUMNS = ['記録日時', '送信日時', 'ID', '区分', '名称', '都道府県', '住所', '送り先URL', '件名', '状態', 'メモ',
  'リストの出典', '返信', '返信日', 'アポ日時', '担当'];

function doPost(e) {
  var p;
  try {
    p = JSON.parse((e && e.postData && e.postData.contents) || '{}');
  } catch (err) {
    return json_({ ok: false, error: 'bad json' });
  }
  if (!TOKEN || TOKEN === 'change-me' || p.token !== TOKEN) return json_({ ok: false, error: 'bad token' });
  if (!p.ID) return json_({ ok: false, error: 'no ID' });
  return json_(save_(p));
}

function save_(p) {
  var lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getSheetByName(SHEET) || ss.getSheets()[0];
    if (sheet.getLastRow() === 0) sheet.appendRow(COLUMNS);
    var head = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0].map(String);
    var idCol = head.indexOf('ID');
    var n = sheet.getLastRow();
    var at = -1;
    if (n > 1 && idCol > -1) {
      var ids = sheet.getRange(2, idCol + 1, n - 1, 1).getValues();
      for (var i = 0; i < ids.length; i++) if (String(ids[i][0]) === String(p.ID)) { at = i + 2; break; }
    }
    var now = Utilities.formatDate(new Date(), 'Asia/Tokyo', 'yyyy-MM-dd HH:mm');
    var old = at > 0 ? sheet.getRange(at, 1, 1, head.length).getValues()[0] : head.map(function () { return ''; });
    var row = head.map(function (k, i) {
      if (k === '記録日時') return now;
      if (!(k in p) || p[k] === '' || p[k] === null) return old[i]; // 送られてこない欄は前の値のまま（人が書いた返信などを消さない）
      var v = String(p[k]).slice(0, 2000);
      return /^[=+\-@]/.test(v) ? "'" + v : v; // 数式として解釈させない
    });
    if (at > 0) sheet.getRange(at, 1, 1, row.length).setValues([row]);
    else sheet.appendRow(row);
    return { ok: true, row: at > 0 ? at : sheet.getLastRow(), updated: at > 0 };
  } finally {
    lock.releaseLock();
  }
}

function json_(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}
