# -*- coding: utf-8 -*-
"""Живые кадры продукта для первого экрана внутренних страниц.

Кадры tl, debt, hw, ai повторяют ячейки «Дня репетитора» с главной, но живут отдельно:
свои классы pd-* в pages.css и свой код в pages.js (атрибут data-pd), чтобы правки главной
их не ломали. Остальные кадры двигаются CSS-циклами, которые pages.js включает классом .is-vis,
только пока кадр виден на экране.
Данные вымышленные, из брифа: репетитор Анна Ковалева, ученики Марина, Артем, Соня, Илья.
"""
from blocks import ic


def frame(title, body, cls='', pd=None, live=True, label=''):
    bar = f'<div class="frame__bar" aria-hidden="true"><span class="frame__dots"><i></i><i></i><i></i></span><span class="frame__t">{title}</span></div>'
    if pd:
        return f'<div class="frame {cls}">{bar}<div class="frame__cell" data-pd="{pd}">{body}</div></div>'
    lv = ' data-live' if live else ''
    al = f' role="img" aria-label="{label}"' if label else ''
    return f'<figure class="frame {cls}"{lv}{al}>{bar}<div class="frame__body" aria-hidden="true">{body}</div></figure>'


TL = '''<figure class="pd-demo pd-tl" role="img" aria-label="Лента дня: четыре урока с 14:00 до 20:00, урок с Соней идет сейчас. Марине К. ушло напоминание за час до урока">
  <div class="pd-tl__in" aria-hidden="true">
    <div class="pd-tl__axis"><span style="--s:0">13:00</span><span style="--s:1">14:00</span><span style="--s:2">15:00</span><span style="--s:3">16:00</span><span style="--s:4">17:00</span><span class="pd-tl__far" style="--s:5">18:00</span><span class="pd-tl__far" style="--s:6">19:00</span><span class="pd-tl__far" style="--s:7">20:00</span></div>
    <div class="pd-tl__track">
      <div class="pd-tl__ls pd-tl__ls--now" style="--s:1"><b>ОГЭ</b><span>Соня В.</span></div>
      <div class="pd-tl__ls pd-tl__ls--paid" style="--s:2.5"><b>Алгебра</b><span>Марина К.</span></div>
      <div class="pd-tl__ls pd-tl__far" style="--s:4.25"><b>Физика</b><span>Артем Д.</span></div>
      <div class="pd-tl__ls pd-tl__ls--paid pd-tl__far" style="--s:6"><b>Английский</b><span>группа B1</span></div>
      <div class="pd-tl__now"><span class="pill-now"><i></i>идет сейчас</span></div>
    </div>
  </div>
  <div class="pd-tl__foot" aria-hidden="true">
    <p class="pd-tl__note"><svg class="ic"><use href="#i-bell"/></svg><span>Напоминание Марине К. уйдет в&nbsp;14:30</span></p>
    <p class="pd-slap"><svg class="ic"><use href="#i-bell"/></svg><span>Напоминание ушло Марине&nbsp;К.</span><time>14:30</time></p>
  </div>
</figure>'''

DEBT = '''<div class="pd-demo pd-debt">
  <p class="pd-debt__lbl" aria-hidden="true">Просрочено</p>
  <p class="pd-debt__sum" aria-hidden="true"><span data-pd-sum>6&nbsp;800</span><small>руб.</small></p>
  <ul class="pd-debt__rows">
    <li data-pd-row="s">
      <span class="av" aria-hidden="true">СВ</span>
      <span class="pd-debt__who"><b>Соня Ветрова</b><span>7&nbsp;дней · 4&nbsp;200&nbsp;руб.</span></span>
      <button class="pd-rbtn" type="button" data-pd-remind aria-label="Напомнить Соне Ветровой об оплате"><span class="pd-swap"><span>Напомнить</span><span class="is-off">Ушло</span><span class="is-off">Оплачено</span></span></button>
    </li>
    <li data-pd-row="a">
      <span class="av" aria-hidden="true">АД</span>
      <span class="pd-debt__who"><b>Артем Дроздов</b><span>2&nbsp;дня · 2&nbsp;600&nbsp;руб.</span></span>
      <button class="pd-rbtn" type="button" data-pd-remind aria-label="Напомнить Артему Дроздову об оплате"><span class="pd-swap"><span>Напомнить</span><span class="is-off">Ушло</span><span class="is-off">Оплачено</span></span></button>
    </li>
  </ul>
</div>'''

