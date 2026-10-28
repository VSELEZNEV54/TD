# -*- coding: utf-8 -*-
"""Шаблоны типов страниц из раздела 6 ТЗ. Один шаблон на тип: каркас задан здесь,
файл контента дает только тексты. Каждая функция возвращает (html внутри <main>, список узлов JSON-LD)."""
import re
import zlib
from html import escape
from pathlib import Path
import demos
import schedule
import features
import previews
import product as P
import stories
import sections as S
import table_pages
import contact_page
import pricing_page
import article_page
import tools_hub
from blocks import (REG, BASE, ok, typo, plain, ic, btn, kicker, phero, sec_head, section, problem,
                    feature_cards, vs, steps, scenarios, points, text_block, faq, related, cta, band,
                    promo, crumbs)

def _offer(name, price, desc):
    o = {"@type": "Offer", "name": name, "price": price, "priceCurrency": "RUB", "description": desc,
         "url": BASE + "/pricing/", "availability": "https://schema.org/InStock"}
    if price != "0":
        o["priceSpecification"] = {"@type": "UnitPriceSpecification", "price": price, "priceCurrency": "RUB",
                                   "referenceQuantity": {"@type": "QuantitativeValue", "value": 1, "unitCode": "MON"}}
    return o


OFFERS = [
    _offer("Пробный период 14 дней", "0", "Полный доступ на 14 дней без карты"),
    _offer("Pro", "990", "До 50 активных учеников, 100 запросов к ИИ в день, живые уроки с онлайн-доской"),
    _offer("Premium", "1990", "Без лимита учеников, ИИ-ассистент без дневного лимита, все возможности Pro"),
]


def app_ld(p, name=None, features=None):
    ld = {"@type": "SoftwareApplication", "name": name or "TeacherDesk", "url": BASE + p['url'],
          "applicationCategory": "BusinessApplication", "applicationSubCategory": "CRM для репетиторов",
          "operatingSystem": "Web, iOS, Android", "inLanguage": "ru-RU",
          "description": p['description'], "offers": OFFERS, "publisher": {"@id": BASE + "/#org"}}
    if features:
        ld["featureList"] = [plain(t) for t in features]
    return ld


# ---------- части главной, которые повторяются на внутренних страницах ----------
SITE = Path(__file__).resolve().parent.parent / 'site'
_HOME = {}


def _balanced(h, start, tag):
    """Вырезает элемент с вложенными одноименными тегами начиная с позиции start."""
    depth, i = 0, start
    rx = re.compile(r'<(/?)' + tag + r'\b', re.I)
    for m in rx.finditer(h, start):
        depth += -1 if m.group(1) else 1
        if depth == 0:
            return h[start:h.index('>', m.end()) + 1]
    return None


def home_part(kind):
    if 'html' not in _HOME:
        f = SITE / 'index.html'
        _HOME['html'] = f.read_text(encoding='utf-8') if f.exists() else ''
    h = _HOME['html']
    if kind == 'fstack':
        a = h.find('<ol class="fstack"')
        return _balanced(h, a, 'ol') if a > -1 else None
    return None


def stories_block(**kw):
    return stories.block(**kw)


DEMO_STICKERS = {
    'week': [('bell', 'Напоминание ушло', 'Марина К. · за час до урока'), ('calendar', 'Перенос виден всем', 'ученик уже знает новое время')],
    'debt': [('wallet', 'Оплата получена', 'Артем Д. · 2 600 руб.'), ('bell', 'Напоминание об оплате', 'уходит само')],
    'card': [('users', 'Вся история ученика', 'уроки, задания, оплаты'), ('note', 'Заметка перед уроком', 'слабое место: текстовые задачи')],
    'cabinet': [('video', 'Вход в урок', 'одной кнопкой из кабинета'), ('cards', 'Мои ошибки', '5 карточек на повторение')],
    'hw': [('check', 'Работа сдана', 'Марина К. · вариант 2'), ('cards', 'Ошибка ушла в карточки', 'задача 6')],
    'board': [('video', 'Видео и доска', 'в одном окне, без Zoom'), ('check', 'Лист сохранен', 'к нему легко вернуться')],
    'ai': [('lock', 'Сервер в России', 'данные учеников не уходят наружу'), ('ai', 'План за минуту', '4 этапа со временем')],
    'report': [('link', 'Ссылка родителю', 'отчет открывается без входа'), ('report', 'Отчет за месяц', 'уроки, задания, прогресс')],
    'journal': [('note', 'Темы и задания', 'рядом с каждым уроком'), ('report', 'Итог месяца', 'уроки и пропуски')],
    'desk': [('calendar', '4 урока сегодня', 'ОГЭ идет сейчас'), ('wallet', 'Должны 6 800 руб.', '2 ученика')],
    'trial': [('check', 'Без карты', 'полный доступ на 14 дней'), ('lock', 'Данные остаются', 'после пробного периода')],
    'tl': [('bell', 'Напоминание ушло', 'Марина К. · 14:30'), ('calendar', 'Урок идет сейчас', 'ОГЭ · Соня В.')],
}
LANDING_FACTS = [('14 дней', 'полного доступа без карты'), ('2 минуты', 'от регистрации до первого урока'), ('9 функций', 'в одном кабинете'), ('РФ', 'данные хранятся на серверах в России')]


