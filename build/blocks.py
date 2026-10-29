# -*- coding: utf-8 -*-
"""Общие куски страниц: шапка, подвал, крошки, первый экран, живые кадры, блоки.

Все тексты из контента проходят через typo(): неразрывные пробелы после коротких слов,
между числом и единицей, перед дефисом-тире. Поэтому в файлах контента &nbsp; писать не нужно.
"""
import re
from html import escape

REG = 'https://app.teacherdesk.ru/register'
LOGIN = 'https://app.teacherdesk.ru/login'
BASE = 'https://teacherdesk.ru'

# Сборка подменяет эту проверку: в выкладке ссылки и кнопки на неопубликованные страницы не выводятся
LINK_OK = lambda url: True  # noqa: E731


def ok(url):
    return LINK_OK(url.split('#')[0])


SECTIONS = {
    'features': ('Возможности', '/features/'),
    'tools': ('Инструменты', '/instrumenty/'),
    'blog': ('Блог', '/blog/'),
    'kb': ('База знаний', '/baza-znanij/'),
}

# ---------- типографика ----------
_UNITS = r'(?:руб|мин|минут|час|секунд|дн|день|дня|недел|месяц|год|лет|учени|урок|запрос|задач|класс|раз|процент|%|шаг|этап|карточ|вопрос|знак|тыс|млн|балл|страниц|файл|колон|человек|занят|ссылк|раз)'


def typo(html):
    """Неразрывные пробелы в текстовых узлах, теги и атрибуты не трогает."""
    if not html:
        return ''
    out = []
    for part in re.split(r'(<[^>]+>)', html):
        if part.startswith('<'):
            out.append(part)
            continue
        t = part
        t = re.sub(r'(?<![А-Яа-яЁёA-Za-z0-9-])([А-Яа-яЁё]{1,2}) (?=\S)', r'\1&nbsp;', t)
        t = re.sub(r'(\d) (?=\d{3}(?!\d))', r'\1&nbsp;', t)
        t = re.sub(r'(\d) (?=' + _UNITS + ')', r'\1&nbsp;', t)
        t = t.replace(' - ', '&nbsp;- ')
        out.append(t)
    return ''.join(out)


def plain(html):
    """Текст без тегов для JSON-LD и проверок."""
    from html import unescape
    t = re.sub(r'<[^>]+>', '', html or '')
    t = unescape(t).replace('\xa0', ' ')
    return re.sub(r'\s+', ' ', t).strip()


def ic(name, cls='ic'):
    return f'<svg class="{cls}" aria-hidden="true"><use href="#i-{name}"/></svg>'


def btn(text, href, kind='primary', size='', icon=None, attrs=''):
    cls = f'btn btn--{kind}' + (f' btn--{size}' if size else '')
    tail = ic(icon) if icon and icon != 'arrow' else ''  # стрелок на кнопках нет
    return f'<a class="{cls}" href="{href}"{attrs}><span>{typo(text)}</span>{tail}</a>'


def kicker(text, geo='sq', reveal=True):
    r = ' data-reveal' if reveal else ''
    return f'<p class="kicker"{r}><i class="geo geo--{geo}" aria-hidden="true"></i>{typo(text)}</p>'


def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')


# ---------- шапка и подвал ----------
SOLUTIONS = ['crm', 'programma', 'prilozhenie', 'besplatnaya', 'onlayn', 'tablica-ucheta', 'shablon-raspisaniya']


FEATURES = ['raspisanie', 'uchet-oplat', 'uchet-uchenikov', 'kabinet-uchenika', 'domashnie-zadaniya', 'onlayn-doska', 'ii-assistent', 'otchety-roditelyam', 'zhurnal-zanyatiy']


