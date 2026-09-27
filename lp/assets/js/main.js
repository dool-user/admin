(function () {
  'use strict';

  var CONFIG = window.LP_CONFIG;
  var STORAGE_KEY = 'lp_params';
  // 郵便番号データ（assets/zip/）の場所。main.js の位置から求める
  var ZIP_BASE = (document.currentScript && document.currentScript.src || '').replace(/js\/main\.js(\?.*)?$/, 'zip/') || '../assets/zip/';
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
  var TRACK_KEYS = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content', 'gclid', 'gbraid', 'wbraid', 'yclid', 'ttclid', 'fbclid', 'tel'];
  var stored = safeStorage(function () { return JSON.parse(sessionStorage.getItem(STORAGE_KEY)) || {}; }, {});
  TRACK_KEYS.forEach(function (k) {
    if (typeof query[k] === 'string' && query[k] !== '' && query[k].indexOf('{') !== 0) stored[k] = query[k];
  });
  // Meta の fbc（広告クリックの識別子）はクリックして来た時刻を含むので、来訪時刻も残す
  if (typeof query.fbclid === 'string' && query.fbclid) stored.fbclid_ts = Date.now();
  safeStorage(function () { sessionStorage.setItem(STORAGE_KEY, JSON.stringify(stored)); });

  function readCookie(name) {
    var m = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'));
    return m ? decodeURIComponent(m[1]) : '';
  }

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
    if (b.url) $$('[data-brand-url]').forEach(function (el) { el.href = b.url; el.textContent = b.url.replace(/^https?:\/\//, '').replace(/\/$/, ''); });
    $$('[data-year]').forEach(function (el) { el.textContent = new Date().getFullYear(); });

    var areaKey = document.body.getAttribute('data-area');
    var area = CONFIG.areas[areaKey];
    if (area) {
      $$('[data-area-name]').forEach(function (el) { el.textContent = area.name; });
      $$('[data-area-short]').forEach(function (el) { el.textContent = area.short; });
    }

    // 対応エリア：短縮形（東京・神奈川…）と一覧（東京都／神奈川県…）
    var prefs = CONFIG.serviceArea || [];
    $$('[data-service-area-short]').forEach(function (el) {
      el.textContent = prefs.map(function (n) { return n.replace(/[都道府県]$/, ''); }).join('・');
    });
    $$('[data-service-area]').forEach(function (list) {
      list.innerHTML = '';
      prefs.forEach(function (n) {
        var li = document.createElement('li');
        li.textContent = n;
        list.appendChild(li);
      });
    });
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
   * 1行に収めたい表示（運営者表示など）
   * はみ出すときだけ文字を少しずつ縮める（最小10px。それでも入らなければ折り返す）
   * ---------------------------------------------------------- */
  function fitLines() {
    $$('[data-fit-line]').forEach(function (el) {
      el.style.fontSize = '';
      el.classList.remove('is-wrap');
      var size = parseFloat(getComputedStyle(el).fontSize);
      while (el.scrollWidth > el.clientWidth && size > 10) {
        size -= 0.5;
        el.style.fontSize = size + 'px';
      }
      // 最小サイズでも収まらない場合は、文字を切らずに折り返す
      if (el.scrollWidth > el.clientWidth) {
        el.style.fontSize = '';
        el.classList.add('is-wrap');
      }
    });
  }
  window.addEventListener('resize', fitLines);

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
      text = 'Webなら24時間いつでも受付中';
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
    if (event === 'tel_click' && window.lpMeta) window.lpMeta.track('Contact', { content_name: params && params.cta_id });
  }
  document.addEventListener('click', function (e) {
    var el = e.target.closest('[data-track]');
    if (!el) return;
    var id = el.getAttribute('data-track');
    track(id.indexOf('tel_') === 0 ? 'tel_click' : 'cta_click', { cta_id: id });
  });

  /* ------------------------------------------------------------
   * PCで電話ボタンを押したとき、番号を大きく案内する
   * （PCでは電話アプリがなく発信できないことがあるため。発信自体はそのまま行う）
   * ---------------------------------------------------------- */
  function initTelToast() {
    var desktop = window.matchMedia('(hover: hover) and (pointer: fine)');
    var toast = null, timer = null;
    document.addEventListener('click', function (e) {
      var a = e.target.closest('[data-tel-link]');
      if (!a || !desktop.matches) return;
      var tel = CONFIG.tel[opts.telMode];
      if (!toast) {
        toast = document.createElement('div');
        toast.className = 'tel-toast';
        toast.setAttribute('role', 'status');
        toast.innerHTML = '<button type="button" aria-label="閉じる">×</button><p>こちらの番号にお電話ください</p><strong></strong><small></small>';
        toast.querySelector('button').addEventListener('click', function () { toast.hidden = true; });
        document.body.appendChild(toast);
      }
      toast.querySelector('strong').textContent = tel.display;
      toast.querySelector('small').textContent = '通話無料　' + tel.label;
      toast.hidden = false;
      clearTimeout(timer);
      timer = setTimeout(function () { toast.hidden = true; }, 8000);
    });
  }

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
   * ページを開いた直後のポップアップ（アイコンタイル型・1セッション1回）
   * ?hidemodal=1 で表示しない
   * ---------------------------------------------------------- */
  var TILE_MESSAGES = {
    power: '<span class="nw">その状況、</span><span class="nw"><em>お電話ですぐ確認</em>できます</span>',
    movein: '<span class="nw">入居日に間に合うよう、</span><span class="nw"><em>お電話で手配</em>を進めます</span>',
    unknown: '<span class="nw">手続きが済んでいるか、</span><span class="nw"><em>お電話で確認</em>できます</span>',
  };

  function initModal() {
    var modal = $('#modal');
    if (!modal || opts.modalHide) return;
    var SHOWN_KEY = 'lp_modal_shown';
    if (safeStorage(function () { return sessionStorage.getItem(SHOWN_KEY); }, null)) return;
    var dialog = $('.ep', modal);
    var res = $('#epRes');
    var lastFocus = null;

    function open() {
      var formEl = $('#entryForm');
      if (formEl && formEl.contains(document.activeElement)) return; // 入力中は出さない
      safeStorage(function () { sessionStorage.setItem(SHOWN_KEY, '1'); });
      lastFocus = document.activeElement;
      modal.hidden = false;
      fitLines();
      if (dialog) dialog.focus();
      track('popup_open', {});
    }
    function close() {
      modal.hidden = true;
      if (lastFocus && lastFocus.focus) lastFocus.focus();
    }
    $$('[data-modal-close]', modal).forEach(function (el) { el.addEventListener('click', close); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !modal.hidden) close(); });

    // タイルは1つだけ選べる。選んだ状況に合わせてボタン上の文言を変える
    $$('[data-tile]', modal).forEach(function (tile) {
      tile.addEventListener('click', function () {
        $$('[data-tile]', modal).forEach(function (t) { t.setAttribute('aria-pressed', String(t === tile)); });
        var key = tile.getAttribute('data-tile');
        if (res && TILE_MESSAGES[key]) res.innerHTML = TILE_MESSAGES[key];
        track('popup_tile_select', { tile: key });
      });
    });

    setTimeout(open, 1000);
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
    building_type: 'お住まいの種類を選択してください',
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
    // ラジオボタンは同じグループの選択肢すべてに反映する
    var targets = input.type === 'radio' && input.form ? $$('input[name="' + name + '"]', input.form) : [input];
    targets.forEach(function (el) { el.classList.toggle('is-invalid', !ok); });
    var err = $('[data-error-for="' + name + '"]');
    if (err) err.textContent = ok ? '' : MESSAGES[name];
    return ok;
  }

  // 郵便番号 → 住所。日本郵便の郵便番号データを上2桁ごとに分けて assets/zip/ に置いている
  var zipCache = {};
  function lookupZip() {
    var zipInput = $('#f-zip');
    var addr = $('#f-address');
    var err = $('[data-error-for="zip"]');
    var zip = toHalfWidth(zipInput.value).replace(/\D/g, '');
    if (zip.length !== 7) { validateField(zipInput); return; }

    var group = zip.slice(0, 2);
    var req = zipCache[group] || (zipCache[group] = fetch(ZIP_BASE + group + '.json').then(function (res) {
      if (!res.ok) throw new Error('HTTP ' + res.status);
      return res.json();
    }));
    req.then(function (data) {
      var r = data[zip.slice(2)];
      if (!r) {
        if (err) err.textContent = '該当する住所が見つかりませんでした。番号をご確認いただくか、直接ご入力ください';
        return;
      }
      if (err) err.textContent = '';
      addr.value = r.join('');
      addr.focus();
      addr.setSelectionRange(addr.value.length, addr.value.length); // 続けて番地を入力できるように
      validateField(addr);
    }).catch(function () {
      delete zipCache[group];
      if (err) err.textContent = '住所を自動入力できませんでした。お手数ですが直接ご入力ください';
    });
  }

  /* ---------- 同意リンク：プライバシーポリシーをページ内で表示 ---------- */
  function initPolicy() {
    var dlg = $('#policyDialog');
    var body = $('#pdBody');
    if (!dlg || !body || typeof dlg.showModal !== 'function') return; // 非対応ブラウザは通常のリンクで開く
    var loaded = false;

    $$('[data-policy]').forEach(function (link) {
      link.addEventListener('click', function (e) {
        e.preventDefault();
        if (loaded) { dlg.showModal(); return; }
        fetch(link.href)
          .then(function (res) { if (!res.ok) throw new Error('HTTP ' + res.status); return res.text(); })
          .then(function (html) {
            var src = new DOMParser().parseFromString(html, 'text/html').querySelector('.policy');
            if (!src) throw new Error('no content');
            var h1 = src.querySelector('h1');
            if (h1) h1.remove();
            var b = CONFIG.brand;
            src.querySelectorAll('[data-brand-company]').forEach(function (el) { el.textContent = b.company; });
            src.querySelectorAll('[data-brand-address]').forEach(function (el) { el.textContent = b.address; });
            body.innerHTML = src.innerHTML;
            loaded = true;
            dlg.showModal();
            body.parentNode.scrollTop = 0;
          })
          .catch(function () { window.location.href = link.href; });
      });
    });

    $$('[data-pd-close]', dlg).forEach(function (btn) { btn.addEventListener('click', function () { dlg.close(); }); });
    dlg.addEventListener('click', function (e) { if (e.target === dlg) dlg.close(); }); // 枠の外をクリック
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
      utm_term: stored.utm_term, utm_content: stored.utm_content, gclid: stored.gclid || stored.gbraid || stored.wbraid, ttclid: stored.ttclid,
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
      if (e.target.name === 'agree' || e.target.name === 'building_type') validateField(e.target);
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
      // Meta 計測用（Conversions API で受信側から送る情報。ピクセルの Lead と event_id で重複を除く）
      var eventId = 'lead_' + Date.now() + '_' + Math.random().toString(36).slice(2, 10);
      data.append('event_id', eventId);
      data.append('fbclid', stored.fbclid || '');
      data.append('fbp', readCookie('_fbp'));
      data.append('fbc', readCookie('_fbc') || (stored.fbclid ? 'fb.1.' + (stored.fbclid_ts || Date.now()) + '.' + stored.fbclid : ''));
      data.append('user_agent', navigator.userAgent);

      var btn = $('button[type="submit"]', form);
      btn.disabled = true;
      $('.btn__main', btn).textContent = '送信中…';

      function done() {
        track('generate_lead', { form_id: 'entry' });
        // Meta の Lead は完了ページで送る（ページ移動で送信が途切れないように）
        safeStorage(function () { sessionStorage.setItem('lp_lead_event', eventId); });
        location.href = CONFIG.thanksUrl;
      }

      if (!CONFIG.formEndpoint) {
        // デモモード：送信先未設定
        console.info('[LP] formEndpoint 未設定のためデモ送信:', Object.fromEntries(data.entries()));
        setTimeout(done, 400);
        return;
      }

      // Google Apps Script はリダイレクト後の応答をブラウザが読めない（CORS）ため、
      // no-cors で送る（受信側には届く。応答は opaque になるので成功扱いにする）
      var isGas = /^https:\/\/script\.google\.com\//.test(CONFIG.formEndpoint);
      fetch(CONFIG.formEndpoint, { method: 'POST', body: new URLSearchParams(data), mode: isGas ? 'no-cors' : 'cors' })
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
  fitLines();
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(fitLines);
  initFixedCta();
  initTelToast();
  initModal();
  initPolicy();
  initForm();
})();
