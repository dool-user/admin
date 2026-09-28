/**
 * 店舗リスト受信用 Google Apps Script
 * leadgen（食べログ新規開店リスト）の結果をスプレッドシートに追記し、件数を Slack に通知します。
 *
 * 使い方：
 *  1. 保存先のスプレッドシートを開き → 拡張機能 → Apps Script を開いて、このファイルの内容を貼り付け
 *  2. プロジェクトの設定（歯車）→ スクリプト プロパティ に次を追加
 *       LEADGEN_TOKEN     … 推測されにくい文字列（例：ランダムな32文字）。第三者の書き込みを防ぐ合言葉
 *       SLACK_WEBHOOK_URL … Slack に通知する場合のみ（https://hooks.slack.com/services/…）
 *  3. デプロイ → 新しいデプロイ → 種類「ウェブアプリ」／実行ユーザー：自分／アクセスできるユーザー：全員
 *  4. 発行された URL の末尾に ?token=<LEADGEN_TOKEN の値> を付けたものを、
 *     GitHub の Settings → Secrets and variables → Actions に LEADGEN_WEBHOOK_URL として登録
 */
var SHEET_NAME = '食べログ新規開店';

function doPost(e) {
  var props = PropertiesService.getScriptProperties();
  var token = props.getProperty('LEADGEN_TOKEN');
  if (!token || !e || !e.parameter || e.parameter.token !== token) {
    return json_({ ok: false, error: 'invalid token' });
  }
  var body = JSON.parse(e.postData.contents);
  var columns = body.columns || [];
  var rows = body.rows || [];

  var lock = LockService.getScriptLock();
  lock.waitLock(30000);
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getSheetByName(SHEET_NAME) || ss.insertSheet(SHEET_NAME);
    if (sheet.getLastRow() === 0) {
      sheet.appendRow(columns);
      sheet.setFrozenRows(1);
    }
    var header = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
    // 送られてきた列がシートに無ければ右端に足す
    columns.forEach(function (c) {
      if (header.indexOf(c) < 0) {
        header.push(c);
        sheet.getRange(1, header.length).setValue(c);
      }
    });
    // 同じ店（URL）が既にあれば追加しない
    var urlCol = header.indexOf('URL') + 1;
    var known = {};
    if (urlCol > 0 && sheet.getLastRow() > 1) {
      sheet.getRange(2, urlCol, sheet.getLastRow() - 1, 1).getValues().forEach(function (r) { known[r[0]] = true; });
    }
    var values = rows
      .filter(function (r) { return !known[r['URL']]; })
      .map(function (r) { return header.map(function (h) { return r[h] == null ? '' : String(r[h]); }); });
    if (values.length) {
      var range = sheet.getRange(sheet.getLastRow() + 1, 1, values.length, header.length);
      range.setNumberFormat('@'); // 電話番号の先頭の0が消えないよう文字列で保存
      range.setValues(values);
    }
    notifySlack_(props, (body.title || '店舗リスト') + '：Uber Eats 未掲載の候補 ' + values.length + '件を追加しました\n' + ss.getUrl());
    return json_({ ok: true, added: values.length });
  } finally {
    lock.releaseLock();
  }
}

function notifySlack_(props, text) {
  var url = props.getProperty('SLACK_WEBHOOK_URL');
  if (!url) return;
  UrlFetchApp.fetch(url, { method: 'post', contentType: 'application/json', payload: JSON.stringify({ text: text }), muteHttpExceptions: true });
}

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}

// エディタから実行して動作確認（シートにテスト行が1行入ります）
function testReceive() {
  var token = PropertiesService.getScriptProperties().getProperty('LEADGEN_TOKEN');
  var res = doPost({
    parameter: { token: token },
    postData: { contents: JSON.stringify({ title: 'テスト', columns: ['取得元', '店名', '電話番号', 'URL'], rows: [{ '取得元': '食べログ', '店名': 'テスト店', '電話番号': '03-0000-0000', 'URL': 'https://example.com/test' }] }) },
  });
  console.log(res.getContent());
}