def header(page, reg, visible):
    """Шапка: «Возможности», «Инструменты», «Решения», «Тарифы», «Блог».
    reg: словарь id -> страница; visible(id) решает, показывать ли ссылку."""
    cur = page['url']
    sec = page.get('section')

    def cur_attr(url, section=None):
        if url == cur:
            return ' aria-current="page"'
        if section and sec == section and page['type'] != 'hub':
            return ' aria-current="true"'
        return ''

    def item(p, n):
        return (f'<a class="mm__i" href="{p["url"]}"{cur_attr(p["url"])}><span class="mm__ic mm__ic--{n % 3}">{ic(p["icon"], "ic ic--20")}</span>'
                f'<span class="mm__tx"><b>{typo(p["nav"])}</b><small>{typo(p.get("card", ""))}</small></span></a>')

    sol = [reg[i] for i in SOLUTIONS if visible(i)]
    feats = [reg[i] for i in FEATURES if visible(i)]
    sol_panel = f'''<div class="mm mm--sol" id="dd-sol">
          <div class="mm__grid">{"".join(item(p, n) for n, p in enumerate(sol))}</div>
          <a class="mm__promo" href="{REG}"><span class="mm__pk">14 дней бесплатно</span><b>Полный доступ ко всем функциям без карты</b><span class="mm__pgo">Начать</span></a>
        </div>'''
    all_f = f'<a class="btn btn--ghost btn--sm mm__all" href="/features/"><span>Все возможности</span></a>' if visible('features') else ''
    feat_panel = f'''<div class="mm mm--feat" id="dd-feat">
          <div class="mm__grid mm__grid--3">{"".join(item(p, n) for n, p in enumerate(feats))}</div>
          {all_f}
        </div>'''
    on_sol = ' is-cur' if page.get('id') in SOLUTIONS else ''
    on_feat = ' is-cur' if sec == 'features' else ''
    def link(pid, section=None):
        if not visible(pid):
            return ''
        p = reg[pid]
        return f'<a href="{p["url"]}"{cur_attr(p["url"], section)}>{p["nav"]}</a>'

    sheet = ['<p class="hdr__sh">Возможности</p>'] + [f'<a href="{p["url"]}"{cur_attr(p["url"])}>{p["nav"]}</a>' for p in feats]
    if visible('instrumenty'):
        sheet.append(f'<a href="{reg["instrumenty"]["url"]}"{cur_attr(reg["instrumenty"]["url"])}>{reg["instrumenty"]["nav"]}</a>')
    sheet.append('<p class="hdr__sh">Решения</p>')
    sheet += [f'<a href="{p["url"]}"{cur_attr(p["url"])}>{p["nav"]}</a>' for p in sol]
    for pid in ('pricing', 'blog'):
        if visible(pid):
            p = reg[pid]
            sheet.append(f'<a href="{p["url"]}"{cur_attr(p["url"])}>{p["nav"]}</a>')
    sheet.append('<p class="hdr__sh">Помощь и информация</p>')
    for pid in ('baza-znanij', 'about', 'kontakty'):
        if visible(pid):
            p = reg[pid]
            sheet.append(f'<a href="{p["url"]}"{cur_attr(p["url"])}>{p["nav"]}</a>')
    sheet.append(f'<a href="{LOGIN}">Войти</a>')
    return f'''<header class="hdr" data-hdr>
  <div class="hdr__bar">
    <a class="hdr__logo" href="/" aria-label="TeacherDesk, на главную"><img class="hdr__word" src="/assets/img/logo.svg" width="142" height="24" alt="TeacherDesk"><img class="hdr__sign" src="/assets/img/sign.svg" width="30" height="30" alt=""></a>
    <nav class="hdr__nav" aria-label="Основное меню">
      <div class="hdr__dd{on_feat}" data-dd>
        <button class="hdr__ddb" type="button" aria-expanded="false" aria-controls="dd-feat">Возможности{ic("chev", "ic ic--12")}</button>
        {feat_panel}
      </div>
      {link('instrumenty', 'tools')}
      <div class="hdr__dd{on_sol}" data-dd>
        <button class="hdr__ddb" type="button" aria-expanded="false" aria-controls="dd-sol">Решения{ic("chev", "ic ic--12")}</button>
        {sol_panel}
      </div>
      {link('pricing')}{link('blog', 'blog')}
    </nav>
    <div class="hdr__act">
      <a class="hdr__login" href="{LOGIN}">Войти</a>
      <a class="btn btn--primary btn--sm" href="{REG}"><span>Начать бесплатно</span></a>
      <details class="hdr__menu" data-menu>
        <summary aria-label="Меню">{ic("menu", "ic ic--20 hdr__menu-open")}{ic("close", "ic ic--20 hdr__menu-close")}</summary>
        <nav class="hdr__sheet" aria-label="Меню для телефона">{''.join(sheet)}</nav>
      </details>
    </div>
  </div>
</header>'''


