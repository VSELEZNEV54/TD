# -*- coding: utf-8 -*-
"""Мини-ролики функций: 4 главы, в каждой сцена из деталей интерфейса.
Детали появляются по времени: data-at="мс от начала главы", data-fx задает эффект
(pop - наклейка, type - печать по словам, count - счетчик, fill - полоса, move - переезд,
press - нажатие, on - включение, hide - исчезает, draw - рисуется). Движок в pages.js.
Данные вымышленные: Анна Ковалева, Марина Кузнецова, Артем Дроздов, Соня Ветрова, среда 30 сентября."""
from blocks import ic


def A(ms, fx=None, **kw):
    s = f' data-at="{ms}"'
    if fx:
        s += f' data-fx="{fx}"'
    for k, v in kw.items():
        s += f' data-{k}="{v}"'
    return s


def toast(ms, icon, title, text, pos='tr', y=False):
    return (f'<p class="mf-toast mf-toast--{pos}"{A(ms, "pop")}><span class="mf-toast__ic{" mf-toast__ic--y" if y else ""}">{ic(icon)}</span>'
            f'<span><b>{title}</b>{text}</span></p>')


def field(label, value, ms=None, fx='type'):
    a = A(ms, fx) if ms is not None else ''
    return f'<span class="mf-field"><small>{label}</small><b{a}>{value}</b></span>'


def row(av, name, meta, chip='', ms=None, fx=None, cls=''):
    a = A(ms, fx) if ms is not None else ''
    return f'<li class="mf-row{(" " + cls) if cls else ""}"{a}><span class="av">{av}</span><span class="mf-row__t"><b>{name}</b><small>{meta}</small></span>{chip}</li>'


def kpi(label, val, unit='', ms=None, frm=None, cls=''):
    a = A(ms, 'count', **{'from': frm, 'to': val.replace(' ', '').replace('&nbsp;', '')}) if ms is not None else ''
    return f'<p class="mf-kpi{(" " + cls) if cls else ""}"><small>{label}</small><b><span{a}>{val}</span>{(" <i>" + unit + "</i>") if unit else ""}</b></p>'


def chip(cls, text, ms=None, fx='pop'):
    a = A(ms, fx) if ms is not None else ''
    return f'<span class="chip chip--{cls}"{a}>{text}</span>'


def phone(body, ms=None):
    a = A(ms) if ms is not None else ''
    return f'<div class="mf-phone phone-frame"{a}><span class="mf-phone__top"><time>14:30</time><i></i></span>{body}</div>'


WEEK = '''<div class="pd-week">
  <div class="pd-week__head"><b>Неделя</b><span>28.09&nbsp;- 02.10</span></div>
  <div class="pd-week__grid">
    <span class="pd-week__d"></span><span class="pd-week__d">пн</span><span class="pd-week__d">вт</span><span class="pd-week__d is-today">ср</span><span class="pd-week__d">чт</span><span class="pd-week__d">пт</span>
    <span class="pd-week__h">09:00</span><i class="pd-wl pd-wl--paid">Алгебра</i><i></i><i></i><i class="pd-wl pd-wl--wait">Геометрия</i><i></i>
    <span class="pd-week__h">12:00</span><i></i><i class="pd-wl pd-wl--paid">Английский</i><i></i><i></i><i class="pd-wl pd-wl--paid">Английский</i>
    <span class="pd-week__h">15:30</span><i></i><i></i>{c33}<i>{c34}</i><i></i>
    <span class="pd-week__h">17:15</span><i></i><i class="pd-wl pd-wl--paid">Русский</i><i class="pd-wl pd-wl--wait">Физика</i><i></i><i></i>
  </div>
</div>'''


