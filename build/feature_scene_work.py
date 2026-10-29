# -*- coding: utf-8 -*-
"""Предметные рабочие экраны для трех этапов роликов возможностей."""
from blocks import ic, typo


def _chip(text, kind='paid', icon=''):
    return f'<span class="chip chip--{kind}">{ic(icon, "ic ic--12") if icon else ""}{typo(text)}</span>'


def payments(stage):
    paid = stage == 2
    rows = [
        ('АД', 'Артем Дроздов', 'Физика · 2 проведенных урока', 'Баланс 0' if paid else '2 600 руб.', 'paid' if paid else 'debt'),
        ('СВ', 'Соня Ветрова', 'Математика · 7 дней к оплате', '4 200 руб.', 'debt'),
        ('МК', 'Марина Кузнецова', 'Алгебра · оплата учтена', 'Баланс 0', 'paid'),
    ]
    lis = ''.join(f'<li class="{"fx-work-pay__changed" if i == 0 else ""}"><span class="av">{av}</span><span class="pay__who"><b>{name}</b><span>{typo(meta)}</span></span>{_chip(value, kind)}</li>' for i, (av, name, meta, value, kind) in enumerate(rows))
    notice = [
        ('wallet', 'Балансы после уроков', '2 урока Артема по 1 300 руб. уже в учете'),
        ('bell', 'Артему отправлено напоминание', 'К оплате 2 600 руб. за два урока'),
        ('check', 'Оплата 2 600 руб. отмечена', 'Долг Артема закрыт, общий баланс обновлен'),
    ][stage]
    return f'''<div class="pay fx-work-pay" data-stage="{stage}">
      <div class="fx-work-pay__head"><span>{ic('wallet')}Финансы</span><span class="chip chip--soon">Сентябрь</span></div>
      <div class="pay__kpi"><p><small>Получено за месяц</small><b>{'41&nbsp;000' if paid else '38&nbsp;400'} <i>руб.</i></b></p><p><small>К оплате</small><b>{'4&nbsp;200' if paid else '6&nbsp;800'} <i>руб.</i></b></p></div>
      <ul class="pay__rows">{lis}</ul>
      <div class="fx-work-pay__notice">{ic(notice[0])}<span><b>{typo(notice[1])}</b><small>{typo(notice[2])}</small></span></div>
    </div>'''


def assistant(stage):
    plan = [('Разминка: устные задачи', '10 мин'), ('Дискриминант на примерах', '15 мин'), ('Практика: 5 уравнений', '25 мин'), ('Разбор ошибок и задание', '10 мин')]
    lines = ''.join(f'<li class="fai__l" style="--n:{i}"><span>0{i + 1}</span><span>{typo(title)}</span><time>{typo(duration)}</time></li>' for i, (title, duration) in enumerate(plan))
    if stage == 0:
        lines = ''.join(f'<li class="fai__l fx-work-ai__placeholder" style="--n:{i}"><span>0{i + 1}</span><i></i><i></i></li>' for i in range(4))
    status = ['Собирает черновик', 'Предпросмотр', 'Подтверждено'][stage]
    return f'''<div class="fx-work-ai" data-stage="{stage}">
      <div class="fai__me"><p>Подготовь план урока по квадратным уравнениям</p><span>Алгебра · 8 класс · 60 минут</span></div>
      <div class="fai__bot"><p class="fai__who">{ic('ai', 'ic ic--16')}ИИ-ассистент<span class="fai__tag">{status}</span></p>
        <ol>{lines}</ol>
        <div class="fai__act"><span class="fai__btn">{ic('check', 'ic ic--12') if stage == 2 else ''}{['Готовим план', 'Подтвердить и сохранить', 'Сохранено в урок'][stage]}</span><span class="fai__ghost">{['Можно уточнить запрос', 'Внести правки', 'Открыть занятие'][stage]}</span></div>
      </div>
      <p class="fx-work-ai__confirm">{ic('lock', 'ic ic--16')}<span>{'План проверен репетитором и сохранен' if stage == 2 else 'Сохранение только после вашего подтверждения'}</span></p>
    </div>'''