# Порядок разделов повторяет основное меню.
FOOTER_COLS = [
    ('Возможности', ['raspisanie', 'uchet-oplat', 'uchet-uchenikov', 'kabinet-uchenika', 'domashnie-zadaniya', 'onlayn-doska', 'ii-assistent', 'otchety-roditelyam', 'zhurnal-zanyatiy']),
    ('Инструменты', ['kalkulyator', 'anketa', 'tablica-ucheta', 'shablon-raspisaniya', 'dogovor', ('instrumenty', 'Все инструменты')]),
    ('Решения', SOLUTIONS + ['pricing', 'otzyvy']),
    ('База знаний', ['pervye-shagi', 'import-iz-excel', 'ustanovka-na-telefon', 'napominaniya-ob-oplate', ('baza-znanij', 'Все инструкции')]),
    ('Полезное', ['blog', 'gde-iskat-uchenikov', 'samozanyatost', 'luchshie-crm', 'about', 'kontakty']),
]
LEGAL = ['privacy', 'terms', 'offer', 'consent', 'marketing', 'cookies', 'requisites']


def footer(reg, visible):
    cols = []
    for title, ids in FOOTER_COLS:
        items = []
        for x in ids:
            pid, label = (x if isinstance(x, tuple) else (x, None))
            if visible(pid):
                p = reg[pid]
                items.append(f'<li><a href="{p["url"]}">{typo(label or p["nav"])}</a></li>')
        if items:
            cols.append(f'''<details class="ftr__col" open>
          <summary class="ftr__h">{title}{ic("plus")}</summary>
          <ul>{''.join(items)}</ul>
        </details>''')
    docs = ''.join(f'<li><a href="{reg[i]["url"]}">{typo(reg[i]["nav"])}</a></li>' for i in LEGAL if visible(i))
    return f'''<footer class="ftr">
  <div class="wrap">
    <div class="ftr__top">
      <div class="ftr__brand">
        <a href="/" aria-label="TeacherDesk, на главную"><img src="/assets/img/logo.svg" width="142" height="24" alt="TeacherDesk" loading="lazy"></a>
        <p>{typo("Платформа для частных репетиторов: расписание, учет оплат, домашние задания и ИИ-ассистент в одном окне.")}</p>
        <a class="ftr__mail" href="mailto:info@teacherdesk.ru">{ic("mail")}info@teacherdesk.ru</a>
      </div>
      <nav class="ftr__cols" aria-label="Карта сайта">
        {''.join(cols)}
      </nav>
    </div>
    <div class="ftr__legal">
      <ul class="ftr__docs">{docs}<li><button class="ftr__cset" type="button" data-cbar-open>Настройки аналитики</button></li></ul>
      <p>ИП Булитко А.В. · ИНН 745604136907 · ОГРНИП 324508100646384 · г. Москва · <a href="mailto:info@teacherdesk.ru">info@teacherdesk.ru</a></p>
      <p>{typo("Персональные данные обрабатываются по 152-ФЗ и хранятся на серверах в России. Регистрация лиц до 14 лет только с согласия родителя или законного представителя.")}</p>
      <p>© 2026&nbsp;TeacherDesk · Разработано в&nbsp;России · 16+</p>
    </div>
  </div>
</footer>'''


def crumbs(trail):
    """trail: [(название, url), ...], последний элемент без ссылки."""
    items = []
    for i, (name, url) in enumerate(trail):
        if i == len(trail) - 1:
            items.append(f'<li aria-current="page">{typo(name)}</li>')
        else:
            items.append(f'<li><a href="{url}">{typo(name)}</a>{ic("chevr", "ic ic--12")}</li>')
    return f'<nav class="crumbs" aria-label="Хлебные крошки"><ol>{"".join(items)}</ol></nav>'


# ---------- первый экран внутренней страницы ----------
def trust_list(items=None, inv=False):
    items = items or ['14 дней бесплатно', 'Без карты', 'Данные хранятся в России']
    cls = 'trust trust--inv' if inv else 'trust'
    lis = ''.join(f'<li>{ic("check")}{typo(x)}</li>' for x in items)
    return f'<ul class="{cls}">{lis}</ul>'


