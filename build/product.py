# -*- coding: utf-8 -*-
"""Блоки раздела «Продукт» (CRM, программа, приложение и другие посадочные под запрос).

Порядок страницы задает templates.product(). Блоки повторяют главную: первый экран со сценой дня,
«День репетитора» с липким оглавлением, ролик «было - собираем - стало», «О сервисе».
Сцену первого экрана и «О сервисе» берем прямо из site/index.html, чтобы правки главной доходили сюда.
Ролик собирается из контента страницы и играет на коде главной (home.js, [data-film]).
"""
import re
from pathlib import Path

import demos
from blocks import REG, ok, typo, ic, btn, kicker, crumbs, trust_list, sec_head, section

SITE = Path(__file__).resolve().parent.parent / 'site'
_HOME = {}


def _home():
    if 'h' not in _HOME:
        f = SITE / 'index.html'
        _HOME['h'] = f.read_text(encoding='utf-8') if f.exists() else ''
    return _HOME['h']


def _balanced(h, start, tag):
    depth = 0
    rx = re.compile(r'<(/?)' + tag + r'\b', re.I)
    for m in rx.finditer(h, start):
        depth += -1 if m.group(1) else 1
        if depth == 0:
            return h[start:h.index('>', m.end()) + 1]
    return ''


def _abs(html):
    """На главной пути к картинкам относительные, на внутренних страницах нужны от корня."""
    return re.sub(r'(src|href)="assets/', r'\1="/assets/', html)


# ---------- 1. первый экран: текст страницы и сцена дня с главной ----------
GEO = ['geo--sq', 'geo--q geo--y', 'geo--q', 'geo--sq geo--ink']


def hero(p, trail, h, facts):
    h_ = _home()
    a = h_.find('<div class="scene" data-scene>')
    scene = _abs(_balanced(h_, a, 'div')) if a > -1 else ''
    acts = btn('Начать бесплатно', REG, 'primary', 'lg')
    if h.get('more'):
        acts += f'<a class="btn btn--ghost btn--lg hero__more" href="{h["more"][1]}"><span>{typo(h["more"][0])}</span></a>'
    fs = ''.join(f'''<div class="fact"><dt><i class="geo {GEO[i % 4]}" aria-hidden="true"></i><span class="fact__n"{f' data-count="{n}"' if n.isdigit() else ''}>{typo(n)}</span><span class="fact__u">{typo(u)}</span></dt><dd>{typo(d)}</dd></div>'''
                 for i, (n, u, d) in enumerate(facts))
    return f'''<section class="hero hero--page" data-hero>
  <div class="hero__bg" aria-hidden="true"></div>
  <div class="wrap hero__in">
    <div class="hero__text">
      {crumbs(trail)}
      <div class="hero__title">
        <p class="kicker kicker--pill hero__kicker"><i class="geo geo--q" aria-hidden="true"></i>{typo(h["kicker"])}</p>
        <h1 class="hero__phrase"><span class="hero__line">{typo(p["h1"])}</span></h1>
      </div>
      <p class="hero__lead">{typo(h["lead"])}</p>
      <div class="hero__cta">{acts}</div>
      {trust_list()}
    </div>

    {scene}
  </div>

  <div class="wrap">
    <dl class="facts" aria-label="Коротко о&nbsp;главном">{fs}</dl>
  </div>
</section>'''


# ---------- 2. какую задачу решает: как «День репетитора», слева липкий заголовок с оглавлением ----------
def tasks(d, visible_url=ok):
    on = ' class="is-on"'
    nav = ''.join(f'<a{on if i == 0 else ""} href="#{it["id"]}"><i aria-hidden="true"></i>{typo(it["nav"])}</a>' for i, it in enumerate(d['items']))
    cells = []
    for it in d['items']:
        more = ''
        if it.get('link') and visible_url(it['link'][1]):
            more = f'<a class="btn btn--ghost btn--sm" href="{it["link"][1]}"><span>{typo(it["link"][0])}</span></a>'
        pts = ''.join(f'<li>{ic("check")}<span>{typo(x)}</span></li>' for x in it.get('points', []))
        cells.append(f'''<article class="cell pcell" id="{it["id"]}" data-reveal>
        <div class="pcell__txt">
          <div class="cell__h">
            <h3 class="h3">{typo(it["h3"])}</h3>
            <p>{typo(it["text"])}</p>
          </div>
          {f'<ul class="pcell__pts">{pts}</ul>' if pts else ''}
          {more}
        </div>
        <div class="pcell__demo">{demos.get(it["demo"])}</div>
      </article>''')
    return f'''<section class="sec sec--tint" id="zadachi" aria-labelledby="h-tasks">
  <div class="wrap dayw">
    <header class="dayw__head">
      {kicker(d.get("kicker", "Какую задачу решает"), "q")}
      <h2 class="h2 h2--sm" id="h-tasks" data-reveal>{typo(d["h2"])}</h2>
      <p class="lead" data-reveal>{typo(d["lead"])}</p>
      <nav class="spy" data-pspy aria-label="{typo(d.get("nav_label", "Задачи"))}" data-reveal>{nav}</nav>
    </header>

    <div class="bento pcells" data-pcells>
      {"".join(cells)}
    </div>
  </div>
</section>'''


