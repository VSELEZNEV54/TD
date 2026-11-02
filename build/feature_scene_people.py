# -*- coding: utf-8 -*-
"""Предметные кадры учета учеников, личного кабинета и проверки заданий."""
from blocks import ic, typo


def _progress():
    return '''<ul class="pd-rep__bars fx-people-progress">
      <li><span>Уравнения</span><span class="pd-bar"><i style="--v:.9"></i></span><b>90%</b></li>
      <li><span>Текстовые задачи</span><span class="pd-bar"><i style="--v:.5"></i></span><b>50%</b></li>
    </ul>'''


def _tabs(items, selected):
    return '<p class="pd-scard__tabs fx-people-tabs">' + ''.join(
        f'<span class="{"is-on" if i == selected else ""}">{text}</span>'
        for i, text in enumerate(items)) + '</p>'


def _student(stage):
    pupils = [('МК', 'Марина К.', 'Алгебра · 9 класс'), ('АД', 'Артем Д.', 'Физика · 8 класс'), ('СВ', 'Соня В.', 'Подготовка к ОГЭ')]
    people = ''.join(f'<li class="{"is-on" if i == 0 else ""}"><span class="av">{initials}</span><span><b>{name}</b><small>{meta}</small></span></li>'
                     for i, (initials, name, meta) in enumerate(pupils))
    if stage == 0:
        panel = f'''<dl class="pd-scard__info fx-people-info">
          <div><dt>Родитель</dt><dd>Елена Кузнецова</dd></div><div><dt>Цель занятий</dt><dd>Подготовка к ОГЭ</dd></div>
        </dl><p class="pd-cab__deck">{ic('users')}<span><b>Контакты семьи</b><small>+7 9•• •••-••-12 · Елена, мама</small></span></p>
        <p class="pd-scard__note fx-people-note">{ic('note')}<span>Пробник раз в месяц. Начали в сентябре.</span></p>'''
    elif stage == 1:
        panel = '''<ul class="pd-scard__hist fx-people-history">
          <li><time>30.09</time><span>Квадратные уравнения</span><span class="chip chip--paid">8 из 10</span></li>
          <li><time>25.09</time><span>Теорема Виета</span><span class="chip chip--done">сдано</span></li>
          <li><time>23.09</time><span>Неравенства</span><span class="chip chip--wait">не сдано</span></li>
        </ul>''' + _progress()
    else:
        panel = f'''<p class="pd-scard__note fx-people-note fx-people-enter">{ic('note')}<span>Путает знак перед 5x. Повторить текстовые задачи перед пробником.</span></p>
          {_progress()}<p class="pd-cab__deck">{ic('check')}<span><b>Последняя работа проверена</b><small>Вариант 2 · 8 из 10 задач</small></span></p>'''
    return f'''<div class="fx-people-register">
      <aside class="fx-people-list"><p class="fhw__m">Ученики · 12</p><ul>{people}</ul></aside>
      <div class="scard fx-people-record">
        <div class="scard__head"><span class="av av--lg">МК</span><span class="scard__who"><b>Марина Кузнецова</b><span>Алгебра · 9 класс</span></span></div>
        {_tabs(['Профиль', 'Задания', 'Заметки'], stage)}
        <div class="fx-people-record__body">{panel}</div>
      </div></div>'''


