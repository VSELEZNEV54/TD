/* Сцены функций следуют общему таймлайну ролика с главной. */
(function () {
  'use strict';
  var film = document.querySelector('[data-film="feature"]');
  if (!film) return;
  var steps = Array.from(film.querySelectorAll('[data-feature-step]'));
  var current = -1;
  function render(t) {
    var next = 0;
    steps.forEach(function (step, i) { if (t >= Number(step.dataset.featureStep)) next = i; });
    if (current === next) return;
    current = next;
    steps.forEach(function (step, i) { step.classList.toggle('is-on', i === next); });
  }
  film.addEventListener('td:film-frame', function (event) { render(event.detail); });
  render(Number(film.dataset.filmTime) || 0);
})();
