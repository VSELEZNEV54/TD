/* TeacherDesk · концепция 2 «Ночная смена»
   Ванильный JS: лампа, которая идет за читателем, появления, раскрытие заголовков по строкам,
   счетчики, наклон окна, липкий скролл функций, прожектор на карточках, таймер старта,
   живая сцена первого экрана. */
(function () {
  'use strict';

  var d = document;
  var w = window;
  var root = d.documentElement;
  w.__tdReady = true;
  root.classList.add('js');

  var RM = w.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var FINE = w.matchMedia('(hover: hover) and (pointer: fine)').matches;
  var HAS_IO = 'IntersectionObserver' in w;

  function $(s, c) { return (c || d).querySelector(s); }
  function $$(s, c) { return Array.prototype.slice.call((c || d).querySelectorAll(s)); }
  function clamp(v, a, b) { return v < a ? a : v > b ? b : v; }
  function fmt(n) { return String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, ' '); }
  function expoOut(t) { return t >= 1 ? 1 : 1 - Math.pow(2, -10 * t); }

  function tween(ms, step, done, ease) {
    var t0 = null;
    function frame(t) {
      if (t0 === null) t0 = t;
      var p = clamp((t - t0) / ms, 0, 1);
      step(ease ? ease(p) : p, p);
      if (p < 1) w.requestAnimationFrame(frame); else if (done) done();
    }
    w.requestAnimationFrame(frame);
  }

  /* один обработчик прокрутки на все */
  var scrollJobs = [];
  var ticking = false;
  function onScroll() {
    if (ticking) return;
    ticking = true;
    w.requestAnimationFrame(function () {
      ticking = false;
      for (var i = 0; i < scrollJobs.length; i++) scrollJobs[i]();
    });
  }
  w.addEventListener('scroll', onScroll, { passive: true });
  w.addEventListener('resize', onScroll, { passive: true });

  /* ---------- шапка и меню ---------- */
  var hdr = $('.hdr');
  scrollJobs.push(function () { hdr.classList.toggle('is-stuck', w.scrollY > 8); });

  var burger = $('.hdr__burger');
  var menu = $('#menu');
  function setMenu(open) {
    root.classList.toggle('menu-open', open);
    burger.setAttribute('aria-expanded', open ? 'true' : 'false');
    d.body.style.overflow = open ? 'hidden' : '';
  }
  if (burger && menu) {
    burger.addEventListener('click', function () { setMenu(!root.classList.contains('menu-open')); });
    menu.addEventListener('click', function (e) { if (e.target.closest('a')) setMenu(false); });
    d.addEventListener('keydown', function (e) { if (e.key === 'Escape') setMenu(false); });
    w.matchMedia('(min-width: 861px)').addEventListener('change', function (e) { if (e.matches) setMenu(false); });
  }

  /* маяк один: желтая кнопка шапки включается, когда кнопка оффера ушла из кадра */
  var heroCta = $('#heroCta');
  if (heroCta && HAS_IO) {
    new IntersectionObserver(function (entries) {
      root.classList.toggle('cta-in', entries[0].isIntersecting);
    }, { rootMargin: '-56px 0px 0px 0px', threshold: 0.2 }).observe(heroCta);
  } else {
    root.classList.remove('cta-in');
  }

  /* ---------- печать по словам: готовим разметку ---------- */
  $$('[data-type]').forEach(function (list) {
    var n = 0;
    $$('li', list).forEach(function (li) {
      var out = d.createDocumentFragment();
      var nodes = Array.prototype.slice.call(li.childNodes);
      while (li.firstChild) li.removeChild(li.firstChild);
      nodes.forEach(function (node) {
        if (node.nodeType === 3) {
          var holder = d.createElement('span');
          node.textContent.split(/(\s+)/).forEach(function (part) {
            if (!part) return;
            if (/^\s+$/.test(part)) { holder.appendChild(d.createTextNode(' ')); return; }
            var s = d.createElement('span');
            s.className = 'wd';
            s.style.setProperty('--w', n++);
            s.textContent = part;
            holder.appendChild(s);
          });
          out.appendChild(holder);
        } else {
          node.classList.add('wd');
          node.style.setProperty('--w', n++);
          out.appendChild(node);
        }
      });
      li.appendChild(out);
    });
  });

  /* цитата: каждое слово отдельным элементом, неразрывные пробелы не трогаем */
  $$('[data-words]').forEach(function (q) {
    var n = 0;
    Array.prototype.slice.call(q.childNodes).forEach(function (node) {
      if (node.nodeType === 3) {
        var frag = d.createDocumentFragment();
        node.textContent.split(/( +)/).forEach(function (part) {
          if (!part) return;
          if (part.charAt(0) === ' ') { frag.appendChild(d.createTextNode(' ')); return; }
          var s = d.createElement('span');
          s.className = 'qw';
          s.style.setProperty('--w', n++);
          s.textContent = part;
          frag.appendChild(s);
        });
        q.replaceChild(frag, node);
      } else if (node.nodeType === 1) {
        node.classList.add('qw');
        node.style.setProperty('--w', n++);
      }
    });
  });

  /* ---------- заголовки секций: раскрытие по строкам через маску ---------- */
  var spEls = $$('.sp');
  function plainText(el) {
    var t = el.getAttribute('data-t');
    if (t === null) {
      t = el.textContent.replace(/[ \t\n\r]+/g, ' ').replace(/^ | $/g, '');
      el.setAttribute('data-t', t);
    }
    return t;
  }
  function splitLines(el) {
    var txt = plainText(el);
    el.textContent = '';
    var words = txt.split(' ').map(function (wd, i) {
      if (i) el.appendChild(d.createTextNode(' '));
      var s = d.createElement('span');
      s.style.display = 'inline-block';
      s.textContent = wd;
      el.appendChild(s);
      return s;
    });
    var lines = [];
    var top = null;
    words.forEach(function (s) {
      var t = s.offsetTop;
      if (top === null || Math.abs(t - top) > 6) { lines.push([]); top = t; }
      lines[lines.length - 1].push(s.textContent);
    });
    el.textContent = '';
    lines.forEach(function (ws, i) {
      if (i) el.appendChild(d.createTextNode(' '));
      var ln = d.createElement('span');
      ln.className = 'ln2';
      ln.style.setProperty('--l', i);
      var inner = d.createElement('span');
      inner.textContent = ws.join(' ');
      ln.appendChild(inner);
      el.appendChild(ln);
    });
    el.classList.add('sp-ok');
  }
  function unsplit(el) {
    el.textContent = plainText(el);
    el.classList.add('sp-ok', 'in', 'done');
  }
  function splitAll() {
    spEls.forEach(function (el) {
      if (RM || el.classList.contains('in')) unsplit(el); else splitLines(el);
    });
  }
  if (spEls.length) {
    var fontsReady = d.fonts && d.fonts.ready ? d.fonts.ready : Promise.resolve();
    var started = false;
    var startSplit = function () {
      if (started) return;
      started = true;
      splitAll();
      if (RM || !HAS_IO) { spEls.forEach(unsplit); return; }
      var ioS = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (!en.isIntersecting) return;
          var el = en.target;
          ioS.unobserve(el);
          el.classList.add('in');
          w.setTimeout(function () { el.classList.add('done'); }, 1700);
        });
      }, { threshold: 0.3, rootMargin: '0px 0px -8% 0px' });
      spEls.forEach(function (el) { ioS.observe(el); });
    };
    fontsReady.then(startSplit);
    w.setTimeout(startSplit, 1200);
    /* при смене ширины строки пересобираются: раскрытые заголовки возвращаются в обычный текст */
    var lastW = root.clientWidth;
    var reT = 0;
    var reSplit = function () {
      w.clearTimeout(reT);
      reT = w.setTimeout(function () {
        if (!started || root.clientWidth === lastW) return;
        lastW = root.clientWidth;
        splitAll();
      }, 120);
    };
    w.addEventListener('resize', reSplit, { passive: true });
    if ('ResizeObserver' in w) new ResizeObserver(reSplit).observe(root);
  }

  /* ---------- счетчики ---------- */
  function runCount(el) {
    var to = parseFloat(el.getAttribute('data-count'));
    if (RM || !to) return;
    var from = to > 100 ? to * 0.6 : 0;
    tween(to > 100 ? 1400 : 900, function (e) { el.textContent = fmt(from + (to - from) * e); }, null, expoOut);
  }

  /* ---------- появления ---------- */
  var rvItems = $$('.rv, [data-words]');
  if (HAS_IO && !RM) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        var el = en.target;
        io.unobserve(el);
        el.classList.add('in');
        $$('[data-count]', el).forEach(runCount);
        if ($('[data-type]', el)) el.classList.add('typed');
      });
    }, { threshold: 0.14, rootMargin: '0px 0px -7% 0px' });
    rvItems.forEach(function (el) { io.observe(el); });
  } else {
    rvItems.forEach(function (el) { el.classList.add('in', 'typed'); });
  }

  /* ---------- первый экран ---------- */
  var hero = $('.hero');
  var heroIn = $('.hero__in');
  var win = $('#heroWin');
  var stage = $('.stage');
  var beam = $('.beam');
  var lit = $('.win__lit');
  var mqTilt = w.matchMedia('(min-width: 900px)');
  var stageTop = 0;
  function measureHero() {
    if (!stage || !heroIn) return;
    stageTop = stage.offsetTop + heroIn.offsetTop;
    hero.style.setProperty('--stage-y', stageTop + 'px');
  }
  measureHero();
  w.addEventListener('resize', measureHero, { passive: true });
  if ('ResizeObserver' in w && heroIn) new ResizeObserver(measureHero).observe(heroIn);
  w.addEventListener('load', measureHero);
  if (d.fonts && d.fonts.ready) d.fonts.ready.then(measureHero);

  /* окно распрямляется при прокрутке */
  if (win && stage && !RM) {
    var lastP = -1;
    scrollJobs.push(function () {
      if (!mqTilt.matches) return;
      var range = Math.max(200, stageTop - w.innerHeight * 0.14);
      var p = clamp(w.scrollY / range, 0, 1);
      p = 1 - Math.pow(1 - p, 1.6);
      if (Math.abs(p - lastP) < 0.002) return;
      lastP = p;
      win.style.setProperty('--p', p.toFixed(3));
    });
  }

  /* приходит оплата */
  var heroSum = $('#heroSum');
  if (win && stage && heroSum && !RM) {
    var live = false;
    var timer = null;
    var cycle = function () {
      if (!live) return;
      stage.classList.add('is-paid');
      tween(1100, function (e) { heroSum.textContent = fmt(8200 + 2600 * e); }, null, expoOut);
      timer = w.setTimeout(function () {
        stage.classList.remove('is-paid');
        heroSum.textContent = fmt(8200);
        timer = w.setTimeout(cycle, 3200);
      }, 5600);
    };
    if (HAS_IO) {
      new IntersectionObserver(function (entries) {
        var vis = entries[0].isIntersecting;
        if (vis && !live) { live = true; timer = w.setTimeout(cycle, 2600); }
        if (!vis && live) { live = false; w.clearTimeout(timer); }
      }, { threshold: 0.1 }).observe(win);
    }
  }

  /* ---------- лампа: один слой света, который идет за читателем ---------- */
  var lampEl = $('.lamp');
  var spotEl = $('#lamp');
  if (lampEl && spotEl && !RM && HAS_IO) {
    var DUR = 900;
    var targets = $$('[data-lamp]').map(function (el) {
      var a = el.getAttribute('data-lamp').split(/\s+/).map(parseFloat);
      return { el: el, x: a[0], y: a[1], r: a[2] || 1, a: isNaN(a[3]) ? 1 : a[3], on: false };
    });
    var L = { cur: null, from: null, off: { x: w.innerWidth / 2, y: 0, r: 1 }, t0: 0, x: w.innerWidth / 2, y: 0, r: 1, a: 0, raf: 0, mx: 0, my: 0, tmx: 0, tmy: 0, ready: false };

    var targetPos = function (t) {
      var r = t.el.getBoundingClientRect();
      return { x: r.left + r.width * t.x, y: r.top + r.height * t.y, r: t.r, a: t.a };
    };
    var requestLamp = function () { if (!L.raf) L.raf = w.requestAnimationFrame(lampFrame); };
    var setTarget = function (t) {
      if (t === L.cur) return;
      L.from = { x: L.x + w.scrollX, y: L.y + w.scrollY, r: L.r, a: L.a };
      if (!t) L.off = { x: L.from.x, y: L.from.y, r: L.r * 1.2 };
      L.cur = t;
      L.t0 = w.performance.now();
      requestLamp();
    };
    var pick = function () {
      if (!L.ready) return;
      var cy = w.innerHeight / 2;
      var best = null;
      var bd = Infinity;
      for (var i = 0; i < targets.length; i++) {
        var t = targets[i];
        if (!t.on) continue;
        var r = t.el.getBoundingClientRect();
        if (!r.width && !r.height) continue;
        var dist = Math.abs(clamp(cy, r.top, r.bottom) - cy) + Math.abs(r.top + r.height * t.y - cy) * 0.05;
        if (dist < bd) { bd = dist; best = t; }
      }
      setTarget(best);
    };
    var lampFrame = function (now) {
      L.raf = 0;
      var to = L.cur ? targetPos(L.cur) : { x: L.off.x - w.scrollX, y: L.off.y - w.scrollY, r: L.off.r, a: 0 };
      var p = L.from ? clamp((now - L.t0) / DUR, 0, 1) : 1;
      if (p < 1) {
        var e = expoOut(p);
        var fx = L.from.x - w.scrollX;
        var fy = L.from.y - w.scrollY;
        L.x = fx + (to.x - fx) * e;
        L.y = fy + (to.y - fy) * e;
        L.r = L.from.r + (to.r - L.from.r) * e;
        L.a = L.from.a + (to.a - L.from.a) * e;
      } else {
        L.from = null;
        L.x = to.x; L.y = to.y; L.r = to.r; L.a = to.a;
      }
      L.mx += (L.tmx - L.mx) * 0.07;
      L.my += (L.tmy - L.my) * 0.07;
      var ox = L.mx * w.innerWidth * 0.03;
      var oy = L.my * w.innerHeight * 0.02;
      lampEl.style.transform = 'translate3d(' + (L.x + ox).toFixed(1) + 'px,' + (L.y + oy).toFixed(1) + 'px,0) scale(' + L.r.toFixed(3) + ')';
      spotEl.style.opacity = L.a.toFixed(3);
      /* конус и пятно на окне первого экрана наклоняются вместе с лампой */
      if (beam && w.scrollY < stageTop + 400) {
        beam.style.transform = 'skewX(' + (L.mx * -3).toFixed(3) + 'deg)';
        if (lit) lit.style.setProperty('--mx', L.mx.toFixed(4));
      }
      var moving = Math.abs(L.tmx - L.mx) > 0.002 || Math.abs(L.tmy - L.my) > 0.002;
      if (p < 1 || moving) requestLamp();
    };

    var ioL = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        for (var i = 0; i < targets.length; i++) if (targets[i].el === en.target) targets[i].on = en.isIntersecting;
      });
      pick();
    }, { rootMargin: '-22% 0px -22% 0px', threshold: 0 });
    targets.forEach(function (t) { ioL.observe(t.el); });
    scrollJobs.push(function () { pick(); requestLamp(); });

    if (FINE) {
      w.addEventListener('pointermove', function (ev) {
        if (ev.pointerType && ev.pointerType !== 'mouse') return;
        L.tmx = (ev.clientX / w.innerWidth - 0.5) * 2;
        L.tmy = (ev.clientY / w.innerHeight - 0.5) * 2;
        requestLamp();
      }, { passive: true });
    }

    /* включаем свет, когда окно первого экрана уже поднялось */
    w.setTimeout(function () {
      root.classList.add('lamp-on');
      var first = targets[0] ? targetPos(targets[0]) : { x: w.innerWidth / 2, y: w.innerHeight / 2, r: 1 };
      L.x = first.x; L.y = first.y; L.r = first.r; L.a = 0;
      L.ready = true;
      pick();
      requestLamp();
    }, 700);
  }

  /* ---------- девять инструментов ---------- */
  var track = $('[data-feats]');
  if (track) {
    var list = $('.feats__list');
    var pin = $('.feats__pin', track);
    var tabs = $$('.feat', track);
    var screens = $$('.scr', track);
    var mqPin = w.matchMedia('(min-width: 1024px) and (min-height: 640px)');
    var cur = 0;
    var N = tabs.length;

    var setActive = function (i, scrollChip) {
      if (i === cur) return;
      cur = i;
      tabs.forEach(function (t, k) {
        t.classList.toggle('is-on', k === i);
        t.setAttribute('aria-pressed', k === i ? 'true' : 'false');
      });
      screens.forEach(function (s, k) { s.classList.toggle('is-on', k === i); });
      list.style.setProperty('--a', i);
      if (scrollChip && !mqPin.matches) {
        var chip = tabs[i];
        list.scrollTo({ left: chip.offsetLeft - (list.clientWidth - chip.offsetWidth) / 2, behavior: RM ? 'auto' : 'smooth' });
      }
    };
    tabs.forEach(function (t, k) { t.setAttribute('aria-pressed', k === 0 ? 'true' : 'false'); });

    /* первый экран включается, когда окно доехало до вьюпорта: иначе его демо никто не увидит */
    var view = $('.feats__view', track);
    if (view && HAS_IO && !RM) {
      screens[0].classList.remove('is-on');
      var ioV = new IntersectionObserver(function (entries) {
        if (!entries[0].isIntersecting) return;
        ioV.disconnect();
        screens[cur].classList.add('is-on');
      }, { threshold: 0.35 });
      ioV.observe(view);
    }

    var hh = function () { return parseFloat(getComputedStyle(root).getPropertyValue('--hh')) || 64; };
    scrollJobs.push(function () {
      if (!mqPin.matches) return;
      var r = track.getBoundingClientRect();
      var total = r.height - pin.offsetHeight;
      if (total <= 0) return;
      var p = clamp((hh() - r.top) / total, 0, 0.9999);
      setActive(Math.floor(p * N), false);
    });

    tabs.forEach(function (t, i) {
      t.addEventListener('click', function () {
        if (mqPin.matches) {
          var r = track.getBoundingClientRect();
          var total = r.height - pin.offsetHeight;
          var y = r.top + w.scrollY - hh() + total * ((i + 0.5) / N);
          w.scrollTo({ top: y, behavior: RM ? 'auto' : 'smooth' });
        } else {
          setActive(i, true);
        }
      });
    });
  }

  /* ---------- прожектор на карточках ---------- */
  if (FINE && !RM) {
    $$('.spot').forEach(function (card) {
      var g = d.createElement('i');
      g.className = 'spot__g';
      g.setAttribute('aria-hidden', 'true');
      var e = d.createElement('i');
      e.className = 'spot__e';
      e.setAttribute('aria-hidden', 'true');
      var ei = d.createElement('i');
      e.appendChild(ei);
      card.appendChild(g);
      card.appendChild(e);
      var raf = 0, x = 0, y = 0;
      card.addEventListener('pointermove', function (ev) {
        var r = card.getBoundingClientRect();
        x = ev.clientX - r.left;
        y = ev.clientY - r.top;
        if (raf) return;
        raf = w.requestAnimationFrame(function () {
          raf = 0;
          var tf = 'translate3d(' + x.toFixed(1) + 'px,' + y.toFixed(1) + 'px,0)';
          g.style.transform = tf;
          ei.style.transform = tf;
        });
      });
    });
  }

  /* ---------- старт за две минуты: линия шкалы и таймер ---------- */
  var tl = $('[data-timeline]');
  var timerEl = $('#timer');
  var fill = $('#tlFill');
  if (tl && timerEl && fill && !RM && HAS_IO) {
    var steps = $$('.tl__s', tl);
    var marks = [0, 0.25, 0.75];
    var show = function (p) {
      var sec = Math.round(120 * p);
      var m = Math.floor(sec / 60);
      var s = sec % 60;
      timerEl.textContent = '0' + m + ':' + (s < 10 ? '0' : '') + s;
      fill.style.transform = 'scaleX(' + p.toFixed(4) + ')';
      steps.forEach(function (st, i) { st.classList.toggle('is-on', p > marks[i] || (i === 0 && p > 0)); });
    };
    steps.forEach(function (st) { st.classList.remove('is-on'); });
    timerEl.textContent = '00:00';
    fill.style.transform = 'scaleX(0)';
    var ioT = new IntersectionObserver(function (entries) {
      if (!entries[0].isIntersecting) return;
      ioT.disconnect();
      tl.classList.add('in');
      w.setTimeout(function () { tween(3200, show, function () { show(1); }); }, 500);
    }, { threshold: 0.35 });
    ioT.observe(tl);
  } else if (tl) {
    tl.classList.add('in');
  }

  onScroll();
})();
