/* Период оплаты и подходящий тариф на странице цен. Списания здесь нет. */
(function () {
  'use strict';
  var root = document.querySelector('[data-pricing-root]');
  if (!root) return;
  var input = root.querySelector('[data-price-students-input]');
  var periodButtons = Array.prototype.slice.call(root.querySelectorAll('[data-price-period]'));
  var months = 1;
  var discount = 0;
  var bases = { pro: 990, premium: 1990 };
  var money = function (n) {
    return new Intl.NumberFormat('ru-RU', { minimumFractionDigits: n % 1 ? 2 : 0, maximumFractionDigits: 2 }).format(n);
  };
  var word = function (n, one, few, many) {
    var a = n % 10, b = n % 100;
    return a === 1 && b !== 11 ? one : a >= 2 && a <= 4 && (b < 12 || b > 14) ? few : many;
  };
  function updatePeriod() {
    Object.keys(bases).forEach(function (key) {
      var base = bases[key];
      var monthly = Math.round(base * (100 - discount)) / 100;
      var total = Math.round(monthly * months * 100) / 100;
      root.querySelectorAll('[data-price-month="' + key + '"]').forEach(function (el) { el.textContent = money(monthly); });
      root.querySelectorAll('[data-price-charge="' + key + '"]').forEach(function (el) {
        el.textContent = money(total) + ' руб. за ' + months + ' ' + word(months, 'месяц', 'месяца', 'месяцев');
      });
      var old = root.querySelector('[data-price-old="' + key + '"]');
      if (old) {
        old.hidden = discount === 0;
        old.textContent = 'Вместо ' + money(base * months) + ' руб. Экономия ' + money(base * months - total) + ' руб.';
      }
    });
    periodButtons.forEach(function (el) {
      var on = +el.getAttribute('data-price-period') === months;
      el.classList.toggle('btn--primary', on);
      el.classList.toggle('btn--ghost', !on);
      el.setAttribute('aria-pressed', on ? 'true' : 'false');
    });
    root.querySelector('[data-price-period-hint]').textContent = months === 1 ?
      'Оплата каждый месяц. Скидки начинаются с 3 месяцев.' :
      'Скидка ' + discount + '%. Весь период ' + months + ' ' + word(months, 'месяц', 'месяца', 'месяцев') + ' оплачивается сразу.';
  }
  function updateStudents() {
    var p = +input.value;
    // Та же шкала и граница зон, что у ползунка на главной.
    var n = p <= 72 ? Math.max(1, Math.round(1 + p / 72 * 49)) : Math.round(51 + (p - 72) / 28 * 49);
    var premium = n > 50;
    var fit = premium ? 2 : 1;
    var text = n >= 100 ? '100+' : String(n);
    var noun = n >= 100 ? 'учеников' : word(n, 'ученик', 'ученика', 'учеников');
    var name = premium ? 'Premium' : 'Pro';
    root.querySelector('[data-price-students]').textContent = text;
    root.querySelector('[data-price-students-word]').textContent = noun;
    input.setAttribute('aria-valuetext', text + ' ' + noun + ', подойдет ' + name);
    root.querySelector('.pricing-seats').style.setProperty('--p', p);
    root.querySelector('.pricing-plans').style.setProperty('--fit', fit);
    root.querySelectorAll('.pricing-seats [data-fit]').forEach(function (el) {
      el.classList.toggle('is-on', +el.getAttribute('data-fit') === fit);
    });
    root.querySelectorAll('[data-price-plan]').forEach(function (el) {
      var key = el.getAttribute('data-price-plan');
      var fit = key === (premium ? 'premium' : 'pro');
      el.classList.toggle('is-fit', fit);
      var button = el.querySelector('.btn');
      button.classList.toggle('btn--primary', fit);
      button.classList.toggle('btn--ghost', !fit);
    });
  }
  periodButtons.forEach(function (el) {
    el.addEventListener('click', function () {
      months = +el.getAttribute('data-price-period');
      discount = +el.getAttribute('data-price-discount');
      updatePeriod();
    });
  });
  input.addEventListener('input', updateStudents);
  updateStudents();
  updatePeriod();
})();