def hero_vis(h):
    vis = demos.get(h['demo'])
    st = h.get('stickers', DEMO_STICKERS.get(h['demo'], []))
    return vis + (S.stickers(st) if st and h['demo'] != 'phone' else '')


# «Часто ищут»: облако ссылок под SEO-текстом, как блоки популярных запросов у маркетплейсов.
# Порядок соседей по типу страницы; в контенте можно задать свой список ключом tags.
LANDINGS = ['crm', 'programma', 'prilozhenie', 'besplatnaya', 'onlayn']
FEATURES = ['raspisanie', 'uchet-oplat', 'uchet-uchenikov', 'kabinet-uchenika', 'domashnie-zadaniya', 'onlayn-doska',
            'ii-assistent', 'otchety-roditelyam', 'zhurnal-zanyatiy']
TOOLS = ['kalkulyator', 'dogovor']
TAGS = {
    'home': LANDINGS + ['onlayn-doska', 'raspisanie', 'uchet-oplat', 'ii-assistent', 'tablica-ucheta', 'pricing'],
    'landing': LANDINGS + ['onlayn-doska', 'raspisanie', 'uchet-oplat', 'ii-assistent', 'zhurnal-zanyatiy', 'tablica-ucheta', 'pricing'],
    'product': LANDINGS + ['onlayn-doska', 'raspisanie', 'uchet-oplat', 'ii-assistent', 'zhurnal-zanyatiy', 'tablica-ucheta', 'pricing'],
    'feature': FEATURES + ['crm', 'programma', 'prilozhenie'],
    'tool': TOOLS + ['tablica-ucheta', 'shablon-raspisaniya', 'crm', 'programma', 'besplatnaya'],
    'table': ['tablica-ucheta', 'shablon-raspisaniya', 'uchet-oplat', 'raspisanie', 'uchet-uchenikov', 'pricing'],
    'ai-access': ['ii-assistent', 'domashnie-zadaniya', 'raspisanie', 'pricing'],
    'hub': LANDINGS + ['pricing', 'features', 'instrumenty', 'onlayn-doska', 'ii-assistent'],
    'pricing': ['besplatnaya', 'crm', 'programma', 'prilozhenie', 'onlayn', 'features', 'instrumenty', 'kalkulyator'],
    'about': LANDINGS + ['features', 'pricing', 'instrumenty'],
}


def seo_tags(p, c, visible, reg, n=12):
    out, seen = [], set()
    for i in c.get('tags') or TAGS.get(p['type'], []):
        q = reg.get(i)
        if not q or i == p['id'] or i in seen or not visible(i):
            continue
        seen.add(i)
        an = q.get('anchors') or [plain(q.get('nav', ''))]
        out.append((an[zlib.crc32((p['id'] + '>' + i).encode()) % len(an)], q['url']))
    return out[:n]


def seo_of(c, p=None, x=None):
    tags = seo_tags(p, c, x.visible, x.reg) if p and x else None
    if c.get('seo'):
        return S.seo_text(c['seo'], tags)
    t = c.get('text')
    return S.seo_text({'h2': t['h2'], 'html': t['html']}, tags) if t else ''


