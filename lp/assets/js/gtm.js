/* Google タグマネージャーの読み込み（config.js の gtmId に「GTM-」から始まるIDを入れると有効） */
(function () {
  var id = window.LP_CONFIG && window.LP_CONFIG.gtmId;
  window.dataLayer = window.dataLayer || [];
  if (!id || !/^GTM-[A-Z0-9]+$/.test(id)) return;
  window.dataLayer.push({ 'gtm.start': new Date().getTime(), event: 'gtm.js' });
  var s = document.createElement('script');
  s.async = true;
  s.src = 'https://www.googletagmanager.com/gtm.js?id=' + id;
  document.head.appendChild(s);
})();