def raspisanie():
    w1 = WEEK.replace('{c33}', f'<i class="pd-wl pd-wl--now"{A(2900, "pop")}>Алгебра</i>').replace('<i>{c34}</i>', '<i></i>')
    w2 = WEEK.replace('{c33}', f'<i class="pd-wl pd-wl--move mf-mv" style="--mx:calc(100% + 5px);--my:0"{A(900, "move")}>Химия</i>').replace('<i>{c34}</i>', '<i></i>')
    return {
        'title': 'Расписание · неделя',
        'h2': 'Урок ставится за секунды, а&nbsp;перенос видят <em class="em">все сразу</em>',
        'lead': 'Четыре коротких главы: как урок появляется в расписании, переезжает на другой день и напоминает о себе ученику.',
        'chapters': [
            {'t': 'Урок за пять секунд', 'cap': 'Выбрали ученика, день и повтор, нажали «Сохранить».', 'scene': f'''<div class="mf mf--split">
  <div class="mf-card mf-card--form">
    <p class="mf-h"><b>Новый урок</b><span>среда</span></p>
    {field("Ученик", "Марина Кузнецова", 300)}{field("Когда", "Ср, 30 сентября · 15:30", 1100)}
    <span class="mf-field"><small>Повтор</small><span class="mf-chips">{chip("paid", "каждую неделю", 1900)}</span></span>
    <span class="mf-btn"{A(2500, "press")}>Сохранить</span>
  </div>
  <div class="mf-card mf-card--soft">{w1}</div>
  {toast(3300, "check", "Урок добавлен", "Марина видит его в&nbsp;кабинете")}
</div>'''},
            {'t': 'Перенос в два клика', 'cap': 'Урок перетащили на четверг, ученику ушло уведомление.', 'scene': f'''<div class="mf mf--one">
  <div class="mf-card mf-card--wide">{w2}</div>
  <span class="mf-cursor" style="--mx:120px;--my:-6px"{A(700, "move")}>{ic("pen", "ic ic--12")}</span>
  {toast(2300, "calendar", "Химия перенесена на&nbsp;четверг", "Катя С. уже видит новое время", "br")}
</div>'''},
            {'t': 'Ученик видит у себя', 'cap': 'В кабинете ученика новое время появляется сразу.', 'scene': f'''<div class="mf mf--center">
  {phone(f"""<p class="mf-ph__hi">Привет, Катя</p>
    <div class="mf-ph__next"><small>Следующий урок</small><b>Чт, 1&nbsp;октября · 15:30</b><span>Химия с&nbsp;Анной К.</span></div>
    <p class="mf-ph__upd"{A(1200, "pop")}>{ic("refresh", "ic ic--12")}Время изменено</p>
    <ul class="mf-ph__list"><li><time>пт</time><b>Химия</b><small>задание к&nbsp;уроку</small></li><li><time>пн</time><b>Химия</b><small>каждую неделю</small></li></ul>""")}
  {toast(2200, "users", "Кабинет ученика", "без пересылки скриншотов в&nbsp;чат", "bl", y=True)}
</div>'''},
            {'t': 'Напоминание за час', 'cap': 'За час до урока ученик получает напоминание сам.', 'scene': f'''<div class="mf mf--center">
  {phone(f"""<p class="mf-ph__clock">14:30</p><p class="mf-ph__date">среда, 30&nbsp;сентября</p>
    <div class="mf-ph__push"{A(900, "pop")}><img src="/assets/img/sign.svg" width="26" height="26" alt=""><span><b>Урок через час</b>Алгебра с&nbsp;Анной в&nbsp;15:30, ссылка в&nbsp;кабинете</span></div>""")}
  {toast(2400, "bell", "Напоминание ушло", "Марина К. · 14:30", "tr")}
</div>'''},
        ],
    }