HW = '''<figure class="pd-demo pd-hw" role="img" aria-label="Задание «Квадратные уравнения, вариант 2»: проверено 7 из 10 задач">
  <div aria-hidden="true">
    <p class="pd-hw__t">Квадратные уравнения, вариант 2</p>
    <p class="pd-hw__m">Марина К. · сдать до&nbsp;2&nbsp;октября</p>
    <ol class="pd-hw__tasks" data-pd-tasks>
      <li class="is-ok">1</li><li class="is-ok">2</li><li class="is-ok">3</li><li class="is-ok">4</li><li class="is-ok">5</li><li class="is-ok">6</li><li class="is-ok">7</li><li data-pd-hw8>8</li><li>9</li><li>10</li>
    </ol>
    <p class="pd-hw__f"><span><b data-pd-n>7</b> из&nbsp;10&nbsp;задач</span><span class="chip chip--wait"><svg class="ic ic--12"><use href="#i-clock"/></svg>в&nbsp;работе</span></p>
    <p class="pd-hw__note sticker"><span class="av av--me">АК</span><span>Задача 6: знак перед 5x</span></p>
    <p class="pd-hw__deck"><svg class="ic"><use href="#i-cards"/></svg><span>Задача 6 ушла в&nbsp;колоду «Мои ошибки»</span></p>
  </div>
</figure>'''

AI = '''<div class="pd-demo pd-ai">
  <p class="pd-ai__me">План урока: квадратные уравнения, 8&nbsp;класс, 60&nbsp;минут</p>
  <div class="pd-ai__bot">
    <p class="pd-ai__who"><span class="pulse" aria-hidden="true"></span>ИИ-ассистент<span class="pd-ai__dots" aria-hidden="true"><i></i><i></i><i></i></span></p>
    <ol class="pd-ai__plan">
      <li><span data-pd-type>Разминка: 3&nbsp;устные задачи на&nbsp;разложение</span><time>10&nbsp;мин</time></li>
      <li><span data-pd-type>Формула дискриминанта на&nbsp;двух примерах</span><time>15&nbsp;мин</time></li>
      <li><span data-pd-type>Самостоятельная работа из&nbsp;5&nbsp;уравнений</span><time>25&nbsp;мин</time></li>
      <li><span data-pd-type>Разбор ошибок и&nbsp;домашнее задание</span><time>10&nbsp;мин</time></li>
    </ol>
  </div>
  <p class="pd-ai__save"><svg class="ic"><use href="#i-lock"/></svg>Сохранится только после вашего подтверждения</p>
</div>'''

# Тот же диалог ассистента, но запрос на задания: подборка с ответами, выдача после проверки.
AI_TASKS = '''<div class="pd-demo pd-ai">
  <p class="pd-ai__me">4 задания: квадратные уравнения, 8&nbsp;класс, с&nbsp;ответами</p>
  <div class="pd-ai__bot">
    <p class="pd-ai__who"><span class="pulse" aria-hidden="true"></span>ИИ-ассистент<span class="pd-ai__dots" aria-hidden="true"><i></i><i></i><i></i></span></p>
    <ol class="pd-ai__plan">
      <li><span data-pd-type>x² - 7x + 12 = 0</span><time>3; 4</time></li>
      <li><span data-pd-type>x² + 2x - 15 = 0</span><time>-5; 3</time></li>
      <li><span data-pd-type>2x² - 8 = 0</span><time>-2; 2</time></li>
      <li><span data-pd-type>Задача: площадь прямоугольника 48&nbsp;см²</span><time>6 и 8</time></li>
    </ol>
  </div>
  <p class="pd-ai__save"><svg class="ic"><use href="#i-lock"/></svg>Ученик получит задания после вашей проверки</p>
</div>'''


