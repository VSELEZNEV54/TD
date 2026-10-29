# -*- coding: utf-8 -*-
"""Тарифы: выбор периода и учеников сразу, затем сравнение и возможности."""
from blocks import REG, FEATURES, btn, crumbs, cta, faq, feature_cards, ic, sec_head, section, typo
import sections as S


PERIODS = [(1, 0, 'Месяц'), (3, 15, '3 месяца'), (6, 16, '6 месяцев'), (12, 20, '12 месяцев')]


def plans():
    options = [
        ('trial', 'Пробный период', '0', 'руб. за 14 дней',
         ['Все 9 функций платформы', 'До 50 учеников и 100 запросов к ИИ в день', 'Без карты'],
         'Полный доступ на две недели', 'Начать бесплатно'),
        ('pro', 'Pro', '990', 'руб. в месяц',
         ['Все 9 функций платформы', 'До 50 активных учеников', '100 запросов к ИИ в день'],
         '990 руб. за 1 месяц', 'Попробовать Pro'),
        ('premium', 'Premium', '1 990', 'руб. в месяц',
         ['Все возможности Pro', 'Без лимита учеников', 'ИИ без дневного лимита'],
         '1 990 руб. за 1 месяц', 'Попробовать Premium'),
    ]
    cards = []
    for key, name, price, unit, ticks, charge, label in options:
        fit = ' is-fit' if key == 'pro' else ''
        tag = '<span class="plan__tag">Подойдет вам</span>' if key != 'trial' else ''
        price_attr = f' data-price-month="{key}"' if key != 'trial' else ''
        charge_attr = f' data-price-charge="{key}"' if key != 'trial' else ''
        old = f'<span class="pfc__d pricing-plan__old" data-price-old="{key}" hidden></span>' if key != 'trial' else ''
        lis = ''.join(f'<li>{ic("check")}<span>{typo(t)}</span></li>' for t in ticks)
        kind = 'primary' if key == 'pro' else 'ghost'
        cards.append(f'''<article class="plan{fit}" data-price-plan="{key}">
          <h2 class="plan__n">{name}{tag}</h2>
          <p class="plan__p"><b{price_attr}>{typo(price)}</b><span>{typo(unit)}</span></p>
          <p class="pfc__d pricing-plan__charge"{charge_attr}>{typo(charge)}</p>{old}
          <ul class="ticks">{lis}</ul>{btn(label, REG, kind)}
        </article>''')
    return ('<div class="plans plans--full pricing-plans">'
            '<span class="plans__hl" aria-hidden="true"><span class="plans__badge">подойдет<br>вам</span></span>'
            + ''.join(cards) + '</div>')


def comparison(c):
    names = ['Пробный', 'Pro', 'Premium']
    header = '<div class="ctab__row ctab__row--h" role="row"><span role="columnheader">Что входит</span>' + ''.join(f'<span role="columnheader">{n}</span>' for n in names) + '</div>'
    rows = []
    for label, *values in c['table']:
        cells = []
        for i, value in enumerate(values):
            if label == 'Цена' and i > 0:
                key = ['pro', 'premium'][i - 1]
                price = '990' if i == 1 else '1 990'
                value = f'<b data-price-month="{key}">{typo(price)}</b><span>руб. в месяц</span><small data-price-charge="{key}">{typo(price)} руб. за 1 месяц</small>'
            elif value is True or value is False:
                value = f'<span class="pricing-compare__value">{ic("check" if value else "x", "ic ic--16")}<span>{"Входит" if value else "Не входит"}</span></span>'
            else:
                value = typo(value)
            cells.append(f'<span role="cell" data-label="{names[i]}">{value}</span>')
        rows.append(f'<div class="ctab__row" role="row"><span role="rowheader">{typo(label)}</span>{"".join(cells)}</div>')
    return section(sec_head('Сравнение планов', 'Что входит в тариф', '', 'h-pricing-compare', 'sq') +
                   f'<div class="ctab pricing-compare" role="table" aria-labelledby="h-pricing-compare">{header}{"".join(rows)}</div>',
                   'pricing-comparison', 'h-pricing-compare')