def uchet_oplat():
    return {
        'title': 'Оплаты · сентябрь',
        'h2': 'Урок проведен, и&nbsp;баланс уже <em class="em">пересчитан</em>',
        'lead': 'От проведенного урока до оплаты на счету: что происходит без единой формулы.',
        'chapters': [
            {'t': 'Урок отмечен', 'cap': 'Провели занятие, и баланс ученика уменьшился сам.', 'scene': f'''<div class="mf mf--split">
  <div class="mf-card">
    <p class="mf-h"><b>Марина Кузнецова</b><span>алгебра</span></p>
    {kpi("Уроков в сентябре", "8", "", 400, 7)}{kpi("Баланс", "-1&nbsp;800", "руб.", 900, 0, "mf-kpi--y")}
    <p class="mf-line"{A(1700)}>{ic("check", "ic ic--12")}30.09 · Квадратные уравнения · проведен</p>
  </div>
  <div class="mf-card mf-card--soft"><ul class="mf-rows">{row("МК", "Марина К.", "8 уроков · 1&nbsp;800&nbsp;руб.", chip("debt", "к&nbsp;оплате", 1200))}{row("АД", "Артем Д.", "7 уроков", chip("debt", "долг 2&nbsp;600"))}{row("СВ", "Соня В.", "5 уроков", chip("debt", "долг 4&nbsp;200"))}</ul></div>
</div>'''},
            {'t': 'Долги на виду', 'cap': 'Кто должен и сколько, видно на главном экране.', 'scene': f'''<div class="mf mf--one">
  <div class="mf-card mf-card--wide">
    <div class="mf-kpis">{kpi("Получено в сентябре", "38&nbsp;400", "руб.", 200, 0)}{kpi("Долги", "6&nbsp;800", "руб.", 500, 0, "mf-kpi--y")}</div>
    <ul class="mf-rows">{row("СВ", "Соня Ветрова", "7 дней · 4&nbsp;200&nbsp;руб.", chip("debt", "долг"), 1200)}{row("АД", "Артем Дроздов", "2 дня · 2&nbsp;600&nbsp;руб.", chip("debt", "долг"), 1500)}</ul>
  </div>
</div>'''},
            {'t': 'Напоминание уходит само', 'cap': 'Родителю приходит вежливое напоминание об оплате.', 'scene': f'''<div class="mf mf--center">
  {phone(f"""<p class="mf-ph__chat">Елена Кузнецова</p>
    <p class="mf-bub mf-bub--in"{A(500)}>Добрый день. Напоминаем об&nbsp;оплате 2&nbsp;уроков по&nbsp;алгебре: 2&nbsp;600&nbsp;руб.<small>TeacherDesk · 10:00</small></p>
    <p class="mf-bub mf-bub--out"{A(2000)}>Спасибо, сегодня оплачу<small>10:12</small></p>""")}
  {toast(1300, "bell", "Напоминание отправлено", "автоматически, без вашего сообщения", "tr", y=True)}
</div>'''},
            {'t': 'Оплата пришла', 'cap': 'Отметили оплату, долг погас, доход за месяц вырос.', 'scene': f'''<div class="mf mf--one">
  <div class="mf-card mf-card--wide">
    <div class="mf-kpis">{kpi("Получено в сентябре", "41&nbsp;000", "руб.", 900, 38400)}{kpi("Долги", "4&nbsp;200", "руб.", 900, 6800, "mf-kpi--y")}</div>
    <ul class="mf-rows">{row("АД", "Артем Дроздов", "2 урока · 2&nbsp;600&nbsp;руб.", chip("done", "оплачено", 700))}{row("СВ", "Соня Ветрова", "7 дней · 4&nbsp;200&nbsp;руб.", chip("debt", "долг"))}</ul>
  </div>
  {toast(400, "wallet", "Оплата получена", "Артем Д. · 2&nbsp;600&nbsp;руб.", "tr")}
</div>'''},
        ],
    }


def uchet_uchenikov():
    card_head = '<p class="mf-h"><span class="mf-who"><span class="av av--lg">МК</span><span><b>Марина Кузнецова</b><small>алгебра · 9 класс</small></span></span><span class="chip chip--paid">баланс 0</span></p>'
    return {
        'title': 'Ученики · карточка',
        'h2': 'Все про ученика в&nbsp;одной <em class="em">карточке</em>',
        'lead': 'Контакты, родители, история занятий и заметки: как собирается карточка и почему ее не нужно искать по чатам.',
        'chapters': [
            {'t': 'Новый ученик', 'cap': 'Имя, предмет и ставка: карточка готова за минуту.', 'scene': f'''<div class="mf mf--split">
  <div class="mf-card mf-card--form"><p class="mf-h"><b>Новый ученик</b><span>карточка</span></p>
    {field("Имя", "Марина Кузнецова", 300)}{field("Предмет и класс", "Алгебра, 9 класс", 1100)}{field("Ставка", "1&nbsp;800 руб. за урок", 1800)}
    <span class="mf-btn"{A(2600, "press")}>Сохранить</span></div>
  <div class="mf-card mf-card--soft"><ul class="mf-rows">{row("АД", "Артем Дроздов", "физика")}{row("СВ", "Соня Ветрова", "ОГЭ")}{row("МК", "Марина Кузнецова", "алгебра", chip("done", "новая"), 3100, "pop")}</ul></div>
</div>'''},
            {'t': 'Контакты родителя', 'cap': 'Мама, телефон и почта рядом с уроками ученика.', 'scene': f'''<div class="mf mf--one">
  <div class="mf-card mf-card--wide">{card_head}
    <div class="mf-grid2">{field("Родитель", "Елена Кузнецова", 400)}{field("Телефон", "+7 9•• •••-••-12", 1200)}{field("Почта", "elena@mail.ru", 1900)}{field("Цель", "ОГЭ на 4 и выше", 2600)}</div>
  </div>
  {toast(3300, "mail", "Приглашение отправлено", "Марина получит доступ в&nbsp;кабинет", "br", y=True)}
</div>'''},
            {'t': 'История занятий', 'cap': 'Что прошли, что задали и как оплачено, по датам.', 'scene': f'''<div class="mf mf--one">
  <div class="mf-card mf-card--wide">{card_head}
    <p class="mf-tabs"><span class="is-on">Занятия</span><span>Задания</span><span>Заметки</span></p>
    <ul class="mf-hist"><li{A(300)}><time>30.09</time><b>Квадратные уравнения</b>{chip("paid", "был")}</li><li{A(700)}><time>25.09</time><b>Теорема Виета</b>{chip("paid", "был")}</li><li{A(1100)}><time>23.09</time><b>Неравенства</b>{chip("soon", "перенос")}</li><li{A(1500)}><time>18.09</time><b>Дискриминант</b>{chip("paid", "был")}</li></ul>
  </div>
</div>'''},
            {'t': 'Заметки под рукой', 'cap': 'Слабые места и договоренности видны перед уроком.', 'scene': f'''<div class="mf mf--one">
  <div class="mf-card mf-card--wide">{card_head}
    <p class="mf-tabs"><span>Занятия</span><span>Задания</span><span class="is-on">Заметки</span></p>
    <p class="mf-note"{A(500, "pop")}>{ic("note")}Слабое место: текстовые задачи</p>
    <p class="mf-note mf-note--w"{A(1400, "pop")}>{ic("calendar")}Каникулы со&nbsp;2 по&nbsp;9 ноября</p>
    <p class="mf-note mf-note--b"{A(2300, "pop")}>{ic("check")}Договорились: пробник раз в&nbsp;месяц</p>
  </div>
</div>'''},
        ],
    }


