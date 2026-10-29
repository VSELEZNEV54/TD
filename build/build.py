#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сборка сайта TeacherDesk.

    python3 build/build.py            просмотр у студии: все страницы, примеры закрыты noindex,
                                      плюс служебный список страниц /_pages/
    python3 build/build.py --release  выкладка: только опубликованные страницы, ссылки на примеры
                                      убираются, служебный список удаляется
    python3 build/build.py --only=crm,programma
                                      собрать и проверить только эти страницы (без карты сайта
                                      и без удаления старых файлов)

Главную (site/index.html) генератор пока не пишет: ее правят вручную.
Внутренние страницы подключают main.css, home.css (компоненты главной) и pages.css, скрипты
main.js, home.js (тарифы, истории, стопка функций, окно вопроса, знак T) и pages.js.
"""
import datetime
import hashlib
import importlib.util
import json
import re
import sys
from html import escape
from pathlib import Path

BUILD = Path(__file__).resolve().parent
ROOT = BUILD.parent
SITE = ROOT / 'site'
sys.path.insert(0, str(BUILD))

import blocks  # noqa: E402
import templates  # noqa: E402
from blocks import BASE, typo, plain  # noqa: E402

RELEASE = '--release' in sys.argv
ONLY = next((a.split('=', 1)[1].split(',') for a in sys.argv if a.startswith('--only=')), None)
ASSETS = ['assets/css/main.css', 'assets/css/home.css', 'assets/css/pages.css',
          'assets/js/main.js', 'assets/js/home.js', 'assets/js/pages.js',
          'assets/css/schedule.css', 'assets/js/schedule.js',
          'assets/css/features.css', 'assets/js/features.js', 'assets/css/tools.css',
          'assets/css/feature-scene-board.css', 'assets/css/feature-scene-people.css',
          'assets/css/feature-scene-work.css',
          'assets/css/tables.css', 'assets/css/contacts.css', 'assets/css/tools-hub.css',
          'assets/css/article.css', 'assets/css/pricing.css', 'assets/js/pricing.js']
MONTHS = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
errors, warns = [], []


def err(page, msg):
    errors.append(f'{page}: {msg}')


class Ctx:
    def __init__(self, pages):
        self.pages = pages
        self.reg = {p['id']: p for p in pages}
        self.by_url = {p['url']: p for p in pages}
        self._partials = {}

    def visible(self, pid):
        p = self.reg.get(pid)
        if not p:
            return False
        return p['status'] == 'published' or not RELEASE

    def section_ids(self, sec):
        return [p['id'] for p in self.pages if p.get('section') == sec]

    def trail(self, p):
        t = [('Главная', '/')]
        sec = blocks.SECTIONS.get(p.get('section'))
        if sec and p['url'] != sec[1]:
            t.append(sec)
        t.append((plain(p['h1']) if p['type'] in ('legal', 'kb', 'article') else p['nav'], p['url']))
        return t

    @staticmethod
    def date(iso):
        d = datetime.date.fromisoformat(iso)
        return f'{d.day}&nbsp;{MONTHS[d.month - 1]} {d.year}'

    @staticmethod
    def plural(n, one, few, many):
        a, b = n % 10, n % 100
        w = one if a == 1 and b != 11 else few if 2 <= a <= 4 and not 12 <= b <= 14 else many
        return f'{n}&nbsp;{w}'


def load_content(pid):
    f = BUILD / 'content' / f'{pid}.py'
    if not f.exists():
        return None
    spec = importlib.util.spec_from_file_location('c_' + pid.replace('-', '_'), f)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.PAGE


def modified(pid):
    """Дата последней правки страницы: по файлу контента, для главной по site/index.html."""
    f = SITE / 'index.html' if pid == 'home' else BUILD / 'content' / f'{pid}.py'
    if not f.exists():
        return datetime.date.today().isoformat()
    return datetime.date.fromtimestamp(f.stat().st_mtime).isoformat()


def og_image(p):
    """Своя картинка для соцсетей из assets/img/og/<id>.jpg (build/og.py), иначе общая."""
    own = f'og/{p["id"]}.jpg'
    return own if (SITE / 'assets' / 'img' / own).exists() else p.get('og', 'og-home.jpg')


def versions():
    v = {}
    for a in ASSETS:
        f = SITE / a
        if f.exists():
            v[a] = hashlib.md5(f.read_bytes()).hexdigest()[:8]
    return v


def faq_ld(html):
    m = re.search(r'<div class="faq" data-faq[^>]*>(.*?)<button', html, re.S)
    if not m:
        return None
    qa = re.findall(r'<summary>(.*?)<span class="faq__x".*?<div class="faq__a">(.*?)</div></details>', m.group(1), re.S)
    return {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": plain(q), "acceptedAnswer": {"@type": "Answer", "text": plain(a)}} for q, a in qa]}


def howto_ld(p, html):
    m = re.search(r'data-howto>(.*?)</ol>', html, re.S)
    if not m:
        return None
    titles = re.findall(r'data-step-t="([^"]+)"', m.group(1))
    texts = re.findall(r'<(?:p|div class="kbs__d")>(.*?)</(?:p|div)>\s*(?:</li>|</div>)', m.group(1), re.S)
    steps = []
    for i, t in enumerate(titles):
        st = {"@type": "HowToStep", "position": i + 1, "name": plain(t)}
        if i < len(texts):
            st["text"] = plain(texts[i])
        steps.append(st)
    return {"@type": "HowTo", "name": plain(p['h1']), "step": steps}


def page_html(p, main, ld_nodes, ctx, ver, assets_css, assets_js):
    noindex = p['status'] != 'published' or p['type'] == 'notfound'
    canon = BASE + p['url']
    css = ''.join(f'<link rel="stylesheet" href="/{a}?v={ver[a]}">\n' for a in assets_css)
    js = ''.join(f'<script src="/{a}?v={ver[a]}" defer></script>\n' for a in assets_js)
    graph = []
    if p['type'] != 'notfound':
        graph.append({"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": plain(n), "item": BASE + u} for i, (n, u) in enumerate(ctx.trail(p))]})
    graph += ld_nodes
    f = faq_ld(main)
    if f:
        graph.append(f)
    h = howto_ld(p, main)
    if h:
        graph.append(h)
    og = og_image(p)
    for node in graph:
        if node.get('@type') == 'Article':
            node['image'] = BASE + '/assets/img/' + og
    if p['type'] not in ('notfound', 'service'):
        graph.insert(0, {"@type": "WebPage", "@id": canon + "#page", "url": canon, "name": p['title'], "description": p['description'],
                         "inLanguage": "ru-RU", "isPartOf": {"@id": BASE + "/#site"}, "publisher": {"@id": BASE + "/#org"},
                         "dateModified": modified(p['id']), "primaryImageOfPage": BASE + "/assets/img/" + og})
    graph.insert(0, {"@type": "Organization", "@id": BASE + "/#org", "name": "TeacherDesk", "url": BASE + "/",
                     "logo": BASE + "/assets/img/logo.svg", "email": "info@teacherdesk.ru",
                     "contactPoint": {"@type": "ContactPoint", "contactType": "customer support", "email": "info@teacherdesk.ru", "availableLanguage": "ru"}})
    ld = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, separators=(',', ':'))
    robots = '<meta name="robots" content="noindex, follow">\n' if noindex else ''
    canon_tag = '' if p['type'] == 'notfound' else f'<link rel="canonical" href="{canon}">\n'
    sprite = (BUILD / 'partials' / 'sprite.svg').read_text(encoding='utf-8')
    ask = (BUILD / 'partials' / 'ask.html').read_text(encoding='utf-8') if 'data-ask-open' in main or 'data-consult-open' in main else ''
    if RELEASE:
        ask = strip_unpublished_links(ask, ctx)
    title = escape(p['title'], quote=True)
    desc = escape(p['description'], quote=True)
    return f'''<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
{robots}{canon_tag}<meta property="og:type" content="{'article' if p['type'] == 'article' else 'website'}">
<meta property="og:site_name" content="TeacherDesk">
<meta property="og:locale" content="ru_RU">
<meta property="og:url" content="{canon}">
<meta property="og:title" content="{escape(plain(p['h1']) or p['title'], quote=True)}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{BASE}/assets/img/{og}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#ffffff">
<link rel="icon" href="/assets/img/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/assets/img/favicon-120.png" type="image/png" sizes="120x120">
<link rel="apple-touch-icon" href="/assets/img/apple-touch-icon.png">
<link rel="preload" href="/assets/fonts/geist-600.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/geist-400.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/playfair-display-italic-500.woff" as="font" type="font/woff" crossorigin>
{css}<script>document.documentElement.classList.add('js')</script>
<script type="application/ld+json">{ld}</script>
</head>
<body id="top" class="pg pg--{p['type']}">

{sprite}
<a class="skip" href="#main">К&nbsp;содержанию</a>

{blocks.header(p, ctx.reg, ctx.visible)}

<main id="main">
{main}
</main>

{blocks.footer(ctx.reg, ctx.visible)}

{ask}
{js}</body>
</html>
'''


def strip_unpublished_links(html, ctx):
    """В выкладке ссылки data-opt на неопубликованные страницы становятся обычным текстом."""
    def fix(m):
        href = m.group(2)
        p = ctx.by_url.get(href.split('#')[0])
        if p and not ctx.visible(p['id']):
            return m.group(3)
        return m.group(0)
    return re.sub(r'<a ([^>]*?)href="(/[^"]*)"[^>]*data-opt[^>]*>(.*?)</a>', fix, html, flags=re.S)


SEO_MIN = {'landing': 4500, 'product': 4500, 'feature': 3500, 'tool': 3000, 'hub': 1500, 'pricing': 2500}
STOP = {'для', 'и', 'в', 'на', 'с', 'по', 'как', 'что'}


def stems(q):
    return [w[:max(4, len(w) - 2)] if len(w) > 5 else w for w in re.findall(r'[a-zа-я0-9]+', q.lower()) if w not in STOP]


def seo_check(p, html):
    """Главный запрос в title и h1, объем SEO-текста по типу страницы."""
    if p['status'] != 'published' or not p.get('query'):
        return
    for name, val in (('title', p['title']), ('h1', plain(p['h1']))):
        miss = [w for w in stems(p['query']) if w not in val.lower()]
        if val and miss and p['type'] not in ('hub', 'pricing'):
            warns.append(f'{p["id"]}: в {name} нет слов главного запроса ({", ".join(miss)})')
    m = re.search(r'<div class="seo__body"[^>]*>(.*?)</div>\s*<button', html, re.S)
    n = len(plain(m.group(1))) if m else 0
    need = SEO_MIN.get(p['type'])
    if need and n < need:
        warns.append(f'{p["id"]}: SEO-текст {n} знаков, нужно от {need}')


def check(p, html, ctx):
    pid = p['id']
    seo_check(p, html)
    t, d = p['title'], p['description']
    if len(t) > 65:
        err(pid, f'title длиннее 65 знаков ({len(t)})')
    if p['type'] != 'notfound' and not 140 <= len(d) <= 160:
        err(pid, f'description {len(d)} знаков, нужно 140-160')
    if html.count('<h1') != 1:
        err(pid, f'h1 на странице: {html.count("<h1")}')
    body = re.sub(r'<script.*?</script>|<style.*?</style>|<!--.*?-->', ' ', html, flags=re.S)
    text = ' '.join(x for x in re.split(r'<[^>]+>', body) if x.strip()) + ' ' + t + ' ' + d
    for ch, name in (('ё', 'буква ё'), ('Ё', 'буква Ё'), ('—', 'длинное тире'), ('–', 'среднее тире'), ('!', 'восклицательный знак')):
        if ch in text:
            i = text.index(ch)
            err(pid, f'{name}: «{text[max(0, i - 30):i + 10].strip()}»')
    for href in re.findall(r'href="(/[^"#?]*)', html):
        if href.startswith('/assets/') or href == '/':
            continue
        q = ctx.by_url.get(href)
        if not q:
            err(pid, f'ссылка на несуществующую страницу {href}')
        elif RELEASE and not ctx.visible(q['id']):
            err(pid, f'ссылка на неопубликованную страницу {href}')


def preview_index(ctx, built):
    groups = [('features', 'Возможности'), ('product', 'Решения'), ('tools', 'Инструменты'), ('blog', 'Блог'),
              ('kb', 'База знаний'), ('trust', 'О сервисе и отзывы'), ('legal', 'Документы'), ('service', 'Служебные')]
    out = []
    for key, name in groups:
        rows = []
        for p in ctx.pages:
            if p.get('section') != key:
                continue
            st = 'опубликована' if p['status'] == 'published' else 'пример'
            ready = 'есть' if p['id'] in built or p['id'] == 'home' else 'нет'
            rows.append(f'<tr><td><a class="tlink" href="{p["url"]}">{escape(p["nav"])}</a></td><td><code>{p["url"]}</code></td>'
                        f'<td>{p["type"]}</td><td><span class="chip {"chip--paid" if st == "опубликована" else "chip--soon"}">{st}</span></td><td>{ready}</td></tr>')
        out.append(f'<h2 class="h3">{name}</h2><table class="pidx"><thead><tr><th>Страница</th><th>Адрес</th><th>Тип</th><th>Статус</th><th>Собрана</th></tr></thead><tbody>{"".join(rows)}</tbody></table>')
    return f'''<section class="phero phero--text"><div class="phero__bg" aria-hidden="true"></div><div class="wrap">
<div class="phero__in"><div class="phero__txt"><p class="kicker kicker--pill phero__k"><span class="pulse" aria-hidden="true"></span>Только для студии</p>
<h1 class="phero__h">Все страницы <em class="em">сайта</em></h1>
<p class="phero__lead">Служебный список для просмотра. На сервер не попадает, поисковики его не видят.</p></div></div></div></section>
<section class="sec"><div class="wrap pidxw">{"".join(out)}</div></section>'''


def main():
    pages = json.loads((BUILD / 'pages.json').read_text(encoding='utf-8'))
    ids = [p['id'] for p in pages]
    urls = [p['url'] for p in pages]
    if len(set(ids)) != len(ids) or len(set(urls)) != len(urls):
        sys.exit('В реестре повторяются id или адреса')
    for k in ('title', 'description'):
        seen = {}
        for p in pages:
            if p[k] in seen:
                err(p['id'], f'{k} совпадает со страницей {seen[p[k]]}')
            seen[p[k]] = p['id']
    ctx = Ctx(pages)
    blocks.LINK_OK = lambda url: url not in ctx.by_url or ctx.visible(ctx.by_url[url]['id'])
    ver = versions()
    manifest_f = BUILD / '.manifest.json'
    old = set(json.loads(manifest_f.read_text())) if manifest_f.exists() else set()
    written, built, missing = set(), set(), []

    for p in pages:
        if p['type'] == 'home':
            continue
        if RELEASE and p['status'] != 'published':
            continue
        if ONLY and p['id'] not in ONLY:
            continue
        try:
            c = load_content(p['id'])
            if c is None:
                missing.append(p['id'])
                continue
            main_html, ld = templates.RENDER[p['type']](p, c, ctx)
        except Exception as e:  # одна сломанная страница не останавливает остальные
            import traceback
            tb = traceback.extract_tb(e.__traceback__)[-1]
            err(p['id'], f'{type(e).__name__}: {e} ({Path(tb.filename).name}:{tb.lineno})')
            continue
        if RELEASE:
            main_html = strip_unpublished_links(main_html, ctx)
        css = ['assets/css/main.css', 'assets/css/home.css', 'assets/css/pages.css']
        js = ['assets/js/main.js', 'assets/js/home.js', 'assets/js/pages.js']
        if p['type'] == 'tool':
            css.append('assets/css/tools.css')
        elif p['type'] == 'table':
            css.append('assets/css/tables.css')
        elif p['type'] == 'contacts':
            css.append('assets/css/contacts.css')
        elif p['type'] == 'pricing':
            css.append('assets/css/pricing.css')
            js.append('assets/js/pricing.js')
        elif p['type'] == 'article':
            css.append('assets/css/article.css')
        if p['id'] == 'instrumenty':
            css.append('assets/css/tools-hub.css')
        if p['type'] == 'feature':
            css.append('assets/css/schedule.css')
            if p['id'] == 'raspisanie':
                js.append('assets/js/schedule.js')
            else:
                css.append('assets/css/features.css')
                scene_css = 'board' if p['id'] == 'onlayn-doska' else 'people' if p['id'] in ('uchet-uchenikov', 'kabinet-uchenika', 'domashnie-zadaniya') else 'work'
                css.append(f'assets/css/feature-scene-{scene_css}.css')
                js.append('assets/js/features.js')
        html = page_html(p, main_html, ld, ctx, ver, css, js)
        html = re.sub(r'(?m)^[ \t]+$', '', html)
        check(p, html, ctx)
        rel = '404.html' if p['type'] == 'notfound' else p['url'].strip('/') + '/index.html'
        out = SITE / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding='utf-8')
        written.add(rel)
        built.add(p['id'])

    if ONLY:
        report(built, missing)
        return

    if not RELEASE:
        p = {'id': '_pages', 'url': '/_pages/', 'type': 'service', 'status': 'example', 'title': 'Все страницы сайта | TeacherDesk',
             'description': 'Служебный список страниц', 'h1': 'Все страницы', 'nav': 'Все страницы', 'section': 'service'}
        html = page_html(p, preview_index(ctx, built), [], ctx, ver,
                         ['assets/css/main.css', 'assets/css/home.css', 'assets/css/pages.css'], ['assets/js/main.js', 'assets/js/pages.js'])
        (SITE / '_pages').mkdir(exist_ok=True)
        (SITE / '_pages' / 'index.html').write_text(html, encoding='utf-8')
        written.add('_pages/index.html')

    # сгенерированные раньше файлы, которых больше нет в сборке
    for rel in sorted(old - written, key=lambda r: -r.count('/')):  # сначала вложенные, чтобы пустые папки тоже ушли
        f = SITE / rel
        if f.exists() and f.name == 'index.html':
            f.unlink()
            try:
                f.parent.rmdir()
            except OSError:
                pass
    manifest_f.write_text(json.dumps(sorted(written), ensure_ascii=False, indent=0))

    urls = [p for p in pages if p['status'] == 'published' and p['type'] != 'notfound']
    sm = ''.join(f'<url><loc>{BASE}{p["url"]}</loc><lastmod>{modified(p["id"])}</lastmod></url>\n' for p in urls)
    (SITE / 'sitemap.xml').write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{sm}</urlset>\n', encoding='utf-8')
    # Clean-param: Яндекс не считает дублями адреса с метками рекламы и рассылок
    (SITE / 'robots.txt').write_text(f'User-agent: *\nAllow: /\nDisallow: /_pages/\n\nUser-agent: Yandex\nAllow: /\nDisallow: /_pages/\n'
                                     f'Clean-param: utm_source&utm_medium&utm_campaign&utm_content&utm_term&yclid&gclid&from\n\n'
                                     f'Sitemap: {BASE}/sitemap.xml\n', encoding='utf-8')

    report(built, missing)


def report(built, missing):
    print(f'Собрано страниц: {len(built)}' + (' (выкладка)' if RELEASE else ' (просмотр)'))
    if missing:
        print('Нет файла контента: ' + ', '.join(missing))
    for w in warns:
        print('Внимание: ' + w)
    if errors:
        print('\nОшибки сборки:')
        for e in errors:
            print('  ' + e)
        sys.exit(1)


if __name__ == '__main__':
    main()
