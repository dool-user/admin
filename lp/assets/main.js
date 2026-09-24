(function () {
  'use strict';

  // --- SPメニュー ---
  var menuBtn = document.getElementById('menuBtn');
  var gnav = document.getElementById('gnav');
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

  // --- 料金タブ ---
  document.querySelectorAll('.tabs__btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      document.querySelectorAll('.tabs__btn').forEach(function (b) {
        b.classList.toggle('is-active', b === btn);
        b.setAttribute('aria-selected', b === btn);
      });
      document.querySelectorAll('.tabs__panel').forEach(function (p) {
        p.classList.toggle('is-active', p.id === 'tab-' + btn.dataset.tab);
      });
    });
  });

  // --- SP固定CTA（FV通過後に表示、フォーム表示中は隠す） ---
  var fixedCta = document.getElementById('fixedCta');
  var hero = document.querySelector('.hero');
  var apply = document.getElementById('apply');
  var heroVisible = true, applyVisible = false;
  function updateCta() { fixedCta.classList.toggle('is-show', !heroVisible && !applyVisible); }
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(function (e) { heroVisible = e[0].isIntersecting; updateCta(); }).observe(hero);
    new IntersectionObserver(function (e) { applyVisible = e[0].isIntersecting; updateCta(); }).observe(apply);
  }

  // --- 郵便番号→住所自動入力（zipcloud API） ---
  var zip = document.getElementById('f-zip');
  var addr = document.getElementById('f-addr');
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

  // --- フォーム送信 ---
  // 送信先を設定してください（例：Formspree / Googleフォーム / 自社API / WordPressならContact Form 7に置換）
  var FORM_ENDPOINT = '';

  var form = document.getElementById('applyForm');
  var errorEl = document.getElementById('formError');
  var done = document.getElementById('formDone');

  form.addEventListener('submit', function (ev) {
    ev.preventDefault();
    var invalid = [];
    form.querySelectorAll('[required]').forEach(function (el) {
      var ok = el.type === 'checkbox' ? el.checked : el.checkValidity() && el.value.trim() !== '';
      el.classList.toggle('is-invalid', !ok);
      if (!ok) invalid.push(el);
    });
    if (invalid.length) {
      errorEl.textContent = '未入力または形式に誤りのある項目があります。';
      errorEl.hidden = false;
      invalid[0].focus();
      return;
    }
    errorEl.hidden = true;

    var finish = function () {
      form.hidden = true;
      done.hidden = false;
      done.scrollIntoView({ behavior: 'smooth', block: 'center' });
      // コンバージョン計測（GA4 / Google広告）
      if (typeof window.gtag === 'function') window.gtag('event', 'generate_lead');
      if (Array.isArray(window.dataLayer)) window.dataLayer.push({ event: 'lp_form_submit' });
    };

    if (!FORM_ENDPOINT) { finish(); return; } // 送信先未設定時はデモ動作

    var btn = form.querySelector('button[type=submit]');
    btn.disabled = true;
    fetch(FORM_ENDPOINT, { method: 'POST', body: new FormData(form), headers: { Accept: 'application/json' } })
      .then(function (r) { if (!r.ok) throw new Error(); finish(); })
      .catch(function () {
        errorEl.textContent = '送信に失敗しました。お手数ですがお電話でお問い合わせください。';
        errorEl.hidden = false;
        btn.disabled = false;
      });
  });
})();