def kabinet_uchenika():
    return {
        'title': 'Кабинет ученика',
        'h2': 'Ученик сам видит урок, задания и&nbsp;<em class="em">свои ошибки</em>',
        'lead': 'Как ученик попадает в кабинет и что он там находит, без пересылок в мессенджер.',
        'chapters': [
            {'t': 'Приглашение по ссылке', 'cap': 'Отправили ссылку, ученик зарегистрировался и попал к вам.', 'scene': f'''<div class="mf mf--split">
  <div class="mf-card"><p class="mf-h"><b>Пригласить ученика</b><span>Марина К.</span></p>
    <p class="mf-link"{A(300)}>{ic("link", "ic ic--12")}teacherdesk.ru/i/marina-k</p>
    <span class="mf-btn"{A(1100, "press")}>Скопировать ссылку</span>
    <ul class="mf-rows">{row("МК", "Марина Кузнецова", "присоединилась", chip("done", "в&nbsp;кабинете", 2600), 2400)}</ul></div>
  {phone(f"""<p class="mf-ph__chat">Марина</p><p class="mf-bub mf-bub--out"{A(1600)}>Вот ссылка в&nbsp;кабинет, там расписание и&nbsp;задания<small>18:02</small></p><p class="mf-bub mf-bub--in"{A(2300)}>Зарегистрировалась<small>18:05</small></p>""")}
</div>'''},
            {'t': 'Следующий урок и вход', 'cap': 'Дата, время и кнопка входа в урок всегда на виду.', 'scene': f'''<div class="mf mf--center">
  {phone(f"""<p class="mf-ph__hi">Привет, Марина</p>
    <div class="mf-ph__next"><small>Следующий урок</small><b>Чт, 1&nbsp;октября · 15:30</b><span>Алгебра с&nbsp;Анной К.</span><span class="mf-ph__go"{A(1200, "press")}>{ic("video", "ic ic--12")}Войти в&nbsp;урок</span></div>
    <ul class="mf-ph__list"><li><time>пт</time><b>Материалы</b><small>конспект урока</small></li></ul>""")}
  {toast(2200, "video", "Урок открывается здесь же", "видео и&nbsp;доска в&nbsp;одном окне", "tr", y=True)}
</div>'''},
            {'t': 'Задания после урока', 'cap': 'Задание появляется сразу, сдать можно в кабинете.', 'scene': f'''<div class="mf mf--center">
  {phone(f"""<p class="mf-ph__hi">Задания</p>
    <ul class="mf-ph__hw"><li{A(300)}><span>{ic("task", "ic ic--12")}Вариант 2</span>{chip("wait", "на&nbsp;проверке")}</li><li{A(700)}><span>{ic("task", "ic ic--12")}Теорема Виета</span>{chip("paid", "9 из&nbsp;10")}</li><li{A(1300, "pop")}><span>{ic("task", "ic ic--12")}Неравенства</span>{chip("done", "новое")}</li></ul>""")}
  {toast(2100, "bell", "Новое задание", "Неравенства, сдать до&nbsp;пятницы", "bl")}
</div>'''},
            {'t': 'Мои ошибки', 'cap': 'Ошибки из проверенных работ возвращаются карточками.', 'scene': f'''<div class="mf mf--center">
  <div class="mf-deck"><span class="mf-deck__c mf-deck__c--3"></span><span class="mf-deck__c mf-deck__c--2"></span>
    <div class="mf-deck__c mf-deck__c--1"{A(300, "pop")}><small>Мои ошибки · 1 из&nbsp;5</small><b>x² - 5x + 6 = 0</b><span>Найдите корни уравнения</span></div>
    <div class="mf-deck__a"{A(1600)}><small>Ответ</small><b>2 и&nbsp;3</b></div></div>
  {toast(2500, "cards", "Повторить завтра", "интервальное повторение", "tr", y=True)}
</div>'''},
        ],
    }


