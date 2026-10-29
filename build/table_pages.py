# -*- coding: utf-8 -*-
"""Посадочные таблицы учета и расписания: интерфейс платформы и сравнение способов работы."""
from blocks import REG, btn, phero, sec_head, section, typo, steps, faq, cta
import demos
import product
import sections


def interface(d):
    cards = []
    for it in d['items']:
        cards.append(f'''<article class="cell pcell" data-reveal>
          <div class="pcell__txt"><h3 class="pfc__t">{typo(it['title'])}</h3>
            <p class="pfc__d">{typo(it['text'])}</p>
            {btn(it['link'][0], it['link'][1], 'ghost', 'sm')}
          </div><div class="pcell__demo">{demos.get(it['demo'])}</div>
        </article>''')
    return section(sec_head('Интерфейс TeacherDesk', d['h2'], d['lead'], 'h-table-interface', 'sq') +
                   '<div class="pcells table-showcases">' + ''.join(cards) + '</div>', 'sec--tint', 'h-table-interface')


def render(p, c, x):
    h = c['hero']
    actions = [btn('Попробовать бесплатно', REG, 'primary', 'lg'),
               btn('Посмотреть интерфейс', '#h-table-interface', 'ghost', 'lg')]
    out = [phero(p, x.trail(p), h['kicker'], h['lead'], demos.get(h['demo']), actions,
                 ['14 дней полного доступа', 'Без карты', 'Работает на телефоне'],
                 variant='feature', after=sections.facts(c['facts']))]
    out.append(interface(c['interface']))
    out.append(product.compare(c['compare']))
    out.append(steps(c['howto'], 'h-table-start'))
    out.append(faq(c['faq'], h2='Частые вопросы'))
    from templates import other_tools
    out.append(other_tools(p, x))
    out.append(cta(c['cta']['title'], c['cta'].get('second')))
    from templates import seo_of, app_ld
    out.append(seo_of(c, p, x))
    html = '\n'.join(out).replace('>Начать бесплатно<', '>Попробовать бесплатно<')
    return '<div class="table-page">' + html + '</div>', [app_ld(p, 'TeacherDesk: ' + p['nav'])]