# ---------- тарифы: общий блок для главной, посадочных и страницы тарифов ----------
def pricing_block(h2='Две недели бесплатно, дальше от <em class="em">990 руб.</em>', link=True, kick='Тарифы', hid='h-price', tint=True):
    lnk = f'<p class="after" data-reveal><a class="btn btn--ghost btn--sm" href="/pricing/"><span>Сравнить тарифы подробно</span></a></p>' if link else ''
    plans = [
        ('0', 'Пробный период', '<b>0</b><span>руб. на&nbsp;14&nbsp;дней</span>',
         ['Полный доступ ко&nbsp;всем функциям', 'До&nbsp;50&nbsp;учеников и&nbsp;100&nbsp;запросов к&nbsp;ИИ в&nbsp;день', 'Без карты'],
         'ghost', 'Начать бесплатно'),
        ('1', 'Pro', '<b>990</b><span>руб. в&nbsp;месяц</span>',
         ['До&nbsp;50&nbsp;активных учеников', 'Живые уроки с&nbsp;онлайн-доской', 'Тесты и&nbsp;тренажеры с&nbsp;автопроверкой', '100&nbsp;запросов к&nbsp;ИИ в&nbsp;день'],
         'primary', 'Попробовать Pro'),
        ('2', 'Premium', '<b>1&nbsp;990</b><span>руб. в&nbsp;месяц</span>',
         ['Без лимита учеников', 'ИИ-ассистент без дневного лимита', 'Все возможности Pro'],
         'ghost', 'Выбрать Premium'),
    ]
    arts = []
    for k, name, price, ticks, kind, label in plans:
        fit = ' is-fit' if k == '1' else ''
        tag = '' if k == '0' else ' <span class="plan__tag">подойдет вам</span>'
        tl = ''.join(f'<li>{ic("check")}{t}</li>' for t in ticks)
        arts.append(f'''<article class="plan{fit}" data-plan="{k}">
        <h3 class="plan__n">{name}{tag}</h3>
        <p class="plan__p">{price}</p>
        <ul class="ticks">{tl}</ul>
        <a class="btn btn--{kind}" href="{REG}"><span>{label}</span></a>
      </article>''')
    return f'''<section class="sec{" sec--tint" if tint else ""}" id="tarify" aria-labelledby="{hid}">
  <div class="wrap">
    <header class="head head--price">
      <div>
        {kicker(kick, "sq")}
        <h2 class="h2" id="{hid}" data-reveal>{typo(h2)}</h2>
      </div>
      <div class="seats" data-seats data-reveal>
        <p class="seats__q"><label for="seats-range">Сколько у&nbsp;вас учеников</label><output class="seats__out" for="seats-range"><b data-seats-n>12</b><span data-seats-w>учеников</span></output></p>
        <div class="seats__track">
          <span class="seats__zones seats__zones--2" aria-hidden="true"><i class="is-on" data-fit="1"></i><i data-fit="2"></i></span>
          <input id="seats-range" type="range" min="0" max="100" step="1" value="16" aria-valuetext="12 учеников, подойдет Pro">
          <div class="seats__pos" aria-hidden="true"><span class="seats__thumb"></span></div>
        </div>
        <p class="seats__lbl seats__lbl--2" aria-hidden="true"><span class="is-on" data-fit="1">до&nbsp;50, Pro</span><span data-fit="2">больше 50, Premium</span></p>
      </div>
    </header>
    <div class="plans" data-plans data-reveal>
      <span class="plans__hl" aria-hidden="true"><span class="plans__badge" data-badge>подойдет<br>вам</span></span>
      {''.join(arts)}
    </div>
    {lnk}
  </div>
</section>'''


# ---------- посадочная ----------
def landing(p, c, x):
    h = c['hero']
    acts = [btn('Начать бесплатно', REG, 'primary', 'lg')]
    if h.get('second') and ok(h['second'][1]):
        acts.append(btn(h['second'][0], h['second'][1], 'ghost', 'lg'))
    out = [phero(p, x.trail(p), h['kicker'], h['lead'], hero_vis(h), acts, after=S.facts(c.get('facts', LANDING_FACTS)))]
    out.append(S.pains(c['pains']) if c.get('pains') else problem(c['problem']))
    f = c['features']
    out.append(S.tabs(x.reg, f, x.visible))
    out.append(S.flip(c['vs']))
    out.append(S.steps3(c.get('steps')))
    out.append(pricing_block(c.get('pricing_h2', 'Две недели бесплатно, дальше от <em class="em">990 руб.</em>'), tint=True))
    out.append(stories_block())
    if c.get('objections'):
        out.append(S.objections(c['objections'], tint=True))
    out.append(faq(c['faq']))
    out.append(related(x.reg, c.get('related') or [i for i in ['crm', 'programma', 'prilozhenie', 'besplatnaya', 'onlayn'] if i != p['id']], x.visible, 'Другие решения').replace('class="sec sec--rel"', 'class="sec sec--rel sec--tint"'))
    cc = c.get('cta', {})
    out.append(cta(cc.get('title'), cc.get('second')))
    out.append(seo_of(c, p, x))
    return '\n'.join(out), [app_ld(p, features=[x.reg[t].get('card', x.reg[t]['nav']) if isinstance(t, str) else t[1] for t in f['items']])]