def domashnie():
    cells = ''.join(f'<li class="mf-t{" mf-t--x" if n == 6 else ""}"{A(300 + n * 220, "on")}>{n}</li>' for n in range(1, 11))
    return {
        'title': 'Задания · алгебра',
        'h2': 'Выдать, проверить и&nbsp;прокомментировать <em class="em">в одном месте</em>',
        'lead': 'Путь задания от выдачи до карточки с ошибкой: без фото тетради в мессенджере.',
        'chapters': [
            {'t': 'Выдать задание', 'cap': 'Тема, файлы и срок: ученик увидит задание сразу.', 'scene': f'''<div class="mf mf--split">
  <div class="mf-card mf-card--form"><p class="mf-h"><b>Новое задание</b><span>Марина К.</span></p>
    {field("Тема", "Квадратные уравнения, вариант 2", 300)}
    <span class="mf-field"><small>Материалы</small><span class="mf-chips"><span class="mf-file"{A(1300, "pop")}>{ic("doc", "ic ic--12")}variant-2.pdf</span><span class="mf-file"{A(1700, "pop")}>{ic("doc", "ic ic--12")}formuly.pdf</span></span></span>
    {field("Сдать до", "пятница, 2&nbsp;октября", 2100)}
    <span class="mf-btn"{A(2900, "press")}>Выдать</span></div>
  {toast(3500, "task", "Задание выдано", "Марина увидит его в&nbsp;кабинете", "br", y=True)}
</div>'''},
            {'t': 'Ученик сдает', 'cap': 'Решение загружают в кабинете, а не присылают в чат.', 'scene': f'''<div class="mf mf--center">
  {phone(f"""<p class="mf-ph__hi">Вариант 2</p><p class="mf-ph__sub">сдать до&nbsp;пятницы</p>
    <span class="mf-file mf-file--big"{A(600, "pop")}>{ic("upload", "ic ic--12")}reshenie.jpg</span>
    <span class="mf-ph__go"{A(1500, "press")}>Сдать работу</span>""")}
  {toast(2300, "check", "Работа сдана", "Марина К. · Вариант 2", "tr")}
</div>'''},
            {'t': 'Проверка', 'cap': 'Отметки по задачам и комментарий к ошибке.', 'scene': f'''<div class="mf mf--one">
  <div class="mf-card mf-card--wide"><p class="mf-h"><b>Квадратные уравнения, вариант 2</b><span>Марина К.</span></p>
    <ol class="mf-tasks">{cells}</ol>
    <p class="mf-bub mf-bub--note"{A(2700, "pop")}><span class="av av--me">АК</span>Задача 6: знак перед 5x</p></div>
</div>'''},
            {'t': 'Ошибка в карточки', 'cap': 'Неверная задача сама уходит ученику на повторение.', 'scene': f'''<div class="mf mf--center">
  <div class="mf-deck"><span class="mf-deck__c mf-deck__c--3"></span><span class="mf-deck__c mf-deck__c--2"></span>
    <div class="mf-deck__c mf-deck__c--1"{A(400, "pop")}><small>Мои ошибки · Марина К.</small><b>Задача 6</b><span>Знак перед 5x при переносе</span></div></div>
  {toast(1500, "cards", "Добавлено в&nbsp;колоду", "«Мои ошибки»: 5 карточек", "tr", y=True)}
</div>'''},
        ],
    }


def board_scene(extra=''):
    return f'''<div class="mf-board">
    <ul class="mf-board__tools"><li class="is-on">{ic("pen", "ic ic--12")}</li><li>{ic("type", "ic ic--12")}</li><li>{ic("shape", "ic ic--12")}</li><li>{ic("eraser", "ic ic--12")}</li></ul>
    <div class="mf-board__sheet">{extra}</div>
    <div class="mf-board__cams"><span class="mf-cam"><span class="av av--me">АК</span><small>Анна</small></span><span class="mf-cam mf-cam--y"><span class="av">МК</span><small>Марина</small></span></div>
  </div>'''


