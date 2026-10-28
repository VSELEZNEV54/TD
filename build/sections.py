# -*- coding: utf-8 -*-
"""Блоки внутренних страниц из дизайн-системы (docs/dizajn-sistema.md, раздел 6).
Каждый блок отличается от соседей фоном, раскладкой или типом контента."""
import re
from html import escape
from blocks import (REG, ic, typo, plain, kicker, sec_head, section, ok, btn)
import demos

COLORS = ['blue', 'yellow', 'ink']


# ---------- «Знакомо?»: лента сообщений от учеников и родителей ----------
def pains(d):
    msgs = []
    for i, m in enumerate(d['msgs']):
        av = ''.join(w[0] for w in m['who'].replace('Мама', 'М').replace('Папа', 'П').split()[:2]).upper()[:2]
        msgs.append(f'''<li class="msg msg--{i % 3}" data-feed-msg>
            <span class="av" aria-hidden="true">{escape(av)}</span>
            <span class="msg__b"><b>{typo(m["who"])}</b><span>{typo(m["text"])}</span><time>{m.get("time", "")}</time></span>
          </li>''')
    count = d.get('count', ['сообщений', 'за вечер'])
    fix = f'<p class="pains2__fix" data-feed-fix>{ic("check")}<span>{typo(d["fix"])}</span></p>' if d.get('fix') else ''
    return f'''<section class="sec sec--pains" aria-labelledby="h-pains">
  <div class="wrap">
    <div class="pains2" data-feed data-feed-total="{d.get("total", len(d["msgs"]))}">
      <div class="pains2__glow" aria-hidden="true"></div>
      <div class="pains2__txt">
        {kicker(d.get("kicker", "Знакомая ситуация"), "q")}
        <h2 class="h2 h2--sm" id="h-pains" data-reveal>{typo(d["h2"])}</h2>
        <p class="pains2__lead" data-reveal>{typo(d["lead"])}</p>
        <p class="pains2__count" aria-hidden="true"><b data-feed-n>{d.get("total", len(d["msgs"]))}</b><span>{typo(count[0])}<br>{typo(count[1])}</span></p>
        {fix}
      </div>
      <div class="chat" role="group" aria-label="Сообщения, которые приходят репетитору">
        <p class="chat__h"><span class="chat__dot" aria-hidden="true"></span>{typo(d.get("chat", "Мессенджер · сегодня"))}</p>
        <ul class="chat__list">{"".join(msgs)}</ul>
        <p class="chat__typing" aria-hidden="true"><i></i><i></i><i></i></p>
      </div>
    </div>
  </div>
</section>'''


# ---------- мини-ролик функции ----------
def film(f):
    """f: словарь из films.py: title, h2, lead, chapters=[{t, cap, dur, scene}]"""
    scenes, caps = [], []
    for i, ch in enumerate(f['chapters']):
        scenes.append(f'<div class="msc{" is-on" if i == 0 else ""}" data-scene="{i}" data-dur="{ch.get("dur", 5200)}">{typo(ch["scene"])}</div>')
        caps.append(f'''<li><button class="mch{" is-on" if i == 0 else ""}" type="button" data-ch="{i}" aria-label="Глава {i + 1}: {escape(plain(ch["t"]))}">
          <span class="mch__n">{i + 1:02d}</span><span class="mch__t"><b>{typo(ch["t"])}</b><small>{typo(ch["cap"])}</small></span>
          <i class="mch__track" aria-hidden="true"><i class="mch__fill"></i></i></button></li>''')
    head = sec_head(f.get('kicker', 'Как это работает'), f['h2'], f.get('lead', ''), 'h-film', 'sq')
    return f'''<section class="sec sec--film" aria-labelledby="h-film">
  <div class="wrap">
    {head}
    <div class="mfilm" data-mfilm>
      <figure class="mfilm__stage" aria-hidden="true">
        <span class="mfilm__glow"></span>
        <div class="mfilm__win">
          <p class="mfilm__bar"><span class="frame__dots"><i></i><i></i><i></i></span><span>{typo(f["title"])}</span><button class="mfilm__play" type="button" data-mf-play tabindex="-1">{ic("pause", "ic ic--fill i-pa")}{ic("play", "ic ic--fill i-pl")}</button></p>
          <div class="mfilm__scenes">{"".join(scenes)}</div>
        </div>
      </figure>
      <ol class="mfilm__chs">{"".join(caps)}</ol>
    </div>
  </div>
</section>'''