# ---------- продукт: продает решение под запрос, потом рассказывает о TeacherDesk ----------
def product(p, c, x):
    """Раздел «Продукт»: первый экран со сценой дня, задачи, ролик «что входит», 14 дней, сравнение,
    о сервисе, все функции, тарифы, истории, вопросы, другие разделы, призыв, SEO-текст."""
    feats = [i for i in x.section_ids('features') if x.reg[i]['type'] == 'feature']
    fa = c.get('all_features', {})
    out = [P.hero(p, x.trail(p), c['hero'], c['hero_facts']),
           P.tasks(c['tasks']),
           P.film(c['film']),
           band(c['band']),
           P.compare(c['compare']),
           P.about(),
           feature_cards(x.reg, feats, x.visible, fa.get('h2', 'Девять функций TeacherDesk в&nbsp;одном кабинете'), fa.get('kicker', 'Все функции'),
                         fa.get('lead', ''), 'h-all', ('Все возможности', '/features/')).replace('class="sec"', 'class="sec sec--tint sec--allf"', 1),
           pricing_block(c.get('pricing_h2', 'Две недели бесплатно, дальше от <em class="em">990 руб.</em>'), tint=False),
           stories_block(tint=True),
           faq(c['faq'], c.get('faq_h2', 'Частые вопросы')),
           related(x.reg, P.SECTIONS, x.visible, c.get('sections_h2', 'Еще на&nbsp;сайте TeacherDesk'), 'Разделы', desc=P.SECTION_DESC).replace('class="sec sec--rel"', 'class="sec sec--rel sec--tint"', 1)]
    cc = c.get('cta', {})
    out.append(cta(cc.get('title'), cc.get('second')))
    out.append(seo_of(c, p, x))
    return '\n'.join(out), [app_ld(p, features=[x.reg[t].get('card', x.reg[t]['nav']) if isinstance(t, str) else t[1] for t in c['features']['items']])]


# ---------- функция ----------
def feature(p, c, x):
    h = c['hero']
    feature_ids = [i for i in x.section_ids('features') if x.reg[i]['type'] == 'feature' and x.visible(i)]
    feature_index = feature_ids.index(p['id']) + 1 if p['id'] in feature_ids else 1
    feature_total = len(feature_ids)
    acts = [btn('Начать бесплатно', REG, 'primary', 'lg')]
    if h.get('second') and ok(h['second'][1]):
        acts.append(btn(h['second'][0], h['second'][1], 'ghost', 'lg'))
    hero = phero(p, x.trail(p), h['kicker'], h['lead'], hero_vis(h), acts,
                 after=S.facts(c['facts']) if c.get('facts') else '', variant='feature')
    counter = schedule.counter(feature_index, feature_total, p['icon'])
    hero = hero.replace('<div class="phero__txt">', '<div class="phero__txt">' + counter, 1)
    out = [hero]
    if p['id'] == 'raspisanie':
        out.extend([schedule.story(c), schedule.situations(c), schedule.capabilities(c), schedule.objections(c)])
    else:
        out.extend(features.body(p, c))
    other_features = [i for i in feature_ids if i != p['id']]
    count_label = x.plural(len(other_features), 'функция', 'функции', 'функций')
    out.append(feature_cards(x.reg, other_features, x.visible,
                             f'Еще {count_label} платформы',
                             'Другие возможности', 'Все функции TeacherDesk связаны между собой. Выберите, что посмотреть дальше.',
                             'h-related', ('Все возможности', '/features/')).replace('<section class="sec"', '<section class="sec sec--tint"', 1))
    out.append(faq(c['faq'], h2='Частые вопросы'))
    cc = c.get('cta', {})
    out.append(cta(cc.get('title'), cc.get('second')))
    out.append(seo_of(c, p, x))
    pts = c.get('points', {}).get('items') or []
    feats = [it.get('title') if isinstance(it, dict) else it[1] if isinstance(it, (list, tuple)) and len(it) > 1 else it for it in pts]
    return '\n'.join(out), [app_ld(p, 'TeacherDesk: ' + p['nav'], [f for f in feats if isinstance(f, str)])]