def onlayn_doska():
    par = '<svg class="mf-draw" viewBox="0 0 220 120"><path class="mf-draw__ax" d="M10 100h200M60 8v104"/><path class="mf-draw__p"{a} d="M28 14c14 70 34 92 62 92s48-22 62-92"/>{pts}</svg>'
    return {
        'title': 'Урок · алгебра · Марина К.',
        'h2': 'Урок открывается из&nbsp;расписания, доска уже <em class="em">готова</em>',
        'lead': 'Видео и доска в одном окне: как проходит онлайн-урок от ссылки до сохраненного листа.',
        'chapters': [
            {'t': 'Урок из расписания', 'cap': 'Ссылка на урок лежит в карточке занятия.', 'scene': f'''<div class="mf mf--split">
  <div class="mf-card"><p class="mf-h"><b>Сегодня</b><span>среда</span></p><ul class="mf-rows">{row("СВ", "14:00 · ОГЭ", "Соня В.", chip("paid", "был"))}{row("МК", "15:30 · Алгебра", "Марина К.", '<span class="mf-btn mf-btn--sm"' + A(900, "press") + '>Начать урок</span>', cls="mf-row--now")}</ul></div>
  <div class="mf-card mf-card--soft"{A(1800)}>{board_scene()}</div>
</div>'''},
            {'t': 'Пишем вместе', 'cap': 'Формулы, графики и чертежи на общей доске.', 'scene': f'''<div class="mf mf--one">
  <div class="mf-card mf-card--wide mf-card--flush">{board_scene('<p class="mf-eq"' + A(300, "type") + '>x² - 5x + 6 = 0</p><p class="mf-eq mf-eq--b"' + A(1300, "type") + '>D = 25 - 24 = 1</p>' + par.format(a=A(2000, "draw"), pts=''))}</div>
</div>'''},
            {'t': 'Ученик рисует с разрешения', 'cap': 'Включили разрешение, и Марина отмечает корни сама.', 'scene': f'''<div class="mf mf--one">
  <div class="mf-card mf-card--wide mf-card--flush">{board_scene('<p class="mf-eq">x² - 5x + 6 = 0</p>' + par.format(a='', pts='<circle class="mf-draw__pt"' + A(1600, "pop") + ' cx="72" cy="100" r="6"/><circle class="mf-draw__pt"' + A(2000, "pop") + ' cx="108" cy="100" r="6"/>') + '<span class="mf-pen"' + A(1200, "pop") + '>' + ic("pen", "ic ic--12") + 'Марина</span>')}</div>
  <p class="mf-switch"{A(400, "on")}><span class="mf-switch__k"></span>Марина может рисовать</p>
</div>'''},
            {'t': 'Листы сохраняются', 'cap': 'После урока листы доски остаются, к ним легко вернуться.', 'scene': f'''<div class="mf mf--one">
  <div class="mf-card mf-card--wide"><p class="mf-h"><b>Листы урока</b><span>30.09 · алгебра</span></p>
    <ul class="mf-sheets"><li{A(300, "pop")}><span class="mf-sheet">{par.format(a='', pts='')}</span><small>Лист 1</small></li><li{A(700, "pop")}><span class="mf-sheet mf-sheet--t"><b>x₁ = 2</b><b>x₂ = 3</b></span><small>Лист 2</small></li><li{A(1100, "pop")}><span class="mf-sheet mf-sheet--e"></span><small>Лист 3</small></li></ul></div>
  {toast(1800, "check", "Листы сохранены", "откройте их на&nbsp;следующем уроке", "br", y=True)}
</div>'''},
        ],
    }