def week():
    body = '''<div class="pd-week pd-week--hero">
      <div class="pd-week__head"><b>Неделя</b><span>28.09&nbsp;- 02.10</span></div>
      <div class="pd-week__grid">
        <span class="pd-week__d"></span><span class="pd-week__d">пн</span><span class="pd-week__d">вт</span><span class="pd-week__d is-today">ср</span><span class="pd-week__d">чт</span><span class="pd-week__d">пт</span>
        <span class="pd-week__h">09:00</span><i class="pd-wl pd-wl--paid" data-s="Алг">Алгебра</i><i></i><i></i><i class="pd-wl pd-wl--wait" data-s="Геом">Геометрия</i><i></i>
        <span class="pd-week__h">10:30</span><i></i><i class="pd-wl pd-wl--paid" data-s="Англ">Английский</i><i></i><i></i><i class="pd-wl pd-wl--paid" data-s="Англ">Английский</i>
        <span class="pd-week__h">14:00</span><i class="pd-wl pd-wl--paid" data-s="Физ">Физика</i><i></i><i class="pd-wl pd-wl--now">ОГЭ</i><i></i><i></i>
        <span class="pd-week__h">15:30</span><i></i><i></i><i class="pd-wl pd-wl--paid" data-s="Алг">Алгебра</i><i class="pd-wl pd-wl--move" data-s="Хим">Химия</i><i></i>
        <span class="pd-week__h">17:15</span><i></i><i class="pd-wl pd-wl--paid" data-s="Рус">Русский</i><i class="pd-wl pd-wl--wait" data-s="Физ">Физика</i><i></i><i></i>
      </div>
    </div>
    <div class="pd-week__foot"><p><b>4 урока</b><span>сегодня</span></p><p><small>СЛЕДУЮЩИЙ УРОК</small><b>Алгебра · 15:30</b></p></div>
    <p class="pd-slap pd-wslap">''' + ic('bell') + '''<span>Перенос: ученик получил уведомление</span><time>чт 15:30</time></p>'''
    return frame('Расписание · неделя', body, 'frame--week', label='Расписание на неделю: урок химии переносится со среды на четверг, ученик получает уведомление')


def board():
    body = f'''<div class="pd-board__in">
      <ul class="pd-board__tools"><li class="is-on">{ic("pen")}</li><li>{ic("type")}</li><li>{ic("shape")}</li><li>{ic("eraser")}</li></ul>
      <div class="pd-board__sheet">
        <p class="pd-board__eq">x² - 5x + 6 = 0</p>
        <p class="pd-board__ln pd-board__ln--1">D = 25 - 24 = 1</p>
        <p class="pd-board__ln pd-board__ln--2">x₁ = 2, &nbsp;x₂ = 3</p>
        <svg class="pd-board__draw" viewBox="0 0 220 120"><path class="pd-board__axes" d="M10 100h200M60 8v104"/><path class="pd-board__par" d="M28 14c14 70 34 92 62 92s48-22 62-92"/><circle class="pd-board__pt pd-board__pt--1" cx="72" cy="100" r="5"/><circle class="pd-board__pt pd-board__pt--2" cx="108" cy="100" r="5"/></svg>
        <span class="pd-board__cur">{ic("pen", "ic ic--12")}Марина</span>
      </div>
      <div class="pd-board__cams">
        <span class="pd-cam"><span class="av av--lg av--me">АК</span><small>Анна К.</small>{ic("mic", "ic ic--12")}</span>
        <span class="pd-cam pd-cam--st"><span class="av av--lg">МК</span><small>Марина К.</small>{ic("mic", "ic ic--12")}</span>
      </div>
    </div>
    <div class="pd-board__foot"><span class="chip chip--paid">{ic("pen", "ic ic--12")}Марине разрешено рисовать</span><span class="pd-board__saved">{ic("check", "ic ic--12")}Лист 2 сохранен</span></div>'''
    return frame('Урок · алгебра · Марина К.', body, 'frame--board', label='Онлайн-урок: видео и доска в одном окне, ученица решает уравнение на доске, лист сохраняется')


