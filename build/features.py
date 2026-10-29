# -*- coding: utf-8 -*-
"""Единый шаблон функций: ролик главной, компактные ситуации и общие карточки .pfc."""
from html import escape
from blocks import ic, typo, plain
from feature_content import FEATURES
import schedule


def visual(kind, lines):
    title, *items = lines
    title = typo(escape(title))
    items = [typo(escape(it)) for it in items]
    if kind == 'metric':
        body = f'<small>{title}</small><b class="fx-mini__value">{items[0]}</b><span>{items[1]}</span>'
    elif kind == 'bars':
        body = f'<span>{title}<b>{items[0]}</b></span><i class="fx-mini__bar" style="--v:.9"></i><span>{items[1]}<b>{items[2]}</b></span><i class="fx-mini__bar" style="--v:.5"></i>'
    elif kind == 'board':
        body = f'<small>{title}</small><b class="fx-mini__equation">x² - 5x + 6 = 0</b><svg viewBox="0 0 180 46" aria-hidden="true"><path d="M10 35 Q40 8 70 30 T145 10 M85 7 L85 40 M15 36 H165"/></svg><span>{items[0]}</span>'
    elif kind == 'notice':
        body = f'<span class="fx-mini__icon">{ic("bell")}</span><b>{title}</b><small>{items[0]}</small>'
    elif kind == 'link':
        body = f'<small>{title}</small><span class="fx-mini__link">{ic("link")}Ссылка в кабинете</span><b class="fx-mini__action">{items[0]}</b>'
    elif kind == 'phone':
        body = f'<i class="fx-mini__notch"></i><small>{title}</small><b>{items[0]}</b><span class="fx-mini__row">{items[1]}</span><span class="fx-mini__action">{ic("check", "ic ic--12")}В кабинете</span>'
    elif kind == 'cards':
        body = f'<small>{title}</small><b class="fx-mini__card">{items[0]}</b><span class="fx-mini__action">{items[1]}</span>'
    elif kind == 'form':
        body = f'<small>{title}</small><span class="fx-mini__row">{items[0]}</span><span class="fx-mini__row">{items[1]}</span><b class="fx-mini__action">{ic("check", "ic ic--12")}Сохранено</b>'
    else:
        mark = ic('check', 'ic ic--12') if kind == 'checklist' else ic('doc', 'ic ic--12')
        rows = ''.join(f'<span class="fx-mini__row">{mark}<span>{it}</span></span>' for it in items)
        body = f'<small>{title}</small>{rows}'
    return f'<div class="fx-mini fx-mini--{kind}{" phone-frame" if kind == "phone" else ""}">{body}</div>'


def capabilities(p, c):
    data = FEATURES[p['id']]
    cards = ''.join(f'''<li><div class="pfc sc-cap sc-cap--{i}" data-live>
      <div class="sc-cap__visual" aria-hidden="true">{visual(card['kind'], card['lines'])}</div>
      <div class="sc-cap__copy"><h3 class="pfc__t">{typo(card['title'])}</h3><p class="pfc__d">{typo(card['desc'])}</p></div>
    </div></li>''' for i, card in enumerate(data['caps']))
    head = schedule.heading('Что умеет', data['cap_h2'], data['cap_lead'], 'h-feature-capabilities', 'sq')
    return f'<section class="sec sec--tint sc-capabilities" aria-labelledby="h-feature-capabilities"><div class="wrap">{head}<ul class="pfcs pfcs--4">{cards}</ul></div></section>'


def app(p, steps):
    if p['id'] == 'onlayn-doska':
        from feature_scene_board import render
        scene = lambda i, st: render(i, st)
    elif p['id'] in ('uchet-uchenikov', 'kabinet-uchenika', 'domashnie-zadaniya'):
        from feature_scene_people import render
        scene = lambda i, st: render(p['id'], i, st)
    else:
        from feature_scene_work import render
        scene = lambda i, st: render(p['id'], i, st)
    panels = []
    for i, st in enumerate(steps):
        panels.append(f'''<div class="fx-step{' is-on' if i == 2 else ''}" data-feature-step="{[6000,11400,16500][i]}">
          <p class="fapp__h">{typo(st['title'])}<span>0{i+1} / 03</span></p>
          {scene(i, st)}<p class="fx-app__note">{ic('check')}<span>{typo(st['note'])}</span></p>
        </div>''')
    label = escape(plain('. '.join(st['title'] + '. ' + st['note'] for st in steps)))
    return f'''<div class="win"><div class="win__bar"><span class="win__crumb"><img src="/assets/img/sign.svg" width="18" height="18" alt="">TeacherDesk / <b>{typo(p['nav'])}</b></span></div>
      <div class="fx-app fx-app--{p['id']}" role="img" aria-label="{label}"><div class="fx-app__steps" aria-hidden="true">{''.join(panels)}</div></div></div>'''