# ---------- 3. что входит: ролик «было - собираем - стало» на коде главной ----------
# места карточек на сцене: x, y, наклон; на телефоне mx, my (как на главной)
TOOL_POS = [(3, 6, -5, 2, 10), (25, 3, 3, 52, 12), (49, 11, -2, 2, 23), (73, 4, 4, 52, 25),
            (8, 37, -4, 2, 36), (30, 40, 3, 52, 38), (54, 34, -3, 2, 49), (78, 39, 2, 52, 51),
            (3, 65, -3, 2, 62), (27, 68, -2, 52, 64), (51, 63, 3, 2, 75), (75, 67, -4, 52, 77)]
BEN_POS = [(3, 12, -2, 2, 57), (77, 14, 2, 51, 57), (4, 40, 1.5, 2, 69), (76, 42, -1.5, 51, 69), (3, 68, -2, 2, 81), (77, 70, 2, 51, 81)]


def film(d):
    tools = []
    for (x, y, r, mx, my), t in zip(TOOL_POS, d['tools']):
        icon, name, body = t[:3]
        ping = f'<span class="ftool__ping">{typo(t[3])}</span>' if len(t) > 3 and t[3] else ''
        tools.append(f'''<div class="ftool" style="--x:{x}%;--y:{y}%;--r:{r}deg;--mx:{mx}%;--my:{my}%">
          <span class="ftool__bar">{ic(icon)}<span class="ftool__name">{typo(name)}</span></span>
          <span class="ftool__body">{typo(body)}</span>{ping}
        </div>''')
    bens = ''.join(f'''<li class="fben" style="--x:{x}%;--y:{y}%;--r:{r}deg;--mx:{mx}%;--my:{my}%"><span class="fben__ic" aria-hidden="true">{ic(icon)}</span><span><b>{typo(t)}</b><small>{typo(s)}</small></span></li>'''
                   for (x, y, r, mx, my), (icon, t, s) in zip(BEN_POS, d['bens']))
    a = d['app']
    now = ' class="is-now"'
    rows = ''.join(f'<li{now if i == 0 else ""}><time>{typo(tm)}</time><span><b>{typo(b)}</b>{typo(sub)}</span>{chip}</li>'
                   for i, (tm, b, sub, chip) in enumerate(a['rows']))
    def kpi(i, t):
        k, v, u = (t + ('руб.',))[:3]
        unit = f' <i>{typo(u)}</i>' if u else ''
        return f'<p class="fapp__kpi{" fapp__kpi--y" if i else ""}"><small>{typo(k)}</small><b>{typo(v)}{unit}</b></p>'
    kpis = ''.join(kpi(i, t) for i, t in enumerate(a['kpis']))
    hw = a.get('bar')
    bar = f'<p class="fapp__hw"><small>{typo(hw[0])}</small><span class="bar"><i style="--v:{hw[1]}"></i></span><b>{typo(hw[2])}</b></p>' if hw else ''
    subs = ''.join(f'<span data-sub>{typo(s)}</span>' for s in d['subs'])
    chs = ''.join(f'<button type="button" data-ch="{i}"><span>{typo(n)}' + (f'<span class="film__lx">: {typo(lx)}</span>' if lx else '') +
                  '</span><i class="film__track"><i class="film__fill"></i></i></button>' for i, (n, lx) in enumerate(d['chapters']))
    hud = d.get('hud', ('Мест', 'сообщений'))
    return f'''<section class="sec sec--film" id="{d.get("anchor", "chto-vhodit")}" aria-labelledby="h-film">
  <div class="wrap">
    {sec_head(d.get("kicker", "Что входит"), d["h2"], d.get("lead", ""), "h-film", "sq")}
  </div>

  <div class="film" data-film data-scene="2">
    <figure class="film__stage">
      <div class="film__tools" aria-hidden="true">
        {"".join(tools)}
      </div>
      <p class="film__hud" aria-hidden="true">{hud[0]}: <b data-film-count>12</b><span>{hud[1]}: <b data-film-msg>20</b></span></p>
      <div class="film__app">
        <div class="win">
          <div class="win__bar"><span class="win__crumb"><img src="/assets/img/sign.svg" width="18" height="18" alt="">TeacherDesk / <b>{typo(a["crumb"])}</b></span><span class="pill-now"><i></i>{a.get("pill", "12 &rarr; 1")}</span></div>
          <div class="fapp" role="img" aria-label="{a["label"]}">
            <div class="fapp__day" aria-hidden="true">
              <p class="fapp__h">{typo(a["title"])}<span>{typo(a["count"])}</span></p>
              <ul class="fapp__ls">{rows}</ul>
            </div>
            <div class="fapp__side" aria-hidden="true">{kpis}{bar}</div>
          </div>
        </div>
      </div>
      <ul class="film__bens" aria-label="{typo(d.get("bens_label", "Что входит"))}">
        {bens}
      </ul>
      <p class="film__trial" aria-hidden="true"><b>14&nbsp;дней</b>бесплатно</p>
      <figcaption class="film__sub">{subs}</figcaption>
    </figure>
    <div class="film__ctrl">
      <button class="film__play" type="button" data-film-play aria-label="Пауза"><svg class="ic ic--fill i-pa" aria-hidden="true"><use href="#i-pause"/></svg><svg class="ic ic--fill i-pl" aria-hidden="true"><use href="#i-play"/></svg></button>
      <div class="film__chapters" role="group" aria-label="Части ролика">{chs}</div>
    </div>
  </div>
</section>'''


