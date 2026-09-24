(function () {
  'use strict';

  var loadedAt = Date.now();
  window.dataLayer = window.dataLayer || [];
  function track(ev) {
    window.dataLayer.push({ event: ev });
    if (typeof window.gtag === 'function') window.gtag('event', ev);
  }

  // --- SPメニュー ---
  var menuBtn = document.getElementById('menuBtn');
  var gnav = document.getElementById('gnav');
  if (menuBtn && gnav) {
    menuBtn.addEventListener('click', function () {
      var open = gnav.classList.toggle('is-open');
      menuBtn.setAttribute('aria-expanded', open);
    });
    gnav.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () {
        gnav.classList.remove('is-open');
        menuBtn.setAttribute('aria-expanded', 'false');
      });
    });
  }

  // --- 料金タブ ---
  var tabBtns = document.querySelectorAll('.tabs__btn');
  tabBtns.forEach(function (btn) {
    btn.addEventListener('click', function () {
      tabBtns.forEach(function (b) {
        b.classList.toggle('is-active', b === btn);
        b.setAttribute('aria-selected', b === btn);
      });
      document.querySelectorAll('.tabs__panel').forEach(function (p) {
        p.classList.toggle('is-active', p.id === 'tab-' + btn.dataset.tab);
      });
    });
  });

  // --- 電話タップ計測（GTMで「tel_click」をコンバージョン登録） ---
  document.querySelectorAll('[data-track="tel"]').forEach(function (a) {
    a.addEventListener('click', function () { track('tel_click'); });
  });

  // --- SP固定CTA（FV通過後に表示、フォーム表示中は隠す） ---
  var fixedCta = document.getElementById('fixedCta');
  var hero = document.querySelector('.hero');
  var apply = document.getElementById('apply');
  if (fixedCta && hero && apply && 'IntersectionObserver' in window) {
    var heroVisible = true, applyVisible = false;
    var updateCta = function () { fixedCta.classList.toggle('is-show', !heroVisible && !applyVisible); };
    new IntersectionObserver(function (e) { heroVisible = e[0].isIntersecting; updateCta(); }).observe(hero);
    new IntersectionObserver(function (e) { applyVisible = e[0].isIntersecting; updateCta(); }).observe(apply);
  }

  // --- 送信完了（サンクス表示）時のコンバージョン ---
  var done = document.getElementById('formDone');
  if (done && done.dataset.sent) {
    track('generate_lead');
    done.scrollIntoView({ block: 'center' });
    // リロードで二重計測しないようURLから ?sent を除去
    if (window.history.replaceState) window.history.replaceState(null, '', window.location.pathname + '#apply');
  }
  // Contact Form 7 使用時
  document.addEventListener('wpcf7mailsent', function () { track('generate_lead'); });

  // --- 郵便番号→住所自動入力（zipcloud API） ---
  var zip = document.getElementById('f-zip');
  var addr = document.getElementById('f-addr');
  if (zip && addr) {
    zip.addEventListener('input', function () {
      var v = zip.value.replace(/[^0-9]/g, '');
      if (v.length !== 7 || addr.value) return;
      fetch('https://zipcloud.ibsnet.co.jp/api/search?zipcode=' + v)
        .then(function (r) { return r.json(); })
        .then(function (d) {
          if (d.results && d.results[0] && !addr.value) {
            var r = d.results[0];
            addr.value = r.address1 + r.address2 + r.address3;
          }
        })
        .catch(function () {});
    });
  }

  // --- 内蔵フォーム: 入力チェック後に送信 ---
  var form = document.getElementById('applyForm');
  if (!form) return;
  var errorEl = document.getElementById('formError');
  var ref = form.querySelector('[name=hn_ref]');
  if (ref) ref.value = document.referrer ? document.referrer + ' → ' + location.href : location.href;

  form.addEventListener('submit', function (ev) {
    var invalid = [];
    form.querySelectorAll('[required]').forEach(function (el) {
      var ok = el.type === 'checkbox' ? el.checked : el.checkValidity() && el.value.trim() !== '';
      el.classList.toggle('is-invalid', !ok);
      if (!ok) invalid.push(el);
    });
    if (invalid.length) {
      ev.preventDefault();
      errorEl.textContent = '未入力または形式に誤りのある項目があります。';
      errorEl.hidden = false;
      invalid[0].focus();
      return;
    }
    form.querySelector('[name=hn_elapsed]').value = Date.now() - loadedAt;
    var btn = form.querySelector('button[type=submit]');
    // 二重送信防止（送信自体は止めない）
    setTimeout(function () { btn.disabled = true; btn.textContent = '送信中…'; }, 0);
  });
})();