def phone():
    rows = [('09:00', 'Алгебра', 'Марина К.', '<span class="chip chip--paid">оплачено</span>'),
            ('11:00', 'Английский', 'Илья П.', '<span class="chip chip--wait">ждет</span>'),
            ('14:00', 'ОГЭ', 'Соня В.', '<span class="pill-now"><i></i>сейчас</span>'),
            ('16:30', 'Физика', 'Артем Д.', '<span class="chip chip--debt">долг</span>')]
    lis = ''.join(f'<li><time>{t}</time><span><b>{s}</b><small>{n}</small></span>{c}</li>' for t, s, n, c in rows)
    return f'''<figure class="pd-pdemo" data-live role="img" aria-label="Телефон с TeacherDesk на главном экране: уроки на сегодня и уведомление о ближайшем уроке">
  <div class="pd-phone2 phone-frame" aria-hidden="true">
    <div class="pd-phone2__scr">
      <div class="pd-phone2__top"><time>9:41</time><span class="pd-phone2__isl"></span><span class="pd-phone2__sig"><i></i><i></i><i></i></span></div>
      <div class="pd-phone2__push"><img src="/assets/img/sign.svg" width="28" height="28" alt=""><span><b>Урок через час</b><small>Алгебра с&nbsp;Мариной в&nbsp;15:30, ссылка в&nbsp;кабинете</small></span><time>сейчас</time></div>
      <p class="pd-phone2__d">Среда, 30&nbsp;сентября</p>
      <p class="pd-phone2__h">Сегодня 4&nbsp;урока</p>
      <ul class="pd-phone2__list">{lis}</ul>
      <p class="pd-phone2__sum"><span>Должны</span><b>6&nbsp;800&nbsp;руб.</b></p>
      <nav class="pd-phone2__tab">{ic("home")}{ic("calendar")}{ic("wallet")}{ic("users")}</nav>
    </div>
  </div>
  <p class="pd-pdemo__tag sticker" style="--tilt:-3deg" aria-hidden="true">{ic("phone")}На главном экране, без магазина</p>
</figure>'''


def card():
    body = f'''<div class="pd-scard__head"><span class="av av--lg">МК</span><span class="pd-scard__who"><b>Марина Кузнецова</b><small>Алгебра · 9&nbsp;класс · 1&nbsp;800&nbsp;руб. за&nbsp;урок</small></span><span class="chip chip--paid">баланс 0</span></div>
    <dl class="pd-scard__info"><div><dt>Родитель</dt><dd>Елена Кузнецова</dd></div><div><dt>Телефон</dt><dd>+7 9•• •••-••-12</dd></div><div><dt>Цель</dt><dd>ОГЭ на&nbsp;4 и&nbsp;выше</dd></div></dl>
    <p class="pd-scard__tabs"><span class="is-on">Занятия</span><span>Задания</span><span>Заметки</span><i class="pd-scard__ul"></i></p>
    <ul class="pd-scard__hist">
      <li><time>30.09</time><span>Квадратные уравнения</span><span class="chip chip--paid">был</span></li>
      <li><time>25.09</time><span>Теорема Виета</span><span class="chip chip--paid">был</span></li>
      <li><time>23.09</time><span>Неравенства</span><span class="chip chip--soon">перенос</span></li>
    </ul>
    <p class="pd-scard__note sticker" style="--tilt:-2deg">{ic("note")}<span>Слабое место: текстовые задачи</span></p>'''
    return frame('Ученики · карточка', body, 'frame--card', label='Карточка ученицы Марины Кузнецовой: контакты родителя, цель, история занятий и заметка репетитора')