# ---------- инструмент ----------
def tool(p, c, x):
    h = c['hero']
    widget = f'<div class="toolbox" id="tool" data-tool="{p["id"]}">{typo(c["tool"])}</div>'
    variant = 'wide' if c.get('wide') else 'tool'
    acts = [btn('Попробовать TeacherDesk бесплатно', REG, 'primary', 'lg')]
    if h.get('cta'):
        acts.append(btn(h['cta'][0], h['cta'][1], 'ghost', 'lg', h['cta'][2] if len(h['cta']) > 2 else None))
    trust = h.get('trust', ['Бесплатно', 'Без регистрации', 'Работает в браузере'])
    note = ''
    if p['status'] == 'example' and c.get('example_note'):
        note = f'<p class="exnote">{ic("note")}<span>{typo(c["example_note"])}</span></p>'
    out = [phero(p, x.trail(p), h['kicker'], h['lead'], widget if variant == 'tool' else '', acts, trust, variant,
                 after=(widget if variant == 'wide' else '') + note)]
    out.append(steps(c['howto'], 'h-howto', tint=True, howto=True))
    if c.get('platform'):
        platform = c['platform']
        cards = ''.join(f'<li><div class="pfc"><span class="pfc__ic">{ic(it["icon"])}</span><h3 class="pfc__t">{typo(it["title"])}</h3><p class="pfc__d">{typo(it["text"])}</p></div></li>' for it in platform['items'])
        out.append(section(sec_head('Дальше в TeacherDesk', platform['title'], platform['lead'], 'h-platform', 'sq') + f'<ul class="pfcs">{cards}</ul>', '', 'h-platform'))
    if c.get('extra'):
        e = c['extra']
        out.append(section(sec_head(e.get('kicker', ''), e['h2'], e.get('lead', ''), 'h-extra', 'sq') + typo(e['html']), '', 'h-extra'))
    out.append(band(c['band']))
    if c.get('objections'):
        out.append(S.objections(c['objections'], h2='Частые <em class="em">сомнения</em>'))
    out.append(faq(c['faq'], tint=True))
    rel = [i for i in TOOLS if i != p['id']]
    out.append(section(sec_head('Инструменты', 'Другие бесплатные <em class="em">инструменты</em>', '', 'h-rel', 'q', ('Все инструменты', '/instrumenty/')) + tool_cards(rel, x).replace('ftools ftools--hub', 'ftools ftools--rel'), '', 'h-rel'))
    cc = c.get('cta', {})
    out.append(cta(cc.get('title'), cc.get('second')))
    out.append(seo_of(c, p, x))
    ld = []
    if c.get('ld') == 'app':
        ld.append({"@type": "SoftwareApplication", "name": plain(p['h1']), "url": BASE + p['url'], "applicationCategory": "EducationalApplication",
                   "operatingSystem": "Web", "inLanguage": "ru-RU", "description": p['description'],
                   "offers": {"@type": "Offer", "price": "0", "priceCurrency": "RUB"}})
    return '\n'.join(out), ld


# ---------- хабы ----------
def tool_cards(ids, x):
    return previews.cards(x.reg, ids, x.visible, 'ftools ftools--free')


RUBRIC_COVER = {'Поиск учеников': 1, 'Налоги': 2, 'Организация': 3, 'Начало работы': 2, 'ИИ на уроках': 1, 'Онлайн-уроки': 3, 'Работа с учениками': 2}


def post_cards(ids, x, cls='posts3'):
    lis = []
    for i, pid in enumerate(ids):
        q = x.reg[pid]
        if not x.visible(pid):
            continue
        n = RUBRIC_COVER.get(q.get('rubric'), 1)
        lis.append(f'''<li data-reveal="piece" style="--i:{i % 6}" data-rubric="{escape(q.get("rubric", ""))}"><a class="pcard" href="{q["url"]}">
        <span class="pcard__pic pc--{n}" aria-hidden="true"><i class="pcard__a"></i><i class="pcard__b"></i><span class="pcard__ic">{ic(q["icon"])}</span></span>
        <span class="pcard__cat">{typo(q.get("rubric", ""))}</span>
        <h3 class="pcard__t">{typo(q["nav"] if len(plain(q["h1"])) > 70 else q["h1"])}</h3>
        <span class="pcard__d">{typo(q.get("card", ""))}</span>
      </a></li>''')
    return f'<ul class="{cls}">{"".join(lis)}</ul>'