# ---------- до и после: переключатель ----------
def flip(d):
    old = ''.join(f'''<li class="fl-old" style="--r:{[-2, 1.5, -1, 2, -1.5, 1][i % 6]}deg"><b>{typo(k)}</b><span>{typo(o)}</span></li>''' for i, (k, o, n) in enumerate(d['rows']))
    new = ''.join(f'''<li class="fl-new"><span class="fl-new__ic">{ic("check")}</span><span><b>{typo(k)}</b><span>{typo(n)}</span></span></li>''' for k, o, n in d['rows'])
    olabel = d.get('old', 'Без TeacherDesk')
    return f'''<section class="sec sec--tint sec--flip" aria-labelledby="h-flip">
  <div class="wrap">
    {sec_head(d.get("kicker", "До и после"), d["h2"], d.get("lead", ""), "h-flip", "q")}
    <div class="flip" data-flip data-side="1">
      <div class="flip__sw" role="tablist" aria-label="Сравнение">
        <button class="flip__b" type="button" role="tab" aria-selected="false" aria-controls="flip-0" id="flip-b0" data-side="0">{typo(olabel)}</button>
        <button class="flip__b" type="button" role="tab" aria-selected="true" aria-controls="flip-1" id="flip-b1" data-side="1">С TeacherDesk</button>
        <i class="flip__knob" aria-hidden="true"></i>
      </div>
      <div class="flip__panes">
        <div class="flip__p flip__p--old" role="tabpanel" id="flip-0" aria-labelledby="flip-b0"><p class="flip__cap">{ic("x")}{typo(d.get("old_cap", "Так это выглядит сейчас"))}</p><ul class="fl-olds">{old}</ul></div>
        <div class="flip__p flip__p--new" role="tabpanel" id="flip-1" aria-labelledby="flip-b1"><p class="flip__cap">{ic("check")}{typo(d.get("new_cap", "Так это работает в TeacherDesk"))}</p><ul class="fl-news">{new}</ul></div>
      </div>
    </div>
  </div>
</section>'''


# ---------- лента дня: ситуации по часам ----------
def timeline(d):
    lis = ''.join(f'''<li class="tln" data-reveal="piece" style="--i:{i}">
        <span class="tln__dot" aria-hidden="true"></span>
        <p class="tln__when">{typo(s.get("when", ""))}</p>
        <div class="tln__card"><span class="tln__n" aria-hidden="true">{i + 1}</span><h3 class="tln__t">{typo(s["title"])}</h3><p>{typo(s["text"])}</p></div>
      </li>''' for i, s in enumerate(d['items']))
    return section(sec_head(d.get('kicker', 'Из жизни репетитора'), d['h2'], d.get('lead', ''), 'h-tln', 'sq') +
                   f'<ol class="tline2">{lis}</ol>', 'sec--tln', 'h-tln')


# ---------- бенто возможностей ----------
ICONS = ['calendar', 'wallet', 'users', 'task', 'bell', 'board', 'ai', 'report', 'note', 'lock', 'phone', 'cards']


def bento(d, icon_seed=0):
    text = ''.join(f'<p>{typo(p)}</p>' for p in d.get('text', []))
    tiles = []
    for i, x in enumerate(d['items']):
        icon = d.get('icons', [])[i] if i < len(d.get('icons', [])) else ICONS[(i + icon_seed) % len(ICONS)]
        tiles.append(f'<li class="bt bt--{i % 6}" data-reveal="piece" style="--i:{i}"><span class="bt__ic bt__ic--{COLORS[i % 3]}">{ic(icon, "ic ic--20")}</span><p>{typo(x)}</p></li>')
    return f'''<section class="sec sec--tint sec--bento" aria-labelledby="h-bento">
  <div class="wrap">
    <div class="bento2">
      <div class="bento2__head" data-reveal>{kicker(d.get("kicker", "Что умеет"), "sq", False)}<h2 class="h2 h2--sm" id="h-bento">{typo(d["h2"])}</h2><div class="bento2__text">{text}</div></div>
      <ul class="bento2__tiles">{"".join(tiles)}</ul>
    </div>
  </div>
</section>'''