# ---------- 5. почему не таблица и не обычная CRM: причины и таблица сравнения ----------
def compare(d):
    why = ''.join(f'''<li class="cmpw" data-reveal="piece" style="--i:{i}"><span class="cmpw__ic" aria-hidden="true">{ic(icon, "ic ic--20")}</span><h3 class="cmpw__t">{typo(t)}</h3><p>{typo(x)}</p></li>'''
                  for i, (icon, t, x) in enumerate(d['why']))
    cols = d['cols']
    me = ' class="cmp__me"'
    head = ''.join(f'<span role="columnheader"{me if i == len(cols) - 1 else ""}>{typo(c)}</span>' for i, c in enumerate(cols))
    rows = []
    for r in d['rows']:
        cells = []
        for j, v in enumerate(r[1:]):
            me = j == len(r) - 2
            mark = ic('check' if me else 'x', 'ic ic--12')
            cells.append(f'<span role="cell" class="cmp__c{" cmp__me" if me else ""}" data-l="{cols[j + 1]}"><i class="cmp__mk" aria-hidden="true">{mark}</i>{typo(v)}</span>')
        rows.append(f'<div class="cmp__r" role="row" data-reveal><span role="rowheader" class="cmp__task">{typo(r[0])}</span>{"".join(cells)}</div>')
    return section(sec_head(d.get('kicker', 'Почему не таблица'), d['h2'], d.get('lead', ''), 'h-cmp', 'q') + f'''<ul class="cmpws">{why}</ul>
    <div class="cmp" role="table" aria-labelledby="h-cmp">
      <div class="cmp__r cmp__r--h" role="row">{head}</div>
      {"".join(rows)}
    </div>''', 'sec--tint sec--cmp', 'h-cmp')


# ---------- 6. о сервисе: заголовок и три плашки с главной ----------
def about():
    h = _home()
    a = h.find('<header class="about__head">')
    b = h.find('<ul class="perks">', a)
    if a < 0 or b < 0:
        return ''
    end = h.index('</ul>', b) + len('</ul>')
    inner = _abs(h[a:end])
    return f'''<section class="sec sec--about sec--about-p" aria-labelledby="h-about">
  <div class="wrap">
    {inner}
  </div>
</section>'''


# ---------- 11. другие разделы сайта ----------
SECTIONS = ['features', 'instrumenty', 'baza-znanij', 'blog']
SECTION_DESC = {
    'features': 'Девять функций для уроков, оплат, заданий и общения с родителями',
    'instrumenty': 'Калькулятор дохода и генератор договора без регистрации',
    'baza-znanij': 'Пошаговые инструкции: от первого ученика до тарифа',
    'blog': 'Полезное: поиск учеников, налоги, онлайн-уроки и ИИ',
}