def kb_cards(ids, x):
    lis = []
    for i, pid in enumerate(ids):
        q = x.reg[pid]
        if not x.visible(pid):
            continue
        lis.append(f'<li data-reveal="piece" style="--i:{i}"><a class="kbc" href="{q["url"]}"><span class="kbc__ic">{ic(q["icon"], "ic ic--20")}</span><span class="kbc__t"><b>{typo(q["nav"])}</b><small>{typo(q.get("card", ""))}</small></span><span class="kbc__go" aria-hidden="true">{ic("arrow")}</span></a></li>')
    return f'<ul class="kbcs">{"".join(lis)}</ul>'


def hub(p, c, x):
    if p['id'] == 'instrumenty':
        return tools_hub.render(p, c, x)
    sec = p['section']
    ids = [i for i in x.section_ids(sec) if i != p['id']]
    if sec == 'tools':
        ids = [i for i in TOOLS if x.visible(i)]
    acts = c.get('actions')
    if acts is None:
        acts = [btn('Начать бесплатно', REG, 'primary', 'lg')] if sec in ('features',) else []
    out = [phero(p, x.trail(p), c['kicker'], c['lead'], '', acts, c.get('trust', sec == 'features'))]
    if sec == 'features':
        stack = home_part('fstack')
        if stack:
            out.append(section(sec_head('Все функции', 'Возможности TeacherDesk <em class="em">в одном кабинете</em>', 'Листайте: карточки ложатся друг на друга, у каждой свой живой кадр.', 'h-all', 'sq') + stack, '', 'h-all'))
        else:
            out.append(feature_cards(x.reg, ids, x.visible, 'Возможности TeacherDesk <em class="em">в одном кабинете</em>', 'Все функции', '', 'h-all'))
    elif sec == 'tools':
        out.append(section('<h2 class="vh" id="h-list">Все инструменты</h2>' + tool_cards(ids, x), label='h-list'))
        out.append(section(sec_head('ИИ-помощник', 'Подготовка к урокам в TeacherDesk', 'Планы, упражнения и задания по предмету, классу и теме. ИИ-помощник доступен в личном кабинете платформы.', 'h-ai-platform', 'sq', ('Посмотреть ИИ-помощника', '/features/ii-assistent/')) + demos.get('ai'), 'sec--tint hub-ai', 'h-ai-platform'))
        out.append(section(sec_head('Таблицы в платформе', 'Расписание и учет без ручных формул', 'Посмотрите, как устроена работа в TeacherDesk, сравните с обычной таблицей и попробуйте платформу бесплатно 14 дней.', 'h-table-pages', 'sq') + previews.cards(x.reg, ['tablica-ucheta', 'shablon-raspisaniya'], x.visible, 'ftools ftools--free'), '', 'h-table-pages'))
    elif sec == 'blog':
        rubrics = []
        for i in ids:
            r = x.reg[i].get('rubric')
            if r and r not in rubrics:
                rubrics.append(r)
        chips = ''.join(f'<button class="rchip" type="button" data-rubric="{escape(r)}" aria-pressed="false">{typo(r)}</button>' for r in rubrics)
        out.append(section('<h2 class="vh" id="h-list">Все статьи</h2>' + f'<div class="rchips" data-rchips role="group" aria-label="Рубрики"><button class="rchip" type="button" data-rubric="" aria-pressed="true">Все статьи</button>{chips}</div>' +
                           post_cards(ids, x, 'posts3 posts3--hub'), label='h-list'))
    elif sec == 'kb':
        out.append(section('<h2 class="vh" id="h-list">Все инструкции</h2>' + kb_cards(ids, x), label='h-list'))
    if c.get('text'):
        out.append(text_block(dict(c['text'], cls='sec--tint')))
    cc = c.get('cta', {})
    out.append(cta(cc.get('title'), cc.get('second')))
    if c.get('seo'):
        out.append(S.seo_text(c['seo'], seo_tags(p, c, x.visible, x.reg)))
    items = [{"@type": "ListItem", "position": n + 1, "url": BASE + x.reg[i]['url'], "name": x.reg[i]['nav']} for n, i in enumerate(ids) if x.visible(i)]
    return '\n'.join(out), [{"@type": "ItemList", "name": plain(p['h1']), "itemListElement": items}]


# ---------- статья ----------
def expand(html, x):
    """[[promo:id]] превращается в блок-переход в продукт или инструмент."""
    # блок-переход на неопубликованную страницу в выкладке не выводим, как и ссылки data-opt
    return re.sub(r'\[\[promo:([\w-]+)\]\]', lambda m: promo(x.reg[m.group(1)]) if x.visible(m.group(1)) else '', html)