def render(p, c, x):
    # Свои data-атрибуты: переключатели этой страницы не меняют тарифы на главной.
    period_buttons = ''.join(f'''<button type="button" class="btn btn--sm btn--{'primary' if m == 1 else 'ghost'}"
        data-price-period="{m}" data-price-discount="{discount}" aria-pressed="{'true' if m == 1 else 'false'}">
        <span>{label}{' · −' + str(discount) + '%' if discount else ''}</span></button>'''
        for m, discount, label in PERIODS)
    first = f'''<section class="pricing-start" id="tarify"><div class="wrap">
      {crumbs(x.trail(p))}
      <header class="pricing-start__head"><h1 class="phero__h">Тарифы TeacherDesk</h1>
        <p class="lead pricing-start__intro">Первые 14 дней полный доступ бесплатно и без карты. Дальше выбирайте тариф и удобный период оплаты.</p></header>
      <div class="pricing-controls">
        <div class="seats pricing-seats"><p class="seats__q"><label for="pricing-students">Сколько у вас учеников</label>
          <output class="seats__out" for="pricing-students"><b data-price-students>12</b><span data-price-students-word>учеников</span></output></p>
          <div class="seats__track">
            <span class="seats__zones seats__zones--2" aria-hidden="true"><i class="is-on" data-fit="1"></i><i data-fit="2"></i></span>
            <input id="pricing-students" type="range" min="0" max="100" value="16" step="1" aria-valuetext="12 учеников, подойдет Pro" data-price-students-input>
            <div class="seats__pos" aria-hidden="true"><span class="seats__thumb"></span></div>
          </div>
          <p class="seats__lbl seats__lbl--2" aria-hidden="true"><span class="is-on" data-fit="1">до 50, Pro</span><span data-fit="2">больше 50, Premium</span></p></div>
        <div class="pricing-period"><p class="seats__q" id="pricing-period-label">Период оплаты</p>
          <div class="pricing-period__options" role="group" aria-labelledby="pricing-period-label">{period_buttons}</div>
          <p class="pfc__d pricing-period__hint" data-price-period-hint>Оплата каждый месяц. Скидки начинаются с 3 месяцев.</p></div>
      </div>
      {plans()}
      <p class="pfc__d pricing-start__foot">Пробный период без карты. Оплата тарифа подключается в личном кабинете, когда вы решите продолжить.</p>
    </div></section>'''
    out = [first, comparison(c)]
    ids = [i for i in FEATURES if x.visible(i)]
    out.append(feature_cards(x.reg, ids, x.visible, 'Посмотрите возможности TeacherDesk',
                             'Знакомство с платформой', 'Расписание, оплаты, задания и уроки связаны в одном кабинете. Выберите функцию, чтобы посмотреть подробнее.',
                             'h-pricing-features', ('Все возможности', '/features/')))
    notes = ''.join(f'<li data-reveal="piece" style="--i:{i}"><span class="note3__ic">{ic(n["icon"], "ic ic--20")}</span><h3 class="note3__t">{typo(n["title"])}</h3><p>{typo(n["text"])}</p></li>' for i, n in enumerate(c['notes']))
    out.append(section(sec_head('Оплата', c['notes_h2'], '', 'h-pay', 'sq') + f'<ul class="note3">{notes}</ul>', '', 'h-pay'))
    if c.get('objections'):
        out.append(S.objections(c['objections'], h2='Сомнения перед оплатой'))
    out.append(faq(c['faq'], h2='Частые вопросы'))
    out.append(cta())
    from templates import seo_of, app_ld
    out.append(seo_of(c, p, x))
    return '<div class="pricing-page" data-pricing-root>' + '\n'.join(out) + '</div>', [app_ld(p)]
