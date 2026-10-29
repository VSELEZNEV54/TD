# -*- coding: utf-8 -*-
"""Карточки-переходы в стиле блока «Бесплатные инструменты» с главной: мини-превью, ярлык, название, описание.
Ими собраны «Другие решения», «Другие инструменты», «Другие инструкции», разделы сайта и ссылки 404."""
import importlib.util
from pathlib import Path
from blocks import typo, ic

CONTENT = Path(__file__).parent / 'content'

TOOL_PREVIEW = {
    'tablica-ucheta': '<span class="mini-sheet" data-sheet><span class="ms__r ms__r--h"><i>Ученик</i><i>Уроков</i><i>Долг</i></span><span class="ms__r"><i>Марина К.</i><i>8</i><i>0</i></span><span class="ms__r"><i>Артем Д.</i><i>7</i><i>2&nbsp;600</i></span><span class="ms__r"><i>Соня В.</i><i>5</i><i>4&nbsp;200</i></span><span class="ms__r ms__r--sum"><i>Итого</i><i>20</i><i data-sheet-sum>6&nbsp;800</i></span></span>',
    'dogovor': '<span class="mini-doc"><span class="md__field"><small>Родитель</small><b>Елена Кузнецова</b></span><span class="md__field"><small>Стоимость урока</small><b>1&nbsp;800&nbsp;руб.</b></span><span class="md__file"><svg class="ic"><use href="#i-doc"/></svg>dogovor.docx</span></span>',
    'kalkulyator': '<span class="mini-calc"><span class="mc__row"><small>Цель в&nbsp;месяц</small><b>80&nbsp;000&nbsp;руб.</b></span><span class="mc__row"><small>Уроков в&nbsp;неделю</small><b>20</b></span><span class="mc__out"><small>Ставка за&nbsp;урок</small><b>1&nbsp;000&nbsp;руб.</b></span></span>',
    'plan-uroka': '<span class="mini-plan"><span class="mp__me">Квадратные уравнения, 8&nbsp;класс</span><span class="mp__row"><i>1</i>Разминка<time>10&nbsp;мин</time></span><span class="mp__row"><i>2</i>Дискриминант<time>15&nbsp;мин</time></span><span class="mp__row"><i>3</i>Самостоятельная<time>25&nbsp;мин</time></span></span>',
    'anketa': '<span class="mini-ad"><span class="ma__h"><span class="av">АК</span><b>Анна Ковалева</b></span><span class="ma__t">Репетитор по&nbsp;математике, ОГЭ и&nbsp;ЕГЭ. Опыт 6&nbsp;лет</span><span class="ma__tags"><i>онлайн</i><i>1&nbsp;800&nbsp;руб.</i><i>8-11 класс</i></span></span>',
    'shablon-raspisaniya': '<span class="mini-wk"><span class="mw__h"><i></i><i>пн</i><i>вт</i><i>ср</i><i>чт</i></span><span class="mw__r"><i>10:00</i><b class="is-a">Алг</b><b></b><b class="is-a">Алг</b><b></b></span><span class="mw__r"><i>15:30</i><b></b><b class="is-b">Англ</b><b></b><b class="is-b">Англ</b></span><span class="mw__r"><i>17:00</i><b class="is-c">ОГЭ</b><b></b><b></b><b class="is-c">ОГЭ</b></span></span>',
    'generator-zadaniy': '<span class="mini-tasks"><span class="mt__h">Present Perfect · B1</span><span class="mt__r"><i>1</i>She ___ (live) here since 2020.</span><span class="mt__r"><i>2</i>I ___ (not / see) him today.</span><span class="mt__r"><i>3</i>___ you ever ___ (be) to Kazan?</span></span>',
}

