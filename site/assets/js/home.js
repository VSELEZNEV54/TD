/* TeacherDesk · главная
   Все сцены играют только пока видны на экране. Помощники берутся из main.js (window.TD). */
(function () {
  'use strict';

  var TD = window.TD;
  if (!TD) return;
  var d = document;
  var w = window;
  var staticPreview = !!d.querySelector('meta[name="teacherdesk-preview"][content="static"]');
  var $ = TD.$, $$ = TD.$$, reduce = TD.reduce, count = TD.count, setSwap = TD.setSwap;
  var Sequence = TD.Sequence, whenVisible = TD.whenVisible, phone = TD.phone;

  /* Адреса авторизации задаются на сервере, без пересборки страниц. */
  if (!staticPreview && /^https?:$/.test(w.location.protocol)) {
    fetch('/api/public-config', { credentials: 'same-origin', cache: 'no-store' })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (config) {
        if (!config) return;
        ['register', 'login'].forEach(function (action) {
          var value = config[action + '_url'];
          if (typeof value !== 'string') return;
          var url;
          try { url = new URL(value); } catch (e) { return; }
          if (!/^https?:$/.test(url.protocol) || url.username || url.password) return;
          $$('a[href="https://app.teacherdesk.ru/' + action + '"]').forEach(function (link) { link.href = url.href; });
        });
      }).catch(function () {});
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

    if (TD.finePointer) {
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
    if (hero && TD.finePointer && !reduce) {
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

  /* ---------- факты: счетчик у чисел с data-count ---------- */
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

  /* ---------- о сервисе: ролик «двенадцать инструментов в один кабинет» ----------
     Состояние сцены - чистая функция от времени ролика t. Часы идут, только пока ролик
     виден на экране и не стоит на паузе. Главы можно выбрать кнопками, как в плеере. */
  var film = $('[data-film]');
  if (film) (function () {
    var featureFilm = /^(schedule|feature)$/.test(film.getAttribute('data-film'));
    var stage = $('.film__tools', film);
    var tools = $$('.ftool', film);
    var bens = $$('.fben', film);
    var subs = $$(featureFilm ? '[data-film-at]' : '[data-sub]', film);
    var countEl = $('[data-film-count]', film);
    var msgEl = $('[data-film-msg]', film);
    var playBtn = $('[data-film-play]', film);
    var chBtns = $$('[data-ch]', film);
    var fills = chBtns.map(function (b) { return $('.film__fill', b); });

    var L = featureFilm ? 23000 : 13500; // длина ролика
    var CH = featureFilm ? [0, 6000, L] : [0, 4600, 6000, L];
    var POP = 130, PING = 1800, PING_STEP = 200, MSG = 4000;
    var GATHER = 4600, GATHER_STEP = 35, APP_IN = 5200, BEN = 6400, BEN_STEP = 650, TRIAL = 10400;
    if (featureFilm) {
      POP = 280; PING = 1800; PING_STEP = 350;
      GATHER = 5400; GATHER_STEP = 60; APP_IN = 6000; BEN = 7600; BEN_STEP = 1600;
    }

    var END_FADE = 450;
    var POSTER = featureFilm ? [5300, L - END_FADE - 1] : [CH[1] - 1, CH[2] - 1, L - END_FADE - 1];

    var t = reduce ? L - 1 : 0;
    var wantPlay = !reduce, playing = false, raf = null, last = null;
    var vis35 = false, anyVis = false, userKick = false;
    var cur = { scene: -1, count: -1, msg: -1 };

    /* куда лететь каждой карточке: от ее центра к центру сцены */
    function measure() {
      var w = stage.offsetWidth, h = stage.offsetHeight;
      tools.forEach(function (el) {
        var x = el.offsetLeft + el.offsetWidth / 2, y = el.offsetTop + el.offsetHeight / 2;
        el.style.setProperty('--gx', (w / 2 - x).toFixed(1) + 'px');
        el.style.setProperty('--gy', (h * 0.47 - y).toFixed(1) + 'px');
      });
    }

    function render() {
      var chapter = t < CH[1] ? 0 : featureFilm ? 1 : t < CH[2] ? 1 : 2;
      var scene = featureFilm ? (chapter === 0 ? 0 : 2) : chapter;
      var shown = 0;
      tools.forEach(function (el, k) {
        var out = t >= GATHER + k * GATHER_STEP;
        var on = !out && t >= k * POP + (featureFilm ? 150 : 0);
        if (on) shown++;
        el.classList.toggle('is-in', on);
        el.classList.toggle('is-out', out);
        el.classList.toggle('is-ping', scene === 0 && t >= PING + k * PING_STEP && !!el.querySelector('.ftool__ping'));
      });
      if (countEl && scene === 0 && shown !== cur.count) { cur.count = shown; countEl.textContent = shown; }
      var msg = Math.min(20, Math.floor(t / MSG * 20));
      if (msgEl && scene === 0 && msg !== cur.msg) { cur.msg = msg; msgEl.textContent = msg; }
      film.classList.toggle('is-app', t >= APP_IN);
      film.classList.toggle('is-trial', !featureFilm && t >= TRIAL);
      film.classList.toggle('is-end', !reduce && t >= L - END_FADE);
      bens.forEach(function (b, j) { b.classList.toggle('is-on', t >= BEN + j * BEN_STEP); });
      if (scene !== cur.scene) {
        cur.scene = scene;
        film.setAttribute('data-scene', scene);
        if (!featureFilm) subs.forEach(function (sp, i) { sp.classList.toggle('is-on', i === scene); });
        chBtns.forEach(function (b, i) { if (i === chapter) { b.setAttribute('aria-current', 'step'); } else { b.removeAttribute('aria-current'); } });
      }
      if (featureFilm) {
        var caption = 0;
        subs.forEach(function (sp, i) { if (t >= Number(sp.getAttribute('data-film-at'))) caption = i; });
        subs.forEach(function (sp, i) { sp.classList.toggle('is-on', i === caption); });
        film.dataset.filmTime = String(t);
        film.dispatchEvent(new CustomEvent('td:film-frame', {detail: t}));
      }
      fills.forEach(function (f, i) {
        var p = Math.max(0, Math.min(1, (t - CH[i]) / (CH[i + 1] - CH[i])));
        f.style.transform = 'scaleX(' + p.toFixed(3) + ')';
      });
    }

    /* перемотка назад и повтор - склейка: карточки не летят из центра обратно */
    function seek(to) {
      var back = to < t;
      t = to;
      film.classList.toggle('is-poster', !wantPlay || reduce);
      if (back) {
        cur.count = cur.msg = -1;
        film.classList.add('is-cut');
        render();
        void film.offsetWidth;
        requestAnimationFrame(function () { film.classList.remove('is-cut'); });
      } else {
        render();
      }
    }

    function frame(ts) {
      if (last !== null) {
        var next = t + Math.min(ts - last, 100);   // после долгой паузы вкладки не перескакиваем сцены
        last = ts;
        if (next >= L) { seek(0); } else { t = next; render(); }
      } else {
        last = ts;
        render();
      }
      raf = requestAnimationFrame(frame);
    }
    function sync() {
      var should = wantPlay && !d.hidden && (vis35 || (userKick && anyVis));
      if (should && !playing) { playing = true; last = null; raf = requestAnimationFrame(frame); }
      else if (!should && playing) { playing = false; cancelAnimationFrame(raf); raf = null; }
      film.classList.toggle('is-playing', playing);
    }
    function setPlay(v) {
      wantPlay = v;
      if (v) film.classList.remove('is-poster');
      if (v) { playBtn.removeAttribute('data-paused'); } else { playBtn.setAttribute('data-paused', ''); }
      playBtn.setAttribute('aria-label', v ? 'Пауза' : 'Смотреть ролик');
      sync();
    }

    if (playBtn) {
      if (reduce) { playBtn.hidden = true; }
      playBtn.addEventListener('click', function () {
        if (!wantPlay) userKick = true;   // нажали «смотреть»: играем, даже если ролик виден частично
        setPlay(!wantPlay);
      });
    }
    chBtns.forEach(function (b, i) {
      b.addEventListener('click', function () {
        /* часы идут - начало главы; стоят (пауза или «уменьшить движение») - готовый кадр главы */
        var running = !reduce && wantPlay;
        if (running) userKick = true;
        seek(running ? (!featureFilm && i === 2 ? CH[2] + 400 : CH[i]) : POSTER[i]);
        sync();
      });
    });

    var rz = null;
    w.addEventListener('resize', function () { clearTimeout(rz); rz = setTimeout(measure, 150); });
    if (d.fonts && d.fonts.ready) d.fonts.ready.then(measure);
    d.addEventListener('visibilitychange', sync);

    film.classList.add('is-ready');
    film.classList.toggle('is-poster', reduce);
    measure();
    render();
    if (!reduce) {
      if ('IntersectionObserver' in w) {
        new IntersectionObserver(function (entries) {
          entries.forEach(function (e) {
            anyVis = e.isIntersecting;
            vis35 = e.isIntersecting && e.intersectionRatio >= 0.35;
            if (!anyVis) userKick = false;
          });
          sync();
        }, { threshold: [0, 0.35] }).observe(film);
      } else {
        vis35 = anyVis = true;
        sync();
      }
    }
  })();

  /* ---------- день репетитора: у каждой карточки свой короткий цикл, оглавление следит за прокруткой ---------- */
  var bento = $('[data-bento]');
  if (bento) (function () {
    var cells = $$('[data-cell]', bento);
    var by = {};
    cells.forEach(function (c) { by[c.getAttribute('data-cell')] = c; });
    var sw = function (key, i) { setSwap($('[data-swap="' + key + '"]', bento), i); };

    if (!reduce) {
      /* a: флажок «идет сейчас» едет по ленте, напоминание уходит */
      if (by.a) {
        var seqA = Sequence([
          [0, function () { by.a.classList.remove('is-run'); by.a.classList.add('is-reset'); sw('tl', 0); }],
          [80, function () { by.a.classList.remove('is-reset'); by.a.classList.add('is-run'); }],
          [5200, function () { sw('tl', 1); }]
        ], 12000);
        whenVisible(by.a, seqA.start, seqA.stop, 0.3);
      }

      /* b: напоминания уходят, Артем платит, сумма убывает */
      if (by.b) {
        var bSum = $('[data-bsum]', by.b);
        var debtRow = $('[data-swap="b2"]', by.b).closest('li');
        var seqB = Sequence([
          [0, function () { sw('b1', 0); sw('b2', 0); debtRow.classList.remove('is-paid'); count(bSum, 6800, 6800, 0); }],
          [1200, function () { sw('b1', 1); }],
          [1650, function () { sw('b2', 1); }],
          [4000, function () { sw('b2', 2); debtRow.classList.add('is-paid'); count(bSum, 6800, 4200, 1000); }]
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
    }

    /* d: план печатается через полсекунды после входа карточки в экран
       и остается на месте до следующего цикла */
    var ai = $('[data-ai]', bento);
    if (ai && by.d && !reduce) {
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

    /* оглавление: подсвечивает карточку у середины экрана, на телефоне листает ленту */
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
        links.forEach(function (a, i) {
          a.classList.toggle('is-on', i === best);
          if (i === best) { a.setAttribute('aria-current', 'true'); } else { a.removeAttribute('aria-current'); }
        });
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

  /* ---------- возможности: карточки ложатся стопкой ----------
     Закрытой карточке ставим --cover: сколько карточек уже наехало на нее (0...3), она чуть уменьшается и темнеет.
     .is-live получает только верхняя открытая карточка: ее живой кадр играет, остальные стоят */
  var fstack = $('[data-fstack]');
  if (fstack) (function () {
    var cards = $$('.fcard', fstack);
    var hooks = {};
    var stick = [], hgt = [], sticky = true;
    var near = false, ticking = false, live = -1;

    function measure() {
      sticky = getComputedStyle(cards[0]).position === 'sticky';
      cards.forEach(function (c, i) {
        stick[i] = parseFloat(getComputedStyle(c).top) || 0;
        hgt[i] = c.offsetHeight || 1;
      });
    }
    function setLive(i) {
      if (i === live) return;
      if (live > -1) { cards[live].classList.remove('is-live'); if (hooks[live]) hooks[live].stop(); }
      live = i;
      if (i > -1) { cards[i].classList.add('is-live'); if (hooks[i]) hooks[i].start(); }
    }
    function update() {
      ticking = false;
      var vh = w.innerHeight;
      var top = cards.map(function (c) { return c.getBoundingClientRect().top; });
      /* насколько каждая карточка уже легла на свое место в стопке: 0 - далеко внизу, 1 - легла */
      var lay = top.map(function (t, i) { return Math.max(0, Math.min(1, 1 - (t - stick[i]) / hgt[i])); });
      var open = -1;
      cards.forEach(function (c, i) {
        if (top[i] < vh * 0.6) open = i;
        if (reduce || !sticky) return;
        var cover = 0;
        for (var j = i + 1; j < cards.length && cover < 3; j++) cover += lay[j];
        c.style.setProperty('--cover', Math.min(3, cover).toFixed(3));
      });
      var box = fstack.getBoundingClientRect();
      setLive(near && box.bottom > vh * 0.35 ? Math.max(0, open) : -1);
    }
    function req() { if (!ticking) { ticking = true; requestAnimationFrame(update); } }

    /* 02 учет оплат: напоминание Соне, оплата от Артема, суммы пересчитываются */
    var pay = $('[data-pay]', fstack);
    if (pay && !reduce) {
      var got = $('[data-pay-got]', pay), debt = $('[data-pay-debt]', pay), toast = $('[data-pay-toast]', pay);
      var swp = function (key, i) { setSwap($('[data-swap="' + key + '"]', pay), i); };
      var seqPay = Sequence([
        [0, function () { swp('pa', 0); swp('ps', 0); toast.classList.remove('is-on'); count(got, 38400, 38400, 0); count(debt, 6800, 6800, 0); }],
        [1200, function () { swp('ps', 1); }],
        [2600, function () { toast.classList.add('is-on'); }],
        [3100, function () { swp('pa', 1); count(debt, 6800, 4200, 1000); count(got, 38400, 41000, 1000); }],
        [7400, function () { toast.classList.remove('is-on'); }]
      ], 9000);
      hooks[cards.indexOf(pay.closest('.fcard'))] = seqPay;
    }

    measure();
    var rz = null;
    w.addEventListener('resize', function () { clearTimeout(rz); rz = setTimeout(function () { measure(); req(); }, 120); });
    w.addEventListener('scroll', function () { if (near) req(); }, { passive: true });
    d.addEventListener('visibilitychange', function () {
      if (d.hidden) { setLive(-1); } else { req(); }
    });
    if ('IntersectionObserver' in w) {
      new IntersectionObserver(function (entries) {
        near = entries[0].isIntersecting;
        req();
      }, { rootMargin: '10% 0px' }).observe(fstack);
    } else {
      near = true;
      req();
    }
  })();

  /* ---------- старт за две минуты: таймер бежит, линия доходит до точки каждого шага ---------- */
  var start = $('[data-start]');
  if (start && !reduce) (function () {
    var steps = $$('[data-step]', start);
    var timerEl = $('[data-timer]', start);
    var fill = $('[data-tl-fill]', start);
    var bar = fill.parentNode;
    var marks = [0, 30, 90];
    var stops = [0, 0, 0];
    var played = false;
    var now = 0;
    var pad2 = function (n) { return (n < 10 ? '0' : '') + n; };
    /* где на линии стоит точка каждого шага: берем по разметке, а не делим на три */
    var measure = function () {
      var w0 = bar.offsetWidth || 1;
      var left = bar.getBoundingClientRect().left;
      steps.forEach(function (st, i) { stops[i] = Math.max(0, Math.min(1, (st.getBoundingClientRect().left + 29 - left) / w0)); });
    };
    var at = function (sec) {
      for (var i = marks.length - 1; i >= 0; i--) {
        if (sec >= marks[i]) {
          var to = i + 1 < marks.length ? marks[i + 1] : 120;
          var end = i + 1 < stops.length ? stops[i + 1] : 1;
          return stops[i] + (end - stops[i]) * Math.min(1, (sec - marks[i]) / (to - marks[i]));
        }
      }
      return 0;
    };
    var show = function (sec) {
      now = sec;
      timerEl.textContent = pad2(Math.floor(sec / 60)) + ':' + pad2(Math.floor(sec % 60));
      fill.style.setProperty('--f', at(sec).toFixed(4));
      steps.forEach(function (st, i) { st.classList.toggle('is-on', sec > 0 && sec >= marks[i]); });
    };

    measure();
    show(0);
    w.addEventListener('resize', function () { measure(); show(now); });
    /* на низком экране (телефон боком) 30% темной полосы не помещаются: порог не выше половины окна */
    var th = Math.min(0.3, w.innerHeight * 0.5 / (start.offsetHeight || 1));

    whenVisible(start, function () {
      if (played) return;
      played = true;
      measure();
      var t0 = null;
      var dur = 6000;
      var tick = function (t) {
        if (t0 === null) t0 = t;
        var p = Math.min(1, (t - t0) / dur);
        /* плавный разгон и торможение, как у секундомера, который останавливают */
        var e = p < .5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2;
        show(Math.max(.01, e * 120));
        if (p < 1) requestAnimationFrame(tick);
      };
      setTimeout(function () { requestAnimationFrame(tick); }, 400);
    }, null, th);
  })();

  /* ---------- отзывы: лента карточек, стрелки листают по одной ---------- */
  var stories = $('[data-stories]');
  if (stories) (function () {
    var list = $$('[data-story]', stories);
    var nEl = $('[data-st-n]'), allEl = $('[data-st-all]');
    var prev = $('[data-st-prev]'), next = $('[data-st-next]');
    if (allEl) allEl.textContent = list.length;
    function step() { return list.length > 1 ? list[1].offsetLeft - list[0].offsetLeft : stories.clientWidth; }
    function at() { return Math.round(stories.scrollLeft / step()); }
    function max() { return Math.round((stories.scrollWidth - stories.clientWidth) / step()); }
    function go(i) {
      stories.scrollTo({ left: Math.max(0, Math.min(max(), i)) * step(), behavior: reduce ? 'auto' : 'smooth' });
    }
    /* счетчик показывает последнюю карточку, которая видна целиком */
    function sync() {
      var i = at(), m = max();
      var box = stories.getBoundingClientRect(), seen = i;
      list.forEach(function (s, k) { var r = s.getBoundingClientRect(); if (r.left >= box.left - 2 && r.right <= box.right + 2) seen = k; });
      if (nEl) nEl.textContent = seen + 1;
      if (prev) prev.disabled = i <= 0;
      if (next) next.disabled = i >= m;
    }
    if (prev) prev.addEventListener('click', function () { go(at() - 1); });
    if (next) next.addEventListener('click', function () { go(at() + 1); });
    var ticking = false;
    var req = function () { if (!ticking) { ticking = true; requestAnimationFrame(function () { ticking = false; sync(); }); } };
    stories.addEventListener('scroll', req, { passive: true });
    w.addEventListener('resize', req);
    sync();
  })();

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
    var badge = $('[data-badge]', plans);
    var names = ['пробный период', 'Pro', 'Premium'];
    var last = -1;

    /* шкала: левые 72% ползунка дают 1-50 учеников (Pro), правые 28% дают 51-100 (Premium) */
    function students(p) {
      if (p <= 72) return Math.max(1, Math.round(1 + p / 72 * 49));
      return Math.round(51 + (p - 72) / 28 * 49);
    }
    /* зона и подпись знают свой тариф по data-fit, без него по порядку */
    function fitOf(el, i) { return el.hasAttribute('data-fit') ? +el.getAttribute('data-fit') : i; }
    function word(n) {
      var a = n % 10, b = n % 100;
      if (a === 1 && b !== 11) return 'ученик';
      if (a >= 2 && a <= 4 && (b < 12 || b > 14)) return 'ученика';
      return 'учеников';
    }
    function update() {
      var p = parseFloat(input.value);
      var n = students(p);
      var fit = n <= 50 ? 1 : 2;
      var txt = p >= 100 ? '100+' : String(n);
      seats.style.setProperty('--p', p);
      outN.textContent = txt;
      outW.textContent = p >= 100 ? 'учеников' : word(n);
      input.setAttribute('aria-valuetext', txt + TD.NB + outW.textContent + ', подойдет ' + names[fit]);
      if (fit === last) return;
      /* наклейка «подойдет вам» заново шлепается, когда рамка переезжает */
      if (last !== -1) setTimeout(function () { TD.replay(badge, 'is-pop'); }, 260);
      last = fit;
      plans.style.setProperty('--fit', fit);
      zones.forEach(function (z, i) { z.classList.toggle('is-on', fitOf(z, i) === fit); });
      lbls.forEach(function (l, i) { l.classList.toggle('is-on', fitOf(l, i) === fit); });
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
    var sumEl = $('[data-sheet-sum]', sheet);
    var sheetDone = false;
    sumEl.textContent = '0';
    whenVisible(sheet, function () {
      if (sheetDone) return;
      sheetDone = true;
      setTimeout(function () { sheet.classList.add('is-live'); count(sumEl, 0, 6800, 1200); }, 600);
    }, null, 0.5);
  } else if (sheet) {
    sheet.classList.add('is-live');
  }

  /* ---------- финал: знак T собирается из трех деталей ---------- */
  var tee = $('[data-tee]');
  if (tee) {
    if (reduce) { tee.classList.add('is-on'); }
    else { whenVisible(tee, function () { setTimeout(function () { tee.classList.add('is-on'); }, 250); }, null, 0.4); }
  }

  /* ---------- окно вопроса и консультации ---------- */
  var ask = $('#ask');
  if (ask && typeof ask.showModal === 'function') (function () {
    var NB = TD.NB;
    var form = $('[data-ask-form]', ask);
    var el = form.elements;
    var done = $('[data-ask-done]', ask);
    var doneTitle = $('[data-ask-done-title]', ask);
    var doneText = $('[data-ask-done-text]', ask);
    var err = $('[data-ask-err]', ask);
    var send = $('[type="submit"]', form);
    var sendText = $('span', send);
    var endpoint = ask.getAttribute('data-endpoint') || '/api/requests';
    var mail = 'info@teacherdesk.ru';
    var FIELDS = ['name', 'phone', 'email', 'preferred_contact', 'question', 'consent'];
    var opener = null, busy = false, keep = false, downOut = false;
    var kind = 'question', sourceTag = '', pendingBody = '', pendingKey = '';

    var mark = function (name, msg, bad) {
      var f = el[name], message = $('#ask-e-' + name, ask);
      if (!f || !message) return;
      if (bad === undefined) bad = !!msg;
      if (bad) f.setAttribute('aria-invalid', 'true'); else f.removeAttribute('aria-invalid');
      message.textContent = msg || '';
    };
    var mode = function (next) {
      kind = next === 'consultation' ? 'consultation' : 'question';
      var consult = kind === 'consultation';
      $('#ask-t', ask).textContent = consult ? 'Проконсультироваться' : 'Задать свой вопрос';
      $('[data-ask-kicker]', ask).textContent = consult ? 'Знакомство с TeacherDesk' : 'Вопрос команде';
      $('[data-ask-lead]', ask).textContent = consult
        ? 'Оставьте контакт. Специалист свяжется с' + NB + 'вами в' + NB + 'течение рабочего дня.'
        : 'Ответим в' + NB + 'течение рабочего дня на' + NB + 'почту или по' + NB + 'телефону.';
      $('[data-ask-contact]', ask).hidden = !consult;
      $('[data-ask-question-label]', ask).textContent = consult ? 'Что хотите узнать (необязательно)' : 'Вопрос';
      el.question.required = !consult;
      if (!consult) el.preferred_contact.value = 'any';
      sendText.textContent = consult ? 'Запросить консультацию' : 'Отправить вопрос';
      if (staticPreview) {
        $('[data-ask-lead]', ask).innerHTML = 'В этой демонстрации отправка формы отключена. По вопросам и консультации напишите на <a class="tlink" href="mailto:' + mail + '">' + mail + '</a>.';
        $$('.ask__f, .ask__okw, .ask__ok--news', form).forEach(function (field) { field.hidden = true; });
        $$('input, textarea, select', form).forEach(function (field) { field.disabled = true; });
        send.hidden = true;
      }
    };
    var showForm = function (next) {
      done.hidden = true;
      form.hidden = false;
      ask.setAttribute('aria-labelledby', 'ask-t');
      ask.removeAttribute('aria-describedby');
      err.textContent = '';
      FIELDS.forEach(function (n) { mark(n, ''); });
      mode(next);
    };
    var open = function (e) {
      var trigger = e && e.currentTarget;
      if (e) e.preventDefault();
      opener = trigger || d.activeElement;
      // Не меняем поля, пока запрос уходит или ответ ожидает открытия окна.
      if (!busy && !keep) {
        var consult = !trigger || trigger.hasAttribute('data-consult-open') || trigger.getAttribute('data-request-kind') === 'consultation';
        sourceTag = trigger ? (trigger.getAttribute('data-source-tag') || '').slice(0, 100) : 'consultation-link';
        showForm(consult ? 'consultation' : 'question');
      }
      keep = false;
      if (!ask.open) ask.showModal();
      setTimeout(function () { if (ask.open) (staticPreview ? $('[data-ask-close]', ask) : done.hidden ? (busy ? send : el.name) : doneTitle).focus(); }, 30);
    };
    var close = function () { ask.close(); };

    $$('[data-ask-open], [data-consult-open]').forEach(function (b) { b.addEventListener('click', open); });
    $$('[data-ask-close]', ask).forEach(function (b) { b.addEventListener('click', close); });
    ask.addEventListener('pointerdown', function (e) { downOut = e.target === ask; });
    ask.addEventListener('click', function (e) { if (downOut && e.target === ask) close(); downOut = false; });
    ask.addEventListener('close', function () { if (opener && typeof opener.focus === 'function') opener.focus(); });
    FIELDS.forEach(function (n) {
      var clear = function () {
        mark(n, '');
        var other = n === 'phone' ? 'email' : n === 'email' ? 'phone' : '';
        if (other && el[n].value.trim() && !el[other].value.trim()) mark(other, '');
      };
      el[n].addEventListener('input', clear);
      el[n].addEventListener('change', clear);
    });

    var check = function () {
      var v = function (n) { return el[n].value.trim(); };
      var digits = v('phone').replace(/\D/g, '');
      var noContact = !v('phone') && !v('email');
      var preferred = kind === 'consultation' ? el.preferred_contact.value : 'any';
      var msgs = {
        name: v('name').length < 2 ? 'Напишите имя, минимум 2 символа.' : v('name').length > 100 ? 'Имя должно быть не длиннее 100 символов.' : '',
        phone: v('phone') && (digits.length < 10 || digits.length > 15 || !/^[+\d\s().-]+$/.test(v('phone'))) ? 'Проверьте номер телефона.' : '',
        email: noContact ? 'Оставьте телефон или email.' : v('email') && (v('email').length > 254 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v('email'))) ? 'Проверьте адрес email.' : '',
        question: !v('question') && kind === 'question' ? 'Напишите вопрос.' : v('question').length > 4000 ? 'Сократите текст до 4000 символов.' : '',
        preferred_contact: '',
        consent: el.consent.checked ? '' : 'Нужно согласие на' + NB + 'обработку данных.'
      };
      if (preferred === 'phone' && !v('phone')) msgs.phone = 'Оставьте номер для звонка.';
      if (preferred === 'email' && !v('email')) msgs.email = 'Оставьте email для ответа.';
      var first = null;
      FIELDS.forEach(function (n) {
        var bad = !!msgs[n] || (n === 'phone' && noContact);
        mark(n, msgs[n], bad);
        if (bad && !first) first = el[n];
      });
      err.textContent = '';
      if (first) first.focus();
      return !first;
    };
    var setBusy = function (value) {
      busy = value;
      $$('input, textarea, select', form).forEach(function (f) { f.disabled = value; });
      if (value) {
        send.setAttribute('aria-disabled', 'true');
        form.setAttribute('aria-busy', 'true');
        sendText.textContent = 'Отправляем...';
      } else {
        send.removeAttribute('aria-disabled');
        form.removeAttribute('aria-busy');
        sendText.textContent = kind === 'consultation' ? 'Запросить консультацию' : 'Отправить вопрос';
      }
    };
    var uuid = function () {
      if (w.crypto && w.crypto.randomUUID) return w.crypto.randomUUID();
      var bytes = new Uint8Array(16);
      if (w.crypto && w.crypto.getRandomValues) w.crypto.getRandomValues(bytes);
      else for (var i = 0; i < bytes.length; i++) bytes[i] = Math.floor(Math.random() * 256);
      bytes[6] = (bytes[6] & 15) | 64;
      bytes[8] = (bytes[8] & 63) | 128;
      return Array.prototype.map.call(bytes, function (b, i) {
        return ([4, 6, 8, 10].indexOf(i) >= 0 ? '-' : '') + ('0' + b.toString(16)).slice(-2);
      }).join('');
    };
    var finish = function (id) {
      doneTitle.textContent = kind === 'consultation' ? 'Запрос на консультацию отправлен' : 'Вопрос отправлен';
      doneText.textContent = 'Обращение сохранено. Ответим в' + NB + 'течение рабочего дня. Номер: ' + id.slice(0, 8) + '.';
      form.reset();
      form.hidden = true;
      done.hidden = false;
      pendingBody = '';
      pendingKey = '';
      ask.setAttribute('aria-labelledby', 'ask-done-t');
      ask.setAttribute('aria-describedby', 'ask-done-d');
      if (ask.open) doneTitle.focus(); else keep = true;
    };

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      if (staticPreview) return;
      if (busy || !check()) return;
      var data = {
        kind: kind,
        name: el.name.value.trim(), phone: el.phone.value.trim(), email: el.email.value.trim(),
        question: el.question.value.trim(),
        preferred_contact: kind === 'consultation' ? el.preferred_contact.value : 'any',
        consent: el.consent.checked, news: !!el.news.checked, website: el.website.value,
        source_path: w.location.pathname.slice(0, 500), source_tag: sourceTag
      };
      var body = JSON.stringify(data);
      // При повторе после обрыва связи сервер вернет уже сохраненное обращение.
      if (body !== pendingBody || !pendingKey) { pendingBody = body; pendingKey = uuid(); }
      var controller = new AbortController();
      var timeout = setTimeout(function () { controller.abort(); }, 15000);
      var cleanup = function () { clearTimeout(timeout); setBusy(false); };
      setBusy(true);
      err.textContent = '';
      fetch(endpoint, {
        method: 'POST', credentials: 'same-origin', signal: controller.signal,
        headers: { 'Content-Type': 'application/json', 'Idempotency-Key': pendingKey }, body: body
      }).then(function (response) {
        return response.json().catch(function () { return null; }).then(function (result) {
          return { response: response, result: result };
        });
      }).then(function (reply) {
        cleanup();
        var result = reply.result;
        if (reply.response.ok && result && result.ok === true && typeof result.id === 'string' && result.id) {
          finish(result.id);
          return;
        }
        var first = null;
        if (result && result.fields) FIELDS.forEach(function (name) {
          if (typeof result.fields[name] !== 'string') return;
          mark(name, result.fields[name]);
          if (!first) first = el[name];
        });
        err.textContent = reply.response.status === 429
          ? 'Слишком много обращений. Попробуйте позже или напишите на' + NB + mail + '.'
          : result && typeof result.message === 'string' ? result.message
          : 'Не получилось отправить. Попробуйте еще раз или напишите на' + NB + mail + '.';
        if (first && ask.open) first.focus();
        if (!ask.open) keep = true;
      }).catch(function (error) {
        cleanup();
        err.textContent = error.name === 'AbortError'
          ? 'Не дождались ответа сервера. Попробуйте еще раз: повторное обращение не создастся.'
          : 'Не получилось отправить. Проверьте соединение и' + NB + 'попробуйте еще раз или напишите на' + NB + mail + '.';
        if (!ask.open) keep = true;
      });
    });
    var openFromHash = function () { if (w.location.hash === '#consultation') open(); };
    w.addEventListener('hashchange', openFromHash);
    openFromHash();
  })();
})();
