/* Состояния урока следуют часам общего ролика из home.js. */
(function () {
  'use strict';
  var film = document.querySelector('[data-film="schedule"]');
  if (!film) return;
  var fields = Array.from(film.querySelectorAll('[data-film-field]'));
  var saved = film.querySelector('[data-film-save]');
  function render(t) {
    fields.forEach(function (field, i) { field.classList.toggle('is-filled', t >= 6800 + i * 1000); });
    film.classList.toggle('is-saving', t >= 10200);
    film.classList.toggle('is-created', t >= 11400);
    film.classList.toggle('is-moved', t >= 14000);
    film.classList.toggle('is-notified', t >= 17300);
    saved.textContent = t >= 14000 ? 'перенесено' : 'сохранено';
  }
  film.addEventListener('td:film-frame', function (event) { render(event.detail); });
  render(Number(film.dataset.filmTime) || 0);
})();
