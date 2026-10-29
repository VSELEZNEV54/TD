# -*- coding: utf-8 -*-
"""Сценарий расписания и общие компактные блоки страниц возможностей."""
from blocks import ic, typo, sec_head, plain


def heading(kick, title, *args):
    """Один заголовок блока, как в «Других возможностях», без смены гарнитуры внутри."""
    return sec_head(kick, plain(title), *args)


def counter(index, total, icon='calendar'):
    return f'<div class="sc-index"><span class="sc-index__icon">{ic(icon)}</span><span>Возможность <b>{index}</b><span class="sc-index__of"> из {total}</span></span></div>'


def story(c):
    # Те же окна, кабинет, наклейки и плеер, что в ролике на главной.
    tools = [
        ('chat', 'Чат с учениками', '<span class="ft-bub">А вторник в силе?</span><span class="ft-bub ft-bub--me">Сейчас проверю календарь</span>', 'Нужно сверить время', '4%', '10%'),
        ('chat', 'Чат с родителями', '<span class="ft-bub">Артем заболел. Перенесем?</span><span class="ft-bub">Завтра не получится, отменяем</span>', 'Перенести и отменить', '38%', '8%'),
        ('chat', 'Чат группы B1', '<span class="ft-bub">А ссылку пришлете?</span><span class="ft-bub">Во сколько завтра?</span>', '+6 сообщений', '72%', '12%'),
        ('calendar', 'Отдельный календарь', '<span class="ft-hand">ср 15:30 → пт 15:30</span><span class="ft-line">Перенести урок вручную</span>', 'Еще написать ученику', '7%', '52%'),
        ('note', 'Повторы в заметках', '<span class="ft-line">Марина: вт и чт, 11:00</span><span class="ft-line">Скопировать на следующую неделю</span>', 'Каждую неделю заново', '39%', '55%'),
        ('bell', 'Напоминания вручную', '<span class="ft-bub">Не забудьте: урок в 15:30</span><span class="ft-file">ссылка_на_урок.txt</span>', 'Написать каждому', '71%', '53%'),
    ]
    windows = ''.join(f'<div class="ftool" style="--x:{x};--y:{y};--r:0deg"><span class="ftool__bar">{ic(icon)}<span class="ftool__name">{typo(title)}</span></span><span class="ftool__body">{typo(body)}</span><span class="ftool__ping">{typo(ping)}</span></div>' for icon, title, body, ping, x, y in tools)
    benefits = [
        ('plus', 'Новый урок за секунды', 'Ученик, дата, повтор, сохранить'),
        ('refresh', 'Повтор задали один раз', 'Без копирования каждой недели'),
        ('calendar', 'Перенос в два клика', 'Новое время сразу у ученика'),
        ('bell', 'Напоминание за час', 'Вместо ручных сообщений'),
        ('video', 'Ссылка рядом с уроком', 'Вход из кабинета ученика'),
        ('phone', 'Неделя и месяц на виду', 'В браузере и на телефоне'),
    ]
    positions = [('3%', '12%'), ('77%', '14%'), ('4%', '40%'), ('76%', '42%'), ('3%', '68%'), ('77%', '70%')]
    stickers = ''.join(f'<li class="fben" style="--x:{positions[i][0]};--y:{positions[i][1]};--r:0deg"><span class="fben__ic" aria-hidden="true">{ic(icon)}</span><span><b>{typo(title)}</b><small>{typo(text)}</small></span></li>' for i, (icon, title, text) in enumerate(benefits))
    subtitles = [
        (0, 'Было: три чата, отдельный календарь и все вручную'),
        (6000, 'Выбрали ученика, дату и повтор. Нажали «Сохранить».'),
        (11400, 'Урок в календаре. Повтор - на следующие недели.'),
        (13000, 'Перенос в два клика. Ученик видит новое время.'),
        (16500, 'Напоминание за час. Ссылка уже в кабинете ученика.'),
        (20000, 'TeacherDesk: все занятия в одном расписании'),
    ]
    subs = ''.join(f'<span data-film-at="{at}">{typo(text)}</span>' for at, text in subtitles)
    return f'''<section class="sec sc-story-section" aria-labelledby="h-schedule-story"><div class="wrap">
      {heading('Было и стало', 'Те же ученики. Другой порядок.', 'От сообщений «давайте перенесем» до урока, который уже виден ученику. Посмотрите, как меняется работа с расписанием.', 'h-schedule-story', 'sq')}
      </div><div class="film sc-film" data-film="schedule" data-scene="2">
        <figure class="film__stage">
          <div class="film__tools" aria-hidden="true">{windows}</div>
          <p class="film__hud" aria-hidden="true">Чатов: <b>3</b><span>сообщений: <b data-film-msg>0</b></span></p>
          <div class="film__app">
            <div class="win">
              <div class="win__bar"><span class="win__crumb"><img src="/assets/img/sign.svg" width="18" height="18" alt="">TeacherDesk / <b>расписание</b></span><span class="pill-now">{ic('calendar', 'ic ic--12')}Неделя</span></div>
              <div class="fapp" role="img" aria-label="Расписание TeacherDesk: выбираем ученика, дату и повтор, сохраняем урок, переносим на пятницу. Ученику приходит напоминание за час.">
                <div class="fapp__day" aria-hidden="true">
                  <p class="fapp__h">Расписание недели<span>28.09 - 02.10</span></p>
                  <div class="sc-calendar">
                    <span style="grid-area:1/1"></span><span class="sc-calendar__day" style="grid-area:1/2">Ср, 30</span><span class="sc-calendar__day" style="grid-area:1/3">Чт, 1</span><span class="sc-calendar__day" style="grid-area:1/4">Пт, 2</span>
                    <time style="grid-area:2/1">09:00</time><i style="grid-area:2/2"></i><i style="grid-area:2/3"></i><i style="grid-area:2/4"></i>
                    <time style="grid-area:3/1">15:30</time><i style="grid-area:3/2"></i><i style="grid-area:3/3"></i><i class="sc-calendar__target" style="grid-area:3/4"></i>
                    <time style="grid-area:4/1">17:00</time><i style="grid-area:4/2"></i><i style="grid-area:4/3"></i><i style="grid-area:4/4"></i>
                    <span class="sc-calendar__event sc-calendar__event--oge"><b>ОГЭ</b><small>Соня В.</small></span>
                    <span class="sc-calendar__event sc-calendar__event--physics"><b>Физика</b><small>Артем Д.</small></span>
                    <span class="sc-calendar__event sc-film__lesson"><b>Алгебра</b><small>Марина К.</small>{ic('refresh', 'ic ic--12')}</span>
                  </div>
                  <p class="sc-calendar__status">{ic('check', 'ic ic--12')}<span>Марина · <span class="sc-film__date"><span>среда</span><span>пятница</span></span> 15:30</span><span class="chip chip--paid" data-film-save>сохранено</span></p>
                </div>
                <div class="fapp__side" aria-hidden="true">
                  <p class="sc-film__form-title">{ic('plus', 'ic ic--12')}Новый урок</p>
                  <p class="fapp__kpi" data-film-field><small>Ученик</small><b>Марина К.</b></p>
                  <p class="fapp__kpi" data-film-field><small>Дата и время</small><b class="sc-film__date"><span>30 сентября · 15:30</span><span>2 октября · 15:30</span></b></p>
                  <p class="fapp__kpi" data-film-field><small>Повтор</small><b>Каждую неделю</b></p>
                  <span class="sc-film__save">Сохранить {ic('check', 'ic ic--12')}</span>
                </div>
              </div>
              <p class="sc-film__notice" aria-hidden="true">{ic('bell')}<span><b>Урок через час</b>Марина видит время и ссылку в своем кабинете</span></p>
            </div>
          </div>
          <ul class="film__bens" aria-label="Что меняется с TeacherDesk">{stickers}</ul>
          <figcaption class="film__sub">{subs}</figcaption>
        </figure>
        <div class="film__ctrl">
          <button class="film__play" type="button" data-film-play aria-label="Пауза">{ic('pause', 'ic ic--fill i-pa')}{ic('play', 'ic ic--fill i-pl')}</button>
          <div class="film__chapters" role="group" aria-label="Части ролика">
            <button type="button" data-ch="0"><span>Было<span class="film__lx">: три чата</span></span><i class="film__track"><i class="film__fill"></i></i></button>
            <button type="button" data-ch="1"><span>Стало<span class="film__lx">: один календарь</span></span><i class="film__track"><i class="film__fill"></i></i></button>
          </div>
        </div>
      </div></section>'''


