#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Технический SEO-аудит собранного сайта: читает готовые HTML из site/ так, как их увидит поисковик.

    python3 build/seo_audit.py                 проверить site/ (обычно после сборки --release)
    python3 build/seo_audit.py --site=путь     проверить другую папку с собранным сайтом

Проверяет мету, canonical, robots, Open Graph, заголовки, внутренние ссылки, глубину и сирот,
микроразметку JSON-LD, sitemap.xml и robots.txt, картинки и вес страниц. Ошибки - то, что мешает
индексации или ломает разметку; замечания - то, что стоит поправить. Код выхода 1, если есть ошибки."""
import gzip
import json
import re
import sys
from collections import deque
from html import unescape
from html.parser import HTMLParser
from pathlib import Path

BUILD = Path(__file__).resolve().parent
SITE = Path(next((a.split('=', 1)[1] for a in sys.argv if a.startswith('--site=')), BUILD.parent / 'site'))
BASE = 'https://teacherdesk.ru'
SKIP = {'/_pages/'}
errors, notes = [], []


def err(url, msg):
    errors.append(f'{url}: {msg}')


def note(url, msg):
    notes.append(f'{url}: {msg}')


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.meta, self.links, self.heads, self.imgs, self.ld = {}, [], [], [], []
        self.lang, self.title, self._t, self._h, self._ld, self.assets = None, '', False, None, None, []
        self.canon = None

    def handle_starttag(self, tag, a):
        a = dict(a)
        if tag == 'html':
            self.lang = a.get('lang')
        elif tag == 'title':
            self._t = True
        elif tag == 'meta':
            k = a.get('name') or a.get('property')
            if k:
                self.meta[k] = a.get('content', '')
        elif tag == 'link':
            if a.get('rel') == 'canonical':
                self.canon = a.get('href')
            elif a.get('href') and a.get('rel') in ('stylesheet', 'preload', 'icon', 'apple-touch-icon'):
                self.assets.append(a['href'])
        elif tag == 'script':
            if a.get('type') == 'application/ld+json':
                self._ld = ''
            elif a.get('src'):
                self.assets.append(a['src'])
        elif tag == 'a' and a.get('href'):
            self.links.append((a['href'], a.get('target'), a.get('rel') or ''))
        elif tag == 'img':
            self.imgs.append(a)
        elif re.fullmatch(r'h[1-6]', tag):
            self._h = [int(tag[1]), '']

    def handle_endtag(self, tag):
        if tag == 'title':
            self._t = False
        elif tag == 'script' and self._ld is not None:
            self.ld.append(self._ld)
            self._ld = None
        elif self._h and tag == f'h{self._h[0]}':
            self.heads.append((self._h[0], ' '.join(self._h[1].split())))
            self._h = None

    def handle_data(self, d):
        if self._t:
            self.title += d
        if self._ld is not None:
            self._ld += d
        if self._h:
            self._h[1] += d


def url_of(f):
    rel = f.relative_to(SITE).as_posix()
    if rel == '404.html':
        return '/404.html'
    return '/' + rel[:-len('index.html')]


def target(href):
    """Файл, который сервер отдаст по ссылке, или None."""
    path = href.split('#')[0].split('?')[0]
    if not path.startswith('/'):
        return None
    f = SITE / path.lstrip('/')
    if path.endswith('/'):
        f = f / 'index.html'
    return f


# ---------- страницы ----------
pages = {}
for f in sorted(SITE.rglob('*.html')):
    u = url_of(f)
    if any(u.startswith(s) for s in SKIP):
        continue
    p = Page()
    p.feed(f.read_text(encoding='utf-8'))
    p.file, p.size = f, f.stat().st_size
    pages[u] = p

indexable = {u for u, p in pages.items() if 'noindex' not in p.meta.get('robots', '') and u != '/404.html'}
titles, descs, h1s = {}, {}, {}
inbound = {u: 0 for u in pages}
graph = {u: set() for u in pages}

for u, p in pages.items():
    idx = u in indexable
    if p.lang != 'ru':
        err(u, f'lang="{p.lang}", нужен ru')
    t, d = p.title.strip(), p.meta.get('description', '')
    if not t:
        err(u, 'нет title')
    if not d:
        err(u, 'нет description')
    if idx:
        titles.setdefault(t, []).append(u)
        descs.setdefault(d, []).append(u)
        if p.canon != BASE + u:
            err(u, f'canonical {p.canon}, ожидался {BASE + u}')
        for k in ('og:title', 'og:description', 'og:url', 'og:image'):
            if not p.meta.get(k):
                err(u, f'нет {k}')
        if p.meta.get('og:url') and p.meta['og:url'] != BASE + u:
            err(u, f'og:url {p.meta["og:url"]} не совпадает с адресом')
        img = p.meta.get('og:image', '')
        if img.startswith(BASE) and not (SITE / img[len(BASE):].lstrip('/')).exists():
            err(u, f'нет файла картинки og:image {img}')
    if u == '/404.html' and 'noindex' not in p.meta.get('robots', ''):
        err(u, 'страница 404 без noindex')
    # заголовки
    h1 = [h for lv, h in p.heads if lv == 1]
    if len(h1) != 1:
        err(u, f'h1 на странице: {len(h1)}')
    elif idx:
        h1s.setdefault(h1[0], []).append(u)
    prev = 0
    for lv, h in p.heads:
        if prev and lv > prev + 1:
            note(u, f'пропуск уровня заголовка h{prev} -> h{lv}: «{h[:50]}»')
        prev = lv
        if not h:
            note(u, f'пустой заголовок h{lv}')
    # ссылки
    for href, tgt, rel in p.links:
        if href.startswith(('mailto:', 'tel:', '#')):
            continue
        if href.startswith(BASE):
            note(u, f'абсолютная ссылка на свой сайт {href}, лучше от корня')
            href = href[len(BASE):] or '/'
        if href.startswith('/'):
            path = href.split('#')[0].split('?')[0]
            f = target(href)
            if path.startswith('/assets/'):
                if not f or not f.exists():
                    err(u, f'нет файла {href}')
                continue
            if not path.endswith('/') and not path.endswith('.html'):
                err(u, f'ссылка без слэша в конце {href}')
            if not f or not f.exists():
                err(u, f'битая ссылка {href}')
                continue
            dest = url_of(f)
            if dest in pages and dest != u:
                if dest in graph[u]:
                    continue
                graph[u].add(dest)
                inbound[dest] += 1
                if idx and dest not in indexable and dest != '/404.html':
                    err(u, f'ссылка на закрытую от индексации страницу {dest}')
        elif href.startswith('http') and tgt == '_blank' and 'noopener' not in rel:
            note(u, f'внешняя ссылка с target=_blank без rel=noopener: {href}')
    # картинки
    for im in p.imgs:
        if 'alt' not in im:
            err(u, f'картинка без alt: {im.get("src")}')
        if not (im.get('width') and im.get('height')):
            note(u, f'картинка без width/height (сдвиг верстки): {im.get("src")}')
    # вес передачи без картинок: HTML, CSS и JS в gzip, шрифты с preload как есть (woff2 уже сжат)
    w = len(gzip.compress(p.file.read_bytes(), 6))
    for a in set(p.assets):
        f = target(a)
        if f and f.exists():
            if f.suffix in ('.css', '.js'):
                w += len(gzip.compress(f.read_bytes(), 6))
            elif f.suffix in ('.woff2', '.woff'):
                w += f.stat().st_size
    p.weight = w
    if w > 400 * 1024:
        err(u, f'вес страницы без картинок {w // 1024} КБ в gzip, бюджет ТЗ 400 КБ')

for name, seen in (('title', titles), ('description', descs), ('h1', h1s)):
    for v, us in seen.items():
        if len(us) > 1:
            err(', '.join(us), f'одинаковый {name}: «{v[:60]}»')

# ---------- глубина и сироты ----------
depth = {'/': 0}
q = deque(['/'])
while q:
    u = q.popleft()
    for v in graph.get(u, ()):
        if v not in depth:
            depth[v] = depth[u] + 1
            q.append(v)
for u in sorted(indexable):
    if u == '/':
        continue
    if u not in depth:
        err(u, 'страница недостижима по ссылкам с главной')
    elif depth[u] > 3:
        note(u, f'глубина {depth[u]} клика от главной, лучше до 3')
    if inbound.get(u, 0) == 0:
        err(u, 'сирота: на страницу никто не ссылается')
    elif inbound[u] < 3:
        note(u, f'мало входящих ссылок со страниц сайта: {inbound[u]}')

# ---------- микроразметка ----------
REQ = {
    'Organization': ['name', 'url'],
    'WebSite': ['name', 'url'],
    'WebPage': ['url', 'name', 'dateModified'],
    'BreadcrumbList': ['itemListElement'],
    'SoftwareApplication': ['name', 'applicationCategory', 'operatingSystem', 'offers'],
    'FAQPage': ['mainEntity'],
    'HowTo': ['name', 'step'],
    'ItemList': ['itemListElement'],
    'Article': ['headline', 'datePublished', 'dateModified', 'author', 'image'],
    'AboutPage': ['name', 'url'],
}
ld_types = {}
for u, p in pages.items():
    if u not in indexable:
        continue
    nodes = []
    for raw in p.ld:
        try:
            data = json.loads(raw)
        except ValueError as e:
            err(u, f'JSON-LD не разбирается: {e}')
            continue
        nodes += data.get('@graph', [data])
    types = [n.get('@type') for n in nodes]
    ld_types[u] = types
    for t in ('Organization',) + (('BreadcrumbList',) if u != '/' else ()):
        if t not in types:
            err(u, f'нет разметки {t}')
    for t in set(types):
        if types.count(t) > 1 and t not in ('Offer',):
            err(u, f'разметка {t} повторяется {types.count(t)} раза')
    for n in nodes:
        t = n.get('@type')
        for k in REQ.get(t, []):
            if not n.get(k):
                err(u, f'{t}: нет поля {k}')
        if t == 'FAQPage':
            for qa in n.get('mainEntity', []):
                if not qa.get('name') or not (qa.get('acceptedAnswer') or {}).get('text'):
                    err(u, 'FAQPage: пустой вопрос или ответ')
            vis = len(re.findall(r'<details', p.file.read_text(encoding='utf-8').split('<div class="faq"', 1)[-1].split('</section>', 1)[0]))
            if vis and vis != len(n.get('mainEntity', [])):
                err(u, f'FAQPage: в разметке {len(n.get("mainEntity", []))} вопросов, на странице {vis}')
        if t == 'BreadcrumbList':
            items = n.get('itemListElement', [])
            if [i.get('position') for i in items] != list(range(1, len(items) + 1)):
                err(u, 'BreadcrumbList: позиции не по порядку')
            if items and items[-1].get('item') != BASE + u:
                err(u, 'BreadcrumbList: последняя крошка не текущая страница')
            for i in items:
                it = i.get('item', '')
                if it.startswith(BASE) and not (target(it[len(BASE):] or '/') or Path('-')).exists():
                    err(u, f'BreadcrumbList: нет страницы {it}')
        if t == 'SoftwareApplication':
            for o in n.get('offers') or []:
                if not (o.get('price') is not None and o.get('priceCurrency')):
                    err(u, 'Offer без цены или валюты')
        if t == 'Article' and len(n.get('headline', '')) > 110:
            note(u, 'Article: headline длиннее 110 знаков')
        if t == 'ItemList':
            for i in n.get('itemListElement', []):
                it = i.get('url', '')
                if it.startswith(BASE) and it[len(BASE):] not in indexable:
                    err(u, f'ItemList ведет на неопубликованную страницу {it}')

# ---------- sitemap и robots ----------
sm = SITE / 'sitemap.xml'
if not sm.exists():
    err('/sitemap.xml', 'нет файла')
else:
    s = sm.read_text(encoding='utf-8')
    locs = re.findall(r'<loc>(.*?)</loc>', s)
    mods = re.findall(r'<lastmod>(.*?)</lastmod>', s)
    in_sm = set()
    for loc in locs:
        u = loc[len(BASE):] if loc.startswith(BASE) else loc
        in_sm.add(u)
        if u not in pages:
            err('/sitemap.xml', f'адрес без страницы {loc}')
        elif u not in indexable:
            err('/sitemap.xml', f'в карте закрытая от индексации страница {loc}')
    for u in sorted(indexable - in_sm):
        err('/sitemap.xml', f'нет страницы {u}')
    if len(mods) != len(locs) or any(not re.fullmatch(r'\d{4}-\d{2}-\d{2}', m) for m in mods):
        err('/sitemap.xml', 'lastmod не у всех адресов или не в формате ГГГГ-ММ-ДД')
rb = SITE / 'robots.txt'
if not rb.exists():
    err('/robots.txt', 'нет файла')
else:
    r = rb.read_text(encoding='utf-8')
    if f'Sitemap: {BASE}/sitemap.xml' not in r:
        err('/robots.txt', 'нет строки Sitemap')
    if re.search(r'^Disallow:\s*/\s*$', r, re.M):
        err('/robots.txt', 'Disallow: / закрывает весь сайт')

# ---------- отчет ----------
print(f'Страниц: {len(pages)}, открыто для индексации: {len(indexable)}, в sitemap: {len(locs) if sm.exists() else 0}')
deep = max((depth.get(u, 99) for u in indexable), default=0)
print(f'Максимальная глубина от главной: {deep}, минимум входящих ссылок: {min((inbound[u] for u in indexable if u != "/"), default=0)}')
heavy = sorted(((p.weight, u) for u, p in pages.items() if u in indexable), reverse=True)[:3]
print('Самые тяжелые без картинок (gzip, со шрифтами): ' + ', '.join(f'{u} {w // 1024} КБ' for w, u in heavy))
if notes:
    print(f'\nЗамечания ({len(notes)}):')
    for n in notes:
        print('  ' + n)
if errors:
    print(f'\nОшибки ({len(errors)}):')
    for e in errors:
        print('  ' + e)
    sys.exit(1)
print('\nОшибок нет')