def phero(page, trail, kick, lead, vis='', actions=None, trust=True, variant='', after=''):
    """Первый экран: крошки, кикер, h1, лид, кнопки, строка доверия и живой кадр справа."""
    if actions is None:
        actions = [btn('Начать бесплатно', REG, 'primary', 'lg')]
    acts = f'<div class="phero__cta">{"".join(actions)}</div>' if actions else ''
    tr = trust_list() if trust is True else (trust_list(trust) if trust else '')
    k = f'<p class="kicker kicker--pill phero__k"><span class="pulse" aria-hidden="true"></span>{typo(kick)}</p>' if kick else ''
    v = f'<div class="phero__vis">{vis}</div>' if vis else ''
    mod = (' phero--' + variant) if variant else ('' if vis else ' phero--text')
    return f'''<section class="phero{mod}">
  <div class="phero__bg" aria-hidden="true"></div>
  <div class="wrap">
    {crumbs(trail)}
    <div class="phero__in">
      <div class="phero__txt">
        {k}
        <h1 class="phero__h">{typo(page["h1"])}</h1>
        <p class="phero__lead">{typo(lead)}</p>
        {acts}
        {tr}
      </div>
      {v}
    </div>
    {after}
  </div>
</section>'''


def sec_head(kick, h2, lead='', hid='', geo='sq', link=None, cls=''):
    lid = f' id="{hid}"' if hid else ''
    ld = f'<p class="lead" data-reveal>{typo(lead)}</p>' if lead else ''
    lk = ''
    if link and ok(link[1]):
        lk = f'<a class="btn btn--ghost btn--sm shead__btn" data-reveal href="{link[1]}"><span>{typo(link[0])}</span></a>'
    k = kicker(kick, geo) if kick else ''
    return f'''<header class="shead{(" " + cls) if cls else ""}">
      <div>{k}<h2 class="h2 h2--sm"{lid} data-reveal>{typo(h2)}</h2></div>
      {ld}{lk}
    </header>'''


def section(inner, cls='', label='', sid=''):
    al = f' aria-labelledby="{label}"' if label else ''
    i = f' id="{sid}"' if sid else ''
    return f'<section class="sec{(" " + cls) if cls else ""}"{i}{al}>\n  <div class="wrap">\n    {inner}\n  </div>\n</section>'


# ---------- блоки ----------
def problem(d):
    """Было и стало: три боли и как они решаются."""
    items = ''.join(f'''<li class="pain" data-reveal="piece" style="--i:{i}">
        <p class="pain__was">{ic("x")}<span>{typo(x["was"])}</span></p>
        <p class="pain__now">{ic("check")}<span>{typo(x["now"])}</span></p>
      </li>''' for i, x in enumerate(d['items']))
    return section(sec_head(d.get('kicker', 'Какую задачу решает'), d['h2'], d.get('lead', ''), 'h-problem', 'q') +
                   f'<ul class="pains">{items}</ul>', label='h-problem')


def feature_cards(reg, items, visible, h2, kick='Что внутри', lead='', hid='h-feat', link=None):
    cards = []
    for i, it in enumerate(items):
        pid, text = (it if isinstance(it, tuple) else (it, None))
        p = reg[pid]
        name = p['nav']
        desc = text or p.get('card', '')
        inner = f'''<span class="pfc__ic">{ic(p["icon"], "ic ic--20")}</span>
          <h3 class="pfc__t">{typo(name)}</h3>
          <p class="pfc__d">{typo(desc)}</p>'''
        if visible(pid):
            cards.append(f'''<li data-reveal="piece" style="--i:{i}"><a class="pfc" href="{p["url"]}">{inner}
          <span class="pfc__go" aria-hidden="true">{ic("arrow")}</span></a></li>''')
        else:
            cards.append(f'<li data-reveal="piece" style="--i:{i}"><div class="pfc">{inner}</div></li>')
    n = len(items)
    cols = {2: 'pfcs--2', 4: 'pfcs--4', 5: 'pfcs--5', 8: 'pfcs--4'}.get(n, '')
    # Один вид сетки функций на всех страницах: компактные карточки, как на страницах продукта.
    return section(sec_head(kick, h2, lead, hid, 'sq', link) + f'<ul class="pfcs {cols}">{"".join(cards)}</ul>', 'sec--allf', label=hid)