def ii_assistent():
    plan = [('Разминка: 3 устные задачи', '10 мин'), ('Формула дискриминанта на двух примерах', '15 мин'), ('Самостоятельная из 5 уравнений', '25 мин'), ('Разбор ошибок и домашнее задание', '10 мин')]
    rows = ''.join(f'<li{A(500 + i * 600)}><span{A(500 + i * 600, "type")}>{t}</span><time>{m}</time></li>' for i, (t, m) in enumerate(plan))
    return {
        'title': 'ИИ-ассистент',
        'h2': 'План урока за&nbsp;минуту, но&nbsp;последнее слово <em class="em">за вами</em>',
        'lead': 'Ассистент работает на сервере в России и ничего не сохраняет без вашего подтверждения.',
        'chapters': [
            {'t': 'Запрос своими словами', 'cap': 'Тема, класс и длительность обычным текстом.', 'scene': f'''<div class="mf mf--one">
  <div class="mf-card mf-card--wide mf-ai"><p class="mf-h"><b>Новый запрос</b><span class="chip chip--wait">10 из&nbsp;100 сегодня</span></p>
    <p class="mf-prompt"><span{A(300, "type", len=1600)}>План урока: квадратные уравнения, 8&nbsp;класс, 60&nbsp;минут</span><i class="caret"></i></p>
    <span class="mf-btn"{A(2400, "press")}>{ic("ai", "ic ic--12")}Собрать</span></div>
</div>'''},
            {'t': 'План за минуту', 'cap': 'Этапы со временем печатаются за секунды.', 'scene': f'''<div class="mf mf--one">
  <div class="mf-card mf-card--wide mf-ai"><p class="mf-bub mf-bub--me">План урока: квадратные уравнения, 8&nbsp;класс, 60&nbsp;минут</p>
    <div class="mf-aibot"><p class="mf-aibot__h"><span class="pulse"></span>ИИ-ассистент</p><ol class="mf-plan">{rows}</ol></div></div>
</div>'''},
            {'t': 'Предпросмотр', 'cap': 'Ассистент показывает результат и ждет вашего «да».', 'scene': f'''<div class="mf mf--split">
  <div class="mf-card mf-ai"><p class="mf-h"><b>Предпросмотр</b><span>план урока</span></p><ol class="mf-plan mf-plan--s">{"".join(f"<li><span>{t}</span><time>{m}</time></li>" for t, m in plan)}</ol>
    <p class="mf-btns"><span class="mf-btn mf-btn--ghost">Изменить</span><span class="mf-btn"{A(1300, "press")}>Сохранить в&nbsp;урок</span></p></div>
  {toast(2100, "lock", "Сохранено после подтверждения", "без вашего «да» ничего не&nbsp;записывается", "br", y=True)}
</div>'''},
            {'t': 'Задания и карточки', 'cap': 'По той же теме: задания на дом и карточки.', 'scene': f'''<div class="mf mf--split">
  <div class="mf-card"><p class="mf-h"><b>Домашнее задание</b><span>5 задач</span></p><ul class="mf-rows mf-rows--t"><li{A(300)}><b>1.</b> x² - 7x + 12 = 0</li><li{A(600)}><b>2.</b> 2x² + 3x - 2 = 0</li><li{A(900)}><b>3.</b> x² - 6x + 9 = 0</li></ul>{chip("done", "в&nbsp;задание Марине", 1500)}</div>
  <div class="mf-deck mf-deck--s"><span class="mf-deck__c mf-deck__c--2"></span><div class="mf-deck__c mf-deck__c--1"{A(1900, "pop")}><small>Карточки · 6 шт.</small><b>Формула дискриминанта</b><span>D = b² - 4ac</span></div></div>
</div>'''},
        ],
    }


def otchety():
    return {
        'title': 'Отчет родителю · сентябрь',
        'h2': 'Отчет за&nbsp;месяц собирается сам, вы&nbsp;добавляете <em class="em">одну фразу</em>',
        'lead': 'Посещаемость, задания и прогресс по темам: как отчет попадает к родителю ссылкой.',
        'chapters': [
            {'t': 'Месяц собирается сам', 'cap': 'Уроки, пропуски и задания считаются по расписанию.', 'scene': f'''<div class="mf mf--one">
  <div class="mf-card mf-card--wide"><p class="mf-h"><span class="mf-who"><span class="av">МК</span><span><b>Марина Кузнецова</b><small>отчет за&nbsp;сентябрь</small></span></span></p>
    <div class="mf-kpis mf-kpis--3">{kpi("Уроков", "8", "", 300, 0)}{kpi("Пропусков", "0", "", 300, 0)}{kpi("Задания", "9", "из 10", 300, 0)}</div></div>
</div>'''},
            {'t': 'Прогресс по темам', 'cap': 'Видно, что получается и что подтянуть.', 'scene': f'''<div class="mf mf--one">
  <div class="mf-card mf-card--wide"><p class="mf-h"><b>Прогресс по&nbsp;темам</b><span>сентябрь</span></p>
    <ul class="mf-bars"><li><span>Квадратные уравнения</span><span class="mf-bar"{A(300, "fill")} style="--v:.9"><i></i></span><b>90%</b></li><li><span>Теорема Виета</span><span class="mf-bar"{A(700, "fill")} style="--v:.75"><i></i></span><b>75%</b></li><li><span>Текстовые задачи</span><span class="mf-bar mf-bar--y"{A(1100, "fill")} style="--v:.5"><i></i></span><b>50%</b></li></ul></div>
</div>'''},
            {'t': 'Комментарий репетитора', 'cap': 'Одна-две фразы от вас делают отчет живым.', 'scene': f'''<div class="mf mf--one">
  <div class="mf-card mf-card--wide"><p class="mf-h"><b>Комментарий</b><span>для&nbsp;Елены Кузнецовой</span></p>
    <p class="mf-quote"><span{A(300, "type", len=2200)}>Марина уверенно решает уравнения. В&nbsp;октябре добавим текстовые задачи, это ее слабое место.</span></p>
    <span class="mf-btn"{A(2900, "press")}>Отправить отчет</span></div>
</div>'''},
            {'t': 'Ссылка родителю', 'cap': 'Родитель открывает отчет по ссылке, без входа.', 'scene': f'''<div class="mf mf--center">
  {phone(f"""<p class="mf-ph__chat">Анна, репетитор</p>
    <div class="mf-bub mf-bub--in mf-bub--card"{A(400)}><b>Отчет за&nbsp;сентябрь · Марина</b><span>8 уроков · 0 пропусков · 9 из&nbsp;10 заданий</span><small>teacherdesk.ru/r/…</small></div>
    <p class="mf-bub mf-bub--out"{A(1800)}>Спасибо, все понятно<small>20:14</small></p>""")}
  {toast(1000, "link", "Ссылка ушла Елене К.", "отчет откроется без регистрации", "tr", y=True)}
</div>'''},
        ],
    }