def cabinet():
    body = f'''<p class="pd-cab__hi">Привет, Марина</p>
    <div class="pd-cab__next"><span class="pd-cab__lbl">Следующий урок</span><b>Чт, 1&nbsp;октября · 15:30</b><span>Алгебра с&nbsp;Анной К.</span><span class="pd-cab__go">{ic("video", "ic ic--12")}Войти в&nbsp;урок</span></div>
    <ul class="pd-cab__hw">
      <li><span>{ic("task")}Квадратные уравнения, вариант 2</span><span class="chip chip--wait">на&nbsp;проверке</span></li>
      <li><span>{ic("task")}Теорема Виета</span><span class="chip chip--paid">9 из&nbsp;10</span></li>
      <li class="pd-cab__new"><span>{ic("task")}Неравенства</span><span class="chip chip--done">новое</span></li>
    </ul>
    <p class="pd-cab__deck">{ic("cards")}<span><b>Мои ошибки</b><small>5 карточек на&nbsp;повторение</small></span></p>'''
    return frame('Кабинет ученика', body, 'frame--cab', label='Кабинет ученицы: следующий урок со ссылкой, домашние задания со статусами и колода ошибок для повторения')


def report():
    bars = [('Квадратные уравнения', .9), ('Теорема Виета', .75), ('Текстовые задачи', .5)]
    lis = ''.join(f'<li><span>{n}</span><span class="pd-bar"><i style="--v:{v}"></i></span><b>{int(v * 100)}%</b></li>' for n, v in bars)
    body = f'''<p class="pd-rep__who"><span class="av">МК</span><span><b>Марина Кузнецова</b><small>Отчет за&nbsp;сентябрь</small></span></p>
    <dl class="pd-rep__stats"><div><dt>Уроков</dt><dd>8</dd></div><div><dt>Пропусков</dt><dd>0</dd></div><div><dt>Задания</dt><dd>9/10</dd></div></dl>
    <ul class="pd-rep__bars">{lis}</ul>
    <p class="pd-rep__c">«Уверенно решает уравнения. В&nbsp;октябре добавим текстовые задачи.»</p>
    <p class="pd-slap pd-rslap">{ic("link")}<span>Ссылка ушла Елене Кузнецовой</span></p>'''
    return frame('Отчет родителю · сентябрь', body, 'frame--rep', label='Отчет родителю за сентябрь: 8 уроков без пропусков, прогресс по темам и комментарий репетитора, ссылка отправлена маме')


def journal():
    # Сегодня среда, 30 сентября, как во всех кадрах сайта
    rows = [('29.09', 'Соня В.', 'ОГЭ, задание 20', '5 задач', 'chip--paid', 'был'),
            ('28.09', 'Артем Д.', 'Законы Ньютона', 'нет', 'chip--debt', 'пропуск'),
            ('25.09', 'Илья П.', 'Present Perfect', 'Упр. 4-6', 'chip--soon', 'перенос'),
            ('23.09', 'Марина К.', 'Квадратные уравнения', 'Вариант 2', 'chip--paid', 'был')]
    lis = ''.join(f'<li><time>{d}</time><b>{w}</b><span>{t}</span><span class="pd-jr__hw">{h}</span><span class="chip {c}">{s}</span></li>' for d, w, t, h, c, s in rows)
    body = f'''<p class="pd-jr__head"><span>Дата</span><span>Ученик</span><span>Тема</span><span>Задано</span><span>Статус</span></p>
    <ul class="pd-jr__rows"><li class="pd-jr__new"><time>30.09</time><b>Марина К.</b><span>Неравенства</span><span class="pd-jr__hw">Вариант 3</span><span class="chip chip--done">сегодня</span></li>{lis}</ul>
    <p class="pd-jr__foot"><span>За&nbsp;сентябрь</span><b>31 урок · 2 пропуска</b></p>'''
    return frame('Журнал · сентябрь', body, 'frame--jr', label='Журнал занятий: даты, ученики, темы, заданное и статусы посещения, итог месяца 31 урок и 2 пропуска')


