# -*- coding: utf-8 -*-
"""Мини-экраны в карточках «Что умеет»: фрагменты того же кабинета, что и в показе на главной."""
import re
from html import escape
from blocks import ic, typo


RAIL = ('home', 'calendar', 'users', 'task', 'chat', 'wallet', 'ai')
RAIL_ON = {'raspisanie': 'calendar', 'uchet-oplat': 'wallet', 'uchet-uchenikov': 'users', 'kabinet-uchenika': 'home', 'domashnie-zadaniya': 'task',
           'onlayn-doska': 'calendar', 'ii-assistent': 'ai', 'otchety-roditelyam': 'users', 'zhurnal-zanyatiy': 'users'}


def rail(pid):
    """Боковая панель кабинета, как в показе на главной: окно ролика читается как тот же продукт."""
    items = ''.join(f'<i{" class=on" if name == RAIL_ON.get(pid) else ""}>{ic(name)}</i>' for name in RAIL)
    return f'<span class="cabrail" aria-hidden="true"><img src="/assets/img/sign.svg" width="22" height="22" alt="">{items}</span>'


def _t(text):
    return typo(escape(text))


def _rows(items, mark=''):
    lis = ''.join(f'<span class="mi__r" style="--n:{i}">{mark}<span>{_t(it)}</span></span>' for i, it in enumerate(items))
    return f'<span class="mi__rows">{lis}</span>'


def _pairs(pairs):
    lis = ''.join(f'<span class="mi__r" style="--n:{i}"><span>{_t(k)}</span><b>{_t(v)}</b></span>' for i, (k, v) in enumerate(pairs))
    return f'<span class="mi__rows">{lis}</span>'


def _action(text, icon='', n=2):
    return f'<span class="mi__a" style="--n:{n}">{ic(icon, "ic ic--12") if icon else ""}{_t(text)}</span>'


def _bars(rows):
    return ''.join(f'<span class="mi__l"><span>{_t(name)}</span><b>{_t(value)}</b></span><span class="mi__bar"><i style="--v:{v}"></i></span>' for name, value, v in rows)


def _wrap(body, kind=''):
    return f'<div class="mi{" mi--" + kind if kind else ""}">{body}</div>'


def metric(title, value, note):
    m = re.match(r'^([\d\s ]+)(.*)$', value)
    num, unit = (m.group(1).strip(), m.group(2).strip()) if m else (value, '')
    return _wrap(f'<small>{_t(title)}</small><span class="mi__big"><b>{_t(num)}</b>{f"<span>{_t(unit)}</span>" if unit else ""}</span><small>{_t(note)}</small>')


def notice(title, note, icon='bell'):
    return _wrap(f'<span class="mi__note"><i>{ic(icon)}</i><span><b>{_t(title)}</b><small>{_t(note)}</small></span></span>')


def link(title, action, note='Ссылка в кабинете'):
    return _wrap(f'<small>{_t(title)}</small><span class="mi__r mi__r--plain">{ic("link", "ic ic--12")}<span>{_t(note)}</span></span>{_action(action, "video", 1)}')


def form(title, pairs, action, icon='check'):
    return _wrap(f'<small>{_t(title)}</small>{_pairs(pairs)}{_action(action, icon)}')


def phone(title, head, rows, action=''):
    tail = _action(action, 'check') if action else ''
    return _wrap(f'<i class="mi__isl"></i><small>{_t(title)}</small><b class="mi__h">{_t(head)}</b>{_rows(rows)}{tail}', 'phone')


def week():
    kinds = ['p', '', '', 'w', '', '', 'p', '', '', 'p', 'p', '', 'n', '', '']
    cells = ''.join(f'<i class="{k}"></i>' if k else '<i></i>' for k in kinds)
    return _wrap(f'<span class="mi__seg"><b>Неделя</b><span>Месяц</span></span><span class="mi__week">{cells}</span>')


def repeat(title, note):
    days = ''.join(f'<i{" class=on" if d in ("ВТ", "ЧТ") else ""}>{d}</i>' for d in ('ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ'))
    return _wrap(f'<small>{_t(title)}</small><span class="mi__days">{days}</span><small>{_t(note)}</small>')


def move(old, new, lesson, note):
    return _wrap(f'<span class="mi__move"><span><small>{_t(old)}</small></span><span class="on"><small>{_t(new)}</small><b>{_t(lesson)}</b></span></span><span class="mi__r mi__r--plain">{ic("check", "ic ic--12")}<span>{_t(note)}</span></span>')


def card(kind, lines):
    """Карточка возможности из строк feature_content.py."""
    title, *items = lines
    if kind == 'metric':
        return metric(title, items[0], items[1])
    if kind == 'bars':
        return _wrap(_bars([(title, items[0], .9), (items[1], items[2], .5)]))
    if kind == 'board':
        graph = '<svg viewBox="0 0 180 46" aria-hidden="true"><path d="M10 35 Q40 8 70 30 T145 10 M85 7 L85 40 M15 36 H165"/></svg>'
        return _wrap(f'<small>{_t(title)}</small><b class="mi__eq">x² - 5x + 6 = 0</b>{graph}<small>{_t(items[0])}</small>')
    if kind == 'notice':
        return notice(title, items[0])
    if kind == 'link':
        return link(title, items[0])
    if kind == 'phone':
        return phone(title, items[0], [items[1]], 'В кабинете')
    if kind == 'cards':
        return _wrap(f'<small>{_t(title)}</small><span class="mi__card" style="--n:0">{_t(items[0])}</span>{_action(items[1], "", 1)}')
    if kind == 'form':
        return _wrap(f'<small>{_t(title)}</small>{_rows(items)}{_action("Сохранено", "check")}')
    mark = ic('check', 'ic ic--12') if kind == 'checklist' else ic('doc', 'ic ic--12')
    return _wrap(f'<small>{_t(title)}</small>{_rows(items, mark)}')


def schedule():
    """Семь карточек страницы расписания: у нее свои сюжеты, тот же набор деталей."""
    return [
        week(),
        form('Новый урок', [('Ученик', 'Марина К.'), ('Повтор', 'Каждую неделю')], 'Сохранить', ''),
        repeat('Каждую неделю', 'Один раз на все недели'),
        move('Ср · 15:30', 'Пт · 15:30', 'Физика · Артем', 'Ученик видит перенос'),
        notice('Урок через час', 'Алгебра · 15:30'),
        link('Алгебра · Марина', 'Войти в урок', 'Ссылка в карточке урока'),
        phone('Сегодня', '4 урока', ['09:00 · Алгебра', '11:00 · Английский', '15:30 · Физика']),
    ]
