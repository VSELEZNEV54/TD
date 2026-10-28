/* TeacherDesk · внутренние страницы
   Живые кадры, статьи, хабы и бесплатные инструменты. Помощники берем из window.TD (main.js). */
(function () {
  'use strict';

  var TD = window.TD;
  if (!TD) return;
  var d = document;
  var w = window;
  var $ = TD.$, $$ = TD.$$, reduce = TD.reduce, NB = TD.NB;

  function money(n) { return TD.fmt(n) + NB + 'руб.'; }
  function num(el, def) { var v = parseFloat(String(el && el.value).replace(',', '.').replace(/\s/g, '')); return isNaN(v) ? (def || 0) : v; }
  function plural(n, one, few, many) {
    var a = n % 10, b = n % 100;
    return a === 1 && b !== 11 ? one : a >= 2 && a <= 4 && (b < 12 || b > 14) ? few : many;
  }

  /* ---------- живые кадры: циклы идут, только пока кадр на экране ---------- */
  var lives = $$('[data-live]');
  if (lives.length && !reduce && 'IntersectionObserver' in w) {
    var lio = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { e.target.classList.toggle('is-vis', e.isIntersecting && !d.hidden); });
    }, { threshold: 0.25 });
    lives.forEach(function (el) { lio.observe(el); });
    d.addEventListener('visibilitychange', function () {
      if (d.hidden) lives.forEach(function (el) { el.classList.remove('is-vis'); });
      else lives.forEach(function (el) { lio.unobserve(el); lio.observe(el); });
    });
  } else {
    lives.forEach(function (el) { el.classList.add('is-vis'); });
  }

  /* ---------- кадры с главной (своя копия, атрибут data-pd) ---------- */
  var Sequence = TD.Sequence, whenVisible = TD.whenVisible;
  $$('[data-pd]').forEach(function (el) {
    var kind = el.getAttribute('data-pd');

    /* лента дня: флажок «идет сейчас» едет, напоминание шлепается наклейкой */
    if (kind === 'tl') {
      var slap = $('.pd-slap', el), foot = slap && slap.parentNode;
      var sent = function (on) { if (slap) { slap.classList.toggle('is-on', on); foot.classList.toggle('is-sent', on); } };
      if (reduce) { sent(true); return; }
      var sA = Sequence([
        [0, function () { el.classList.remove('is-run'); el.classList.add('is-reset'); sent(false); }],
        [80, function () { el.classList.remove('is-reset'); el.classList.add('is-run'); }],
        [5200, function () { sent(true); }]
      ], 12000);
      whenVisible(el, sA.start, sA.stop, 0.3);
    }

    /* долги: напоминания уходят, Артем платит, сумма убывает. Кнопки можно нажать самому */
    if (kind === 'debt') {
      var sum = $('[data-pd-sum]', el);
      var amount = { s: 4200, a: 2600 };
      var names = { s: 'Соне Ветровой', a: 'Артему Дроздову' };
      var rows = {};
      $$('[data-pd-row]', el).forEach(function (li) { rows[li.getAttribute('data-pd-row')] = { li: li, btn: $('[data-pd-remind]', li), st: 0 }; });
      var shown = 6800;
      var setRow = function (key, st, pressed) {
        var r = rows[key];
        if (!r) return;
        r.st = st;
        if (st) { r.btn.setAttribute('data-state', st); r.btn.setAttribute('aria-disabled', 'true'); }
        else { r.btn.removeAttribute('data-state'); r.btn.removeAttribute('aria-disabled'); }
        TD.setSwap($('.pd-swap', r.btn), st);
        r.btn.setAttribute('aria-label', st === 0 ? 'Напомнить ' + names[key] + ' об оплате' : st === 1 ? 'Напоминание ' + names[key] + ' ушло' : 'Оплата получена');
        r.li.classList.toggle('is-paid', st === 2);
        if (pressed && !reduce) { r.btn.classList.add('is-press'); setTimeout(function () { r.btn.classList.remove('is-press'); }, 180); }
        var t = 6800;
        Object.keys(rows).forEach(function (k) { if (rows[k].st === 2) t -= amount[k]; });
        if (t !== shown) { TD.count(sum, shown, t, st ? 1000 : 0); shown = t; }
      };
      var took = false;
      var sB = Sequence([
        [0, function () { setRow('s', 0); setRow('a', 0); }],
        [1200, function () { setRow('s', 1, true); }],
        [1700, function () { setRow('a', 1, true); }],
        [4000, function () { setRow('a', 2); }]
      ], 11000);
      Object.keys(rows).forEach(function (key) {
        rows[key].btn.addEventListener('click', function () {
          if (rows[key].st !== 0) return;
          if (!took) { took = true; sB.stop(); }
          setRow(key, 1, true);
          if (key === 'a') setTimeout(function () { setRow('a', 2); }, reduce ? 0 : 2200);
        });
      });
      el.addEventListener('focusin', function () { if (took) return; took = true; sB.stop(); setRow('s', 0); setRow('a', 0); });
      if (!reduce) whenVisible(el, function () { if (!took) sB.start(); }, sB.stop, 0.3);
    }

    /* задание: восьмая задача получает галочку, ошибка уходит в колоду */
    if (kind === 'hw') {
      var hw = $('.pd-hw', el), n8 = $('[data-pd-hw8]', el), cnt = $('[data-pd-n]', el);
      var done = function (on) { n8.classList.toggle('is-ok', on); cnt.textContent = on ? '8' : '7'; hw.classList.toggle('is-done', on); };
      if (reduce) { done(true); return; }
      var sC = Sequence([[0, function () { done(false); }], [1800, function () { done(true); }]], 10000);
      whenVisible(el, sC.start, sC.stop, 0.3);
    }

    /* ассистент печатает план по словам */
    if (kind === 'ai') {
      var ai = $('.pd-ai', el);
      var lines = $$('.pd-ai__plan li', el).map(function (li) {
        var span = $('[data-pd-type]', li);
        var words = span.textContent.split(/(\s+)/);
        span.textContent = '';
        var ws = [];
        words.forEach(function (wd) {
          if (/^\s+$/.test(wd)) { span.appendChild(d.createTextNode(wd)); return; }
          var s = d.createElement('span'); s.className = 'w'; s.textContent = wd; span.appendChild(s); ws.push(s);
        });
        return { li: li, words: ws };
      });
      var showAll = function () { lines.forEach(function (l) { l.li.classList.add('is-go', 'is-done'); l.words.forEach(function (x) { x.classList.add('is-in'); }); }); };
      if (reduce) { showAll(); return; }
      ai.classList.add('is-live');
      var played = false;
      whenVisible(el, function () {
        if (played) return;
        played = true;
        ai.classList.add('is-typing');
        var t = 500;
        lines.forEach(function (l, i) {
          setTimeout(function () { l.li.classList.add('is-go'); }, t);
          l.words.forEach(function (x) { t += 70; setTimeout(function () { x.classList.add('is-in'); }, t); });
          t += 240;
          setTimeout(function () { l.li.classList.add('is-done'); if (i === lines.length - 1) ai.classList.remove('is-typing'); }, t);
        });
      }, null, 0.3);
    }
  });

  /* Тарифы с ползунком, знак T в призыве, превью таблицы и окно «Задать свой вопрос»
     ведет home.js: внутренние страницы подключают его вместе с главной */

  /* ---------- «Знакомо?»: сообщения приходят по одному, счетчик растет ---------- */
  $$('[data-feed]').forEach(function (box) {
    var msgs = $$('[data-feed-msg]', box);
    var n = $('[data-feed-n]', box), fix = $('[data-feed-fix]', box);
    if (reduce || !msgs.length) return;
    var total = parseInt(box.getAttribute('data-feed-total') || msgs.length, 10);
    box.classList.add('is-armed');
    if (n) n.textContent = '0';
    var played = false;
    whenVisible(box, function () {
      if (played) return;
      played = true;
      box.classList.add('is-typing');
      var step = 850;
      msgs.forEach(function (m, i) { setTimeout(function () { m.classList.add('is-in'); }, 500 + i * step); });
      TD.count(n, 0, total, 500 + msgs.length * step);
      setTimeout(function () {
        box.classList.remove('is-typing');
        if (fix) fix.classList.add('is-in');
      }, 700 + msgs.length * step);
    }, null, 0.35);
  });

  /* ---------- мини-ролик функции: главы по очереди, детали появляются по времени ---------- */
  $$('[data-mfilm]').forEach(function (film) {
    var scenes = $$('.msc', film), chs = $$('[data-ch]', film), play = $('[data-mf-play]', film);
    var cur = 0, timers = [], running = false, paused = false;
    /* печать по словам: каждое слово в своей обертке */
    $$('[data-fx="type"]', film).forEach(function (el) {
      var parts = el.textContent.split(/(\s+)/);
      el.textContent = '';
      parts.forEach(function (p) {
        if (/^\s+$/.test(p)) { el.appendChild(d.createTextNode(p)); return; }
        if (!p) return;
        var s = d.createElement('span'); s.className = 'w'; s.textContent = p; el.appendChild(s);
      });
    });
    var reset = function (sc) {
      $$('[data-at]', sc).forEach(function (el) {
        el.classList.remove('is-in');
        if (el.getAttribute('data-fx') === 'count') el.textContent = TD.fmt(+el.getAttribute('data-from') || 0);
        $$('.w', el).forEach(function (w) { w.classList.remove('is-in'); });
      });
    };
    var fire = function (el) {
      el.classList.add('is-in');
      var fx = el.getAttribute('data-fx');
      if (fx === 'count') TD.count(el, +el.getAttribute('data-from') || 0, +el.getAttribute('data-to'), 900);
      if (fx === 'type') {
        var ws = $$('.w', el), len = +el.getAttribute('data-len') || 900;
        ws.forEach(function (w, k) { timers.push(setTimeout(function () { w.classList.add('is-in'); }, k * len / Math.max(1, ws.length))); });
      }
    };
    var showAll = function (sc) {
      $$('[data-at]', sc).forEach(function (el) {
        el.classList.add('is-in');
        if (el.getAttribute('data-fx') === 'count') el.textContent = TD.fmt(+el.getAttribute('data-to'));
        $$('.w', el).forEach(function (w) { w.classList.add('is-in'); });
      });
    };
    var mark = function (i) {
      scenes.forEach(function (s, k) { s.classList.toggle('is-on', k === i); });
      chs.forEach(function (c, k) {
        c.classList.toggle('is-on', k === i);
        c.classList.toggle('is-done', k < i);
        if (k === i) c.setAttribute('aria-current', 'step'); else c.removeAttribute('aria-current');
      });
    };
    var show = function (i) {
      timers.forEach(clearTimeout); timers = [];
      cur = i;
      mark(i);
      var sc = scenes[i];
      if (reduce) { showAll(sc); return; }
      reset(sc);
      var dur = +sc.getAttribute('data-dur') || 5200;
      film.style.setProperty('--dur', dur + 'ms');
      TD.replay(chs[i], 'is-run');
      $$('[data-at]', sc).forEach(function (el) {
        timers.push(setTimeout(function () { fire(el); }, +el.getAttribute('data-at')));
      });
      timers.push(setTimeout(function () { show((cur + 1) % scenes.length); }, dur));
    };
    var stop = function () {
      timers.forEach(clearTimeout); timers = [];
      running = false;
      film.classList.add('is-hold');
    };
    var start = function () {
      if (running || paused) return;
      running = true;
      film.classList.remove('is-hold');
      show(cur);
    };
    film.classList.add('is-ready');
    chs.forEach(function (c, k) {
      c.addEventListener('click', function () {
        paused = false; film.classList.remove('is-paused');
        running = true; film.classList.remove('is-hold');
        show(k);
      });
    });
    if (play) play.addEventListener('click', function () {
      paused = !paused;
      film.classList.toggle('is-paused', paused);
      if (paused) stop(); else start();
    });
    if (reduce) { show(0); return; }
    mark(0);
    var vis = false;
    if ('IntersectionObserver' in w) {
      new IntersectionObserver(function (es) {
        vis = es[0].isIntersecting;
        if (vis && !d.hidden) start(); else stop();
      }, { threshold: 0.35 }).observe(film);
      d.addEventListener('visibilitychange', function () { if (d.hidden) stop(); else if (vis) start(); });
    } else { start(); }
  });

  /* ---------- до и после: переключатель, сам переворачивается один раз при первом показе ---------- */
  $$('[data-flip]').forEach(function (fl) {
    var btns = $$('.flip__b', fl);
    var touched = false;
    var set = function (side) {
      fl.setAttribute('data-side', side);
      btns.forEach(function (b) {
        var on = b.getAttribute('data-side') === String(side);
        b.setAttribute('aria-selected', on ? 'true' : 'false');
        b.setAttribute('tabindex', on ? '0' : '-1');
      });
    };
    btns.forEach(function (b, i) {
      b.addEventListener('click', function () { touched = true; set(b.getAttribute('data-side')); });
      b.addEventListener('keydown', function (e) {
        if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') { e.preventDefault(); touched = true; var o = btns[1 - i]; set(o.getAttribute('data-side')); o.focus(); }
      });
    });
    fl.classList.add('is-ready');
    if (reduce) { set(1); return; }
    set(0);
    whenVisible(fl, function () { setTimeout(function () { if (!touched) set(1); }, 1600); }, null, 0.5);
  });

  /* ---------- вкладки функций: сами листаются, пока человек не выбрал вкладку ---------- */
  $$('[data-tabs]').forEach(function (tb) {
    var tabs = $$('[role="tab"]', tb), panes = $$('[data-pane]', tb);
    var cur = 0, auto = !reduce, timer = null, vis = false, STEP = 6500;
    var set = function (i, focus) {
      cur = i;
      tabs.forEach(function (t, k) {
        var on = k === i;
        t.setAttribute('aria-selected', on ? 'true' : 'false');
        t.setAttribute('tabindex', on ? '0' : '-1');
        t.classList.toggle('is-run', on && auto);
      });
      panes.forEach(function (p, k) { p.classList.toggle('is-on', k === i); });
      if (focus) tabs[i].focus();
      if (auto) TD.replay(tabs[i], 'is-run');
    };
    var tick = function () {
      clearTimeout(timer);
      if (!auto || !vis) return;
      timer = setTimeout(function () { set((cur + 1) % tabs.length); tick(); }, STEP);
    };
    tb.style.setProperty('--step', STEP + 'ms');
    tabs.forEach(function (t, k) {
      t.addEventListener('click', function () { auto = false; clearTimeout(timer); tb.classList.add('is-manual'); set(k); });
      t.addEventListener('keydown', function (e) {
        var dir = { ArrowDown: 1, ArrowRight: 1, ArrowUp: -1, ArrowLeft: -1 }[e.key];
        if (!dir) return;
        e.preventDefault(); auto = false; clearTimeout(timer); tb.classList.add('is-manual');
        set((k + dir + tabs.length) % tabs.length, true);
      });
    });
    tb.classList.add('is-ready');
    set(0);
    if (reduce) return;
    whenVisible(tb, function () { vis = true; tick(); }, function () { vis = false; clearTimeout(timer); }, 0.3);
  });

  /* ---------- статья: полоса прогресса чтения и активный пункт содержания ---------- */
  var prog = $('[data-rprog]');
  var body = $('.art__body');
  if (prog && body) {
    var ticking = false;
    var heads = $$('h2[id]', body);
    var links = $$('[data-toc] a');
    var upd = function () {
      ticking = false;
      var r = body.getBoundingClientRect();
      var p = Math.min(1, Math.max(0, -r.top / Math.max(1, r.height - w.innerHeight * 0.6)));
      prog.style.setProperty('--p', p.toFixed(4));
      var cur = 0;
      heads.forEach(function (h, i) { if (h.getBoundingClientRect().top < w.innerHeight * 0.3) cur = i; });
      links.forEach(function (a, i) { a.classList.toggle('is-on', i === cur); });
    };
    w.addEventListener('scroll', function () { if (!ticking) { ticking = true; requestAnimationFrame(upd); } }, { passive: true });
    upd();
  }

  /* ---------- блог: фильтр по рубрикам ---------- */
  var chips = $('[data-rchips]');
  if (chips) {
    var cards = $$('.posts3--hub > li');
    chips.addEventListener('click', function (e) {
      var b = e.target.closest('[data-rubric]');
      if (!b) return;
      var r = b.getAttribute('data-rubric');
      $$('[data-rubric]', chips).forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
      cards.forEach(function (li) { li.classList.toggle('is-hidden', !!r && li.getAttribute('data-rubric') !== r); });
    });
  }

  /* ---------- копирование текста ---------- */
  function copyText(text, btn) {
    var done = function () {
      if (!btn) return;
      var lbl = $('span', btn);
      var old = lbl ? lbl.textContent : '';
      btn.classList.add('is-done');
      if (lbl) lbl.textContent = 'Скопировано';
      setTimeout(function () { btn.classList.remove('is-done'); if (lbl) lbl.textContent = old; }, 1600);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done, function () { fallback(text); done(); });
    } else { fallback(text); done(); }
  }
  function fallback(text) {
    var ta = d.createElement('textarea');
    ta.value = text; ta.setAttribute('readonly', ''); ta.style.position = 'fixed'; ta.style.opacity = '0';
    d.body.appendChild(ta); ta.select();
    try { d.execCommand('copy'); } catch (e) { /* без буфера обмена текст остается выделенным */ }
    d.body.removeChild(ta);
  }
  d.addEventListener('click', function (e) {
    var b = e.target.closest('[data-copy]');
    if (!b) return;
    var sel = b.getAttribute('data-copy');
    var src = sel ? $(sel) : (b.closest('.ad') && $('.ad__t', b.closest('.ad')));
    if (src) copyText(src.value !== undefined && src.tagName === 'TEXTAREA' ? src.value : src.innerText.trim(), b);
  });

  /* ---------- калькулятор дохода ---------- */
  var calc = $('[data-calc]');
  if (calc) (function () {
    var f = calc.elements;
    var WEEKS = 4.33;
    var out = $('[data-calc-out]');
    var mode = function () { return (calc.querySelector('[name=mode]:checked') || {}).value || 'income'; };
    var set = function (sel, text) { var el = $(sel, out); if (el) el.textContent = text; };
    var upd = function () {
      var m = mode();
      $$('[data-mode]', calc).forEach(function (el) {
        el.hidden = el.getAttribute('data-mode') !== m;
        var input = $('input', el);
        if (input) input.disabled = el.hidden;
      });
      var active = [m === 'income' ? f.rate : f.target, f.perweek, f.cancel, f.months].filter(Boolean);
      var invalid = active.some(function (el) { return el.value === '' || !el.validity.valid; });
      var perWeek = num(f.perweek, 0);
      var cancel = num(f.cancel, 0) / 100;
      var tax = num(calc.querySelector('[name=tax]:checked'), 0) / 100;
      var months = num(f.months, 12);
      var lessons = perWeek * WEEKS * (1 - cancel);
      set('[data-o-main-l]', m === 'income' ? 'Доход в месяц после налога' : 'Ставка за урок');
      set('[data-o-year-l]', 'За ' + months + NB + plural(months, 'рабочий месяц', 'рабочих месяца', 'рабочих месяцев'));
      if (invalid || (m === 'rate' && lessons === 0)) {
        set('[data-o-main]', '...');
        ['[data-o-year]', '[data-o-gross]', '[data-o-lessons]', '[data-o-tax]'].forEach(function (sel) { set(sel, 'Нет данных'); });
        set('[data-o-explain]', invalid ? 'Проверьте поля: значения должны быть в указанных пределах.' : 'Укажите хотя бы один урок в неделю, чтобы рассчитать ставку.');
        out.classList.add('is-empty');
        return;
      }
      out.classList.remove('is-empty');
      var rate, gross, net;
      if (m === 'income') {
        rate = num(f.rate, 0);
        gross = rate * lessons;
        net = gross * (1 - tax);
        set('[data-o-main]', TD.fmt(net));
        set('[data-o-explain]', 'При заданной нагрузке и ' + TD.fmt(cancel * 100) + '% неоплаченных отмен');
      } else {
        var target = num(f.target, 0);
        rate = Math.ceil(target / (1 - tax) / lessons / 50) * 50;
        gross = rate * lessons;
        net = gross * (1 - tax);
        set('[data-o-main]', TD.fmt(rate));
        set('[data-o-explain]', 'Округлено вверх до 50 руб. Такой урок дает около ' + money(net) + ' в месяц после налога.');
      }
      set('[data-o-year]', money(net * months));
      set('[data-o-gross]', money(gross));
      set('[data-o-lessons]', Math.round(lessons) + NB + plural(Math.round(lessons), 'урок', 'урока', 'уроков'));
      set('[data-o-tax]', money(gross - net));
    };
    calc.addEventListener('input', upd);
    calc.addEventListener('change', upd);
    calc.addEventListener('submit', function (e) { e.preventDefault(); upd(); });
    upd();
  })();

  /* ---------- шаблон таблицы учета: долг считается по формуле ---------- */
  var sheet = $('[data-ledger]');
  if (sheet) (function () {
    var upd = function () {
      var total = 0, sumL = 0;
      $$('tbody tr', sheet).forEach(function (tr) {
        var rate = num($('[name=rate]', tr)), les = num($('[name=lessons]', tr)), paid = num($('[name=paid]', tr));
        var debt = rate * les - paid;
        total += debt; sumL += les;
        var cell = $('[data-debt]', tr);
        cell.textContent = TD.fmt(debt);
        cell.classList.toggle('is-debt', debt > 0);
      });
      $('[data-total]', sheet).textContent = TD.fmt(total);
      $('[data-total-l]', sheet).textContent = TD.fmt(sumL);
    };
    sheet.addEventListener('input', upd);
    upd();
  })();

  /* ---------- шаблон расписания: печать только сетки ---------- */
  $$('[data-print]').forEach(function (b) {
    b.addEventListener('click', function () {
      d.documentElement.classList.add('is-print');
      w.print();
      setTimeout(function () { d.documentElement.classList.remove('is-print'); }, 400);
    });
  });

  /* ---------- конструктор объявления ---------- */
  var adf = $('[data-adform]');
  if (adf) (function () {
    var f = adf.elements;
    var outT = $('[data-ad-out]');
    var v = function (n) { return (f[n] && f[n].value || '').trim(); };
    var pick = function (n) { var c = adf.querySelector('[name=' + n + ']:checked'); return c ? c.value : ''; };
    var upd = function () {
      var subj = v('subject') || 'математике';
      var who = v('who') || 'школьников 5-11 классов';
      var exp = num(f.exp, 0);
      var lines = [];
      lines.push('Репетитор по ' + subj + (v('goal') ? ', ' + v('goal') : '') + '.');
      lines.push('Занимаюсь с ' + who + (exp ? '. Опыт ' + exp + NB + plural(exp, 'год', 'года', 'лет') : '') + '.');
      var fmt = pick('format');
      if (fmt) lines.push('Формат: ' + fmt + '.');
      if (v('about')) lines.push(v('about').replace(/\s+$/, '').replace(/([^.])$/, '$1.'));
      lines.push('Первое занятие: знакомство и диагностика, чтобы понять уровень и составить план.');
      if (num(f.price, 0)) lines.push('Стоимость: ' + money(num(f.price, 0)) + ' за ' + (v('len') || '60') + NB + 'минут.');
      lines.push('Расписание, задания и оплаты веду в личном кабинете: ученик всегда видит в своем кабинете, что задано и когда урок, а родитель раз в месяц получает отчет.');
      if (v('name')) lines.push(v('name'));
      outT.textContent = lines.join('\n');
    };
    adf.addEventListener('input', upd);
    adf.addEventListener('change', upd);
    upd();
  })();

  /* ---------- генератор договора: превью и файл docx ---------- */
  var doc = $('[data-docform]');
  if (doc) (function () {
    var f = doc.elements;
    var marks = {};
    var state = $('[data-doc-state]', doc);
    var required = $$('[required]', doc);
    if (f.date && !f.date.value) {
      var today = new Date();
      var pad = function (v) { return v < 10 ? '0' + v : String(v); };
      f.date.value = today.getFullYear() + '-' + pad(today.getMonth() + 1) + '-' + pad(today.getDate());
    }
    $$('[data-f]', d).forEach(function (m) { (marks[m.getAttribute('data-f')] = marks[m.getAttribute('data-f')] || []).push(m); });
    var val = function (n) {
      var el = f[n];
      if (!el) return '';
      if (el.length && !el.tagName) { var c = doc.querySelector('[name=' + n + ']:checked'); return c ? c.value : ''; }
      var value = (el.value || '').trim();
      if (value && el.type === 'date') {
        value = new Date(value + 'T12:00:00').toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' });
      }
      if (value && n === 'price') value = TD.fmt(num(el));
      return value;
    };
    var upd = function (e) {
      if (f.until && f.date) f.until.min = f.date.value;
      required.forEach(function (el) { el.setCustomValidity(el.value.trim() ? '' : 'Заполните это поле.'); });
      Object.keys(marks).forEach(function (k) {
        var t = val(k) || marks[k][0].getAttribute('data-ph');
        marks[k].forEach(function (m) {
          if (m.textContent !== t) {
            m.textContent = t;
            if (e && e.target && e.target.name === k) TD.replay(m, 'is-new');
          }
        });
      });
      if (state) {
        var left = required.filter(function (el) { return !el.validity.valid; }).length;
        state.textContent = left ? 'Осталось заполнить или проверить ' + left + NB + plural(left, 'поле', 'поля', 'полей') + '.' : 'Все поля заполнены. Проверьте текст договора и скачайте файл.';
      }
    };
    doc.addEventListener('input', upd);
    doc.addEventListener('change', upd);
    upd();
    var download = function () {
      upd();
      if (!doc.reportValidity()) return;
      var paper = $('[data-doc]');
      var paras = $$('h3, p', paper).map(function (p) { return { text: p.innerText.trim(), head: p.tagName === 'H3' }; });
      var blob = docx(paras);
      var a = d.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = 'dogovor-repetitora.docx';
      d.body.appendChild(a); a.click();
      if (state) state.textContent = 'Договор скачан. Файл можно открыть и отредактировать в Word или Google Документах.';
      setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 500);
    };
    var dl = $('[data-docx]');
    if (dl) dl.addEventListener('click', download);
    doc.addEventListener('submit', function (e) { e.preventDefault(); download(); });
  })();

  /* docx без библиотек: три XML-файла в zip без сжатия */
  function docx(paras) {
    var esc = function (s) { return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); };
    var body = paras.map(function (p) {
      var pr = p.head ? '<w:pPr><w:jc w:val="center"/><w:spacing w:after="200"/></w:pPr>' : '<w:pPr><w:spacing w:after="120"/><w:jc w:val="both"/></w:pPr>';
      var rpr = p.head ? '<w:rPr><w:b/><w:sz w:val="26"/></w:rPr>' : '<w:rPr><w:sz w:val="24"/></w:rPr>';
      return '<w:p>' + pr + '<w:r>' + rpr + '<w:t xml:space="preserve">' + esc(p.text) + '</w:t></w:r></w:p>';
    }).join('');
    var files = [
      ['[Content_Types].xml', '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>'],
      ['_rels/.rels', '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>'],
      ['word/document.xml', '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>' + body + '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1134" w:right="850" w:bottom="1134" w:left="1418" w:header="708" w:footer="708" w:gutter="0"/></w:sectPr></w:body></w:document>']
    ];
    return new Blob([zip(files)], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });
  }

  var CRC = (function () {
    var t = [];
    for (var n = 0; n < 256; n++) { var c = n; for (var k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0; }
    return t;
  })();
  function crc32(b) { var c = 0xFFFFFFFF; for (var i = 0; i < b.length; i++) c = CRC[(c ^ b[i]) & 0xFF] ^ (c >>> 8); return (c ^ 0xFFFFFFFF) >>> 0; }

  function zip(files) {
    var enc = new TextEncoder();
    var parts = [], central = [], offset = 0;
    var u16 = function (v) { return [v & 255, (v >>> 8) & 255]; };
    var u32 = function (v) { return [v & 255, (v >>> 8) & 255, (v >>> 16) & 255, (v >>> 24) & 255]; };
    files.forEach(function (f) {
      var name = enc.encode(f[0]), data = enc.encode(f[1]), crc = crc32(data);
      var head = [].concat([0x50, 0x4b, 3, 4], u16(20), u16(0x0800), u16(0), u16(0), u16(0x21), u32(crc), u32(data.length), u32(data.length), u16(name.length), u16(0));
      parts.push(new Uint8Array(head), name, data);
      central.push(new Uint8Array([].concat([0x50, 0x4b, 1, 2], u16(20), u16(20), u16(0x0800), u16(0), u16(0), u16(0x21), u32(crc), u32(data.length), u32(data.length), u16(name.length), u16(0), u16(0), u16(0), u16(0), u32(0), u32(offset))), name);
      offset += head.length + name.length + data.length;
    });
    var size = central.reduce(function (s, a) { return s + a.length; }, 0);
    var end = new Uint8Array([].concat([0x50, 0x4b, 5, 6], u16(0), u16(0), u16(files.length), u16(files.length), u32(size), u32(offset), u16(0)));
    return new Blob(parts.concat(central, [end]));
  }

  /* ---------- ИИ-генераторы: пока пример ответа, без запроса к серверу ---------- */
  $$('[data-gen]').forEach(function (form) {
    var res = $(form.getAttribute('data-gen'));
    if (!res) return;
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var f = form.elements;
      var tpl = $('template', res);
      res.classList.add('is-busy');
      $('[data-gen-empty]', res).hidden = true;
      var list = $('[data-gen-list]', res);
      list.innerHTML = '';
      var head = $('[data-gen-head]', res);
      var subj = (f.subject && f.subject.value) || '';
      var topic = (f.topic && f.topic.value.trim()) || (f.topic && f.topic.placeholder) || '';
      var grade = (f.grade && f.grade.value) || '';
      var len = parseInt((f.len && f.len.value) || '60', 10);
      head.textContent = [subj, topic, grade].filter(Boolean).join(' · ');
      setTimeout(function () {
        res.classList.remove('is-busy');
        var items = JSON.parse(tpl.innerHTML);
        var k = len / 60;
        items.forEach(function (it, i) {
          var li = d.createElement('li');
          li.style.setProperty('--i', i);
          var t = d.createElement('span');
          t.textContent = it[0].replace('{тема}', topic.toLowerCase());
          if (it[2]) { var s = d.createElement('small'); s.textContent = it[2]; t.appendChild(s); }
          li.appendChild(t);
          var tm = d.createElement('time');
          tm.textContent = it[1] ? Math.max(5, Math.round(it[1] * k / 5) * 5) + NB + 'мин' : '';
          li.appendChild(tm);
          list.appendChild(li);
        });
      }, reduce ? 0 : 1600);
    });
  });

  /* ---------- раздел «Продукт»: оглавление задач следит за прокруткой, как «День репетитора» на главной ---------- */
  var pspy = $('[data-pspy]'), pcells = $('[data-pcells]');
  if (pspy && pcells) (function () {
    var links = $$('a', pspy);
    var cells = links.map(function (a) { return d.getElementById(a.getAttribute('href').slice(1)); });
    var phone = TD.phone, ticking = false, at = 0;
    var mark = function () {
      ticking = false;
      var best = 0, bestD = Infinity;
      var mid = phone.matches ? pcells.getBoundingClientRect().left + pcells.clientWidth / 2 : w.innerHeight * 0.45;
      cells.forEach(function (c, i) {
        if (!c) return;
        var r = c.getBoundingClientRect();
        var dist = phone.matches ? Math.abs(r.left + r.width / 2 - mid) : Math.abs(r.top + r.height / 2 - mid);
        if (dist < bestD) { bestD = dist; best = i; }
      });
      links.forEach(function (a, i) {
        a.classList.toggle('is-on', i === best);
        if (i === best) { a.setAttribute('aria-current', 'true'); } else { a.removeAttribute('aria-current'); }
      });
      if (phone.matches && best !== at) {
        var on = links[best];
        pspy.scrollTo({ left: on.offsetLeft - (pspy.clientWidth - on.offsetWidth) / 2, behavior: reduce ? 'auto' : 'smooth' });
      }
      at = best;
    };
    var req = function () { if (!ticking) { ticking = true; requestAnimationFrame(mark); } };
    w.addEventListener('scroll', req, { passive: true });
    pcells.addEventListener('scroll', req, { passive: true });
    w.addEventListener('resize', req);
    links.forEach(function (a, i) {
      a.addEventListener('click', function (e) {
        if (!phone.matches || !cells[i]) return;
        e.preventDefault();
        var pad = parseFloat(getComputedStyle(pcells).paddingLeft) || 0;
        pcells.scrollTo({ left: cells[i].offsetLeft - pcells.offsetLeft - pad, behavior: reduce ? 'auto' : 'smooth' });
      });
    });
    mark();
  })();
})();