def desk():
    rows = [('09:00', 'Алгебра', 'Марина К.', ''), ('11:00', 'Английский', 'Илья П.', ''), ('14:00', 'ОГЭ', 'Соня В.', '<span class="pill-now"><i></i>сейчас</span>'), ('16:30', 'Физика', 'Артем Д.', '')]
    lis = ''.join(f'<li{" class=is-now" if c else ""}><time>{t}</time><span><b>{s}</b> {n}</span>{c}</li>' for t, s, n, c in rows)
    rail = ''.join(f'<li{" class=is-on" if i == 0 else ""}>{ic(x)}</li>' for i, x in enumerate(['home', 'calendar', 'users', 'task', 'wallet', 'board', 'ai']))
    body = f'''<div class="pd-desk__in">
      <ul class="pd-desk__rail">{rail}</ul>
      <div class="pd-desk__main">
        <div class="pd-desk__p pd-desk__p--today"><p class="pd-desk__h">{ic("calendar")}Сегодня, среда</p><ul class="pd-desk__ls">{lis}</ul></div>
        <div class="pd-desk__p"><p class="pd-desk__h">{ic("wallet")}Должны</p><p class="pd-desk__n">6&nbsp;800 <small>руб.</small></p><p class="pd-desk__s">2 ученика</p></div>
        <div class="pd-desk__p"><p class="pd-desk__h">{ic("task")}Проверить</p><p class="pd-desk__n">3</p><p class="pd-desk__s">работы сдали</p></div>
        <div class="pd-desk__p pd-desk__p--ai"><p class="pd-desk__h">{ic("ai")}Ассистент</p><p class="pd-desk__s">План урока по&nbsp;ОГЭ готов</p><span class="pd-desk__dots"><i></i><i></i><i></i></span></div>
      </div>
    </div>'''
    return frame('TeacherDesk · главный экран', body, 'frame--desk', label='Главный экран кабинета: уроки на сегодня, долги учеников, работы на проверку и ассистент в одном окне')


def trial():
    items = ['Расписание и напоминания', 'Учет оплат и долгов', 'Задания и проверка', 'Онлайн-доска и видео', 'ИИ-ассистент, 100 запросов в&nbsp;день', 'До 50 активных учеников']
    lis = ''.join(f'<li>{ic("check")}<span>{x}</span></li>' for x in items)
    body = f'''<p class="pd-trial__k">Пробный период</p>
    <p class="pd-trial__n"><b>14</b><span>дней полного доступа без&nbsp;карты</span></p>
    <span class="pd-trial__bar"><i></i></span>
    <ul class="pd-trial__list">{lis}</ul>
    <p class="pd-trial__after">{ic("lock")}<span>После: данные остаются, их можно смотреть и&nbsp;выгружать</span></p>'''
    return frame('Ваш кабинет', body, 'frame--trial', label='Пробный период: 14 дней полного доступа без карты, что в него входит и что будет с данными после')


def get(name):
    if name == 'tl':
        return frame('Расписание · сегодня', TL, 'frame--tl', pd='tl')
    if name == 'debt':
        return frame('Оплаты · кто должен', DEBT, 'frame--debt', pd='debt')
    if name == 'hw':
        return frame('Задания · проверка', HW, 'frame--hw', pd='hw')
    if name == 'ai':
        return frame('ИИ-ассистент', AI, 'frame--ai', pd='ai')
    if name == 'ai-tasks':
        return frame('ИИ-ассистент · задания', AI_TASKS, 'frame--ai', pd='ai')
    return {'week': week, 'board': board, 'phone': phone, 'card': card, 'cabinet': cabinet,
            'report': report, 'journal': journal, 'desk': desk, 'trial': trial}[name]()
