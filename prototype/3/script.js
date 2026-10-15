/* TeacherDesk · концепция 3 «Конструктор»
   Ванильный JS: рост деталей знака в секции, липкие слои, появления, живые наклейки интерфейса. */
(function () {
  'use strict';

  var doc = document;
  var root = doc.documentElement;
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)');
  var desktop = window.matchMedia('(min-width: 1100px)');
  var phone = window.matchMedia('(max-width: 719px)');
  var $ = function (s, c) { return (c || doc).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || doc).querySelectorAll(s)); };
  var hasIO = 'IntersectionObserver' in window;
  var hasSticky = !!(window.CSS && CSS.supports && CSS.supports('position', 'sticky'));
  var clamp = function (v) { return v < 0 ? 0 : v > 1 ? 1 : v; };

  /* ---------- Общий кадр прокрутки и пересчет размеров ---------- */
  var onScroll = [];
  var onMeasure = [];
  var scrollRaf = 0;
  var measureRaf = 0;
  function runScroll() { scrollRaf = 0; onScroll.forEach(function (fn) { fn(); }); }
  function runMeasure() { measureRaf = 0; onMeasure.forEach(function (fn) { fn(); }); }
  function queueMeasure() { cancelAnimationFrame(measureRaf); measureRaf = requestAnimationFrame(runMeasure); }

  /* ---------- Таймеры, которые можно разом отменить ---------- */
  function Timeline() { this.ids = []; }
  Timeline.prototype.at = function (ms, fn) { this.ids.push(setTimeout(fn, ms)); return this; };
  Timeline.prototype.clear = function () { this.ids.forEach(clearTimeout); this.ids = []; };

  /* Запускает демо, пока блок на экране, и останавливает, когда он ушел */
  function whileVisible(el, start, stop) {
    if (!el) return;
    if (!hasIO) { start(); return; }
    var on = false;
    var seen = false;
    var slab = el.closest('.slab');
    function sync() {
      var want = seen && !(slab && slab.classList.contains('is-covered'));
      if (want && !on) { on = true; start(); }
      else if (!want && on) { on = false; stop(); }
    }
    new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { seen = e.isIntersecting; });
      sync();
    }, { threshold: 0.35 }).observe(el);
    if (slab) slab.addEventListener('cover', sync);
  }

  /* ---------- 1. Появление по скроллу, один раз ---------- */
  function initReveal() {
    var items = $$('[data-reveal], [data-reveal-tee], [data-clock]');
    function show(el) {
      el.classList.add('is-in');
      var d = parseInt(el.style.getPropertyValue('--d'), 10) || 0;
      setTimeout(function () { el.classList.add('is-done'); }, d + 950);
    }
    if (!hasIO || reduce.matches) { items.forEach(show); return; }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        io.unobserve(e.target);
        show(e.target);
      });
    }, { rootMargin: '0px 0px -12% 0px', threshold: 0.12 });
    items.forEach(function (el) { io.observe(el); });
  }

  /* ---------- 2. Счетчики фактов ---------- */
  function countTo(el, to, ms, format) {
    var from = parseFloat(el.getAttribute('data-from') || '0');
    var t0 = performance.now();
    function frame(now) {
      var p = Math.min(1, (now - t0) / ms);
      var eased = 1 - Math.pow(1 - p, 4);
      el.textContent = format(from + (to - from) * eased);
      if (p < 1) requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  }
  var factsShown = false;
  function showFacts() {
    if (factsShown) return;
    factsShown = true;
    var list = $('.facts');
    if (!list) return;
    list.classList.add('is-in');
    if (reduce.matches) return;
    $$('[data-count]', list).forEach(function (el) {
      var to = parseInt(el.getAttribute('data-count'), 10);
      countTo(el, to, to > 100 ? 1400 : 700, function (v) { return String(Math.round(v)); });
    });
  }

  /* ---------- 3. Первый экран: полоса знака вырастает в бумажную секцию.
        Плакат замирает, знак масштабируется от левого верхнего угла полосы,
        пока бумага не займет окно, и на ней проявляются факты ---------- */
  function initZoom() {
    var hero = $('[data-hero]');
    var stage = $('[data-stage]');
    var tee = $('[data-tee]');
    var facts = $('[data-facts]');
    if (!hero || !stage || !tee || !facts) { showFacts(); return; }
    var bar = $('.tee__bar', tee);
    var rect = $('.tee__rect', tee);
    var cap = $('.tee__cap', tee);
    var block = $('.tee__block', tee);
    var stem = $('.tee__stem', tee);
    var mq = $('[data-marquee]', stage);
    var fade = [$('[data-hero-body]', stage), $('[data-hero-ink]', stage), $('[data-hero-art]', stage), $('.badge', stage)]
      .filter(Boolean);
    var on = false;
    var dist = 1;
    var y0 = 0;
    var u = 1;
    var w0 = 1;
    var vw = 1;
    var vh = 1;
    var cur = -1;
    var target = 0;
    var raf = 0;
    var io = null;

    function watchStatic() {
      if (io || factsShown) return;
      if (!hasIO || reduce.matches) { showFacts(); return; }
      io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (!e.isIntersecting || on) return;
          io.disconnect();
          showFacts();
        });
      }, { rootMargin: '0px 0px -12% 0px', threshold: 0.12 });
      io.observe(facts);
    }

    /* Полоса растет вниз, ее скругленный торец остается четвертью круга
       с радиусом в высоту полосы и уходит за правый край окна.
       Блок и ножка держатся за торец и уезжают вместе с ним */
    function apply(p) {
      var a = 1 - clamp(p / 0.14);
      var z = clamp((p - 0.05) / 0.7);
      var eh = 1 - Math.pow(1 - z, 3);
      var ew = z * z;
      var h = u + (vh + 4 - u) * eh;
      var ws = w0 + (vw + 4 - w0) * ew;
      var sh = h / u;
      var dx = ws + h - (w0 + u);
      var f = clamp((p - 0.5) / 0.3);
      var m = clamp((p - 0.04) / 0.26);
      var live = p > 0;
      tee.style.transform = live ? 'translate3d(0,' + (-y0 * eh).toFixed(2) + 'px,0)' : '';
      rect.style.transform = live ? 'scale(' + (ws / w0).toFixed(4) + ',' + sh.toFixed(4) + ')' : '';
      cap.style.transform = live ? 'translate3d(' + (ws - w0).toFixed(2) + 'px,0,0) scale(' + sh.toFixed(4) + ')' : '';
      block.style.transform = live ? 'translate3d(' + dx.toFixed(2) + 'px,0,0) scale(1,' + sh.toFixed(4) + ')' : '';
      stem.style.transform = live ? 'translate3d(' + dx.toFixed(2) + 'px,' + (h - u).toFixed(2) + 'px,0)' : '';
      fade.forEach(function (el) {
        el.style.opacity = a < 1 ? a.toFixed(3) : '';
        el.style.transform = a < 1 ? 'translate3d(0,' + (-36 * (1 - a)).toFixed(1) + 'px,0)' : '';
      });
      if (mq) mq.style.transform = m > 0 ? 'translate3d(0,' + (m * 108).toFixed(1) + '%,0)' : '';
      facts.style.opacity = f.toFixed(3);
      facts.style.transform = 'translate3d(0,' + ((1 - f) * 44).toFixed(1) + 'px,0)';
      hero.classList.toggle('is-out', a <= 0);
      hero.classList.toggle('is-live', live);
      if (f > 0.3) showFacts();
    }

    function reset() {
      cancelAnimationFrame(raf);
      raf = 0;
      cur = -1;
      [tee, rect, cap, block, stem].forEach(function (el) { el.style.transform = ''; });
      fade.forEach(function (el) { el.style.opacity = ''; el.style.transform = ''; });
      if (mq) mq.style.transform = '';
      facts.style.opacity = '';
      facts.style.transform = '';
      hero.classList.remove('is-out', 'is-live');
      hero.style.removeProperty('--zoom-d');
    }

    function tick() {
      raf = 0;
      var d = target - cur;
      if (Math.abs(d) < 0.0015) cur = target;
      else { cur += d * 0.24; raf = requestAnimationFrame(tick); }
      apply(cur);
    }

    function update() {
      if (!on) return;
      target = clamp(window.pageYOffset / dist);
      if (cur < 0) { cur = target; apply(cur); return; }
      if (target !== cur && !raf) raf = requestAnimationFrame(tick);
    }

    function measure() {
      var want = desktop.matches && !reduce.matches && hasSticky && window.innerHeight >= 660;
      if (want !== on) {
        on = want;
        hero.classList.toggle('is-zoom', on);
        if (!on) reset();
      }
      if (!on) { watchStatic(); return; }
      vh = window.innerHeight;
      vw = stage.clientWidth;
      u = bar.offsetHeight || 1;
      w0 = Math.max(1, bar.offsetWidth - u);
      dist = Math.round(vh * 0.72);
      y0 = bar.offsetTop;
      hero.style.setProperty('--zoom-d', dist + 'px');
      cur = -1;
      update();
    }

    onMeasure.push(measure);
    onScroll.push(update);
    measure();
  }

  /* ---------- 4. Желтый блок вырастает в секцию «День»:
        окно секции раскрывается от угла у правого края на всю ширину ---------- */
  function initGrow() {
    var day = $('[data-grow]');
    if (!day) return;
    var prev = day.previousElementSibling;
    var canClip = !!(window.CSS && CSS.supports && CSS.supports('clip-path', 'inset(0 0 0 10px)'));
    var on = false;
    var last = '';
    var seedH = 76;
    var seedW = 200;

    function update() {
      if (!on) return;
      var r = day.getBoundingClientRect();
      var vh = window.innerHeight;
      var q = clamp((vh - seedH - r.top) / (vh * 0.46));
      var v = q >= 1 ? 'none' : 'inset(0 0 0 ' + ((r.width - seedW) * (1 - q)).toFixed(1) + 'px)';
      /* заголовок секции появляется, когда блок дорос до ширины окна */
      if (q > 0.9) day.classList.add('is-open');
      if (v === last) return;
      last = v;
      day.style.webkitClipPath = v;
      day.style.clipPath = v;
    }

    function measure() {
      var want = desktop.matches && !reduce.matches && hasSticky && canClip;
      if (want !== on) {
        on = want;
        day.classList.toggle('is-grow', on);
        if (prev) prev.classList.toggle('pre-grow', on);
        if (!on) { day.style.webkitClipPath = ''; day.style.clipPath = ''; last = ''; }
      }
      if (!on) return;
      seedW = Math.round(Math.min(250, Math.max(176, window.innerWidth * 0.16)));
      last = '';
      update();
    }

    onMeasure.push(measure);
    onScroll.push(update);
    measure();
  }

  /* ---------- 5. Липкие слои: секция дочитывается и замирает,
        следующая наезжает сверху ---------- */
  var pins = [];
  function initPins() {
    var all = $$('.slab');
    pins = $$('[data-pin]');
    if (!pins.length || !hasSticky) { pins = []; return; }
    var active = false;

    function measure() {
      active = desktop.matches && !reduce.matches;
      var vh = window.innerHeight;
      pins.forEach(function (el) {
        if (!active) {
          el.classList.remove('is-pin', 'is-covered');
          el.style.removeProperty('--pin');
          return;
        }
        /* секция успевает подняться на треть экрана, прежде чем замереть:
           нижний ряд контента остается читаемым. Перед растущим блоком замирает сразу */
        var lift = el.getAttribute('data-pin') === '0' ? 0 : Math.round(vh * 0.3);
        el.style.setProperty('--pin', Math.min(0, vh - el.offsetHeight - lift) + 'px');
        el.classList.add('is-pin');
      });
      cover();
    }

    /* Слой, полностью закрытый следующим, ставит свои циклы на паузу */
    function cover() {
      if (!active) return;
      pins.forEach(function (el) {
        var next = all[all.indexOf(el) + 1];
        var covered = !!next && next.getBoundingClientRect().top < -48;
        if (covered !== el.classList.contains('is-covered')) {
          el.classList.toggle('is-covered', covered);
          el.dispatchEvent(new Event('cover'));
        }
      });
    }

    onMeasure.push(measure);
    onScroll.push(cover);
    measure();
    if ('ResizeObserver' in window) {
      var ro = new ResizeObserver(queueMeasure);
      pins.forEach(function (el) { ro.observe(el); });
    }
  }

  /* Положение элемента в документе без учета липкости */
  function naturalTop(el) {
    var stuck = pins.filter(function (p) { return p.classList.contains('is-pin'); });
    stuck.forEach(function (p) { p.classList.remove('is-pin'); });
    var y = el.getBoundingClientRect().top + window.pageYOffset;
    stuck.forEach(function (p) { p.classList.add('is-pin'); });
    return y;
  }

  /* Якоря и клавиатурный фокус ведут к настоящему месту секции,
     даже если ее слой сейчас замер под следующим */
  function initAnchors() {
    var quiet = false;
    doc.addEventListener('click', function (e) {
      var a = e.target.closest ? e.target.closest('a[href^="#"]') : null;
      if (!a || e.defaultPrevented || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      var id = a.getAttribute('href').slice(1);
      var target = id ? doc.getElementById(id) : null;
      if (!target) return;
      e.preventDefault();
      var offset = target.classList.contains('slab') ? 0 : 92;
      var y = id === 'top' ? 0 : Math.max(0, naturalTop(target) - offset);
      window.scrollTo({ top: y, behavior: reduce.matches ? 'auto' : 'smooth' });
      if (history.pushState) history.pushState(null, '', '#' + id);
      if (!target.hasAttribute('tabindex')) target.setAttribute('tabindex', '-1');
      quiet = true;
      target.focus({ preventScroll: true });
      quiet = false;
    });
    doc.addEventListener('focusin', function (e) {
      var el = e.target;
      if (quiet || !pins.length || !el.matches || !el.matches(':focus-visible')) return;
      var slab = el.closest('.is-pin');
      if (!slab) return;
      var shown = el.getBoundingClientRect().top + window.pageYOffset;
      var real = naturalTop(el);
      if (Math.abs(real - shown) > 4) {
        window.scrollTo({ top: Math.max(0, real - window.innerHeight * 0.4), behavior: 'auto' });
      }
    });
  }

  /* ---------- 6. Шапка: меню на телефоне ---------- */
  function initMenu() {
    var hdr = $('[data-hdr]');
    var btn = $('[data-burger]');
    var menu = $('[data-menu]');
    if (!hdr || !btn || !menu) return;
    function set(open) {
      hdr.classList.toggle('is-open', open);
      btn.setAttribute('aria-expanded', String(open));
      root.style.overflow = open ? 'hidden' : '';
    }
    btn.addEventListener('click', function () { set(!hdr.classList.contains('is-open')); });
    menu.addEventListener('click', function (e) { if (e.target.closest('a')) set(false); });
    doc.addEventListener('keydown', function (e) { if (e.key === 'Escape') set(false); });
    if (desktop.addEventListener) desktop.addEventListener('change', function () { set(false); });
  }

  /* ---------- 7. Первый экран: оплата приходит, статус меняется ---------- */
  function initHero() {
    var art = $('[data-hero-art]');
    if (!art) return;
    var pay = $('[data-pay]', art);
    var flip = $('[data-flip]', art);
    if (!pay || !flip) return;
    if (reduce.matches) { pay.classList.add('is-on'); flip.classList.add('is-b'); return; }
    var tl = new Timeline();
    function cycle() {
      tl.clear();
      pay.classList.remove('is-on');
      flip.classList.remove('is-b');
      tl.at(2600, function () { pay.classList.add('is-on'); })
        .at(3300, function () { flip.classList.add('is-b'); })
        .at(9400, function () { pay.classList.remove('is-on'); })
        .at(10400, function () { flip.classList.remove('is-b'); })
        .at(11400, cycle);
    }
    whileVisible(art, cycle, function () { tl.clear(); });
  }

  /* ---------- 8. Кто придет: напоминание шлепается на карточку, статус меняется ---------- */
  function initSchedule() {
    var box = $('[data-demo="schedule"]');
    if (!box) return;
    var toast = $('[data-toast]', box);
    var flip = $('[data-sch-flip]', box);
    function done() { toast.classList.add('is-on'); if (flip) flip.classList.add('is-b'); }
    if (reduce.matches || !hasIO) { done(); return; }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        io.disconnect();
        setTimeout(function () { toast.classList.add('is-on'); }, 1400);
        setTimeout(function () { if (flip) flip.classList.add('is-b'); }, 1900);
      });
    }, { threshold: 0.5 });
    io.observe(box);
  }

  /* ---------- 9. Долги: напомнили, оплата пришла, сумма убыла ---------- */
  function initDebts() {
    var box = $('[data-demo="debts"]');
    if (!box) return;
    var total = $('[data-debt-total]', box);
    var count = $('[data-debt-count]', box);
    var rows = $$('[data-debt]', box);
    var tl = new Timeline();
    var sum = 6800;
    var fmt = function (v) { return Math.round(v).toLocaleString('ru-RU').replace(/\s/g, ' '); };

    function render() {
      var left = rows.filter(function (r) { return !r.classList.contains('is-paid'); });
      var next = left.reduce(function (a, r) { return a + parseInt(r.getAttribute('data-debt'), 10); }, 0);
      count.textContent = left.length === 2 ? '2 ученика' : left.length === 1 ? '1 ученик' : 'долгов нет';
      if (next === sum) return;
      if (reduce.matches) { total.textContent = fmt(next); }
      else { total.setAttribute('data-from', String(sum)); countTo(total, next, 900, fmt); }
      sum = next;
    }
    function remind(row, auto) {
      if (row.classList.contains('is-sent') || row.classList.contains('is-paid')) return;
      var btn = $('[data-remind]', row);
      if (auto) { btn.classList.add('is-press'); setTimeout(function () { btn.classList.remove('is-press'); }, 220); }
      row.classList.add('is-sent');
      btn.textContent = 'Отправлено';
      btn.disabled = true;
      tl.at(2600, function () {
        row.classList.remove('is-sent');
        row.classList.add('is-paid');
        btn.textContent = 'Оплачено';
        render();
      });
    }
    function reset() {
      rows.forEach(function (r) {
        r.classList.remove('is-sent', 'is-paid');
        var b = $('[data-remind]', r);
        b.textContent = 'Напомнить';
        b.disabled = false;
      });
      render();
    }
    function cycle() {
      tl.clear();
      reset();
      tl.at(2600, function () { remind($('[data-debt-auto]', box), true); })
        .at(11500, cycle);
    }
    rows.forEach(function (row) {
      $('[data-remind]', row).addEventListener('click', function () {
        remind(row, false);
        tl.at(9000, cycle);
      });
    });
    if (reduce.matches) return;
    whileVisible(box, cycle, function () { tl.clear(); });
  }

  /* ---------- 10. Домашнее задание: задачи закрашиваются ---------- */
  function initHomework() {
    var box = $('[data-demo="hw"]');
    if (!box || reduce.matches) return;
    var cells = $$('[data-hw-cells] i', box);
    var n = $('[data-hw-n]', box);
    var flip = $('[data-hw-flip]', box);
    var tl = new Timeline();
    function set(k) {
      cells.forEach(function (c, i) { c.classList.toggle('is-on', i < k); });
      n.textContent = String(k);
      flip.classList.toggle('is-b', k === 10);
    }
    function cycle() {
      tl.clear();
      set(7);
      tl.at(1800, function () { set(8); })
        .at(3200, function () { set(9); })
        .at(4600, function () { set(10); })
        .at(9600, cycle);
    }
    whileVisible(box, cycle, function () { tl.clear(); });
  }

  /* ---------- 11. ИИ-ассистент печатает план по словам ---------- */
  function initAI() {
    var box = $('[data-demo="ai"]');
    if (!box) return;
    var plan = $('[data-ai-plan]', box);
    var replay = $('[data-ai-replay]', box);
    var items = $$('li', plan);
    if (reduce.matches) { replay.hidden = true; return; }

    items.forEach(function (li) {
      var span = $('[data-type]', li);
      var words = span.textContent.split(' ');
      span.textContent = '';
      words.forEach(function (w, i) {
        var s = doc.createElement('span');
        s.className = 'w';
        s.textContent = w;
        span.appendChild(s);
        if (i < words.length - 1) span.appendChild(doc.createTextNode(' '));
      });
    });

    var tl = new Timeline();
    function type() {
      tl.clear();
      plan.classList.add('is-typing');
      items.forEach(function (li) {
        li.classList.add('is-wait');
        li.classList.remove('is-now');
        $$('.w', li).forEach(function (w) { w.classList.add('is-off'); });
      });
      var t = 500;
      items.forEach(function (li) {
        tl.at(t, function () { li.classList.remove('is-wait'); li.classList.add('is-now'); });
        $$('.w', li).forEach(function (w) {
          t += 75;
          tl.at(t, function () { w.classList.remove('is-off'); });
        });
        t += 120;
        tl.at(t, function () { li.classList.remove('is-now'); });
        t += 260;
      });
      tl.at(t, function () { plan.classList.remove('is-typing'); });
    }
    replay.addEventListener('click', type);
    if (!hasIO) return;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        io.disconnect();
        type();
      });
    }, { threshold: 0.45 });
    plan.classList.add('is-typing');
    items.forEach(function (li) { li.classList.add('is-wait'); });
    io.observe(box);
  }

  /* ---------- 12. Две минуты: таймер идет вместе со шкалой ---------- */
  function initClock() {
    var clock = $('[data-clock]');
    var out = $('[data-clock-time]');
    if (!clock || !out || reduce.matches || !hasIO) return;
    out.textContent = '0:00';
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        io.disconnect();
        var t0 = performance.now();
        (function frame(now) {
          var p = Math.min(1, (now - t0) / 2800);
          var sec = Math.round(p * 120);
          out.textContent = Math.floor(sec / 60) + ':' + ('0' + (sec % 60)).slice(-2);
          if (p < 1) requestAnimationFrame(frame);
        })(t0);
      });
    }, { rootMargin: '0px 0px -12% 0px', threshold: 0.12 });
    io.observe(clock);
  }

  /* ---------- 13. Подвал: на телефоне колонки свернуты, на десктопе всегда раскрыты ---------- */
  function initFooter() {
    var cols = $$('.ftr__col');
    if (!cols.length) return;
    function sync() {
      cols.forEach(function (d) {
        var s = $('summary', d);
        if (phone.matches) { d.removeAttribute('open'); s.removeAttribute('tabindex'); }
        else { d.setAttribute('open', ''); s.setAttribute('tabindex', '-1'); }
      });
    }
    cols.forEach(function (d) {
      $('summary', d).addEventListener('click', function (e) { if (!phone.matches) e.preventDefault(); });
    });
    sync();
    if (phone.addEventListener) phone.addEventListener('change', sync);
  }

  function init() {
    initFooter();
    initReveal();
    initZoom();
    initGrow();
    initPins();
    initAnchors();
    initMenu();
    initHero();
    initSchedule();
    initDebts();
    initHomework();
    initAI();
    initClock();

    window.addEventListener('scroll', function () {
      if (!scrollRaf) scrollRaf = requestAnimationFrame(runScroll);
    }, { passive: true });
    window.addEventListener('resize', queueMeasure, { passive: true });
    window.addEventListener('load', queueMeasure);
    if (doc.fonts && doc.fonts.ready) doc.fonts.ready.then(queueMeasure);
  }
  if (doc.readyState === 'loading') doc.addEventListener('DOMContentLoaded', init);
  else init();
})();
