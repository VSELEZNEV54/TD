# -*- coding: utf-8 -*-
"""Страница контактов: опубликованные почты, справка и реквизиты сервиса."""
from html import escape
from blocks import BASE, btn, cta, ic, phero, plain, sec_head, section, typo
import previews


def render(p, c, x):
    hours = f'<p class="contact-hours">{ic("clock")}<span>Поддержка: {typo(c["hours"])}</span></p>'
    hero = phero(p, x.trail(p), c['kicker'], c['lead'],
                 actions=[btn('Написать нам', 'mailto:info@teacherdesk.ru', 'primary', 'lg'),
                          btn('Открыть базу знаний', '/baza-znanij/', 'ghost', 'lg')],
                 trust=False, after=hours)
    cards = ''.join(f'''<li data-reveal="piece" style="--i:{i}"><div class="pfc contact-card">
      <span class="pfc__ic">{ic(r['icon'], 'ic ic--20')}</span>
      <h3 class="pfc__t">{typo(r['title'])}</h3><p class="pfc__d">{typo(r['desc'])}</p>
      <a class="contact-card__mail tlink" href="mailto:{escape(r['email'], quote=True)}">{r['email']}{ic('arrow', 'ic ic--12')}</a>
    </div></li>''' for i, r in enumerate(c['routes']))
    out = [hero, section(sec_head('Контакты', c['routes_h2'], c['routes_lead'], 'h-contact-routes') +
                         f'<ul class="pfcs">{cards}</ul>', 'sec--tint', 'h-contact-routes')]
    help_cards = previews.cards(x.reg, c['help_pages'], x.visible, desc=c['help_desc'])
    if help_cards:
        out.append(section(sec_head('Помощь', c['help_h2'], c['help_lead'], 'h-contact-help', 'q') + help_cards,
                           label='h-contact-help'))
    company_rows = ''.join(f'<div><dt>{typo(k)}</dt><dd>{typo(v)}</dd></div>' for k, v in c['company'])
    company = f'''<div class="contact-company">
      <dl class="contact-company__facts">{company_rows}</dl>
      <div class="contact-company__more"><p>{typo(c['company_note'])}</p>
      <div class="contact-company__actions">{btn('Все реквизиты', '/requisites/', 'ghost')}{btn('Документы сервиса', '/terms/', 'ghost')}</div></div>
    </div>'''
    out.append(section(sec_head('О сервисе', c['company_h2'], c['company_lead'], 'h-contact-company') + company,
                       'sec--tint', 'h-contact-company'))
    out.append(cta('Попробуйте TeacherDesk на своих учениках', ('Возможности платформы', '/features/')))
    ld = {'@type': 'ContactPage', 'name': plain(p['h1']), 'url': BASE + p['url'],
          'about': {'@id': BASE + '/#org'},
          'mainEntity': {'@type': 'Organization', '@id': BASE + '/#org', 'name': 'TeacherDesk',
                         'contactPoint': [{'@type': 'ContactPoint', 'contactType': r['title'], 'email': r['email']}
                                          for r in c['routes']]}}
    return '<div class="contact-page">' + '\n'.join(out) + '</div>', [ld]
