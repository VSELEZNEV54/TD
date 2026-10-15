/* Переключатель концепций главной TeacherDesk.
   Подключение в конце body: <script src="../shared/switcher.js" data-concept="1" defer></script>
   1. Рисует плашку внизу экрана (стили изолированы в shadow DOM).
   2. Ссылки на внутренние страницы сайта (/features/raspisanie/ и т.д.) в прототипе
      никуда не ведут: адреса сохранены как в будущей архитектуре, а клик показывает подсказку. */
(function () {
  if (window.self !== window.top) return; // в превью на обзорной странице плашка не нужна
  var CONCEPTS = [
    { n: 1, name: 'Живое окно' },
    { n: 2, name: 'Ночная смена' },
    { n: 3, name: 'Конструктор' },
  ];
  var me = document.currentScript || document.querySelector('script[data-concept]');
  var cur = parseInt((me && me.getAttribute('data-concept')) || '0', 10);
  var host = document.createElement('div');
  host.setAttribute('data-concept-switcher', '');
  host.style.cssText = 'position:fixed;left:50%;bottom:16px;transform:translateX(-50%);z-index:2147483000;';
  var root = host.attachShadow ? host.attachShadow({ mode: 'open' }) : host;
  var links = CONCEPTS.map(function (c) {
    var on = c.n === cur;
    return '<a href="../' + c.n + '/index.html"' + (on ? ' aria-current="page"' : '') + '>' +
      '<b>' + c.n + '</b><span>' + c.name + '</span></a>';
  }).join('');
  root.innerHTML =
    '<style>' +
    ':host{all:initial}' +
    '.wrap{display:grid;justify-items:center;gap:8px}' +
    'nav{display:flex;align-items:center;gap:4px;padding:5px;border-radius:999px;background:#1B1C26;color:#fff;' +
    'font:500 13px/1 Geist,system-ui,-apple-system,"Segoe UI",sans-serif;box-shadow:0 12px 32px rgba(20,21,30,.35),0 0 0 1px rgba(255,255,255,.10);white-space:nowrap}' +
    'p{margin:0 8px 0 12px;color:#A9ABBA;font-weight:400}' +
    'a{display:flex;align-items:center;gap:8px;height:34px;padding:0 14px 0 6px;border-radius:999px;color:#D8D9E3;text-decoration:none;transition:background-color .15s,color .15s}' +
    'a b{display:grid;place-items:center;width:22px;height:22px;border-radius:999px;background:rgba(255,255,255,.12);font-weight:600;font-size:12px}' +
    'a:hover{background:rgba(255,255,255,.10);color:#fff}' +
    'a[aria-current]{background:#F4EA00;color:#22232E}' +
    'a[aria-current] b{background:#22232E;color:#F4EA00}' +
    'a:focus-visible{outline:2px solid #fff;outline-offset:2px}' +
    'a.all{padding:0 14px;color:#A9ABBA}' +
    '.toast{max-width:min(92vw,460px);padding:12px 16px;border-radius:14px;background:#FFFFFF;color:#22232E;' +
    'font:400 13px/1.4 Geist,system-ui,-apple-system,"Segoe UI",sans-serif;box-shadow:0 16px 40px rgba(20,21,30,.38),0 0 0 1px rgba(34,35,46,.12);' +
    'opacity:0;transform:translateY(6px);transition:opacity .2s,transform .2s cubic-bezier(.16,1,.3,1);pointer-events:none;text-align:center}' +
    '.toast.on{opacity:1;transform:none;pointer-events:auto}' +
    '.toast code{font:400 12px/1 "Geist Mono",ui-monospace,monospace;color:#3547C0;background:#EBEEFE;padding:2px 6px;border-radius:6px;white-space:nowrap}' +
    '.toast a{display:inline;height:auto;padding:0;color:#3547C0;text-decoration:underline;border-radius:4px}' +
    '.toast a:hover{background:none;color:#22232E}' +
    '.toast a:focus-visible{outline:2px solid #445BF6;outline-offset:2px}' +
    '@media (max-width:720px){p,nav a span{display:none}nav a{padding:0 6px}nav a.all{display:none}}' +
    '@media (prefers-reduced-motion:reduce){.toast,a{transition:none}}' +
    '</style>' +
    '<div class="wrap"><div class="toast" role="status" aria-live="polite"></div>' +
    '<nav aria-label="Концепции дизайна главной"><p>Концепция</p>' + links +
    '<a class="all" href="../index.html">Все</a></nav></div>';
  document.body.appendChild(host);

  /* Внутренние ссылки прототипа: адрес как в архитектуре, перехода нет */
  var toast = root.querySelector('.toast');
  var timer;
  function hint(path) {
    toast.innerHTML = 'Страница <code>' + path.replace(/[<>&"]/g, '') + '</code> заложена в архитектуре сайта. ' +
      'В прототипе собрана только главная. <a href="../architecture.html">Открыть архитектуру</a>';
    toast.classList.add('on');
    clearTimeout(timer);
    timer = setTimeout(function () { toast.classList.remove('on'); }, 4200);
  }
  function onClick(e) {
    var a = e.target.closest && e.target.closest('a[href]');
    if (!a) return;
    var href = a.getAttribute('href');
    if (!href || href.charAt(0) !== '/' || href.charAt(1) === '/') return;
    e.preventDefault();
    if (href === '/') { window.scrollTo({ top: 0, behavior: 'smooth' }); return; }
    hint(href);
  }
  document.addEventListener('click', onClick);
  document.addEventListener('auxclick', onClick);
})();