def article(p, c, x):
    return article_page.render(p, c, x)

# ---------- инструкция базы знаний ----------
def kb(p, c, x):
    lis = []
    for i, s in enumerate(c['steps']):
        lis.append(f'''<li class="kbs" data-step-t="{escape(plain(s["title"]))}">
        <div class="kbs__txt"><span class="kbs__n" aria-hidden="true">{i + 1}</span><h2 class="kbs__t">{typo(s["title"])}</h2><div class="kbs__d">{typo(s["text"] if s["text"].lstrip().startswith("<") else "<p>" + s["text"] + "</p>")}</div></div>
        <figure class="kbs__shot" aria-hidden="true"><span class="kbs__bar"><i></i><i></i><i></i><em>teacherdesk.ru</em></span>
          <span class="kbs__ui"><span class="kbs__rail">{"".join(ic(n, "ic ic--12") for n in ("home", "calendar", "users", "task", "wallet"))}</span>
            <span class="kbs__main"><span class="kbs__sk kbs__sk--h"></span><span class="kbs__card"><span class="kbs__ic kbs__ic--{i % 3}">{ic(s.get("icon", p["icon"]), "ic ic--20")}</span><span class="kbs__cap"><b>{typo(s.get("shot", "Шаг " + str(i + 1)))}</b><span class="kbs__sk"></span><span class="kbs__sk kbs__sk--s"></span></span></span>
              <span class="kbs__row"><span class="kbs__sk kbs__sk--m"></span><span class="kbs__btn">Шаг {i + 1}</span></span></span></span></figure>
      </li>''')
    note = f'<p class="exnote">{ic("note")}<span>Это пример инструкции: скриншоты и названия кнопок уточним по интерфейсу продукта.</span></p>' if p['status'] == 'example' else ''
    tips = ''
    if c.get('tips'):
        tips = section(f'<div class="kbtips" data-reveal><h2 class="h3" id="h-tips">{typo(c.get("tips_h2", "Полезно знать"))}</h2><div class="prose">{typo(c["tips"])}</div></div>', '', 'h-tips')
    out = [f'''<section class="kbhead">
  <div class="wrap">
    {crumbs(x.trail(p))}
    <h1 class="art__h">{typo(p["h1"])}</h1>
    <p class="art__lead">{typo(c["lead"])}</p>
    <p class="kbhead__meta">{ic("clock")}<span>{x.plural(len(c["steps"]), "шаг", "шага", "шагов")} · около {x.plural(c.get("minutes", 2), "минуты", "минут", "минут")}</span></p>
    {note}
  </div>
</section>
<section class="sec sec--kb" aria-label="Шаги">
  <div class="wrap"><ol class="kbsteps" data-howto>{"".join(lis)}</ol></div>
</section>''', tips]
    nb = [i for i in x.section_ids('kb') if i != p['id'] and i != 'baza-znanij']
    out.append(related(x.reg, c.get('related') or nb[:4], x.visible, 'Другие инструкции', 'База знаний'))
    cc = c.get('cta', {})
    out.append(cta(cc.get('title'), cc.get('second')))
    return '\n'.join(o for o in out if o), []


# ---------- тарифы ----------
YES = ic('check') + '<span class="vh">есть</span>'
NO = ic('x', 'ic ic--no') + '<span class="vh">нет</span>'


def pricing(p, c, x):
    return pricing_page.render(p, c, x)