def story(p, c):
    data = FEATURES[p['id']]
    positions = [('4%', '10%'), ('38%', '8%'), ('72%', '12%'), ('7%', '52%'), ('39%', '55%'), ('71%', '53%')]
    messages = c.get('pains', {}).get('msgs', [])
    first = messages[0] if messages else {'who': 'Ученик', 'text': data['before']}
    tools = [('chat', first['who'], first['text'], 'Сообщение в переписке')]
    for i, (title, old, new) in enumerate(c['vs']['rows']):
        tools.append((['note', 'chat', 'doc', 'calendar', 'sheet'][i % 5], title, old, 'Все вручную'))
    assert len(tools) == 6
    windows = ''.join(f'''<div class="ftool" style="--x:{positions[i][0]};--y:{positions[i][1]};--r:0deg">
      <span class="ftool__bar">{ic(icon)}<span class="ftool__name">{typo(title)}</span></span>
      <span class="ftool__body"><span class="ft-bub">{typo(text)}</span></span><span class="ftool__ping">{typo(ping)}</span></div>''' for i, (icon, title, text, ping) in enumerate(tools))
    ben_positions = [('3%', '12%'), ('77%', '14%'), ('4%', '40%'), ('76%', '42%'), ('3%', '68%'), ('77%', '70%')]
    ben_icons = [{'metric': p['icon'], 'list': 'users', 'form': 'plus', 'checklist': 'task', 'bars': 'report', 'document': 'doc', 'notice': 'lock' if p['id'] == 'ii-assistent' else 'bell', 'link': 'link', 'phone': 'phone', 'cards': 'cards', 'board': 'board'}[card['kind']] for card in data['caps'][:6]]
    bens = ''.join(f'''<li class="fben" style="--x:{ben_positions[i][0]};--y:{ben_positions[i][1]};--r:0deg"><span class="fben__ic" aria-hidden="true">{ic(ben_icons[i])}</span><span><b>{typo(card['title'])}</b><small>{typo(card['desc'])}</small></span></li>''' for i, card in enumerate(data['caps'][:6]))
    steps = data['steps']
    subtitles = [(0, data['before']), (6000, steps[0]['title'] + '. ' + steps[0]['note']), (11400, steps[1]['title'] + '. ' + steps[1]['note']), (16500, steps[2]['title'] + '. ' + steps[2]['note']), (20000, 'TeacherDesk: ' + data['cap_lead'][0].lower() + data['cap_lead'][1:])]
    subs = ''.join(f'<span data-film-at="{at}">{typo(text)}</span>' for at, text in subtitles)
    head = schedule.heading('Было и стало', data['headline'], data['lead'], 'h-feature-story', 'sq')
    before, after = data['labels']
    return f'''<section class="sec sc-story-section" aria-labelledby="h-feature-story"><div class="wrap">{head}</div>
      <div class="film sc-film fx-film" data-film="feature" data-scene="2">
        <figure class="film__stage"><div class="film__tools" aria-hidden="true">{windows}</div>
          <p class="film__hud" aria-hidden="true">Без TeacherDesk</p>
          <div class="film__app">{app(p, steps)}</div>
          <ul class="film__bens" aria-label="Что меняется с TeacherDesk">{bens}</ul>
          <figcaption class="film__sub">{subs}</figcaption>
        </figure>
        <div class="film__ctrl"><button class="film__play" type="button" data-film-play aria-label="Пауза">{ic('pause', 'ic ic--fill i-pa')}{ic('play', 'ic ic--fill i-pl')}</button>
          <div class="film__chapters" role="group" aria-label="Части ролика">
            <button type="button" data-ch="0"><span>Было<span class="film__lx">: {typo(before)}</span></span><i class="film__track"><i class="film__fill"></i></i></button>
            <button type="button" data-ch="1"><span>Стало<span class="film__lx">: {typo(after)}</span></span><i class="film__track"><i class="film__fill"></i></i></button>
          </div>
        </div>
      </div></section>'''


def body(p, c):
    data = FEATURES[p['id']]
    return [story(p, c), schedule.situations(c, texts=data['situations'], icons=[p['icon'], 'clock', 'chat', 'calendar'], lead=c['scenarios'].get('lead', '')), capabilities(p, c), schedule.objections(c)]