PREVIEW = {
    'crm': '<span class="mini-ad"><span class="ma__h"><span class="av">МК</span><b>Марина Кузнецова</b></span><span class="ma__t">Алгебра, 9&nbsp;класс. Следующий урок в&nbsp;среду в&nbsp;15:30</span><span class="ma__tags"><i>оплачено</i><i>8 уроков</i><i>ДЗ сдано</i></span></span>',
    'programma': '<span class="mini-wk"><span class="mw__h"><i></i><i>пн</i><i>вт</i><i>ср</i><i>чт</i></span><span class="mw__r"><i>12:00</i><b></b><b class="is-c">Физ</b><b></b><b class="is-c">Физ</b></span><span class="mw__r"><i>15:30</i><b class="is-a">Алг</b><b></b><b class="is-a">Алг</b><b></b></span><span class="mw__r"><i>18:00</i><b></b><b class="is-b">Англ</b><b class="is-b">Англ</b><b></b></span></span>',
    'prilozhenie': '<span class="mini-plan"><span class="mp__me">Сегодня, среда</span><span class="mp__row"><i>1</i>Марина К.<time>15:30</time></span><span class="mp__row"><i>2</i>Артем Д.<time>17:00</time></span><span class="mp__row"><i>3</i>Соня В.<time>18:30</time></span></span>',
    'besplatnaya': '<span class="mini-calc"><span class="mc__row"><small>Пробный период</small><b>14&nbsp;дней</b></span><span class="mc__row"><small>Учеников</small><b>до&nbsp;50</b></span><span class="mc__out"><small>Карта</small><b>не&nbsp;нужна</b></span></span>',
    'onlayn': '<span class="mini-doc"><span class="md__field"><small>Урок онлайн</small><b>Среда, 15:30</b></span><span class="md__field"><small>Ученик</small><b>Марина Кузнецова</b></span><span class="md__file"><svg class="ic"><use href="#i-video"/></svg>Войти в&nbsp;урок</span></span>',
    'features': '<span class="mini-tasks"><span class="mt__h">9 функций в&nbsp;одном окне</span><span class="mt__r"><i>1</i>Расписание и&nbsp;напоминания</span><span class="mt__r"><i>2</i>Оплаты и&nbsp;долги</span><span class="mt__r"><i>3</i>Задания и&nbsp;ИИ-ассистент</span></span>',
    'instrumenty': '<span class="mini-doc"><span class="md__field"><small>Калькулятор ставки</small><b>1&nbsp;000&nbsp;руб. за&nbsp;урок</b></span><span class="md__field"><small>Генератор договора</small><b>Документ с вашими данными</b></span><span class="md__file"><svg class="ic"><use href="#i-download"/></svg>dogovor.docx</span></span>',
    'pricing': '<span class="mini-calc"><span class="mc__row"><small>Pro</small><b>990&nbsp;руб.</b></span><span class="mc__row"><small>Premium</small><b>1&nbsp;990&nbsp;руб.</b></span><span class="mc__out"><small>14&nbsp;дней</small><b>бесплатно</b></span></span>',
}

# ярлык над названием, если в реестре нет своего
TAG = {'product': 'Решение', 'features': 'Возможности', 'tools': 'Инструмент', 'kb': 'Инструкция', 'blog': 'Статья', 'about': 'О сервисе'}
HUB_TAG = {'features': 'Раздел', 'instrumenty': 'Раздел', 'baza-znanij': 'Раздел', 'blog': 'Раздел', 'pricing': 'Тарифы'}

_content = {}


def _page(pid):
    if pid not in _content:
        f = CONTENT / f'{pid}.py'
        c = {}
        if f.exists():
            spec = importlib.util.spec_from_file_location('pv_' + pid.replace('-', '_'), f)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            c = getattr(mod, 'PAGE', {})
        _content[pid] = c
    return _content[pid]


def _plan(title, rows):
    r = ''.join(f'<span class="mp__row"><i>{i}</i>{typo(x)}</span>' for i, x in enumerate(rows[:3], 1))
    return f'<span class="mini-plan"><span class="mp__me">{typo(title)}</span>{r}</span>'


def _blog(reg, visible):
    posts = [p for p in reg.values() if p.get('type') == 'article' and visible(p['id'])][:3]
    rows = ''.join(f'<span class="mt__r"><i>{i}</i>{typo(p["nav"])}</span>' for i, p in enumerate(posts, 1))
    return f'<span class="mini-tasks"><span class="mt__h">Блог для репетиторов</span>{rows}</span>'


def _kb(reg):
    # Список инструкций, чтобы превью хаба не повторяло карточку «Первые шаги» рядом с ним.
    docs = [p for p in reg.values() if p.get('type') == 'kb'][:3]
    rows = ''.join(f'<span class="mt__r"><i>{i}</i>{typo(p["nav"])}</span>' for i, p in enumerate(docs, 1))
    return f'<span class="mini-tasks"><span class="mt__h">База знаний</span>{rows}</span>'


def preview(pid, reg, visible):
    if pid in TOOL_PREVIEW:
        return TOOL_PREVIEW[pid]
    if pid in PREVIEW:
        return PREVIEW[pid]
    if pid == 'blog':
        return _blog(reg, visible)
    if pid == 'baza-znanij':
        return _kb(reg)
    p = reg[pid]
    steps = _page(pid).get('steps') or []
    if steps:
        return _plan(p['nav'], [s['title'] for s in steps])
    return _plan(p['nav'], [p.get('card', '')])


def cards(reg, ids, visible, cls='ftools ftools--rel', desc=None):
    """desc: {id: описание} поверх карточки из реестра."""
    lis = []
    for pid in ids:
        if not visible(pid):
            continue
        q = reg[pid]
        tag = q.get('tag') or HUB_TAG.get(pid) or TAG.get(q.get('section'), '')
        d = (desc or {}).get(pid) or q.get('card', '')
        lis.append(f'''<li data-reveal="piece" style="--i:{len(lis)}"><a class="ftc" href="{q["url"]}">
        <span class="ftc__pic" aria-hidden="true">{preview(pid, reg, visible)}</span>
        <span class="ftc__tag">{typo(tag)}</span>
        <h3 class="ftc__t">{typo(q["nav"])}</h3>
        <span class="ftc__d">{typo(d)}</span>
        <span class="ftc__go" aria-hidden="true">{ic("arrow")}</span>
      </a></li>''')
    return f'<ul class="{cls}">{"".join(lis)}</ul>' if lis else ''
