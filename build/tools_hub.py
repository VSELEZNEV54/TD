# -*- coding: utf-8 -*-
"""Одна сетка инструментов и переходы к возможностям платформы."""
from blocks import BASE, FEATURES, cta, feature_cards, ic, phero, sec_head, section, typo
import previews


CATALOG = [
    ('kalkulyator', 'Калькулятор дохода', 'Бесплатно, без регистрации',
     'Доход за месяц и ставка под вашу нагрузку', 'kalkulyator'),
    ('dogovor', 'Генератор договора', 'Бесплатно, без регистрации',
     'Данные сторон, условия занятий и файл DOCX', 'dogovor'),
    ('tablica-ucheta', 'Таблица учета', '14 дней в TeacherDesk',
     'Ученики, занятия, оплаты и баланс в платформе', 'tablica-ucheta'),
    ('shablon-raspisaniya', 'Таблица расписания', '14 дней в TeacherDesk',
     'Неделя, месяц, повторы и переносы в календаре', 'shablon-raspisaniya'),
    ('ii-assistent', 'ИИ-помощник', '14 дней в TeacherDesk',
     'План урока и задания в личном кабинете', 'plan-uroka'),
]


def catalog(x):
    cards = []
    for pid, title, tag, desc, preview_id in CATALOG:
        if not x.visible(pid):
            continue
        visual = previews.preview(preview_id, x.reg, x.visible)
        cards.append(f'''<li data-reveal="piece" style="--i:{len(cards)}"><a class="ftc" href="{x.reg[pid]['url']}">
          <span class="ftc__pic" aria-hidden="true">{visual}</span>
          <span class="ftc__tag">{typo(tag)}</span><h3 class="ftc__t">{typo(title)}</h3>
          <span class="ftc__d">{typo(desc)}</span><span class="ftc__go" aria-hidden="true">{ic('arrow')}</span>
        </a></li>''')
    return '<ul class="ftools ftools--hub tools-catalog">' + ''.join(cards) + '</ul>'


def render(p, c, x):
    out = [phero(p, x.trail(p), c['kicker'], c['lead'], actions=[], trust=c['trust'])]
    out.append(section('<h2 class="vh" id="h-tools-list">Инструменты для репетитора</h2>' + catalog(x), label='h-tools-list'))
    service = c['service']
    out.append(section(sec_head(service['kicker'], service['h2'], service['lead'], 'h-tools-service', 'sq') +
                       f'<div class="prose tools-service__copy">{typo(service["html"])}</div>', label='h-tools-service'))
    out.append(feature_cards(x.reg, FEATURES, x.visible,
                             'Все возможности TeacherDesk', 'Возможности платформы',
                             'Выберите задачу и посмотрите, как она устроена в одном кабинете.',
                             'h-tools-features', ('Все возможности', '/features/')))
    out.append(cta(c['cta']['title'], c['cta'].get('second')))
    from templates import seo_of
    out.append(seo_of(c, p, x))
    shown = [it for it in CATALOG if x.visible(it[0])]
    items = [{'@type': 'ListItem', 'position': i + 1, 'url': BASE + x.reg[pid]['url'], 'name': title}
             for i, (pid, title, _, _, _) in enumerate(shown)]
    return '\n'.join(out), [{'@type': 'ItemList', 'name': 'Инструменты для репетитора', 'itemListElement': items}]