def zhurnal():
    return {
        'title': 'Журнал · сентябрь',
        'h2': 'Журнал ведется по&nbsp;урокам, а&nbsp;не&nbsp;по <em class="em">вечерам</em>',
        'lead': 'Что прошли, что задали и кто пропустил: как журнал заполняется вместе с расписанием.',
        'chapters': [
            {'t': 'Урок отмечен', 'cap': 'Проведенный урок встает в журнал с темой.', 'scene': f'''<div class="mf mf--one">
  <div class="mf-card mf-card--wide"><p class="mf-jh"><span>Дата</span><span>Ученик</span><span>Тема</span><span>Статус</span></p>
    <ul class="mf-jr"><li class="mf-jr--new"{A(400, "pop")}><time>30.09</time><b>Марина К.</b><span>Неравенства</span>{chip("paid", "был")}</li><li><time>30.09</time><b>Соня В.</b><span>ОГЭ, задание 20</span>{chip("paid", "был")}</li><li><time>29.09</time><b>Илья П.</b><span>Present Perfect</span>{chip("paid", "был")}</li></ul></div>
</div>'''},
            {'t': 'Что задано', 'cap': 'Задание к уроку записано рядом с темой.', 'scene': f'''<div class="mf mf--one">
  <div class="mf-card mf-card--wide"><p class="mf-jh"><span>Дата</span><span>Ученик</span><span>Тема</span><span>Задано</span></p>
    <ul class="mf-jr"><li><time>30.09</time><b>Марина К.</b><span>Неравенства</span><em{A(400, "type")}>Вариант 3</em></li><li><time>30.09</time><b>Соня В.</b><span>ОГЭ, задание 20</span><em{A(1000, "type")}>5 задач</em></li><li><time>29.09</time><b>Илья П.</b><span>Present Perfect</span><em{A(1600, "type")}>Упр. 4-6</em></li></ul></div>
</div>'''},
            {'t': 'Пропуск виден', 'cap': 'Пропуски отмечены, их легко обсудить с родителем.', 'scene': f'''<div class="mf mf--one">
  <div class="mf-card mf-card--wide"><p class="mf-jh"><span>Дата</span><span>Ученик</span><span>Тема</span><span>Статус</span></p>
    <ul class="mf-jr"><li><time>28.09</time><b>Артем Д.</b><span>Импульс</span>{chip("debt", "пропуск", 600)}</li><li><time>25.09</time><b>Артем Д.</b><span>Законы Ньютона</span>{chip("paid", "был")}</li><li><time>23.09</time><b>Марина К.</b><span>Неравенства</span>{chip("soon", "перенос")}</li></ul></div>
  {toast(1600, "note", "Артем: 1 пропуск в&nbsp;сентябре", "видно в&nbsp;отчете родителю", "br", y=True)}
</div>'''},
            {'t': 'Итог месяца', 'cap': 'Сколько уроков проведено и сколько пропущено.', 'scene': f'''<div class="mf mf--one">
  <div class="mf-card mf-card--wide"><p class="mf-h"><b>Сентябрь</b><span>итог</span></p>
    <div class="mf-kpis mf-kpis--3">{kpi("Уроков", "31", "", 300, 0)}{kpi("Пропусков", "2", "", 300, 0, "mf-kpi--y")}{kpi("Учеников", "12", "", 300, 0)}</div>
    <p class="mf-line"{A(1400)}>{ic("report", "ic ic--12")}Статистика уходит в&nbsp;отчеты родителям</p></div>
</div>'''},
        ],
    }


FILMS = {'raspisanie': raspisanie, 'uchet-oplat': uchet_oplat, 'uchet-uchenikov': uchet_uchenikov,
         'kabinet-uchenika': kabinet_uchenika, 'domashnie-zadaniya': domashnie, 'onlayn-doska': onlayn_doska,
         'ii-assistent': ii_assistent, 'otchety-roditelyam': otchety, 'zhurnal-zanyatiy': zhurnal}


def get(pid):
    return FILMS[pid]() if pid in FILMS else None