def vs(d):
    rows = ''.join(f'''<div class="vs__row" role="row" data-reveal style="--i:{i}">
        <span class="vs__k" role="rowheader">{typo(k)}</span>
        <span class="vs__old" role="cell">{ic("x")}<span>{typo(o)}</span></span>
        <span class="vs__new" role="cell">{ic("check")}<span>{typo(n)}</span></span>
      </div>''' for i, (k, o, n) in enumerate(d['rows']))
    old = d.get('old', 'Таблица и мессенджеры')
    table = f'''<div class="vs" role="table" aria-label="{escape(plain(d["h2"]))}">
      <div class="vs__row vs__row--h" role="row"><span role="columnheader">Задача</span><span role="columnheader">{typo(old)}</span><span role="columnheader">TeacherDesk</span></div>
      {rows}
    </div>'''
    return section(sec_head(d.get('kicker', 'Сравнение'), d['h2'], d.get('lead', ''), 'h-vs', 'q') + table, 'sec--tint', 'h-vs')


def steps(d, hid='h-steps', tint=False, howto=False):
    """Шаги с цифрами антиквой. howto=True добавляет разметку для HowTo (собирается в build)."""
    lis = ''.join(f'''<li class="pstep" data-reveal="piece" style="--i:{i}" data-step-t="{escape(plain(s["title"]))}">
        <span class="pstep__n" aria-hidden="true">{i + 1}</span>
        <h3 class="pstep__t">{typo(s["title"])}</h3>
        <p>{typo(s["text"])}</p>
      </li>''' for i, s in enumerate(d['steps']))
    attr = ' data-howto' if howto else ''
    return section(sec_head(d.get('kicker', 'По шагам'), d['h2'], d.get('lead', ''), hid, 'q') +
                   f'<ol class="psteps"{attr}>{lis}</ol>', 'sec--tint' if tint else '', hid)


def scenarios(d):
    lis = ''.join(f'''<li class="scn" data-reveal="piece" style="--i:{i}">
        <p class="scn__m"><span class="scn__n" aria-hidden="true">{i + 1}</span><span class="scn__when">{typo(s.get("when", ""))}</span></p>
        <h3 class="scn__t">{typo(s["title"])}</h3>
        <p class="scn__d">{typo(s["text"])}</p>
      </li>''' for i, s in enumerate(d['items']))
    return section(sec_head(d.get('kicker', 'Из жизни репетитора'), d['h2'], d.get('lead', ''), 'h-scn', 'q') +
                   f'<ol class="scns">{lis}</ol>', 'sec--tint', 'h-scn')


def points(d):
    lis = ''.join(f'<li data-reveal style="--i:{i}">{ic("check")}<span>{typo(x)}</span></li>' for i, x in enumerate(d['items']))
    text = ''.join(f'<p>{typo(p)}</p>' for p in d.get('text', []))
    return section(f'''<div class="pts">
      <div class="pts__head">{kicker(d.get("kicker", "Что умеет"), "sq")}<h2 class="h2 h2--sm" id="h-pts" data-reveal>{typo(d["h2"])}</h2>
        <div class="pts__text" data-reveal>{text}</div></div>
      <ul class="pts__list">{lis}</ul>
    </div>''', label='h-pts')


def text_block(d, hid='h-text'):
    """Обычный текст под SEO: заголовок и абзацы в две колонки."""
    body = typo(d['html'])
    return section(f'''<div class="tblock">
      <div class="tblock__head">{kicker(d.get("kicker", "Подробнее"), "q")}<h2 class="h2 h2--sm" id="{hid}" data-reveal>{typo(d["h2"])}</h2></div>
      <div class="tblock__body prose" data-reveal>{body}</div>
    </div>''', d.get('cls', ''), hid)