def situations(c, texts=None, icons=None, lead=None):
    texts = texts or ['Нужно найти новое окно, перенести встречу и сообщить ученику.', 'Два занятия в неделю на весь год. А один четверг придется сдвинуть.', 'Вместо начала урока - сообщение «а мы сегодня занимаемся?».', 'Между уроками есть свободное время. Осталось быстро его найти.']
    icons = icons or ['calendar','refresh','bell','clock']
    lead = 'Планы меняются. Хорошо, когда расписание успевает за ними.' if lead is None else lead
    cards = ''.join(f'<li class="sc-situation" data-reveal="piece"><span class="sc-situation__top">{ic(icons[i])}<small>{typo(s["when"])}</small></span><h3 class="pfc__t">{typo(s["title"])}</h3><p class="pfc__d">{typo(texts[i])}</p></li>' for i,s in enumerate(c['scenarios']['items']))
    return f'<section class="sec sc-situations" aria-labelledby="h-schedule-situations"><div class="wrap">{heading(c["scenarios"]["kicker"],c["scenarios"]["h2"],lead,"h-schedule-situations","sq")}<ul class="sc-situations__grid">{cards}</ul></div></section>'


def capabilities(c):
    week = ''.join('<i></i>' for _ in range(15))
    month = ''.join('<i></i>' for _ in range(35))
    visuals = [
        f'<div class="sc-mini-week"><p><span>Неделя</span><span>Месяц</span></p><div class="sc-mini-week__body"><div class="sc-mini-week__week">{week}</div><div class="sc-mini-week__month">{month}</div></div></div>',
        '<div class="sc-mini-form"><span><i>Ученик</i><b>Марина К.</b></span><span><i>Повтор</i><b>Каждую неделю</b></span><p>Сохранить <b>✓</b></p></div>',
        '<div class="sc-mini-repeat"><span>Каждую неделю</span><div><i>ПН</i><i>ВТ</i><i>СР</i><i>ЧТ</i><i>ПТ</i></div><b>Один раз - на все недели</b></div>',
        '<div class="sc-mini-move"><span>СР · 15:30</span><span>ПТ · 15:30</span><b>Физика · Артем</b><i>Ученик видит перенос ✓</i></div>',
        f'<div class="sc-mini-reminder"><span>14:30</span><div>{ic("bell")}<p><b>Урок через час</b><small>Алгебра · 15:30</small></p></div></div>',
        f'<div class="sc-mini-link"><small>Алгебра · Марина</small><span>{ic("link")}Ссылка в карточке урока</span><b>{ic("video")}Войти в урок</b></div>',
        f'<div class="sc-mini-phone phone-frame"><span class="sc-mini-phone__notch"></span><small>Сегодня</small><b>4 урока</b><i>09:00 · Алгебра</i><i>11:00 · Английский</i><i>15:30 · Физика</i><span class="sc-mini-phone__nav">{ic("home")}{ic("calendar")}{ic("clock")}</span></div>',
    ]
    titles = ['Календарь занятий','Создание урока','Повторяющиеся уроки','Перенос занятий','Напоминания ученикам','Ссылка на урок','Расписание на телефоне']
    descs = ['Неделя и месяц, свободные окна','Ученик, дата, время и повтор','Занятия на все следующие недели','Новое время в кабинете ученика','Почта и push за час до занятия','Вход в занятие из кабинета ученика','Уроки и переносы в мобильном браузере']
    tiles = ''.join(f'<li><div class="pfc sc-cap sc-cap--{i}" data-live><div class="sc-cap__visual" aria-hidden="true">{visuals[i]}</div><div class="sc-cap__copy"><h3 class="pfc__t">{typo(titles[i])}</h3><p class="pfc__d">{typo(descs[i])}</p></div></div></li>' for i in range(7))
    head = heading('Что умеет', 'Календарь репетитора на неделю и месяц', 'Повторы, переносы и напоминания в одном расписании.', 'h-schedule-capabilities', 'sq')
    return f'<section class="sec sec--tint sc-capabilities" aria-labelledby="h-schedule-capabilities"><div class="wrap">{head}<ul class="pfcs pfcs--4">{tiles}</ul></div></section>'


def objections(c):
    cards = ''.join(f'<li class="sc-objection" data-reveal="piece"><div class="sc-objection__question"><p>{ic("chat")}Сомнение <span>0{i+1}</span></p><h3 class="pfc__t">{typo(q)}</h3></div><div class="sc-objection__answer"><p>{ic("check")}На практике</p><div class="pfc__d">{typo(a)}</div></div></li>' for i,(q,a) in enumerate(c['objections']))
    head = heading('Сомнения', 'Сомнения, которые есть у каждого репетитора', '', 'h-schedule-objections', 'q')
    return f'<section class="sec sc-objections" aria-labelledby="h-schedule-objections"><div class="wrap">{head}<ul class="sc-objections__grid">{cards}</ul></div></section>'
