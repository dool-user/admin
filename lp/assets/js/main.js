(function () {
  'use strict';

  var CONFIG = window.LP_CONFIG;
  var STORAGE_KEY = 'lp_params';
  var $ = function (sel, root) { return (root || document).querySelector(sel); };
  var $$ = function (sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); };

  function safeStorage(fn, fallback) {
    try { return fn(); } catch (e) { return fallback; }
  }

  /* ------------------------------------------------------------
   * URLパラメータ
   * 広告URLの書式に合わせて、次の3状態を区別する
   *   ?callhide    → 値なしで存在 = ON
   *   ?hidemodal=  → 空の値       = OFF（テンプレート上の空欄）
   *   ?hidemodal=1 → 値あり       = ON（0 / false は OFF）
   * ---------------------------------------------------------- */
  function parseQuery(search) {
    var out = {};
    search.replace(/^\?/, '').split('&').forEach(function (pair) {
      if (!pair) return;
      var idx = pair.indexOf('=');
      var key = decodeURIComponent(idx < 0 ? pair : pair.slice(0, idx));
      var val = idx < 0 ? true : decodeURIComponent(pair.slice(idx + 1).replace(/\+/g, ' '));
      out[key] = val;
    });
    return out;
  }

  var query = parseQuery(location.search);
  // 計測系パラメータはセッション内で保持（ページ内遷移・リロード後もフォームに渡す）
  var TRACK_KEYS = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content', 'gclid', 'gbraid', 'wbraid', 'yclid', 'tel'];
  var stored = safeStorage(function () { return JSON.parse(sessionStorage.getItem(STORAGE_KEY)) || {}; }, {});
  TRACK_KEYS.forEach(function (k) {
    if (typeof query[k] === 'string' && query[k] !== '' && query[k].indexOf('{') !== 0) stored[k] = query[k];
  });
  safeStorage(function () { sessionStorage.setItem(STORAGE_KEY, JSON.stringify(stored)); });

  function flag(name) {
    var v = query[name];
    if (v === true) return true;
    if (typeof v !== 'string' || v === '') return false;
    return !/^(0|false|off|no)$/i.test(v);
  }

  var opts = {
    telMode: stored.tel === 'yakan' ? 'yakan' : 'default',
    callHide: flag('callhide'),
    mvHide: flag('mvhide'),
    modalHide: flag('hidemodal'),
    ctaOrder: typeof query.ctaorder === 'string' ? query.ctaorder : '',
  };

  /* ------------------------------------------------------------
   * 営業時間判定（通常番号のみ。夜間番号は常時受付扱い）
   * ---------------------------------------------------------- */
  function isOpenNow() {
    if (opts.telMode === 'yakan') return true;
    // 日本時間で判定
    var jst = new Date(Date.now() + (new Date().getTimezoneOffset() + 540) * 60000);
    var h = jst.getHours();
    return h >= CONFIG.businessHours.start && h < CONFIG.businessHours.end;
  }

  /* ------------------------------------------------------------
   * 電話番号・ブランド・エリア差し込み
   * ---------------------------------------------------------- */
  function applyContent() {
    var tel = CONFIG.tel[opts.telMode];
    $$('[data-tel-link]').forEach(function (a) { a.setAttribute('href', 'tel:' + tel.href); });
    $$('[data-tel-display]').forEach(function (el) { el.textContent = tel.display; });
    $$('[data-tel-label]').forEach(function (el) { el.textContent = tel.label; });

    var b = CONFIG.brand;
    $$('[data-brand-name]').forEach(function (el) { el.textContent = b.name; });
    $$('[data-brand-company]').forEach(function (el) { el.textContent = b.company; });
    $$('[data-brand-address]').forEach(function (el) { el.textContent = b.address; });
    $$('[data-brand-license]').forEach(function (el) { el.textContent = b.license; });
    $$('[data-year]').forEach(function (el) { el.textContent = new Date().getFullYear(); });

    var areaKey = document.body.getAttribute('data-area');
    var area = CONFIG.areas[areaKey];
    if (area) {
      $$('[data-area-name]').forEach(function (el) { el.textContent = area.name; });
      $$('[data-area-short]').forEach(function (el) { el.textContent = area.short; });
      $$('[data-area-utility]').forEach(function (el) { el.textContent = area.utility; });
      var list = $('[data-area-cities]');
      if (list) {
        list.innerHTML = '';
        area.cities.forEach(function (c) {
          var li = document.createElement('li');
          li.textContent = c;
          list.appendChild(li);
        });
      }
    }
  }

  /* ------------------------------------------------------------
   * 表示切替（callhide / mvhide / ctaorder）
   * ---------------------------------------------------------- */
  function applyLayout() {
    if (opts.mvHide) $$('[data-mv]').forEach(function (el) { el.classList.add('is-hidden'); });
    if (opts.callHide) $$('[data-call]').forEach(function (el) { el.classList.add('is-hidden'); });

    // ctaorder=form → フォーム優先。未指定で営業時間外なら自動でフォーム優先
    var formFirst = opts.ctaOrder === 'form' || (opts.ctaOrder !== 'tel' && !isOpenNow());
    if (formFirst) {
      $$('[data-cta-group]').forEach(function (group) {
        var form = $('[data-cta="form"]', group);
        if (form) group.insertBefore(form, group.firstChild);
      });
    }
  }

  /* ------------------------------------------------------------
   * 受付状況の表示（ボタン上）
   * 受付時間内は「ただいま受付中」、時間外はWeb申込へ誘導
   * ---------------------------------------------------------- */
  function applyStatus() {
    var els = $$('[data-open-status]');
    if (!els.length) return;
    var h = CONFIG.businessHours;
    var open = isOpenNow();
    var text;
    if (opts.callHide) {
      text = 'Webなら24時間お申し込みいただけます';
      open = true;
    } else if (opts.telMode === 'yakan') {
      text = 'ただいま夜間も受付中です';
    } else if (open) {
      text = 'ただいまお電話受付中（' + h.end + ':00まで）';
    } else {
      text = '電話は' + h.start + ':00から／Webは24時間受付中';
    }
    els.forEach(function (el) {
      el.innerHTML = '<span class="dot" aria-hidden="true"></span>';
      var span = document.createElement('span');
      span.textContent = text;
      el.appendChild(span);
      el.classList.toggle('is-closed', !open);
      el.hidden = false;
    });
  }

  /* ------------------------------------------------------------
   * 計測（GTM dataLayer）
   * ---------------------------------------------------------- */
  window.dataLayer = window.dataLayer || [];
  function track(event, params) {
    var payload = { event: event, lp_area: document.body.getAttribute('data-area'), lp_tel_mode: opts.telMode };
    for (var k in params) payload[k] = params[k];
    window.dataLayer.push(payload);
  }
  document.addEventListener('click', function (e) {
    var el = e.target.closest('[data-track]');
    if (!el) return;
    var id = el.getAttribute('data-track');
    track(id.indexOf('tel_') === 0 ? 'tel_click' : 'cta_click', { cta_id: id });
  });

  /* ------------------------------------------------------------
   * 固定CTA（MVを過ぎたら表示、フォーム表示中は隠す）
   * ---------------------------------------------------------- */
  function initFixedCta() {
    var bar = $('#fixedCta');
    var form = $('#form');
    if (!bar || !('IntersectionObserver' in window)) { if (bar) bar.classList.add('is-show'); return; }
    var pastTop = false, formVisible = false;
    function update() { bar.classList.toggle('is-show', pastTop && !formVisible); }
    var sentinel = $('[data-mv]:not(.is-hidden)') || $('.cta');
    new IntersectionObserver(function (entries) {
      pastTop = !entries[0].isIntersecting && entries[0].boundingClientRect.top < 0;
      update();
    }).observe(sentinel);
    new IntersectionObserver(function (entries) {
      formVisible = entries[0].isIntersecting;
      update();
    }, { threshold: 0.05 }).observe(form);
  }

  /* ------------------------------------------------------------
   * 離脱防止モーダル（1セッション1回）
   * PC：マウスが画面上端から出たとき / SP：45秒滞在かつ未申込
   * ---------------------------------------------------------- */
  function initModal() {
    var modal = $('#modal');
    if (!modal || opts.modalHide) return;
    var SHOWN_KEY = 'lp_modal_shown';
    if (safeStorage(function () { return sessionStorage.getItem(SHOWN_KEY); }, null)) return;
    var shown = false, lastFocus = null;

    function open(reason) {
      if (shown) return;
      var formEl = $('#entryForm');
      if (formEl && formEl.contains(document.activeElement)) return; // 入力中は出さない
      shown = true;
      safeStorage(function () { sessionStorage.setItem(SHOWN_KEY, '1'); });
      lastFocus = document.activeElement;
      modal.hidden = false;
      var close = $('.modal__close', modal);
      if (close) close.focus();
      track('modal_open', { modal_reason: reason });
    }
    function close() {
      modal.hidden = true;
      if (lastFocus && lastFocus.focus) lastFocus.focus();
    }
    $$('[data-modal-close]', modal).forEach(function (el) { el.addEventListener('click', close); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !modal.hidden) close(); });

    document.addEventListener('mouseout', function (e) {
      if (!e.relatedTarget && e.clientY <= 0) open('exit_intent');
    });
    setTimeout(function () {
      if (window.matchMedia('(max-width: 767px)').matches) open('idle');
    }, 45000);
  }

  /* ------------------------------------------------------------
   * フォーム
   * ---------------------------------------------------------- */
  var MESSAGES = {
    name: 'お名前を入力してください',
    kana: 'フリガナを全角カタカナで入力してください',
    tel: '電話番号をハイフンなしの半角数字で入力してください',
    email: 'メールアドレスの形式が正しくありません',
    zip: '郵便番号を7桁で入力してください',
    address: '引越し先の住所を入力してください',
    start_date: '利用開始日を選択してください',
    agree: '個人情報の取り扱いへの同意が必要です',
  };

  function toHalfWidth(str) {
    return str.replace(/[０-９－ー―]/g, function (s) {
      if (/[－ー―]/.test(s)) return '-';
      return String.fromCharCode(s.charCodeAt(0) - 0xFEE0);
    });
  }

  function validateField(input) {
    var name = input.name;
    if (!MESSAGES[name]) return true;
    if (name === 'tel') input.value = toHalfWidth(input.value).replace(/[-\s]/g, '');
    if (name === 'zip') input.value = toHalfWidth(input.value).trim();
    var ok = input.checkValidity();
    input.classList.toggle('is-invalid', !ok);
    var err = $('[data-error-for="' + name + '"]');
    if (err) err.textContent = ok ? '' : MESSAGES[name];
    return ok;
  }

  function lookupZip() {
    var zipInput = $('#f-zip');
    var addr = $('#f-address');
    var zip = toHalfWidth(zipInput.value).replace(/\D/g, '');
    if (zip.length !== 7) { validateField(zipInput); return; }
    var cb = 'zipcb_' + Date.now();
    var script = document.createElement('script');
    window[cb] = function (res) {
      delete window[cb];
      script.remove();
      if (res && res.results && res.results[0]) {
        var r = res.results[0];
        addr.value = r.address1 + r.address2 + r.address3;
        addr.focus();
        validateField(addr);
      } else {
        var err = $('[data-error-for="zip"]');
        if (err) err.textContent = '該当する住所が見つかりませんでした';
      }
    };
    script.onerror = function () {
      delete window[cb];
      script.remove();
      var err = $('[data-error-for="zip"]');
      if (err) err.textContent = '住所を自動入力できませんでした。お手数ですが直接ご入力ください';
    };
    script.src = 'https://zipcloud.ibsnet.co.jp/api/search?zipcode=' + zip + '&callback=' + cb;
    document.head.appendChild(script);
  }

  function initForm() {
    var form = $('#entryForm');
    if (!form) return;
    var status = $('#formStatus');

    // 利用開始日は今日以降
    var date = $('#f-date');
    if (date) {
      var jst = new Date(Date.now() + (new Date().getTimezoneOffset() + 540) * 60000);
      var pad = function (n) { return ('0' + n).slice(-2); };
      date.min = jst.getFullYear() + '-' + pad(jst.getMonth() + 1) + '-' + pad(jst.getDate());
    }

    // 計測用 hidden 項目
    var hidden = {
      utm_source: stored.utm_source, utm_medium: stored.utm_medium, utm_campaign: stored.utm_campaign,
      utm_term: stored.utm_term, gclid: stored.gclid || stored.gbraid || stored.wbraid,
      area: document.body.getAttribute('data-area'), landing_url: location.href, referrer: document.referrer,
    };
    Object.keys(hidden).forEach(function (k) {
      if (form.elements[k] && hidden[k]) form.elements[k].value = hidden[k];
    });

    var zipBtn = $('#zipSearch');
    if (zipBtn) zipBtn.addEventListener('click', lookupZip);

    var started = false;
    form.addEventListener('focusin', function () {
      if (!started) { started = true; track('form_start', {}); }
    });
    form.addEventListener('blur', function (e) {
      if (e.target.matches('input, textarea')) validateField(e.target);
    }, true);
    form.addEventListener('change', function (e) {
      if (e.target.name === 'agree') validateField(e.target);
    });

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      status.textContent = '';
      status.classList.remove('is-error');

      var fields = $$('input, textarea', form).filter(function (el) { return MESSAGES[el.name]; });
      var firstInvalid = null;
      fields.forEach(function (el) { if (!validateField(el) && !firstInvalid) firstInvalid = el; });
      if (firstInvalid) {
        firstInvalid.focus();
        status.textContent = '入力内容をご確認ください';
        status.classList.add('is-error');
        return;
      }
      if (form.elements.website && form.elements.website.value) return; // bot

      var data = new FormData(form);
      var services = data.getAll('services').join('、');
      data.delete('services');
      data.append('services', services);
      data.append('tel_mode', opts.telMode);
      data.append('submitted_at', new Date().toISOString());

      var btn = $('button[type="submit"]', form);
      btn.disabled = true;
      $('.btn__main', btn).textContent = '送信中…';

      function done() {
        track('generate_lead', { form_id: 'entry' });
        location.href = CONFIG.thanksUrl;
      }

      if (!CONFIG.formEndpoint) {
        // デモモード：送信先未設定
        console.info('[LP] formEndpoint 未設定のためデモ送信:', Object.fromEntries(data.entries()));
        setTimeout(done, 400);
        return;
      }

      fetch(CONFIG.formEndpoint, { method: 'POST', body: new URLSearchParams(data) })
        .then(function (res) {
          if (!res.ok && res.type !== 'opaque') throw new Error('HTTP ' + res.status);
          done();
        })
        .catch(function () {
          btn.disabled = false;
          $('.btn__main', btn).textContent = 'この内容で申し込む';
          status.textContent = '送信に失敗しました。時間をおいて再度お試しいただくか、お電話でお申し込みください。';
          status.classList.add('is-error');
        });
    });
  }

  applyContent();
  applyLayout();
  applyStatus();
  initFixedCta();
  initModal();
  initForm();
})();
