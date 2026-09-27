/* Meta ピクセルの読み込み（config.js の metaPixelId に数字のIDを入れると有効）
 * - 全ページで PageView を送る
 * - 電話ボタンのタップ（Contact）は main.js、Web申込（Lead）は thanks.html から window.lpMeta.track で送る
 * - Lead はフォーム受信側（gas/form-receiver.gs）からも Conversions API で送り、同じ event_id で重複を除く
 * ※ GTM にも Meta ピクセルのタグを入れると二重計測になるので入れないこと
 */
(function () {
  var id = window.LP_CONFIG && String(window.LP_CONFIG.metaPixelId || '');
  var enabled = /^\d{5,20}$/.test(id);

  window.lpMeta = {
    enabled: enabled,
    track: function (name, params, eventId) {
      if (!enabled || !window.fbq) return;
      window.fbq('track', name, params || {}, eventId ? { eventID: eventId } : undefined);
    },
  };
  if (!enabled) return;

  /* Meta 提供のベースコード */
  !function (f, b, e, v, n, t, s) {
    if (f.fbq) return; n = f.fbq = function () { n.callMethod ? n.callMethod.apply(n, arguments) : n.queue.push(arguments); };
    if (!f._fbq) f._fbq = n; n.push = n; n.loaded = !0; n.version = '2.0'; n.queue = [];
    t = b.createElement(e); t.async = !0; t.src = v; s = b.getElementsByTagName(e)[0]; s.parentNode.insertBefore(t, s);
  }(window, document, 'script', 'https://connect.facebook.net/en_US/fbevents.js');

  window.fbq('init', id);
  window.fbq('track', 'PageView');
})();