# ---------- о сервисе ----------
def about(p, c, x):
    out = [phero(p, x.trail(p), c['kicker'], c['lead'], '', [btn('Начать бесплатно', REG, 'primary', 'lg')], False)]
    facts = ''.join(f'<li data-reveal="piece" style="--i:{i}"><b>{typo(a)}</b><span>{typo(b)}</span></li>' for i, (a, b) in enumerate(c['facts']))
    out.append(section(f'''<div class="ab-story">
      <div class="ab-story__txt">{kicker("История", "q")}<h2 class="h2 h2--sm" id="h-story" data-reveal>{typo(c["story_h2"])}</h2><div class="prose" data-reveal>{typo(c["story"])}</div></div>
      <ul class="ab-story__facts">{facts}</ul>
    </div>''', '', 'h-story'))
    vals = ''.join(f'<li class="val" data-reveal="piece" style="--i:{i}"><span class="val__n" aria-hidden="true">{i + 1}</span><h3 class="val__t">{typo(v["title"])}</h3><p>{typo(v["text"])}</p></li>' for i, v in enumerate(c['values']))
    out.append(section(sec_head('Ценности', c['values_h2'], '', 'h-val', 'sq') + f'<ul class="vals">{vals}</ul>', 'sec--tint', 'h-val'))
    cont = ''.join(f'<li data-reveal="piece" style="--i:{i}"><span>{typo(k)}</span><a class="tlink" href="mailto:{v}">{v}</a></li>' for i, (k, v) in enumerate(c['contacts']))
    out.append(section(f'''<div class="contacts">
      <div>{kicker("Контакты", "q")}<h2 class="h2 h2--sm" id="h-cont" data-reveal>{typo(c["contacts_h2"])}</h2></div>
      <ul class="contacts__list">{cont}</ul>
      <p class="contacts__req" data-reveal>{typo(c["requisites"])} <a class="tlink" href="/requisites/">Все реквизиты</a></p>
    </div>''', '', 'h-cont'))
    out.append(cta())
    out.append(seo_of({'seo': c.get('seo')}, p, x) if c.get('seo') else '')
    org = {"@type": "AboutPage", "name": plain(p['h1']), "url": BASE + p['url'], "about": {"@id": BASE + "/#org"}}
    return '\n'.join(out), [org]


def reviews(p, c, x):
    out = [phero(p, x.trail(p), c['kicker'], c['lead'], '', [btn('Начать бесплатно', REG, 'primary', 'lg')], False)]
    if p['status'] == 'example':
        out.append(f'<div class="wrap"><p class="exnote">{ic("note")}<span>{typo(c["note"])}</span></p></div>')
    out.append(stories_block(link=False, h2='Как работают <em class="em">репетиторы</em> в TeacherDesk'))
    out.append(cta())
    return '\n'.join(out), []


def legal(p, c, x):
    note = ''
    if p['status'] == 'example':
        note = f'<p class="exnote">{ic("note")}<span>{typo(c.get("note", "Текст перенесен с текущего сайта teacherdesk.ru и ждет проверки юристом клиента."))}</span></p>'
    out = f'''<section class="kbhead kbhead--legal">
  <div class="wrap">
    {crumbs(x.trail(p))}
    <h1 class="art__h">{typo(p["h1"])}</h1>
    <p class="kbhead__meta">{ic("clock")}<span>Редакция от&nbsp;{typo(c.get("updated", ""))}</span></p>
    {note}
  </div>
</section>
<section class="sec sec--legal" aria-label="Текст документа">
  <div class="wrap"><div class="prose prose--legal">{typo(c["html"])}</div></div>
</section>'''
    return out, []


def notfound(p, c, x):
    links = previews.cards(x.reg, ['features', 'pricing', 'instrumenty', 'crm'], x.visible, 'ftools nf__links')
    out = f'''<section class="phero phero--text phero--404">
  <div class="phero__bg" aria-hidden="true"></div>
  <div class="wrap">
    <div class="nf">
      <p class="nf__code" aria-hidden="true">404</p>
      <h1 class="phero__h">{typo(p["h1"])}</h1>
      <p class="phero__lead">{typo(c["lead"])}</p>
      <div class="phero__cta">{btn("На главную", "/", "primary", "lg")}</div>
      <h2 class="vh">Разделы сайта</h2>
      {links}
    </div>
  </div>
</section>'''
    return out, []


def ai_access(p, c, x):
    out = [phero(p, x.trail(p), 'ИИ-помощник в платформе', c['lead'], demos.get('ai'),
                 [btn('Попробовать TeacherDesk бесплатно', REG, 'primary', 'lg'), btn('Все возможности ИИ', '/features/ii-assistent/', 'ghost', 'lg')],
                 ['14 дней полного доступа', 'В личном кабинете', 'Без карты'])]
    out.append(steps(c['howto'], 'h-howto', tint=True))
    out.append(cta('Подготовьте первый урок в TeacherDesk', ('ИИ-помощник', '/features/ii-assistent/')))
    out.append(seo_of(c, p, x))
    return '\n'.join(out), []


RENDER = {'landing': landing, 'product': product, 'feature': feature, 'tool': tool, 'table': table_pages.render,
          'contacts': contact_page.render, 'ai-access': ai_access, 'hub': hub, 'article': article, 'kb': kb,
          'pricing': pricing, 'about': about, 'reviews': reviews, 'legal': legal, 'notfound': notfound}