def faq(items, h2='Частые <em class="em">вопросы</em>', kick='Вопросы', tint=False):
    det = []
    for i, (q, a) in enumerate(items):
        o = ' open' if i == 0 else ''
        a_html = a if a.lstrip().startswith('<') else f'<p>{a}</p>'
        det.append(f'<details name="faq"{o}><summary>{typo(q)}<span class="faq__x" aria-hidden="true">{ic("plus", "ic")}</span></summary><div class="faq__a">{typo(a_html)}</div></details>')
    return f'''<section class="sec sec--faq{" sec--tint" if tint else ""}" aria-labelledby="h-faq">
  <div class="wrap">
    <div class="faqw">
      <header class="faqw__head">
        {kicker(kick, "sq")}
        <h2 class="h2 h2--sm" id="h-faq" data-reveal>{typo(h2)}</h2>
        <p class="faqw__mail" data-reveal>{typo("Не нашли ответ? Задайте вопрос или напишите на")} <a class="tlink" href="mailto:info@teacherdesk.ru">info@teacherdesk.ru</a>{typo(", отвечаем в течение рабочего дня.")}</p>
      </header>
      <div class="faq" data-faq data-reveal>
        {''.join(det)}
        <button class="btn btn--dark faq__ask" type="button" data-ask-open><span>Задать свой вопрос</span></button>
      </div>
    </div>
  </div>
</section>'''


def related(reg, ids, visible, h2='Еще по теме', kick='Дальше', hid='h-rel', link=None, desc=None):
    """Карточки-переходы в стиле блока «Бесплатные инструменты» с главной."""
    import previews  # previews берет помощники отсюда, поэтому импорт внутри
    ul = previews.cards(reg, ids, visible, desc=desc)
    if not ul:
        return ''
    return section(sec_head(kick, h2, '', hid, 'q', link) + ul, 'sec--rel', hid)


def cta(title=None, second=None, trust=None):
    title = title or 'Попробуйте TeacherDesk на своих учениках <span class="pill-now pill-now--xl"><i aria-hidden="true"></i>сегодня</span>'
    sec = ''
    if second and ok(second[1]):
        sec = f'<a class="btn btn--onblue btn--lg" href="{second[1]}"><span>{typo(second[0])}</span></a>'
    return f'''<section class="cta" aria-labelledby="h-cta">
  <div class="wrap">
    <div class="cta__box" data-reveal>
      <div class="tee" aria-hidden="true" data-tee><i class="tee__bar"></i><i class="tee__block"></i><i class="tee__stem"></i></div>
      <h2 class="cta__t" id="h-cta">{typo(title)}</h2>
      <div class="cta__act">
        <a class="btn btn--white btn--lg" href="{REG}"><span>Начать бесплатно</span></a>
        {sec}
      </div>
      {trust_list(trust or ['14 дней полного доступа', 'Без карты', 'Данные хранятся в России'], inv=True)}
    </div>
  </div>
</section>'''


def band(d):
    """Темная плашка «надоело вести вручную?» с переходом в продукт."""
    acts = btn(d.get('btn', 'Перенести в TeacherDesk'), REG, 'white', 'lg')
    if d.get('second') and ok(d['second'][1]):
        acts += f'<a class="btn btn--onblue btn--lg" href="{d["second"][1]}"><span>{typo(d["second"][0])}</span></a>'
    pts = ''.join(f'<li>{ic("check")}{typo(x)}</li>' for x in d.get('points', []))
    return f'''<section class="sec sec--band" aria-labelledby="h-band">
  <div class="wrap">
    <div class="band2" data-reveal>
      <div class="band2__glow" aria-hidden="true"></div>
      <div class="band2__txt">
        {kicker(d.get("kicker", "Когда учеников станет больше"), "q", False)}
        <h2 class="h2 h2--sm" id="h-band">{typo(d["title"])}</h2>
        <p class="band2__lead">{typo(d["text"])}</p>
        <div class="band2__act">{acts}</div>
      </div>
      <ul class="band2__pts">{pts}</ul>
    </div>
  </div>
</section>'''


def promo(p):
    """Переход в продукт или инструмент внутри статьи."""
    return f'''<aside class="promo" data-reveal>
  <span class="promo__ic">{ic(p["icon"], "ic ic--20")}</span>
  <span class="promo__t"><b>{typo(p["nav"])}</b><span>{typo(p.get("card", ""))}</span></span>
  <a class="btn btn--dark btn--sm" href="{p["url"]}"><span>Открыть</span></a>
</aside>'''