def _cabinet(stage):
    status = ['Сдать работу', 'На проверке', '8 из 10'][stage]
    status_class = ['chip--act', 'chip--wait', 'chip--done'][stage]
    next_lesson = f'''<div class="pd-cab__next fx-people-next">
      <span class="pd-cab__lbl">Следующее занятие</span><b>Чт, 1 октября · 15:30</b><span>Алгебра с Анной К.</span>
      <span class="pd-cab__go">{ic('video', 'ic ic--12')}Войти в урок</span></div>'''
    assignment = f'''<ul class="pd-cab__hw fx-people-work">
      <li><span>{ic('task')}<span><b>Квадратные уравнения</b><small>Вариант 2 · до 2 октября</small></span></span><span class="chip {status_class}">{status}</span></li>
      <li><span>{ic('task')}<span><b>Теорема Виета</b><small>Работа от 25 сентября</small></span></span><span class="chip chip--paid">проверено</span></li></ul>'''
    if stage == 0:
        detail = f'''<p class="pd-cab__deck">{ic('doc')}<span><b>Материалы к занятию</b><small>Конспект и условия задач</small></span></p>'''
    elif stage == 1:
        detail = f'''<p class="pd-cab__deck fx-people-enter">{ic('check')}<span><b>Решение отправлено</b><small>Решение.pdf · ожидает проверки Анны</small></span></p>'''
    else:
        detail = f'''<div class="pd-cab__deck fx-people-enter">{ic('cards')}<span><b>Мои ошибки · 2 карточки</b><small>Задачи 6 и 9 · пора повторить</small></span></div>'''
    return f'''<div class="fx-people-cabinet">
      <div class="fx-people-greeting"><span class="pd-cab__hi">Привет, Марина</span><span class="av av--lg">МК</span></div>
      {next_lesson}{assignment}{detail}
      <p class="fhw__m fx-people-caption">Мой прогресс по алгебре</p>{_progress()}
    </div>'''


def _homework(stage):
    if stage == 0:
        body = f'''<div class="fx-people-assignment">
          <p class="pd-cab__lbl">Задание для Марины</p><p class="fhw__t">Квадратные уравнения</p><p class="fhw__m">Вариант 2 · 10 задач</p>
          <div class="fx-people-paper"><span class="fx-people-question">1. Решите уравнение</span><b>x² − 5x + 6 = 0</b><span class="fx-people-paper__line"></span><span class="fx-people-paper__line"></span></div>
          <p class="pd-cab__deck">{ic('doc')}<span><b>Условия и конспект</b><small>Материалы прикреплены</small></span></p>
          <div class="fx-people-assignment__foot"><span class="chip chip--wait">Срок: 2 октября</span><span class="fai__btn fx-people-enter">{ic('check', 'ic ic--12')}Выдано в кабинет</span></div>
        </div>'''
    elif stage == 1:
        rows = [('МК', 'Марина Кузнецова', 'Решение.pdf · только что', 'chip--done', 'сдано'),
                ('АД', 'Артем Дроздов', 'Срок: 2 октября', 'chip--wait', 'не сдано'),
                ('СВ', 'Соня Ветрова', 'Проверка завершена', 'chip--paid', '9 из 10')]
        lis = ''.join(f'<li><span class="av">{initials}</span><span class="fx-people-person"><b>{name}</b><small>{meta}</small></span><span class="chip {cl}">{status}</span></li>' for initials, name, meta, cl, status in rows)
        body = f'''<div class="fx-people-submissions"><p class="fhw__t">Кто сдал работу</p><p class="fhw__m">Квадратные уравнения · вариант 2</p><ul>{lis}</ul>
          <p class="pd-cab__deck fx-people-enter">{ic('doc')}<span><b>Марина: решение.pdf</b><small>Открыто для проверки</small></span></p></div>'''
    else:
        cells = ''.join(f'<li class="{"is-err" if i in (6, 9) else ""}" style="--n:{i - 1}">{i}</li>' for i in range(1, 11))
        body = f'''<div class="fhw fx-people-review"><p class="fhw__t">Квадратные уравнения</p><p class="fhw__m">Марина К. · вариант 2</p><ol class="fhw__cells">{cells}</ol>
          <p class="fhw__f"><span><b>8</b> из 10 верно</span><span class="chip chip--done">{ic('check', 'ic ic--12')}проверено</span></p>
          <p class="pd-scard__note fx-people-note fx-people-enter">{ic('pen')}<span>Задача 6: проверь знак перед 5x.</span></p>
          <p class="pd-cab__deck">{ic('cards')}<span><b>2 ошибки в колоде</b><small>Повторить задачи 6 и 9</small></span></p></div>'''
    return '<div class="fx-people-homework">' + body + '</div>'


def render(feature_id, stage, step):
    """Кадр без обертки плеера; подпись шага выводит общий шаблон."""
    renderer = {'uchet-uchenikov': _student, 'kabinet-uchenika': _cabinet, 'domashnie-zadaniya': _homework}.get(feature_id)
    return typo(renderer(stage)) if renderer else ''
