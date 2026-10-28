#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Обновляет на главной (site/index.html) то, что должно совпадать с внутренними страницами:
шапку, подвал, блок тарифов, общее окно вопроса и консультации, JSON-LD (тарифы и FAQ из видимых вопросов),
SEO-текст с «Часто ищут» перед подвалом и версии общих CSS и JS.

    python3 build/sync_home.py

Главную пока правят вручную, поэтому скрипт меняет только эти куски между метками
и ничего больше не трогает. Запускать, когда меняется реестр страниц или блок тарифов."""
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

BUILD = Path(__file__).resolve().parent
SITE = BUILD.parent / 'site'
sys.path.insert(0, str(BUILD))
import blocks  # noqa: E402
import templates  # noqa: E402
import stories  # noqa: E402
import sections as S  # noqa: E402
import previews  # noqa: E402
from blocks import plain  # noqa: E402


def swap(html, start, end, new, name):
    a = html.find(start)
    if a < 0:
        sys.exit(f'Не нашел начало блока «{name}»')
    b = html.find(end, a)
    if b < 0:
        sys.exit(f'Не нашел конец блока «{name}»')
    return html[:a] + new + html[b:]


def release_cleanup(html, reg, visible):
    """Выкладка: на главной не остается ссылок на неопубликованные страницы (ТЗ, раздел 11).
    Карточку инструмента или статьи заменяем следующей опубликованной той же разметки, кнопку убираем,
    ссылку «подробнее» убираем, остальные ссылки становятся текстом."""
    from blocks import ic, typo
    import previews
    hidden = {p['url'] for p in reg.values() if not visible(p['id'])}
    shown = set(re.findall(r'<a class="(?:ftc|pcard)" href="([^"]+)"', html))
    spare = {'ftc': [p for p in reg.values() if p['type'] == 'tool' and visible(p['id']) and p['url'] not in shown],
             'pcard': [p for p in reg.values() if p['type'] == 'article' and visible(p['id']) and p['url'] not in shown]}

    def card(kind, q, n):
        if kind == 'ftc':
            return f'''<li data-reveal="piece"><a class="ftc" href="{q["url"]}">
        <span class="ftc__pic" aria-hidden="true">{getattr(previews, "TOOL_PREVIEW", {}).get(q["id"], "")}</span>
        <span class="ftc__tag">{typo(q.get("tag", ""))}</span>
        <h3 class="ftc__t">{typo(q["nav"])}</h3>
        <span class="ftc__d">{typo(q.get("card", ""))}</span>
        <span class="ftc__go" aria-hidden="true">{ic("arrow")}</span>
      </a></li>'''
        return f'''<li data-reveal="piece"><a class="pcard" href="{q["url"]}">
        <span class="pcard__pic pc--{n}" aria-hidden="true"><i class="pcard__a"></i><i class="pcard__b"></i><span class="pcard__ic">{ic(q["icon"])}</span></span>
        <span class="pcard__cat">{typo(q.get("rubric", ""))}</span>
        <h3 class="pcard__t">{typo(q["h1"])}</h3>
      </a></li>'''

    def swap_card(m):
        kind, url = m.group(1), m.group(2)
        if url not in hidden:
            return m.group(0)
        if not spare[kind]:
            return ''
        n = re.search(r'pc--(\d)', m.group(0))
        return card(kind, spare[kind].pop(0), n.group(1) if n else 1)
    html = re.sub(r'<li data-reveal="piece"><a class="(ftc|pcard)" href="([^"]+)">.*?</a></li>', swap_card, html, flags=re.S)
    off = lambda m: m.group(2).split('#')[0] in hidden  # noqa: E731
    html = re.sub(r'<a class="(btn[^"]*)"[^>]*? href="([^"]+)"[^>]*>.*?</a>', lambda m: '' if off(m) else m.group(0), html, flags=re.S)
    html = re.sub(r' ?<a class="(tlink)" href="([^"]+)"[^>]*>.*?</a>', lambda m: '' if off(m) else m.group(0), html, flags=re.S)
    html = re.sub(r'<a ()[^>]*?href="([^"]+)"[^>]*>(.*?)</a>', lambda m: m.group(3) if off(m) else m.group(0), html, flags=re.S)
    return re.sub(r'<p class="[^"]*"(?: data-reveal)?>\s*</p>\n?', '', html)


def main():
    pages = json.loads((BUILD / 'pages.json').read_text(encoding='utf-8'))
    reg = {p['id']: p for p in pages}
    release = '--release' in sys.argv
    visible = (lambda pid: pid in reg and (reg[pid]['status'] == 'published' or not release))
    by_url = {p['url']: p for p in pages}
    blocks.LINK_OK = lambda url: url not in by_url or visible(by_url[url]['id'])
    f = SITE / 'index.html'
    html = f.read_text(encoding='utf-8')

    html = swap(html, '<header class="hdr" data-hdr>', '\n\n<main', blocks.header(reg['home'], reg, visible) + '\n', 'шапка')
    end = html.index('</footer>', html.index('<footer class="ftr">')) + len('</footer>')
    html = html[:html.index('<footer class="ftr">')] + blocks.footer(reg, visible) + html[end:]
    html = swap(html, '<!-- 7. Отзывы', '<!-- 8.', stories.block(comment=True) + '\n\n', 'истории')
    html = swap(html, '<!-- 8. Тарифы', '<!-- 9.', '<!-- 8. Тарифы: пробный период, Pro и Premium, ползунок «сколько учеников» -->\n' +
                templates.pricing_block() + '\n\n', 'тарифы')
    tools = previews.cards(reg, templates.TOOLS, visible, 'ftools ftools--free')
    tools = '''<!-- 9. Бесплатные инструменты -->
<section class="sec" id="instrumenty" aria-labelledby="h-free"><div class="wrap">
  <header class="res__head"><div><p class="kicker" data-reveal><i class="geo geo--q" aria-hidden="true"></i>Бесплатные инструменты</p>
    <h2 class="h2 h2--sm" id="h-free" data-reveal>Рассчитайте доход и подготовьте <em class="em">договор</em></h2></div>
    <a class="btn btn--ghost btn--sm" data-reveal href="/instrumenty/"><span>Все инструменты</span></a></header>
  ''' + tools + '\n</div></section>\n\n'
    html = swap(html, '<!-- 9. Бесплатные инструменты', '<!-- 10.', tools, 'инструменты')
    # Одна форма для главной и внутренних страниц: правки не теряются при следующей сборке.
    ask = (BUILD / 'partials' / 'ask.html').read_text(encoding='utf-8').rstrip()
    html, replaced = re.subn(r'<dialog\b[^>]*\bid="ask"[^>]*>.*?</dialog>', lambda m: ask, html, count=1, flags=re.S)
    if replaced != 1:
        sys.exit('Не нашел общее окно вопроса на главной')
    html = re.sub(r'<!-- Окно «Задать свой вопрос».*?-->', '<!-- Общее окно вопроса и консультации: build/partials/ask.html -->', html, count=1, flags=re.S)
    # чекбокс рассылки: ссылка на согласие, пока документ виден (в выкладке до публикации просто текст)
    doc = ('<a class="tlink" href="/marketing-consent/" target="_blank" rel="noopener" data-opt>согласие на&nbsp;рассылку</a>'
           if visible('marketing') else 'согласие на&nbsp;рассылку')
    html = re.sub(r'(<label class="ask__ok ask__ok--news">.*?\()(.*?)(\)</span></label>)', lambda m: m.group(1) + doc + m.group(3), html, flags=re.S)

    # SEO-текст и «Часто ищут» в конце главной, перед подвалом. Текст в build/content/home.py
    hc = BUILD / 'content' / 'home.py'
    if hc.exists():
        spec = importlib.util.spec_from_file_location('c_home', hc)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        c = mod.PAGE
        seo = '<!-- 12b. SEO-текст и «Часто ищут» (build/content/home.py, обновляет sync_home.py) -->\n' + \
              S.seo_text(c['seo'], templates.seo_tags(reg['home'], c, visible, reg)) + '\n\n'
        mark = '<!-- 12b. SEO-текст'
        if mark in html:
            html = swap(html, mark, '</main>', seo, 'SEO-текст')
        else:
            html = html.replace('</main>', seo + '</main>', 1)

    # иконка сайта в PNG для выдачи Яндекса и экрана «Домой» на iPhone
    if 'favicon-120.png' not in html:
        html = re.sub(r'(<link rel="icon" href="/?assets/img/favicon\.svg" type="image/svg\+xml">)',
                      lambda m: m.group(1) + '\n<link rel="icon" href="/assets/img/favicon-120.png" type="image/png" sizes="120x120">'
                      '\n<link rel="apple-touch-icon" href="/assets/img/apple-touch-icon.png">', html, count=1)

    # иконки: в спрайт главной добавляем символы, которых в нем нет (шапка и подвал берут их из общего спрайта)
    a = html.find('<svg xmlns="http://www.w3.org/2000/svg" style="display:none"')
    if a > -1:
        b = html.index('</svg>', a)
        have = set(re.findall(r'<symbol id="([^"]+)"', html[a:b]))
        common = (BUILD / 'partials' / 'sprite.svg').read_text(encoding='utf-8')
        extra = [m.group(0) for m in re.finditer(r'<symbol id="([^"]+)".*?</symbol>', common, re.S) if m.group(1) not in have]
        if extra:
            html = html[:b] + '\n'.join(extra) + '\n' + html[b:]

    # JSON-LD: тарифы из шаблона, вопросы из видимого FAQ
    m = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    ld = json.loads(m.group(1))
    faq = html[html.index('<div class="faq"'):html.index('data-ask-open')]
    qa = re.findall(r'<summary>(.*?)<span class="faq__x".*?<div class="faq__a">(.*?)</div></details>', faq, re.S)
    for node in ld['@graph']:
        if node.get('@type') == 'SoftwareApplication':
            node['offers'] = templates.OFFERS
            node['operatingSystem'] = 'Web, iOS, Android'
            node['applicationSubCategory'] = 'CRM для репетиторов'
            node['featureList'] = [reg[i]['nav'] + ': ' + reg[i]['card'] for i in templates.FEATURES if reg[i].get('card') and visible(i)]
        if node.get('@type') == 'FAQPage':
            node['mainEntity'] = [{"@type": "Question", "name": plain(q), "acceptedAnswer": {"@type": "Answer", "text": plain(a)}} for q, a in qa]
    html = html[:m.start(1)] + json.dumps(ld, ensure_ascii=False, separators=(',', ':')) + html[m.end(1):]

    if release:
        html = release_cleanup(html, reg, visible)

    # версии общих файлов, чтобы браузер не взял старые стили из кэша
    for a in ('assets/css/main.css', 'assets/css/home.css', 'assets/js/main.js', 'assets/js/home.js'):
        v = hashlib.md5((SITE / a).read_bytes()).hexdigest()[:8]
        html = re.sub(r'(["\'])' + re.escape(a) + r'(\?v=[0-9a-f]+)?\1', lambda m: m.group(1) + a + '?v=' + v + m.group(1), html)

    f.write_text(html, encoding='utf-8')
    print(f'Главная обновлена: шапка, подвал, тарифы, JSON-LD ({len(qa)} вопросов)')


if __name__ == '__main__':
    main()
