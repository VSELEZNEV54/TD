/* TeacherDesk · общие скрипты сайта
   Ванильный JS без библиотек. Помощники лежат в window.TD, их берут скрипты страниц. */
(function () {
  'use strict';

  var d = document;
  var w = window;
  d.documentElement.classList.add('js');

  var reduce = w.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var finePointer = w.matchMedia('(hover: hover) and (pointer: fine)').matches;
  var phone = w.matchMedia('(max-width: 720px)');
  var NB = '\u00A0';

  function $(s, c) { return (c || d).querySelector(s); }
  function $$(s, c) { return Array.prototype.slice.call((c || d).querySelectorAll(s)); }

  function fmt(n) {
    return String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, NB);
  }

  /* Плавный счетчик: expo-out, меняется только текст. */
  function count(el, from, to, dur, done) {
    if (!el) return;
    if (el._raf) cancelAnimationFrame(el._raf);
    if (reduce || from === to || !dur) { el.textContent = fmt(to); if (done) done(); return; }
    var t0 = null;
    function tick(t) {
      if (t0 === null) t0 = t;
      var p = Math.min(1, (t - t0) / dur);
      var e = p === 1 ? 1 : 1 - Math.pow(2, -10 * p);
      el.textContent = fmt(from + (to - from) * e);
      if (p < 1) { el._raf = requestAnimationFrame(tick); } else if (done) { done(); }
    }
    el._raf = requestAnimationFrame(tick);
  }

  /* Переключатель состояний: показывает i-го ребенка, остальные гасит. */
  function setSwap(el, idx) {
    if (!el) return;
    Array.prototype.forEach.call(el.children, function (c, i) {
      c.classList.toggle('is-off', i !== idx);
    });
  }

  /* Очередь шагов, которую можно остановить и запустить заново. */
  function Sequence(steps, loopAt) {
    var timers = [];
    var self = {
      running: false,
      start: function () {
        if (self.running) return;
        self.running = true;
        steps.forEach(function (s) { timers.push(setTimeout(s[1], s[0])); });
        if (loopAt) timers.push(setTimeout(function () { self.stop(); self.start(); }, loopAt));
      },
      stop: function () {
        timers.forEach(clearTimeout);
        timers = [];
        self.running = false;
      }
    };
    return self;
  }

  function whenVisible(el, onEnter, onLeave, threshold) {
    if (!el || !('IntersectionObserver' in w)) { if (el && onEnter) onEnter(); return; }
    new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { if (onEnter) onEnter(); } else if (onLeave) { onLeave(); }
      });
    }, { threshold: threshold || 0.2 }).observe(el);
  }

  /* Перезапуск CSS-анимации по классу. */
  function replay(el, cls) {
    if (!el || reduce) return;
    el.classList.remove(cls);
    void el.offsetWidth;
    el.classList.add(cls);
  }

  w.TD = {
    $: $, $$: $$, reduce: reduce, finePointer: finePointer, phone: phone, NB: NB,
    fmt: fmt, count: count, setSwap: setSwap, Sequence: Sequence, whenVisible: whenVisible, replay: replay
  };

  /* ---------- шапка ---------- */
  var hdr = $('[data-hdr]');
  if (hdr) {
    var onScroll = function () { hdr.classList.toggle('is-scrolled', w.scrollY > 12); };
    w.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }
  var menu = $('[data-menu]');
  if (menu) {
    menu.addEventListener('click', function (e) {
      if (e.target.closest('a')) menu.removeAttribute('open');
    });
    d.addEventListener('click', function (e) {
      if (menu.open && !menu.contains(e.target)) menu.removeAttribute('open');
    });
    d.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && menu.open) { menu.removeAttribute('open'); $('summary', menu).focus(); }
    });
  }

  /* меню «Решения»: открывается наведением и кликом, закрывается Esc и кликом мимо */
  $$('[data-dd]').forEach(function (dd) {
    var b = $('button', dd);
    var set = function (on) { dd.classList.toggle('is-open', on); b.setAttribute('aria-expanded', on ? 'true' : 'false'); };
    b.addEventListener('click', function () { set(!dd.classList.contains('is-open')); });
    if (finePointer) {
      dd.addEventListener('mouseenter', function () { set(true); });
      dd.addEventListener('mouseleave', function () { set(false); });
    }
    dd.addEventListener('focusout', function (e) { if (!dd.contains(e.relatedTarget)) set(false); });
    d.addEventListener('click', function (e) { if (!dd.contains(e.target)) set(false); });
    d.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && dd.classList.contains('is-open')) { set(false); b.focus(); }
    });
  });

  /* ---------- появление по скроллу, один раз ---------- */
  var reveals = $$('[data-reveal]');
  if (reduce || !('IntersectionObserver' in w)) {
    reveals.forEach(function (el) { el.classList.add('is-in'); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      var n = 0;
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        var el = e.target;
        el.style.setProperty('--i', Math.min(n++, 6));
        el.classList.add('is-in');
        io.unobserve(el);
        /* после появления убираем служебные стили, чтобы hover не наследовал задержку */
        setTimeout(function () {
          el.removeAttribute('data-reveal');
          el.classList.remove('is-in');
          el.style.removeProperty('--i');
        }, 1500);
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -6% 0px' });
    reveals.forEach(function (el) { io.observe(el); });
  }

  /* ---------- подвал: на телефоне колонки свернуты ---------- */
  var cols = $$('.ftr__col');
  if (cols.length) {
    var syncCols = function () {
      cols.forEach(function (c) {
        var s = $('summary', c);
        if (phone.matches) { c.removeAttribute('open'); s.removeAttribute('tabindex'); }
        else { c.setAttribute('open', ''); s.setAttribute('tabindex', '-1'); }
      });
    };
    syncCols();
    if (phone.addEventListener) { phone.addEventListener('change', syncCols); } else if (phone.addListener) { phone.addListener(syncCols); }
  }

  /* ---------- SEO-текст: свернут до первых абзацев (все страницы, включая главную) ---------- */
  $$('[data-seo]').forEach(function (s) {
    var b = $('[data-seo-more]', s), body = $('.seo__body', s);
    s.classList.add('is-clamped');
    if (body.scrollHeight <= body.clientHeight + 24) { s.classList.remove('is-clamped'); b.hidden = true; return; }
    b.addEventListener('click', function () {
      var open = s.classList.toggle('is-open');
      b.setAttribute('aria-expanded', open ? 'true' : 'false');
      $('span', b).textContent = open ? 'Свернуть' : 'Читать полностью';
    });
  });

  /* ---------- куки: счетчики только после «Разрешить» ----------
     Выбор хранится в localStorage. Метрику и GA подключать по событию td:analytics,
     до выбора и после «Не разрешать» код счетчиков не загружается (политика cookies, раздел 1). */
  var KEY = 'td-analytics';
  var store = function (v) {
    try { if (v === undefined) return w.localStorage.getItem(KEY); w.localStorage.setItem(KEY, v); } catch (e) { /* приватный режим */ }
    return null;
  };
  var grant = function () {
    w.TD.analytics = 'granted';
    d.documentElement.setAttribute('data-analytics', 'granted');
    d.dispatchEvent(new CustomEvent('td:analytics'));
  };
  var cbar = null;
  var showBar = function (focus) {
    if (!cbar) {
      var doc = $('.ftr__docs a[href*="cookies"]');
      var href = doc ? doc.getAttribute('href') : 'https://teacherdesk.ru/cookies';
      cbar = d.createElement('section');
      cbar.className = 'cbar';
      cbar.setAttribute('aria-label', 'Настройки аналитики');
      cbar.innerHTML = '<p class="cbar__t">Разрешить Яндекс.Метрику и' + NB + 'Google Analytics для статистики посещений и' + NB + 'переходов? <a class="tlink" href="' + href + '">О' + NB + 'данных и' + NB + 'куки</a>.</p>' +
        '<div class="cbar__act"><button class="btn btn--primary btn--sm" type="button" data-v="granted"><span>Разрешить</span></button>' +
        '<button class="btn btn--ghost btn--sm" type="button" data-v="denied"><span>Не разрешать</span></button></div>';
      d.body.appendChild(cbar);
      $$('button', cbar).forEach(function (b) {
        b.addEventListener('click', function () {
          var v = b.getAttribute('data-v');
          store(v);
          if (v === 'granted' && w.TD.analytics !== 'granted') grant();
          cbar.classList.remove('is-on');
          setTimeout(function () { cbar.hidden = true; }, reduce ? 0 : 400);
        });
      });
    }
    cbar.hidden = false;
    void cbar.offsetWidth;
    cbar.classList.add('is-on');
    if (focus) $('button', cbar).focus();
  };
  var choice = store();
  if (choice === 'granted') grant();
  else if (choice !== 'denied') setTimeout(showBar, reduce ? 0 : 1200);
  $$('[data-cbar-open]').forEach(function (b) { b.addEventListener('click', function () { showBar(true); }); });
})();