# ---------- сомнения ----------
def objections(items, h2='Сомнения, которые есть у&nbsp;каждого <em class="em">репетитора</em>', tint=False):
    cards = ''.join(f'''<li class="obj" data-reveal="piece" style="--i:{i}">
        <p class="obj__q sticker" style="--tilt:{[-1.5, 1.2, -1][i % 3]}deg">«{typo(q)}»</p>
        <div class="obj__a"><span class="obj__k">{ic("check")}Отвечаем</span><p>{typo(a)}</p></div>
      </li>''' for i, (q, a) in enumerate(items))
    return section(sec_head('Сомнения', h2, '', 'h-obj', 'q') + f'<ul class="objs">{cards}</ul>', 'sec--tint' if tint else 'sec--obj', 'h-obj')


# ---------- вкладки функций с живым окном ----------
FEATURE_DEMO = {'raspisanie': 'week', 'uchet-oplat': 'debt', 'uchet-uchenikov': 'card', 'kabinet-uchenika': 'cabinet',
                'domashnie-zadaniya': 'hw', 'onlayn-doska': 'board', 'ii-assistent': 'ai', 'otchety-roditelyam': 'report',
                'zhurnal-zanyatiy': 'journal'}


def tabs(reg, d, visible):
    items = [it if isinstance(it, tuple) else (it, None) for it in d['items']]
    btns, panes = [], []
    for i, (pid, text) in enumerate(items):
        p = reg[pid]
        on = i == 0
        btns.append(f'''<button class="tab2" type="button" role="tab" id="tab-{pid}" aria-controls="pane-{pid}" aria-selected="{"true" if on else "false"}" data-tab="{i}">
          <span class="tab2__ic tab2__ic--{COLORS[i % 3]}">{ic(p["icon"], "ic ic--20")}</span>
          <span class="tab2__t"><b>{typo(p["nav"])}</b><small>{typo(text or p.get("card", ""))}</small></span>
          <i class="tab2__bar" aria-hidden="true"><i></i></i>
        </button>''')
        more = f'<a class="btn btn--ghost btn--sm" href="{p["url"]}"><span>Подробнее<span class="vh">: {typo(p["nav"])}</span></span></a>' if visible(pid) else ''
        panes.append(f'<div class="tabs2__pane{" is-on" if on else ""}" role="tabpanel" id="pane-{pid}" aria-labelledby="tab-{pid}" data-pane="{i}">{demos.get(FEATURE_DEMO[pid])}{more}</div>')
    return section(sec_head(d.get('kicker', 'Что внутри'), d['h2'], d.get('lead', ''), 'h-tabs', 'sq', ('Все возможности', '/features/')) +
                   f'''<div class="tabs2" data-tabs>
      <div class="tabs2__list" role="tablist" aria-label="Функции">{"".join(btns)}</div>
      <div class="tabs2__stage">{"".join(panes)}</div>
    </div>''', 'sec--tabs', 'h-tabs')


# ---------- три шага с мини-экранами ----------
STEP_SHOTS = {
    'form': '<span class="ms3 ms3--form"><span class="ms3__f"><small>Имя</small><b>Анна Ковалева</b></span><span class="ms3__f"><small>Телефон</small><b>+7 9•• •••-45-12</b></span><span class="ms3__btn">Начать бесплатно</span></span>',
    'list': '<span class="ms3 ms3--list"><span class="ms3__r"><i class="av">МК</i><b>Марина Кузнецова</b><em>алгебра</em></span><span class="ms3__r"><i class="av">АД</i><b>Артем Дроздов</b><em>физика</em></span><span class="ms3__r ms3__r--new"><i class="av">СВ</i><b>Соня Ветрова</b><em>приглашена</em></span></span>',
    'lesson': '<span class="ms3 ms3--lesson"><span class="ms3__day">Ср, 30 сентября</span><span class="ms3__ls"><time>15:30</time><b>Алгебра</b><em>Марина К.</em></span><span class="ms3__note"><svg class="ic"><use href="#i-bell"/></svg>Напоминание уйдет за час</span></span>',
    'phone': '<span class="ms3 ms3--home"><span class="ms3__apps"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><b><img src="/assets/img/sign.svg" width="26" height="26" alt=""></b></span><span class="ms3__cap">TeacherDesk на главном экране</span></span>',
    'board': '<span class="ms3 ms3--board"><span class="ms3__eq">x² - 5x + 6 = 0</span><svg viewBox="0 0 120 50"><path d="M4 44h112M30 4v44" stroke="#A3A6BC" stroke-width="1.5" fill="none"/><path d="M14 6c8 36 18 40 30 40s22-4 30-40" stroke="#445BF6" stroke-width="2.5" fill="none" stroke-linecap="round"/></svg><span class="ms3__note"><svg class="ic"><use href="#i-video"/></svg>Урок по ссылке из расписания</span></span>',
    'invite': '<span class="ms3 ms3--invite"><span class="ms3__link"><svg class="ic"><use href="#i-link"/></svg>teacherdesk.ru/i/marina</span><span class="ms3__btn">Скопировать ссылку</span><span class="ms3__note"><svg class="ic"><use href="#i-check"/></svg>Марина в кабинете</span></span>',
}
ORDER = ['form', 'list', 'lesson']


