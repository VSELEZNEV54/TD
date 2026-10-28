# -*- coding: utf-8 -*-
"""Общий шаблон статьи: широкая обложка, текст слева и содержание справа."""
from html import escape
from pathlib import Path
import re
from blocks import BASE, REG, btn, crumbs, cta, faq, ic, plain, sec_head, section, typo

SITE = Path(__file__).resolve().parent.parent / 'site'


def home_faq():
    """FAQ читается из видимого блока главной, чтобы ответы не расходились."""
    html = (SITE / 'index.html').read_text(encoding='utf-8')
    start = html.find('<div class="faq"')
    end = html.find('data-ask-open', start)
    if start < 0 or end < 0:
        raise ValueError('Не найден общий FAQ на главной')
    pairs = re.findall(r'<summary>(.*?)<span class="faq__x".*?<div class="faq__a">(.*?)</div></details>',
                       html[start:end], re.S)
    if not pairs:
        raise ValueError('Общий FAQ на главной пуст')
    return [(plain(q), a) for q, a in pairs]


def media(p, variant='inline', caption=''):
    from templates import RUBRIC_COVER
    label = escape('Иллюстрация к статье: ' + plain(p['h1']), quote=True)
    picture = f'''<div class="article-media__picture pcard__pic pc--{RUBRIC_COVER.get(p.get('rubric'), 1)}" role="img" aria-label="{label}">
      <i class="pcard__a" aria-hidden="true"></i><i class="pcard__b" aria-hidden="true"></i>
      <span class="pcard__ic" aria-hidden="true">{ic(p['icon'])}</span>
    </div>'''
    caption = f'<figcaption>{typo(caption)}</figcaption>' if caption else ''
    return f'<figure class="article-media article-media--{variant}">{picture}{caption}</figure>'


def sidebar(p, toc):
    nav = f'<nav class="art__toc" aria-label="Ключевые блоки статьи"><h2 class="art__toch">В статье</h2><ol data-toc>{toc}</ol></nav>' if toc else ''
    return f'''<aside class="article-sidebar" aria-label="Навигация и знакомство с TeacherDesk">
      {nav}
      <div class="article-sidebar__promos">
      <section class="pfc article-promo article-promo--trial" aria-labelledby="h-article-trial">
        <span class="article-promo__badge">14 дней бесплатно</span>
        <h3 class="pfc__t" id="h-article-trial">Попробуйте TeacherDesk на своих учениках</h3>
        <p class="pfc__d">Расписание, оплаты и задания в одном кабинете. Полный доступ без карты.</p>
        {btn('Попробовать бесплатно', REG, 'white')}
      </section>
      <section class="pfc article-promo article-promo--consult" aria-labelledby="h-article-consult">
        <span class="article-promo__icon" aria-hidden="true">{ic('chat', 'ic ic--20')}</span>
        <h3 class="pfc__t" id="h-article-consult">Поможем разобраться с сервисом</h3>
        <p class="pfc__d">Расскажем, как начать и перенести работу в TeacherDesk. Оставьте запрос на консультацию.</p>
        <button class="btn btn--ghost" type="button" data-ask-open data-consult-open data-source-tag="article-{escape(p['id'], quote=True)}"><span>Быстрая консультация</span></button>
      </section>
      </div>
    </aside>'''


def render(p, c, x):
    from templates import expand, post_cards
    secs = c['sections']
    # Только выбранные редактором ключевые блоки. Полный список заголовков не выводим.
    targets = {s.get('id') or 'r' + str(i + 1) for i, s in enumerate(secs)}
    entries = c.get('toc', [])[:3]
    if any(sid not in targets for sid, _ in entries):
        raise ValueError('Краткая навигация ведет к неизвестному разделу статьи')
    toc = ''.join(f'<li><a href="#{escape(sid, quote=True)}">{typo(escape(label))}</a></li>' for sid, label in entries)
    # Две иллюстрации в тексте плюс широкая обложка. Существующие тексты не меняются.
    positions = [max(0, len(secs) // 3 - 1), max(0, 2 * len(secs) // 3 - 1)]
    body = []
    for i, s in enumerate(secs):
        sid = s.get('id') or 'r' + str(i + 1)
        body.append(f'<h2 id="{sid}">{typo(s["h2"])}</h2>\n{typo(expand(s["html"], x))}')
        for pos in positions:
            if i == pos:
                body.append(media(p, caption=plain(s['h2'])))
    words = len(plain(' '.join(s['html'] for s in secs)).split())
    mins = max(3, round(words / 180))
    note = ''
    if p['status'] == 'example':
        note = f'<p class="exnote">{ic("note")}<span>Это пример страницы: текст демонстрационный, настоящая статья появится позже.</span></p>'
    head = f'''<div class="rprog" data-rprog aria-hidden="true"><i></i></div>
<article class="art article-page">
  <header class="art__head"><div class="wrap art__hw">
    {crumbs(x.trail(p))}
    <p class="art__cat"><span class="pcard__cat">{typo(p.get('rubric', ''))}</span><span>{mins}&nbsp;мин чтения</span></p>
    <h1 class="art__h">{typo(p['h1'])}</h1>
    <p class="art__lead">{typo(c['lead'])}</p>
    <p class="art__meta"><span class="av av--me" aria-hidden="true">TD</span><span><b>{typo(c.get('author', 'Редакция TeacherDesk'))}</b><small>Опубликовано <time datetime="{c['published']}">{x.date(c['published'])}</time> · обновлено <time datetime="{c.get('updated', c['published'])}">{x.date(c.get('updated', c['published']))}</time></small></span></p>
    {note}
    {media(p, 'cover')}
  </div></header>
  <div class="wrap art__in">
    {sidebar(p, toc)}
    <div class="art__body prose">{''.join(body)}</div>
  </div>
</article>'''
    out = [head]
    rel = [i for i in c.get('related', []) if i in x.reg and x.reg[i]['type'] == 'article' and i != p['id']]
    if not rel:
        rel = [i for i in x.section_ids('blog') if i != p['id'] and x.reg[i]['type'] == 'article'][:3]
    if rel:
        out.append(section(sec_head('Читайте также', 'Еще статьи для репетиторов', '', 'h-also', 'q', ('Все статьи', '/blog/')) + post_cards(rel, x), label='h-also'))
    out.append(faq(home_faq(), 'Частые вопросы'))
    cc = c.get('cta', {})
    out.append(cta(cc.get('title'), cc.get('second')))
    ld = {'@type': 'Article', 'headline': plain(p['h1']), 'description': p['description'], 'inLanguage': 'ru-RU',
          'datePublished': c['published'], 'dateModified': c.get('updated', c['published']),
          'author': {'@type': 'Organization', 'name': 'TeacherDesk'}, 'publisher': {'@id': BASE + '/#org'},
          'mainEntityOfPage': BASE + p['url'], 'image': BASE + '/assets/img/og-home.jpg'}
    return '\n'.join(out), [ld]
