/* TeacherDesk · концепция 1 «Живое окно»
   Ванильный JS без библиотек. Все сцены играют только пока видны на экране. */
(function () {
  'use strict';

  var d = document;
  var w = window;
  var reduce = w.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var finePointer = w.matchMedia('(hover: hover) and (pointer: fine)').matches;
  var phone = w.matchMedia('(max-width: 720px)');
  var NB = ' ';

  function $(s, c) { return (c || d).querySelector(s); }
  function $$(s, c) { return Array.prototype.slice.call((c || d).querySelectorAll(s)); }

  function fmt(n) {
    return String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, NB);
  }

  /* Плавный счетчик: expo-out, только текст. */
  function count(el, from, to, dur, done) {
    if (!el) return;
    if (el._raf) cancelAnimationFrame(el._raf);
    if (reduce || from === to) { el.textContent = fmt(to); if (done) done(); return; }
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
  function swap(key, idx) {
    $$('[data-swap="' + key + '"]').forEach(function (el) { setSwap(el, idx); });
  }

  /* Очередь шагов с возможностью остановки. */
  function Sequence(steps, loopAt) {
    var timers = [];
    var self = {
      running: false,
      start: function () {
        if (self.running) return;
        self.running = true;
        steps.forEach(function (s) {
          timers.push(setTimeout(s[1], s[0]));
        });
        if (loopAt) {
          timers.push(setTimeout(function () { self.stop(); self.start(); }, loopAt));
        }
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
        if (e.isIntersecting) { onEnter && onEnter(); } else { onLeave && onLeave(); }
      });
    }, { threshold: threshold || 0.2 }).observe(el);
  }

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
        }, 1400);
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -6% 0px' });
    reveals.forEach(function (el) { io.observe(el); });
  }

  /* ---------- первый экран: окно и линейка дня ----------
     Состояние окна это чистая функция от времени t (минуты от полуночи).
     Шкала играет сама по опорным событиям, но ее можно тащить и листать с клавиатуры. */
  var scene = $('[data-scene]');
  if (scene) (function () {
    var T0 = 480, T1 = 1260, SPAN = T1 - T0;
    var EV = [
      { t: 480, txt: 'план на день готов' },
      { t: 540, txt: 'напоминания об оплате ушли' },
      { t: 840, txt: 'урок начался' },
      { t: 842, txt: 'оплата получена' },
      { t: 1010, txt: 'долг закрыт' },
      { t: 1230, txt: 'отчет родителям ушел' }
    ];
    /* пороги смены чипа в строке урока и номер чипа «идет сейчас» */
    var ROWS = [
      { at: [540, 840, 900], now: 2 },
      { at: [842, 930, 990], now: 2 },
      { at: [540, 1010, 1035, 1095], now: 3 },
      { at: [1140, 1200], now: 1 }
    ];

    var ruler = $('[data-ruler]', scene);
    var track = $('[data-track]', scene);
    var thumb = $('[data-thumb]', scene);
    var rtime = $('[data-rtime]', scene);
    var clock = $('[data-clock]', scene);
    var got = $('[data-got]', scene);
    var debt = $('[data-debt]', scene);
    var hwBar = $('[data-hwbar]', scene);
    var hwNum = $('[data-hwnum]', scene);
    var play = $('[data-play]', scene);
    var rows = $$('[data-row]', scene).map(function (li) { return { li: li, sw: $('.swap', li) }; });
    var toasts = $$('.toast', scene);
    var segs = $$('.ruler__ls', scene);
    var dots = $$('.ruler__ev', scene);
    var dotT = [480, 540, 842, 1010, 1230];
    if (!ruler || !thumb) return;

    var time = 842;
    var cur = {};

    function hhmm(t) {
      var h = Math.floor(t / 60), m = Math.floor(t % 60);
      return (h < 10 ? '0' : '') + h + ':' + (m < 10 ? '0' : '') + m;
    }

    function apply(t, instant) {
      t = Math.max(T0, Math.min(T1, t));
      time = t;
      ruler.style.setProperty('--p', ((t - T0) / SPAN * 100).toFixed(3));

      var e = 0;
      EV.forEach(function (ev, i) { if (t >= ev.t) e = i; });

      var label = hhmm(t);
      if (label !== cur.label || e !== cur.ev) {
        cur.label = label;
        clock.textContent = label;
        rtime.textContent = label;
        thumb.setAttribute('aria-valuenow', Math.round(t));
        thumb.setAttribute('aria-valuetext', label + ', ' + EV[e].txt);
      }

      rows.forEach(function (row, i) {
        var idx = 0;
        ROWS[i].at.forEach(function (x) { if (t >= x) idx++; });
        if (cur['r' + i] === idx) return;
        cur['r' + i] = idx;
        setSwap(row.sw, idx);
        row.li.classList.toggle('is-now', idx === ROWS[i].now);
        if (segs[i]) {
          segs[i].classList.toggle('is-now', idx === ROWS[i].now);
          segs[i].classList.toggle('is-past', idx > ROWS[i].now);
        }
      });

      var g = t >= 1010 ? 4400 : t >= 842 ? 1800 : 0;
      if (cur.got !== g) {
        if (instant || cur.got === undefined) { count(got, g, g, 0); } else { count(got, cur.got, g, 800); }
        cur.got = g;
      }
      var db = t >= 1010 ? 4200 : 6800;
      if (cur.debt !== db) {
        if (instant || cur.debt === undefined) { count(debt, db, db, 0); } else { count(debt, cur.debt, db, 800); }
        cur.debt = db;
      }
      var hw = t >= 990 ? 8 : 7;
      if (cur.hw !== hw) {
        cur.hw = hw;
        hwNum.textContent = hw;
        hwBar.style.setProperty('--v', hw / 10);
      }

      if (cur.ev !== e) {
        cur.ev = e;
        toasts.forEach(function (el, i) {
          el.classList.toggle('is-on', i === e);
          el.classList.toggle('is-prev', i === e - 1);
          el.classList.toggle('is-past', i < e - 1);
        });
      }
      dots.forEach(function (el, i) { el.classList.toggle('is-past', t >= dotT[i]); });
    }

    /* --- автопроигрывание по опорным событиям --- */
    var playing = false, userPaused = false, hover = false, visible = false, dragging = false;
    var raf = null, timer = null, idle = null, stop = 0;

    function clearRun() {
      if (raf) cancelAnimationFrame(raf);
      raf = null;
      clearTimeout(timer);
      timer = null;
    }
    function tween(from, to, dur, each, done) {
      var t0 = null;
      function step(ts) {
        if (t0 === null) t0 = ts;
        var k = Math.min(1, (ts - t0) / dur);
        var e = k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;
        each(from + (to - from) * e);
        if (k < 1) { raf = requestAnimationFrame(step); } else { raf = null; if (done) done(); }
      }
      raf = requestAnimationFrame(step);
    }
    function nextStop(first) {
      if (stop >= EV.length - 1 && time >= EV[EV.length - 1].t) {
        /* финал держим, затем мягко гасим содержимое и возвращаемся в утро */
        timer = setTimeout(rewind, 4200);
        return;
      }
      timer = setTimeout(function () {
        var to = EV[stop + 1].t;
        var from = time;
        stop++;
        tween(from, to, to - from < 10 ? 500 : 1000, function (t) { apply(t); }, function () { nextStop(); });
      }, first ? 1500 : 1150);
    }
    function rewind() {
      scene.classList.add('is-rewind');
      timer = setTimeout(function () {
        tween(time, T0, 700, function (t) { apply(t, true); }, function () {
          stop = 0;
          apply(T0, true);
          scene.classList.remove('is-rewind');
          nextStop(true);
        });
      }, 320);
    }
    function sync() {
      var should = !reduce && !userPaused && !hover && visible && !dragging && !d.hidden;
      if (should && !playing) {
        playing = true;
        stop = 0;
        EV.forEach(function (ev, i) { if (time >= ev.t) stop = i; });
        nextStop(time === T0);
      } else if (!should && playing) {
        playing = false;
        clearRun();
        scene.classList.remove('is-rewind');
      }
    }
    function setPaused(v) {
      userPaused = v;
      if (play) {
        if (v) { play.setAttribute('data-paused', ''); } else { play.removeAttribute('data-paused'); }
        play.setAttribute('aria-label', v ? 'Проиграть день' : 'Остановить день');
      }
      sync();
    }
    /* человек взял шкалу в руки: автопроигрывание уступает и вернется после паузы */
    function takeControl() {
      clearTimeout(idle);
      setPaused(true);
      if (!reduce) idle = setTimeout(function () { setPaused(false); }, 12000);
    }

    if (play) {
      if (reduce) { play.hidden = true; }
      play.addEventListener('click', function () {
        clearTimeout(idle);
        if (userPaused && time >= T1 - 1) apply(T0, true);
        setPaused(!userPaused);
      });
    }

    /* --- перетаскивание --- */
    function tFromX(x) {
      var r = track.getBoundingClientRect();
      return T0 + Math.max(0, Math.min(1, (x - r.left) / r.width)) * SPAN;
    }
    function snap(t) {
      var best = null;
      EV.forEach(function (ev) {
        if (Math.abs(ev.t - t) <= 9 && (best === null || Math.abs(ev.t - t) < Math.abs(best - t))) best = ev.t;
      });
      return best !== null ? best : Math.round(t / 5) * 5;
    }
    var press = null;
    ruler.addEventListener('pointerdown', function (e) {
      if (e.button) return;
      press = { id: e.pointerId, x: e.clientX, active: e.pointerType !== 'touch' };
      if (press.active) {
        dragging = true;
        takeControl();
        ruler.classList.add('is-drag');
        try { ruler.setPointerCapture(e.pointerId); } catch (err) {}
        apply(snap(tFromX(e.clientX)));
        e.preventDefault();
        thumb.focus({ preventScroll: true });
      }
    });
    ruler.addEventListener('pointermove', function (e) {
      if (!press || e.pointerId !== press.id) return;
      if (!press.active) {
        if (Math.abs(e.clientX - press.x) < 6) return;
        press.active = true;
        dragging = true;
        takeControl();
        ruler.classList.add('is-drag');
        try { ruler.setPointerCapture(e.pointerId); } catch (err) {}
      }
      apply(snap(tFromX(e.clientX)));
    });
    function release(e, cancelled) {
      if (!press || e.pointerId !== press.id) return;
      if (!press.active && !cancelled) { takeControl(); apply(snap(tFromX(e.clientX))); }
      press = null;
      dragging = false;
      ruler.classList.remove('is-drag');
      sync();
    }
    ruler.addEventListener('pointerup', function (e) { release(e, false); });
    ruler.addEventListener('pointercancel', function (e) { release(e, true); });

    thumb.addEventListener('keydown', function (e) {
      var t = null, i;
      var step = e.shiftKey ? 60 : 15;
      if (e.key === 'ArrowRight' || e.key === 'ArrowUp') t = Math.round(time / 5) * 5 + step;
      if (e.key === 'ArrowLeft' || e.key === 'ArrowDown') t = Math.round(time / 5) * 5 - step;
      if (e.key === 'Home') t = T0;
      if (e.key === 'End') t = T1;
      if (e.key === 'PageUp') { for (i = 0; i < EV.length; i++) { if (EV[i].t > time) { t = EV[i].t; break; } } if (t === null) t = T1; }
      if (e.key === 'PageDown') { for (i = EV.length - 1; i >= 0; i--) { if (EV[i].t < time) { t = EV[i].t; break; } } if (t === null) t = T0; }
      if (t === null) return;
      e.preventDefault();
      takeControl();
      apply(t);
    });

    if (finePointer) {
      [$('.scene__fig', scene), $('.deck', scene)].forEach(function (el) {
        if (!el) return;
        el.addEventListener('pointerenter', function () { hover = true; sync(); });
        el.addEventListener('pointerleave', function () { hover = false; sync(); });
      });
    }
    d.addEventListener('visibilitychange', sync);

    if (reduce) {
      apply(842, true);
    } else {
      apply(T0, true);
      whenVisible(scene, function () { visible = true; sync(); }, function () { visible = false; sync(); }, 0.25);
    }

    /* параллакс за курсором: слои на разной глубине */
    var hero = $('[data-hero]');
    if (hero && finePointer && !reduce) {
      var tx = 0, ty = 0, cx = 0, cy = 0, praf = null;
      var loop = function () {
        cx += (tx - cx) * 0.08;
        cy += (ty - cy) * 0.08;
        scene.style.setProperty('--mx', cx.toFixed(4));
        scene.style.setProperty('--my', cy.toFixed(4));
        if (Math.abs(tx - cx) > 0.001 || Math.abs(ty - cy) > 0.001) {
          praf = requestAnimationFrame(loop);
        } else { praf = null; }
      };
      hero.addEventListener('pointermove', function (e) {
        var r = hero.getBoundingClientRect();
        tx = ((e.clientX - r.left) / r.width - 0.5) * -1;
        ty = ((e.clientY - r.top) / r.height - 0.5) * -1;
        if (!praf) praf = requestAnimationFrame(loop);
      });
      hero.addEventListener('pointerleave', function () {
        tx = 0; ty = 0;
        if (!praf) praf = requestAnimationFrame(loop);
      });
    }
  })();

  /* ---------- факты: считаем только 990 ---------- */
  var facts = $$('[data-count]');
  if (facts.length && !reduce) {
    facts.forEach(function (el) { el.textContent = '0'; });
    var started = false;
    whenVisible(facts[0].closest('.facts'), function () {
      if (started) return;
      started = true;
      facts.forEach(function (el) {
        setTimeout(function () { count(el, 0, parseInt(el.getAttribute('data-count'), 10), 1400); }, 900);
      });
    }, null, 0.3);
  }

  /* ---------- бенто: у каждой ячейки свой короткий цикл ---------- */
  var bento = $('[data-bento]');
  if (bento) (function () {
    var cells = $$('[data-cell]', bento);
    var by = {};
    cells.forEach(function (c) { by[c.getAttribute('data-cell')] = c; });

    if (!reduce) {
      /* a: флажок «идет сейчас» едет по ленте, напоминание уходит */
      if (by.a) {
        var seqA = Sequence([
          [0, function () { by.a.classList.remove('is-run'); by.a.classList.add('is-reset'); swap('tl', 0); }],
          [80, function () { by.a.classList.remove('is-reset'); by.a.classList.add('is-run'); }],
          [5200, function () { swap('tl', 1); }]
        ], 12000);
        whenVisible(by.a, seqA.start, seqA.stop, 0.3);
      }

      /* b: напоминания уходят, Артем платит, сумма убывает */
      if (by.b) {
        var bSum = $('[data-bsum]', by.b);
        var debtRow = $('[data-swap="b2"]', by.b).closest('li');
        var seqB = Sequence([
          [0, function () { swap('b1', 0); swap('b2', 0); debtRow.classList.remove('is-paid'); count(bSum, 6800, 6800, 0); }],
          [1200, function () { swap('b1', 1); }],
          [1650, function () { swap('b2', 1); }],
          [4000, function () { swap('b2', 2); debtRow.classList.add('is-paid'); count(bSum, 6800, 4200, 1000); }]
        ], 11000);
        whenVisible(by.b, seqB.start, seqB.stop, 0.3);
      }

      /* c: восьмая задача получает галочку */
      if (by.c) {
        var bHw = $('[data-bhw]', by.c);
        var hw8 = $('[data-hw8]', by.c);
        var seqC = Sequence([
          [0, function () { hw8.classList.remove('is-ok'); bHw.textContent = '7'; }],
          [1800, function () { hw8.classList.add('is-ok'); bHw.textContent = '8'; }]
        ], 10000);
        whenVisible(by.c, seqC.start, seqC.stop, 0.3);
      }

      /* d: план печатается через полсекунды после входа ячейки в экран
         и остается на месте до следующего цикла */
      var ai = $('[data-ai]', bento);
      if (ai && by.d) {
        var typeTimers = [];
        var lines = $$('[data-type]', ai).map(function (el) {
          var words = el.textContent.split(' ');
          el.textContent = '';
          var spans = words.map(function (word, i) {
            var s = d.createElement('span');
            s.className = 'w is-in';
            s.textContent = word;
            el.appendChild(s);
            if (i < words.length - 1) el.appendChild(d.createTextNode(' '));
            return s;
          });
          return { li: el.closest('li'), words: spans };
        });
        var clearType = function () { typeTimers.forEach(clearTimeout); typeTimers = []; };
        var wait = function () {
          clearType();
          ai.classList.add('is-live', 'is-typing');
          lines.forEach(function (line) {
            line.li.classList.remove('is-done', 'is-go');
            line.words.forEach(function (x) { x.classList.remove('is-in'); });
          });
        };
        var typePlan = function () {
          var t = 0;
          lines.forEach(function (line, li) {
            typeTimers.push(setTimeout(function () { line.li.classList.add('is-go'); }, t));
            line.words.forEach(function (x) {
              typeTimers.push(setTimeout(function () { x.classList.add('is-in'); }, t));
              t += 80;
            });
            typeTimers.push(setTimeout(function () {
              line.li.classList.add('is-done');
              if (li === lines.length - 1) ai.classList.remove('is-typing');
            }, t));
            t += 240;
          });
        };
        var seqD = Sequence([[0, wait], [500, typePlan]], 12000);
        whenVisible(by.d, seqD.start, function () {
          seqD.stop();
          clearType();
          /* ушли с экрана посреди печати: показываем готовый план, а не обрывок */
          ai.classList.remove('is-typing');
          lines.forEach(function (line) {
            line.li.classList.add('is-done', 'is-go');
            line.words.forEach(function (x) { x.classList.add('is-in'); });
          });
        }, 0.3);
      }
    }

    /* оглавление: подсвечивает ячейку у центра экрана, на телефоне листает ленту */
    var spy = $('[data-spy]');
    if (spy) {
      var links = $$('a', spy);
      var ticking = false;
      var spyAt = 0;
      var mark = function () {
        ticking = false;
        var best = 0, bestD = Infinity;
        var mid = phone.matches ? bento.getBoundingClientRect().left + bento.clientWidth / 2 : w.innerHeight * 0.45;
        cells.forEach(function (c, i) {
          var r = c.getBoundingClientRect();
          var dist = phone.matches ? Math.abs(r.left + r.width / 2 - mid) : Math.abs(r.top + r.height / 2 - mid);
          if (dist < bestD) { bestD = dist; best = i; }
        });
        links.forEach(function (a, i) { a.classList.toggle('is-on', i === best); });
        /* на телефоне активная пилюля оглавления всегда в кадре */
        if (phone.matches && best !== spyAt) {
          var on = links[best];
          spy.scrollTo({ left: on.offsetLeft - (spy.clientWidth - on.offsetWidth) / 2, behavior: reduce ? 'auto' : 'smooth' });
        }
        spyAt = best;
      };
      var req = function () { if (!ticking) { ticking = true; requestAnimationFrame(mark); } };
      w.addEventListener('scroll', req, { passive: true });
      bento.addEventListener('scroll', req, { passive: true });
      w.addEventListener('resize', req);
      links.forEach(function (a, i) {
        a.addEventListener('click', function (e) {
          if (!phone.matches || !cells[i]) return;
          e.preventDefault();
          var pad = parseFloat(getComputedStyle(bento).paddingLeft) || 0;
          bento.scrollTo({ left: cells[i].offsetLeft - bento.offsetLeft - pad, behavior: reduce ? 'auto' : 'smooth' });
        });
      });
      mark();
    }
  })();

  /* ---------- девять функций: вкладки ---------- */
  var tabsRoot = $('[data-tabs]');
  if (tabsRoot) {
    var list = $('[role="tablist"]', tabsRoot);
    var tabs = $$('[role="tab"]', tabsRoot);
    var panels = $$('[role="tabpanel"]', tabsRoot);
    var curTab = 0;
    var auto = !reduce;
    var seen = false;
    var liveT = null;

    var activate = function (i, focus) {
      if (i === curTab && seen) return;
      tabs[curTab].classList.remove('is-active', 'is-auto');
      tabs[curTab].setAttribute('aria-selected', 'false');
      tabs[curTab].setAttribute('tabindex', '-1');
      panels[curTab].classList.remove('is-active', 'is-live');
      curTab = i;
      tabs[curTab].classList.add('is-active');
      tabs[curTab].setAttribute('aria-selected', 'true');
      tabs[curTab].removeAttribute('tabindex');
      panels[curTab].classList.add('is-active');
      if (auto) tabs[curTab].classList.add('is-auto');
      if (focus) tabs[curTab].focus({ preventScroll: true });
      clearTimeout(liveT);
      liveT = setTimeout(function () { panels[curTab].classList.add('is-live'); }, 80);
      /* на узких экранах список вкладок это горизонтальная лента */
      if (list.scrollWidth > list.clientWidth + 4) {
        var t = tabs[curTab];
        list.scrollTo({ left: t.offsetLeft - (list.clientWidth - t.offsetWidth) / 2, behavior: reduce ? 'auto' : 'smooth' });
      }
    };

    var stopAuto = function () {
      auto = false;
      tabs.forEach(function (t) { t.classList.remove('is-auto'); });
    };

    tabs.forEach(function (t, i) {
      t.addEventListener('click', function () { stopAuto(); activate(i); });
      t.addEventListener('animationend', function (e) {
        if (e.animationName === 'toolbar' && auto) activate((i + 1) % tabs.length);
      });
      t.addEventListener('keydown', function (e) {
        var n = null;
        if (e.key === 'ArrowDown' || e.key === 'ArrowRight') n = (curTab + 1) % tabs.length;
        if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') n = (curTab - 1 + tabs.length) % tabs.length;
        if (e.key === 'Home') n = 0;
        if (e.key === 'End') n = tabs.length - 1;
        if (n === null) return;
        e.preventDefault();
        stopAuto();
        activate(n, true);
      });
    });

    var stage = $('.tools__stage', tabsRoot);
    stage.addEventListener('pointerenter', function () { tabsRoot.classList.add('is-paused'); });
    stage.addEventListener('pointerleave', function () { tabsRoot.classList.remove('is-paused'); });

    whenVisible(tabsRoot, function () {
      tabsRoot.classList.remove('is-paused');
      if (seen) return;
      seen = true;
      if (auto) tabs[curTab].classList.add('is-auto');
      panels[curTab].classList.add('is-live');
    }, function () { tabsRoot.classList.add('is-paused'); }, 0.3);
  }

  /* ---------- старт за две минуты ---------- */
  var start = $('[data-start]');
  if (start && !reduce) {
    var steps = $$('[data-step]', start);
    var timerEl = $('[data-timer]', start);
    var marks = [30, 90, 120];
    var played = false;
    var pad2 = function (n) { return (n < 10 ? '0' : '') + n; };
    var show = function (s) { timerEl.textContent = pad2(Math.floor(s / 60)) + ':' + pad2(Math.floor(s % 60)); };

    steps.forEach(function (s) { s.classList.remove('is-on'); });
    show(0);

    whenVisible(start, function () {
      if (played) return;
      played = true;
      var t0 = null;
      var dur = 4600;
      var tick = function (t) {
        if (t0 === null) t0 = t;
        var p = Math.min(1, (t - t0) / dur);
        var sec = p * 120;
        show(sec);
        marks.forEach(function (m, i) { if (sec >= m) steps[i].classList.add('is-on'); });
        if (p < 1) { requestAnimationFrame(tick); return; }
        setTimeout(function () { start.classList.add('is-pushed'); }, 500);
        setTimeout(function () { start.classList.remove('is-pushed'); }, 6800);
      };
      setTimeout(function () { requestAnimationFrame(tick); }, 500);
    }, null, 0.3);
  }

  /* ---------- тарифы: ползунок «сколько учеников» ---------- */
  var seats = $('[data-seats]');
  var plans = $('[data-plans]');
  if (seats && plans) (function () {
    var input = $('input', seats);
    var outN = $('[data-seats-n]', seats);
    var outW = $('[data-seats-w]', seats);
    var zones = $$('.seats__zones i', seats);
    var lbls = $$('.seats__lbl span', seats);
    var cards = $$('[data-plan]', plans);
    var names = ['Free', 'Pro', 'Premium'];
    var last = -1;

    function students(p) {
      if (p <= 16) return Math.min(3, 1 + Math.floor(p / 5.4));
      if (p <= 72) return Math.round(4 + (p - 16) / 56 * 46);
      return Math.round(51 + (p - 72) / 28 * 49);
    }
    function word(n) {
      var a = n % 10, b = n % 100;
      if (a === 1 && b !== 11) return 'ученик';
      if (a >= 2 && a <= 4 && (b < 12 || b > 14)) return 'ученика';
      return 'учеников';
    }
    function update() {
      var p = parseFloat(input.value);
      var n = students(p);
      var fit = n <= 3 ? 0 : n <= 50 ? 1 : 2;
      var txt = p >= 100 ? '100+' : String(n);
      seats.style.setProperty('--p', p);
      outN.textContent = txt;
      outW.textContent = p >= 100 ? 'учеников' : word(n);
      input.setAttribute('aria-valuetext', txt + NB + outW.textContent + ', подойдет ' + names[fit]);
      if (fit === last) return;
      last = fit;
      plans.style.setProperty('--fit', fit);
      zones.forEach(function (z, i) { z.classList.toggle('is-on', i === fit); });
      lbls.forEach(function (l, i) { l.classList.toggle('is-on', i === fit); });
      cards.forEach(function (c, i) {
        var on = i === fit;
        var btn = $('.btn', c);
        c.classList.toggle('is-fit', on);
        btn.classList.toggle('btn--primary', on);
        btn.classList.toggle('btn--ghost', !on);
      });
    }
    input.addEventListener('input', update);
    update();
  })();

  /* ---------- шаблон таблицы: сумма считается по формуле ---------- */
  var sheet = $('[data-sheet]');
  if (sheet && !reduce) {
    var sum = $('[data-sheet-sum]', sheet);
    var sheetDone = false;
    sum.textContent = '0';
    whenVisible(sheet, function () {
      if (sheetDone) return;
      sheetDone = true;
      setTimeout(function () { sheet.classList.add('is-live'); count(sum, 0, 6800, 1200); }, 600);
    }, null, 0.5);
  } else if (sheet) {
    sheet.classList.add('is-live');
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
})();