DEFAULT_STEPS = [
    {'title': 'Создайте аккаунт', 'text': 'Нужны имя и телефон. Карта не нужна, 14 дней полного доступа бесплатно.'},
    {'title': 'Добавьте учеников', 'text': 'Вручную или ссылкой-приглашением: ученик зарегистрируется и попадет в свой кабинет.'},
    {'title': 'Поставьте первый урок', 'text': 'TeacherDesk напомнит ученику за час до занятия и посчитает оплату после урока.'},
]


def steps3(d=None):
    d = d or {}
    st = d.get('steps', DEFAULT_STEPS)
    lis = ''.join(f'''<li class="st3" data-reveal="piece" style="--i:{i}" data-step-t="{escape(plain(s["title"]))}">
        <span class="st3__shot" aria-hidden="true">{STEP_SHOTS.get(s.get("shot"), STEP_SHOTS[ORDER[i % 3]])}</span>
        <p class="st3__m"><span class="st3__n" aria-hidden="true">{i + 1}</span><span class="st3__time">{typo((d.get("times") or ["30 секунд", "1 минута", "30 секунд"])[i % 3])}</span></p>
        <h3 class="st3__t">{typo(s["title"])}</h3><p>{typo(s["text"])}</p>
      </li>''' for i, s in enumerate(st))
    times = d.get('times', ["30 секунд", "1 минута", "30 секунд"])
    return section(sec_head(d.get('kicker', 'Быстрый старт'), d.get('h2', 'От регистрации до первого урока <em class="em">две минуты</em>'), '', 'h-st3', 'sq') +
                   f'<ol class="st3s" data-howto>{lis}</ol>', 'sec--st3', 'h-st3')


# ---------- SEO-текст в конце страницы и «Часто ищут» ----------
def seo_text(d, tags=None):
    """tags: [(анкор, адрес)] - облако ссылок на соседние страницы под текстом, всегда раскрыто."""
    if not d:
        return ''
    html = typo(d["html"]).replace('<table', '<div class="seo__tbl"><table').replace('</table>', '</table></div>')
    tg = ''
    if tags:
        lis = ''.join(f'<li><a class="seo__tag" href="{u}">{typo(a)}</a></li>' for a, u in tags)
        tg = f'\n      <nav class="seo__tags" aria-labelledby="h-seo-tags"><p class="seo__tagh" id="h-seo-tags">Часто ищут</p><ul>{lis}</ul></nav>'
    return f'''<section class="seo" aria-labelledby="h-seo">
  <div class="wrap">
    <div class="seo__in" data-seo>
      <h2 class="seo__h" id="h-seo">{typo(d["h2"])}</h2>
      <div class="seo__body" id="seo-body">{html}</div>
      <button class="seo__more" type="button" data-seo-more aria-expanded="false" aria-controls="seo-body"><span>Читать полностью</span>{ic("chev", "ic ic--12")}</button>{tg}
    </div>
  </div>
</section>'''


# ---------- наклейки вокруг живого окна первого экрана ----------
def stickers(items):
    out = []
    for i, (icon, title, text) in enumerate(items[:2]):
        out.append(f'<p class="hst hst--{i}" aria-hidden="true"><span class="hst__ic hst__ic--{COLORS[(i + 1) % 3]}">{ic(icon)}</span><span><b>{typo(title)}</b>{typo(text)}</span></p>')
    return ''.join(out)


def facts(items):
    lis = ''.join(f'<li><b>{typo(n)}</b><span>{typo(t)}</span></li>' for n, t in items)
    return f'<ul class="pfacts" data-reveal>{lis}</ul>'