def report(stage):
    bars = [('Квадратные уравнения', .9), ('Теорема Виета', .75), ('Текстовые задачи', .5)]
    graph = ''.join(f'<li style="--n:{i}"><span>{typo(name)}</span><span class="pd-bar"><i style="--v:{value}"></i></span><b>{int(value * 100)}%</b></li>' for i, (name, value) in enumerate(bars))
    return f'''<div class="rep fx-work-report" data-stage="{stage}">
      <p class="rep__t"><b>Отчет за сентябрь</b>{_chip('Для родителя', 'soon')}</p>
      <p class="fx-work-report__student"><span class="av">МК</span><span><b>Марина Кузнецова</b><small>Алгебра · Анна Ковалева</small></span></p>
      <dl class="rep__kpi"><div><dt>Уроков</dt><dd>8</dd></div><div><dt>Пропусков</dt><dd>0</dd></div><div><dt>Задания</dt><dd>9/10</dd></div></dl>
      <ul class="pd-rep__bars fx-work-report__graph">{graph}</ul>
      <blockquote class="fx-work-report__comment"><span>{ic('note', 'ic ic--12')}Комментарий Анны</span><p>{typo('Уверенно решает уравнения. Дальше повторим текстовые задачи.')}</p></blockquote>
      <p class="fx-work-report__share">{ic('link', 'ic ic--16')}<span><b>{['Итоги собраны из занятий', 'Отчет готов к отправке', 'Елена открыла отчет'][stage]}</b><small>{['Посещаемость, задания и результаты', 'Проверили цифры и добавили комментарий', 'По одной ссылке с телефона'][stage]}</small></span>{ic('check', 'ic ic--16') if stage == 2 else ''}</p>
    </div>'''


def journal(stage):
    rows = [
        ('30.09', 'Марина К.', 'Квадратные уравнения', 'Вариант 2', 'была', 'paid'),
        ('28.09', 'Артем Д.', 'Законы Ньютона', 'Задачи 4-6', 'пропуск', 'debt'),
        ('25.09', 'Илья П.', 'Present Perfect', 'Упр. 4-6', 'перенос', 'soon'),
    ]
    lis = ''.join(f'''<li class="{'fx-work-journal__selected' if (stage == 0 and i == 0) or (stage == 1 and i == 1) else ''}" style="--n:{i}"><time>{date}</time><b>{pupil}</b><span class="fx-work-journal__topic" data-label="Тема">{typo(topic)}</span><span class="pd-jr__hw" data-label="Задано">{typo(hw)}</span>{_chip(status, kind)}</li>''' for i, (date, pupil, topic, hw, status, kind) in enumerate(rows))
    return f'''<div class="log fx-work-journal" data-stage="{stage}">
      <div class="fx-work-journal__head"><span>{ic('calendar', 'ic ic--16')}Сентябрь</span><span class="chip chip--soon">Все ученики</span></div>
      <p class="pd-jr__head"><span>Дата</span><span>Ученик</span><span>Тема</span><span>Задано</span><span>Статус</span></p>
      <ul class="pd-jr__rows">{lis}</ul>
      <div class="fx-work-journal__detail">{ic(['pen', 'users', 'report'][stage], 'ic ic--16')}<span><b>{['Тема и задание записаны', 'Посещаемость видна по датам', 'Итог за сентябрь'][stage]}</b><small>{['30 сентября · Марина К. · из расписания', 'Занятие, пропуск и перенос различаются', 'Данные для оплат и отчетов рядом'][stage]}</small></span></div>
      <p class="log__sum"><span>За сентябрь</span><b>31 урок · 2 пропуска</b></p>
    </div>'''


def render(feature_id, stage, step):
    renderer = {'uchet-oplat': payments, 'ii-assistent': assistant, 'otchety-roditelyam': report, 'zhurnal-zanyatiy': journal}.get(feature_id)
    return renderer(stage) if renderer else ''
