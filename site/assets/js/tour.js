/* TeacherDesk · показ кабинета на первом экране главной.
   Сценарий это плоский список шагов со своими длительностями: курсор едет к элементу, нажимает,
   экран меняется. Часы идут только пока окно на экране, вкладка активна и показ не на паузе. */
(function () {
  'use strict';

  var root = document.querySelector('[data-tour]');
  if (!root) return;
  var $ = function (s, r) { return (r || root).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || root).querySelectorAll(s)); };

  var view = $('[data-tour-view]');
  var app = $('[data-tour-app]');
  var cursor = $('[data-tour-cursor]');
  var tap = $('[data-tour-tap]');
  var toastBox = $('[data-tour-toast]');
  var ctl = $('.tctl');
  var playBtn = $('[data-tour-play]');
  var chips = $$('[data-tour-go]');
  /* на внутренних страницах показ начинается с раздела этой страницы */
  var ROUTE = (root.getAttribute('data-tour-route') || 'home,schedule,students,tasks,chats,money').split(',');
  var URLS = { home: 'главная', schedule: 'расписание', students: 'ученики', tasks: 'задания', chats: 'чаты', money: 'финансы', lesson: 'живой урок', ai: 'ассистент', me: 'главная', myhw: 'задания', mycards: 'мои ошибки' };
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- масштаб ---------- */
  var cx = 0, cy = 0, lastTarget = null;
  function place(x, y) {
    cx = x; cy = y;
    cursor.style.transform = 'translate(' + x.toFixed(1) + 'px,' + y.toFixed(1) + 'px)';
  }
  function pointOf(el) {
    var r = el.getBoundingClientRect(), v = view.getBoundingClientRect();
    return { x: r.left - v.left + r.width / 2, y: r.top - v.top + r.height / 2 };
  }
  /* первый замер делает ResizeObserver сразу после раскладки, и только после него идет показ:
     при загрузке скрипт не заставляет браузер считать страницу раньше времени */
  var fitted = false, initDone = false;
  function fit() {
    var w = parseFloat(getComputedStyle(root).getPropertyValue('--w')) || 1200;
    root.style.setProperty('--s', (view.clientWidth / w).toFixed(4));
    if (!fitted) {
      fitted = true;
      /* курсор выезжает из правого нижнего угла окна */
      place(view.clientWidth * .78, view.clientHeight * .86);
      if (initDone) sync();
    } else if (lastTarget && lastTarget.offsetParent) { var p = pointOf(lastTarget); place(p.x, p.y); }
  }
  root.classList.add('is-ready');
  if (window.ResizeObserver) new ResizeObserver(fit).observe(view);
  else { fit(); window.addEventListener('resize', fit); }

  /* ---------- состояние: все изменения записываются, чтобы вернуть кабинет в начало ---------- */
  var undo = [];
  function on(sel, cls) {
    var el = typeof sel === 'string' ? $(sel) : sel;
    var had = el.classList.contains(cls);
    el.classList.add(cls);
    undo.push(function () { el.classList.toggle(cls, had); });
  }
  function off(sel, cls) {
    var el = typeof sel === 'string' ? $(sel) : sel;
    var had = el.classList.contains(cls);
    el.classList.remove(cls);
    undo.push(function () { el.classList.toggle(cls, had); });
  }
  function text(sel, val) {
    $$(sel).forEach(function (el) {
      var was = el.textContent;
      el.textContent = val;
      undo.push(function () { el.textContent = was; });
    });
  }
  function setY(el, y) { el.style.setProperty('--y', y); }

  var screen = 'home';
  function show(name) {
    screen = name;
    $$('.ts', app).forEach(function (s) { s.classList.toggle('is-on', s.getAttribute('data-s') === name); });
    $$('[data-nav]', app).forEach(function (n) { n.classList.toggle('is-on', n.getAttribute('data-nav') === name); });
    $('[data-tour-url]').textContent = URLS[name];
    toastBox.classList.remove('is-on');
  }
  function hover(el) {
    $$('.is-hover', app).forEach(function (h) { h.classList.remove('is-hover'); });
    if (el) el.classList.add('is-hover');
  }
  function resetAll() {
    while (undo.length) undo.pop()();
    $$('.ts__scroll', app).forEach(function (s) { setY(s, 0); });
    hover(null);
    toastBox.classList.remove('is-on');
  }
  function toast(title, sub) {
    $('[data-toast-t]').textContent = title;
    $('[data-toast-s]').textContent = sub;
    toastBox.classList.add('is-on');
  }
  var money = function (n) { return String(Math.round(n)).replace(/\B(?=(\d{3})+$)/g, ' '); };

  /* ---------- шаги сценария ---------- */
  var OPS = [], CH = [];
  function add(d, start, tick) { OPS.push({ d: d, start: start, tick: tick }); }
  function wait(ms) { add(ms); }
  function act(fn) { add(0, fn); }
  function move(sel, d) {
    var sx, sy, tx, ty, nx, ny, el;
    d = d || 850;
    add(d, function () {
      el = $(sel);
      var p = pointOf(el);
      sx = cx; sy = cy; tx = p.x; ty = p.y;
      /* путь чуть выгнут, как у руки */
      var bow = Math.min(36, Math.hypot(tx - sx, ty - sy) * .08);
      nx = -(ty - sy) / (Math.hypot(tx - sx, ty - sy) || 1) * bow;
      ny = (tx - sx) / (Math.hypot(tx - sx, ty - sy) || 1) * bow;
      lastTarget = el;
    }, function (p) {
      var e = p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2;
      var b = Math.sin(p * Math.PI);
      place(sx + (tx - sx) * e + nx * b, sy + (ty - sy) * e + ny * b);
      if (p >= .8) hover(el);
    });
  }
  function click(fn) {
    add(260, function () {
      cursor.classList.add('is-down');
      if (lastTarget) lastTarget.classList.add('is-press');
      tap.style.left = cx + 'px'; tap.style.top = cy + 'px';
      tap.classList.remove('is-on'); void tap.offsetWidth; tap.classList.add('is-on');
    }, function (p) {
      if (p >= 1) {
        cursor.classList.remove('is-down');
        if (lastTarget) lastTarget.classList.remove('is-press');
        hover(null);
        if (fn) fn();
      }
    });
  }
  function scrollTo(box, sel, d) {
    var el, from, to;
    add(d || 2200, function () {
      el = $(box);
      from = parseFloat(el.style.getPropertyValue('--y')) || 0;
      var max = Math.max(0, el.scrollHeight - el.parentNode.clientHeight);
      if (sel === 'end') { to = max; return; }
      if (sel === 'top') { to = 0; return; }
      var s = parseFloat(getComputedStyle(root).getPropertyValue('--s')) || 1;
      var t = $(sel, el).getBoundingClientRect(), b = el.getBoundingClientRect();
      to = Math.min(max, (t.top - b.top) / s - 16);
      /* блок уже целиком на экране: не листаем */
      if ((t.bottom - b.top) / s - from <= el.parentNode.clientHeight) to = from;
    }, function (p) {
      var e = p < .5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2;
      setY(el, (from + (to - from) * e).toFixed(1));
    });
  }
  function type(sel, str, d) {
    var el;
    add(d || 1400, function () { el = $(sel); el.textContent = ''; undo.push(function () { el.textContent = ''; }); },
      function (p) { el.textContent = str.slice(0, Math.round(p * str.length)); });
  }
  function count(sel, from, to, d) {
    var el;
    add(d || 900, function () { el = $(sel); undo.push(function () { el.textContent = money(from); }); },
      function (p) { el.textContent = money(from + (to - from) * (1 - Math.pow(1 - p, 3))); });
  }
  /* начало раздела: курсор едет к пункту меню и нажимает. Кнопка под окном прыгает сразу после нажатия */
  function chapter(name, firstWait) {
    CH.push({ name: name, at: OPS.length });
    if (firstWait) wait(firstWait);
    move('[data-nav="' + name + '"]', 900);
    click(function () { show(name); });
    CH[CH.length - 1].jump = OPS.length;
  }

  var SCENES = {};
  /* Главная */
  SCENES.home = function () {
  chapter('home', 500);
  wait(500);
  scrollTo('[data-s="home"] .ts__scroll', '[data-home-debts]', 1200);
  move('[data-home-debts]', 900);
  wait(500);
  scrollTo('[data-s="home"] .ts__scroll', 'end', 2200);
  wait(1200);
  scrollTo('[data-s="home"] .ts__scroll', 'top', 1300);
  wait(200);
  };

  /* Расписание: карточка урока, затем новый урок */
  SCENES.schedule = function () {
  chapter('schedule');
  wait(800);
  move('[data-lesson]');
  click(function () { on('[data-drawer="lesson"]', 'is-on'); });
  wait(2600);
  move('[data-drawer="lesson"] [data-close]', 700);
  click(function () { off('[data-drawer="lesson"]', 'is-on'); });
  wait(350);
  move('[data-create]');
  click(function () { on('[data-modal]', 'is-on'); });
  wait(250);
  type('[data-type-student]', 'Катя Соколова, химия', 900);
  wait(450);
  move('[data-save]', 650);
  click(function () {
    off('[data-modal]', 'is-on');
    on('[data-newlesson]', 'is-on');
    text('[data-lesson-n]', '13');
    toast('Урок создан', 'Катя С. получит напоминание за час');
  });
  wait(2200);
  };

  /* Ученики: провалиться в карточку */
  SCENES.students = function () {
  chapter('students');
  wait(800);
  move('[data-marina]');
  click(function () { on('[data-card]', 'is-on'); });
  wait(1500);
  move('[data-tab="hw"]', 750);
  click(function () { pane('hw'); });
  wait(1700);
  move('[data-tab="contacts"]', 700);
  click(function () { pane('contacts'); });
  wait(2100);
  };

  /* Задания: проверка */
  SCENES.tasks = function () {
  chapter('tasks');
  wait(800);
  move('[data-task]');
  click(function () { on('[data-drawer="task"]', 'is-on'); });
  wait(2500);
  move('[data-accept]', 800);
  click(function () {
    off('[data-drawer="task"]', 'is-on');
    on('[data-task]', 'is-done');
    text('[data-taskst]', 'проверено');
    text('[data-badge]', '2');
    text('[data-badge2]', '2');
    toast('Работа принята', '3 ошибки ушли Марине в карточки');
  });
  wait(2300);
  };

  /* Чаты */
  SCENES.chats = function () {
  chapter('chats');
  wait(600);
  move('[data-chat]');
  click(function () {
    on('.tchat__room', 'is-b');
    off('.tch.is-on', 'is-on');
    on('[data-chat]', 'is-on');
    var u = $('[data-unread]'); u.style.display = 'none';
    undo.push(function () { u.style.display = ''; });
  });
  wait(1500);
  move('[data-input]', 650);
  click(function () { on('[data-input]', 'is-focus'); });
  type('[data-typing]', 'Да, перенесла. Новое время уже в расписании', 1900);
  wait(200);
  move('[data-send]', 500);
  click(function () {
    text('[data-reply-text]', 'Да, перенесла. Новое время уже в расписании');
    on('[data-reply-out]', 'is-on');
    text('[data-typing]', '');
    off('[data-input]', 'is-focus');
  });
  wait(1700);
  };

  /* Финансы */
  SCENES.money = function () {
  chapter('money');
  wait(1000);
  move('[data-remind]');
  click(function () {
    on($('[data-remind]').parentNode, 'is-done');
    toast('Напоминание ушло', 'Соня В. · 4 200 руб.');
  });
  wait(1800);
  move('[data-mark]', 800);
  click(function () {
    on($('[data-mark]').parentNode, 'is-done');
    text('[data-debtn]', '1 ученик');
    toast('Долг закрыт', 'Артем Д. · 2 600 руб. за 2 урока');
    var bar = $('[data-gotbar]'); bar.style.width = '86%';
    undo.push(function () { bar.style.width = '82%'; });
  });
  count('[data-debt]', 6800, 4200);
  count('[data-got]', 64800, 67400, 500);
  wait(1900);
  };

  /* Живой урок: разбор на доске, ученик рисует с разрешения */
  SCENES.lesson = function () {
  chapter('lesson');
  wait(400);
  type('[data-bl1]', 'D = 25 - 24 = 1', 1100);
  wait(300);
  move('[data-allow]', 800);
  click(function () { on('[data-allow]', 'is-on'); text('[data-allow-t]', 'Марина рисует'); });
  wait(300);
  type('[data-bl2]', 'x₁ = 2,  x₂ = 3', 1200);
  act(function () { on('[data-ring]', 'is-on'); });
  wait(1000);
  move('[data-mat]', 800);
  click(function () { toast('Конспект открыт', 'Марина видит его на доске'); });
  wait(1800);
  move('[data-endlesson]', 800);
  click(function () { toast('Лист доски сохранен', 'Останется у урока и у ученика'); });
  wait(2200);
  };

  /* Ассистент: запрос, предпросмотр, подтверждение */
  SCENES.ai = function () {
  chapter('ai');
  wait(300);
  move('[data-ai-input]', 700);
  click(function () { on('[data-ai-input]', 'is-focus'); });
  type('[data-ai-typing]', 'План урока: квадратные уравнения', 1500);
  move('[data-ai-send]', 500);
  click(function () {
    on('[data-ai-q]', 'is-on');
    text('[data-ai-typing]', '');
    off('[data-ai-input]', 'is-focus');
  });
  wait(800);
  act(function () { on('[data-ai-a]', 'is-on'); on('[data-ai-prev]', 'is-on'); });
  wait(2200);
  move('[data-ai-save]', 800);
  click(function () {
    text('[data-ai-st]', 'сохранено');
    toast('План сохранен', 'К уроку Марины К. в четверг');
  });
  wait(2400);
  };

  /* Кабинет ученика */
  SCENES.me = function () {
  chapter('me', 500);
  wait(900);
  move('[data-join]', 800);
  click(function () { toast('Урок откроется по ссылке', 'Видео и доска в одном окне'); });
  wait(2000);
  };
  SCENES.myhw = function () {
  chapter('myhw');
  wait(700);
  move('[data-myhw]', 800);
  click(function () { on('[data-drawer="myhw"]', 'is-on'); });
  wait(1800);
  move('[data-myhw-send]', 800);
  click(function () {
    off('[data-drawer="myhw"]', 'is-on');
    text('[data-myhw-st]', 'на проверке');
    toast('Работа сдана', 'Анне К. пришло уведомление');
  });
  wait(2200);
  };
  SCENES.mycards = function () {
  chapter('mycards');
  wait(1000);
  move('[data-flash-show]', 800);
  click(function () { on('[data-flash]', 'is-open'); });
  wait(1500);
  move('[data-flash-ok]', 800);
  click(function () {
    off('[data-flash]', 'is-open');
    text('[data-cards-n]', '4');
    toast('Карточка вернется позже', 'Интервальное повторение');
  });
  wait(2200);
  };

  ROUTE.forEach(function (name) { SCENES[name](); });

  function pane(name) {
    $$('[data-tab]').forEach(function (t) { t.classList.toggle('is-on', t.getAttribute('data-tab') === name); });
    $$('[data-pane]').forEach(function (t) { t.classList.toggle('is-on', t.getAttribute('data-pane') === name); });
    undo.push(function () {
      $$('[data-tab]').forEach(function (t) { t.classList.toggle('is-on', t.getAttribute('data-tab') === 'history'); });
      $$('[data-pane]').forEach(function (t) { t.classList.toggle('is-on', t.getAttribute('data-pane') === 'history'); });
    });
  }

  /* длина каждого раздела для заливки кнопок */
  CH.forEach(function (c, i) {
    var end = i + 1 < CH.length ? CH[i + 1].at : OPS.length, sum = 0;
    for (var k = c.at; k < end; k++) sum += OPS[k].d;
    c.end = end; c.total = sum;
  });

  /* ---------- проигрыватель ---------- */
  var i = 0, cur = null, curT = 0, chIdx = 0, raf = 0, last = 0;
  var user = !reduce, visible = true;

  function setChapter(n) {
    if (n === chIdx && chips[n].classList.contains('is-on')) return;
    chIdx = n;
    chips.forEach(function (c, k) {
      c.classList.toggle('is-on', k === n);
      c.setAttribute('aria-pressed', k === n ? 'true' : 'false');
      if (k !== n) c.style.removeProperty('--p');
    });
  }
  function paintProgress() {
    var c = CH[chIdx], done = 0;
    for (var k = c.at; k < i && k < c.end; k++) done += OPS[k].d;
    if (cur) done += curT;
    chips[chIdx].style.setProperty('--p', Math.min(1, done / c.total).toFixed(3));
  }
  function advance(dt) {
    var guard = 0;
    while (dt >= 0 && guard++ < 50) {
      if (!cur) {
        if (i >= OPS.length) { resetAll(); show(ROUTE[0]); i = 0; setChapter(0); }
        for (var n = CH.length - 1; n >= 0; n--) { if (i >= CH[n].at) { setChapter(n); break; } }
        cur = OPS[i]; curT = 0;
        if (cur.start) cur.start();
      }
      if (!cur.d) { cur = null; i++; continue; }
      var left = cur.d - curT;
      if (dt < left) {
        curT += dt;
        if (cur.tick) cur.tick(curT / cur.d);
        break;
      }
      dt -= left;
      if (cur.tick) cur.tick(1);
      cur = null; i++;
    }
    paintProgress();
  }
  function frame(ts) {
    raf = 0;
    if (!isOn()) return;
    advance(Math.min(ts - last, 60));
    last = ts;
    raf = requestAnimationFrame(frame);
  }
  function isOn() { return user && visible && !document.hidden; }
  function sync() {
    ctl.classList.toggle('is-paused', !user);
    root.classList.toggle('is-run', user);
    playBtn.setAttribute('aria-label', user ? 'Остановить показ' : 'Запустить показ');
    if (fitted && isOn() && !raf) { last = performance.now(); raf = requestAnimationFrame(frame); }
  }
  function jump(n) {
    resetAll();
    show(CH[n].name);
    i = CH[n].jump; cur = null; curT = 0;
    setChapter(n);
    paintProgress();
  }

  playBtn.addEventListener('click', function () { user = !user; sync(); });
  chips.forEach(function (c, n) { c.addEventListener('click', function () { jump(n); }); });
  document.addEventListener('visibilitychange', sync);
  if (window.IntersectionObserver) {
    new IntersectionObserver(function (es) { visible = es[0].isIntersecting; sync(); }, { threshold: .15 }).observe(view);
  }

  show(ROUTE[0]);
  initDone = true;
  sync();
})();
