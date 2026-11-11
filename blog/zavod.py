#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Контент-завод блога TeacherDesk: план, черновики, проверки, картинки.

    python3 blog/zavod.py plan                 даты по графику, проверка плана, таблица плана
    python3 blog/zavod.py tablica              обновить таблицу-базу: blog/plan.md и blog/kontent-plan.xlsx
    python3 blog/zavod.py podskazki [--all]    есть ли главный запрос темы в подсказках Яндекса (поле suggest)
    python3 blog/zavod.py status               где сейчас каждая статья плана
    python3 blog/zavod.py next 5 [--json]      следующие темы, которые надо довести до выхода
    python3 blog/zavod.py new SLUG             создать blog/stati/SLUG.md с шапкой из карточки
    python3 blog/zavod.py card SLUG            карточка темы и разрешенные ссылки для писателя
    python3 blog/zavod.py lint SLUG|--all      механика статьи: шапка, объем, символы, ссылки
    python3 blog/zavod.py text SLUG            статья простым текстом для критика
    python3 blog/zavod.py titles               все статьи блога и темы плана, чтобы искать дубли
    python3 blog/zavod.py verdict SLUG         применить вердикт критика из blog/proverka/SLUG.json
    python3 blog/zavod.py prompt SLUG cover|1|2  полный промпт картинки с общим стилем
    python3 blog/zavod.py img SLUG cover|1|2 FILE  сжать и обрезать картинку в site/assets/img/blog/SLUG/
    python3 blog/zavod.py redate               переставить даты невышедших статей по графику

Python 3 без внешних библиотек. Картинки обрабатывает sips (встроен в macOS).
"""
import datetime
import json
import re
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / 'build'))
sys.path.insert(0, str(HERE))
import blog_md  # noqa: E402
import xlsx  # noqa: E402

PLAN = HERE / 'plan.json'
STATI = HERE / 'stati'
PROVERKA = HERE / 'proverka'
IMG = ROOT / 'site' / 'assets' / 'img' / 'blog'
REG = ROOT / 'build' / 'pages.json'
LINKABLE = {'product', 'feature', 'tool', 'table', 'pricing', 'hub', 'article'}
SIZES = {'cover': (1600, 900), '1': (1200, 800), '2': (1200, 800)}

STOP_BRANDS = ['miro', 'zoom', 'зум', 'skype', 'скайп', 'discord', 'дискорд', 'google meet', 'телемост', 'microsoft teams',
               'chatgpt', 'чатgpt', 'чат gpt', 'yandexgpt', 'gigachat', 'гигачат', 'deepseek', 'claude', 'gemini',
               'progressme', 'edvibe', 'meleto', 'tutoria', 'skysmart', 'скайсмарт', 'тетрика', 'фоксфорд', 'учи.ру',
               'sboard', 'edloop', 'notion', 'trello', 'amocrm', 'битрикс', 'bitrix', 'repetit.ru', 'repetitor.tech', 'edvara']
STOP_CLAIMS = [(r'premium|премиум', 'тарифа Premium нет'), (r'бесплатн\w* навсегда|free[- ]тариф', 'бесплатного тарифа навсегда нет'),
               (r'152-фз', '152-ФЗ в текстах не пишем'), (r'кабинет\w* родител', 'кабинета родителя нет'),
               (r'(teacherdesk|платформ\w*|сервис\w*)[^.]{0,80}(отчет\w* родител|пропуск\w*)', 'отчетов родителям и учета пропусков в продукте нет'),
               (r'\d[\d ]* (пользовател|репетитор\w*) уже', 'число пользователей не пишем')]
CLICHES = ['в современном мире', 'не секрет, что', 'давайте разбер', 'в этой статье мы', 'важно отметить', 'стоит отметить',
           'играет важную роль', 'на сегодняшний день', 'осуществля', 'в рамках', 'данный ', 'является ключев']
STOP = {'для', 'и', 'в', 'на', 'с', 'по', 'как', 'что', 'ли', 'за', 'к', 'о', 'а', 'не'}


# ---------- план ----------
def load_plan():
    return json.loads(PLAN.read_text(encoding='utf-8'))


def save_plan(plan):
    """Записать plan.json в компактном виде: шапка по строке на ключ, карточка в 6 строк. Так diff читается."""
    j = lambda v: json.dumps(v, ensure_ascii=False)  # noqa: E731
    line1 = ('month', 'slug', 'rubric', 'icon', 'pk', 'freq', 'suggest')
    own = set(line1) | {'sk', 'h1', 'angle', 'outline'}
    tail = ('cta', 'check', 'links', 'season')
    out = ['{']
    keys = [k for k in plan if k != 'cards']
    out += [f' {j(k)}: {j(plan[k])},' for k in keys]
    out.append(' "cards": [')
    for i, c in enumerate(plan['cards']):
        if i and c.get('month') != plan['cards'][i - 1].get('month'):
            out.append('')  # пустая строка между месяцами плана
        rest = [k for k in tail if k in c] + [k for k in c if k not in own and k not in tail]
        lines = ['  {' + ', '.join(f'{j(k)}: {j(c[k])}' for k in line1 if k in c) + ',']
        lines += [f'   {j(k)}: {j(c[k])},' for k in ('sk', 'h1', 'angle', 'outline') if k in c]
        lines.append('   ' + ', '.join(f'{j(k)}: {j(c[k])}' for k in rest) + '}' + (',' if i < len(plan['cards']) - 1 else ''))
        out += lines
    out += [' ]', '}']
    PLAN.write_text('\n'.join(out) + '\n', encoding='utf-8')


def schedule(plan):
    """Дата выхода каждой темы: по порядку, по дням недели из графика, начиная со start."""
    cfg = plan['schedule']
    d = datetime.date.fromisoformat(cfg['start'])
    days, per = set(cfg['weekdays']), cfg.get('per_day', 1)
    out, left = {}, per
    for card in plan['cards']:
        while d.weekday() not in days:
            d += datetime.timedelta(days=1)
        out[card['slug']] = d.isoformat()
        left -= 1
        if not left:
            d += datetime.timedelta(days=1)
            left = per
    return out


def card_of(plan, slug):
    c = next((c for c in plan['cards'] if c['slug'] == slug), None)
    if not c:
        sys.exit(f'Нет темы {slug} в blog/plan.json')
    return c


def links_for(plan, card):
    return plan['schedule']['links_by_month'].get(str(card['month']), 3)


def registry():
    pages = [p for p in json.loads(REG.read_text(encoding='utf-8')) if p['status'] != 'hidden']
    return {p['id']: p for p in pages}


def article_state(slug):
    f = STATI / f'{slug}.md'
    if not f.exists():
        return None, {}
    try:
        head, _ = blog_md.split(f.read_text(encoding='utf-8'))
    except ValueError:
        return 'broken', {}
    return head.get('status', 'draft'), head


def images_ready(slug):
    return all((IMG / slug / f'{n}.jpg').exists() for n in blog_md.IMAGES)


def allowed_links(plan, date):
    """Куда можно ссылаться статье с этой датой: опубликованные страницы и статьи завода, вышедшие раньше."""
    reg = registry()
    dates = schedule(plan)
    ok = {}
    for p in reg.values():
        if p['status'] == 'published' and p['type'] in LINKABLE and p['id'] not in dates:
            ok[p['url']] = p['nav']
    for c in plan['cards']:
        st, head = article_state(c['slug'])
        d = head.get('date') or dates[c['slug']]
        if st == 'approved' and d < date:
            ok[head.get('url') or f'/blog/{c["slug"]}/'] = head.get('nav') or c['h1']
    return ok


def cmd_plan(plan):
    dates = schedule(plan)
    reg = registry()
    errs = []
    slugs = [c['slug'] for c in plan['cards']]
    for s in {s for s in slugs if slugs.count(s) > 1}:
        errs.append(f'слаг повторяется: {s}')
    pks = [c['pk'] for c in plan['cards']]
    for s in {s for s in pks if pks.count(s) > 1}:
        errs.append(f'главный запрос повторяется: {s}')
    replace = set(plan.get('replace', []))
    for c in plan['cards']:
        if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', c['slug']):
            errs.append(f'{c["slug"]}: слаг только латиница через дефис')
        if c['slug'] in reg and c['slug'] not in replace:
            errs.append(f'{c["slug"]}: такая страница уже есть в реестре (добавьте в replace, если статья заменяет пример)')
        hit = next((p for p in reg.values() if p.get('query') == c['pk'] and p['id'] != c['slug']), None)
        if hit:
            errs.append(f'{c["slug"]}: запрос «{c["pk"]}» уже ведет страница {hit["url"]}')
        for l in c.get('links', []):
            if l in dates and dates[l] >= dates[c['slug']]:
                errs.append(f'{c["slug"]}: ссылка на {l}, который выйдет позже')
            elif l not in dates and l not in reg:
                errs.append(f'{c["slug"]}: ссылка на неизвестную страницу {l}')
        for k in ('month', 'slug', 'rubric', 'icon', 'pk', 'h1', 'angle', 'cta'):
            if not c.get(k):
                errs.append(f'{c.get("slug", "?")}: нет поля {k}')
    write_table(plan)
    print(f'Тем в плане: {len(plan["cards"])}, первая выходит {dates[slugs[0]]}, последняя {dates[slugs[-1]]}.')
    if errs:
        print('\nОшибки плана:\n  ' + '\n  '.join(errs))
        sys.exit(1)


def stage(slug):
    st, head = article_state(slug)
    if st is None:
        return 'нет'
    if st == 'approved':
        return 'одобрена' + ('' if images_ready(slug) else ', нет картинок')
    return {'draft': 'черновик', 'hold': 'отложена', 'broken': 'сломана шапка'}.get(st, st)


def cmd_status(plan):
    dates = schedule(plan)
    today = blog_md.today(sys.argv).isoformat()
    buf = 0
    for i, c in enumerate(plan['cards'], 1):
        s = stage(c['slug'])
        st, head = article_state(c['slug'])
        d = head.get('date') or dates[c['slug']]
        if s == 'одобрена':
            s = 'вышла' if d <= today else 'ждет даты'
            buf += d > today
        print(f'{i:>3}  {d}  {s:<22} {c["slug"]}')
    print(f'\nВ буфере (одобрены и ждут даты): {buf}')


def cmd_next(plan, n, as_json):
    dates = schedule(plan)
    tasks = []
    for c in plan['cards']:
        st, head = article_state(c['slug'])
        if st == 'approved' and images_ready(c['slug']):
            continue
        if st == 'hold':
            continue
        tasks.append({'slug': c['slug'], 'date': head.get('date') or dates[c['slug']], 'has_draft': st is not None,
                      'approved': st == 'approved', 'has_images': images_ready(c['slug']),
                      'has_verdict': (PROVERKA / f'{c["slug"]}.json').exists(), 'check': bool(c.get('check'))})
        if len(tasks) >= n:
            break
    if as_json:
        print(json.dumps(tasks, ensure_ascii=False, indent=1))
    else:
        for t in tasks:
            print(f'{t["date"]}  {t["slug"]}  черновик: {"да" if t["has_draft"] else "нет"}, одобрена: {"да" if t["approved"] else "нет"}, '
                  f'картинки: {"да" if t["has_images"] else "нет"}')


def cmd_new(plan, slug):
    c = card_of(plan, slug)
    f = STATI / f'{slug}.md'
    if f.exists():
        print(f'{f.relative_to(ROOT)} уже есть, не трогаю')
        return
    date = schedule(plan)[slug]
    head = [('id', slug), ('url', f'/blog/{slug}/'), ('status', 'draft'), ('date', date), ('links', links_for(plan, c)),
            ('rubric', c['rubric']), ('icon', c['icon']), ('query', c['pk']), ('anchors', '; '.join([c['pk']] + c.get('sk', [])[:2])),
            ('nav', ''), ('card', ''), ('title', ''), ('description', ''), ('h1', ''), ('lead', ''), ('toc', ''),
            ('cover_prompt', ''), ('cover_alt', ''), ('img1_prompt', ''), ('img1_alt', ''), ('img1_caption', ''),
            ('img2_prompt', ''), ('img2_alt', ''), ('img2_caption', ''), ('sources', '')]
    STATI.mkdir(exist_ok=True)
    f.write_text('---\n' + '\n'.join(f'{k}: {v}' for k, v in head) + '\n---\n\n', encoding='utf-8')
    print(f'Создан {f.relative_to(ROOT)}, выход {date}, ссылок можно: {links_for(plan, c)}')


def cmd_card(plan, slug):
    c = card_of(plan, slug)
    date = schedule(plan)[slug]
    n = links_for(plan, c)
    print(f'Тема №{plan["cards"].index(c) + 1}, выход {date}, месяц {c["month"]}')
    for k in ('h1', 'rubric', 'pk', 'sk', 'freq', 'angle', 'outline', 'cta', 'check', 'season', 'note'):
        if c.get(k) not in (None, '', []):
            v = c[k]
            print(f'{k}: ' + ('; '.join(v) if isinstance(v, list) else str(v)))
    if n == 0:
        print('links: 0. В тексте ни одной ссылки и ни одного [[promo:...]].')
        return
    print(f'links: {n}. От 1 до {n} ссылок, считая [[promo:id]]. Предложено планом: {", ".join(c.get("links", [])) or "нет"}')
    print('Разрешенные адреса:')
    for url, nav in sorted(allowed_links(plan, date).items()):
        print(f'  {url}  {nav}')


# ---------- таблица-база ----------
MONTHS = ['январь', 'февраль', 'март', 'апрель', 'май', 'июнь', 'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь']
DAYS = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс']
ORDER = ['вышла', 'готова', 'ждет картинок', 'на доработке', 'пишется', 'отложена', 'в плане']
FILL = {'вышла': 'done', 'готова': 'ready', 'ждет картинок': 'work', 'на доработке': 'work', 'пишется': 'work',
        'отложена': 'hold', 'ошибка в файле': 'hold', 'в плане': 'plan'}
OLD = {'published': 'опубликована', 'example': 'пример, не выпущена', 'hidden': 'скрыта'}


def words_of(slug):
    try:
        _, c = blog_md.parse(STATI / f'{slug}.md')
    except Exception:
        return None
    text = re.sub(r'<[^>]+>', ' ', ' '.join(s['html'] for s in c['sections']))
    return len(re.findall(r'[А-Яа-яA-Za-z0-9-]+', text)) or None


def card_state(slug, date, today):
    """Статус темы: в плане, пишется, на доработке, ждет картинок, готова, вышла, отложена."""
    st, head = article_state(slug)
    rounds = None
    vf = PROVERKA / f'{slug}.json'
    if vf.exists():
        try:
            rounds = json.loads(vf.read_text(encoding='utf-8')).get('round')
        except ValueError:
            pass
    if st is None:
        return 'в плане', None, rounds
    if st == 'broken':
        return 'ошибка в файле', None, rounds
    words = words_of(slug)
    if st == 'hold':
        return 'отложена', words, rounds
    if st == 'approved':
        if not images_ready(slug):
            return 'ждет картинок', words, rounds
        return ('вышла' if date <= today else 'готова'), words, rounds
    return ('на доработке' if vf.exists() else 'пишется'), words, rounds


def table_rows(plan):
    dates = schedule(plan)
    today = blog_md.today(sys.argv).isoformat()
    reg = registry()
    out = []
    for i, c in enumerate(plan['cards'], 1):
        st, head = article_state(c['slug'])
        d = head.get('date') or dates[c['slug']]
        state, words, rounds = card_state(c['slug'], d, today)
        links = []
        for l in c.get('links', []):
            links.append(f'/blog/{l}/' if l in dates else reg[l]['url'] if l in reg else l)
        cta = reg.get(c.get('cta'), {})
        out.append({'n': i, 'date': datetime.date.fromisoformat(d), 'state': state, 'card': c, 'words': words,
                    'rounds': rounds, 'links': links, 'cta': f'{cta.get("nav", c.get("cta", ""))} {cta.get("url", "")}'.strip(),
                    'n_links': links_for(plan, c), 'h1': head.get('h1') or c['h1']})
    return out, today


def old_articles(plan):
    """Статьи сайта, написанные до завода (build/content): что с ними сейчас."""
    dates = schedule(plan)
    replace = set(plan.get('replace', []))
    out = []
    for p in json.loads(REG.read_text(encoding='utf-8')):
        if p['type'] != 'article' or p['id'] in dates and p['id'] not in replace:
            continue
        nxt = f'заменяется статьей завода {datetime.date.fromisoformat(dates[p["id"]]).strftime("%d.%m.%Y")}' if p['id'] in replace and p['id'] in dates else ''
        out.append({'url': p['url'], 'h1': p.get('h1', ''), 'query': p.get('query', ''), 'state': OLD.get(p['status'], p['status']), 'next': nxt})
    return out


def write_table(plan):
    rows, today = table_rows(plan)
    old = old_articles(plan)
    td = datetime.date.fromisoformat(today)
    month = lambda d: f'{MONTHS[d.month - 1]} {d.year}'  # noqa: E731
    counts = {s: sum(r['state'] == s for r in rows) for s in ORDER + ['ошибка в файле']}
    months = []
    for r in rows:
        m = month(r['date'])
        if not months or months[-1][0] != m:
            months.append([m, 0, 0, 0, 0, 0])
        mm = months[-1]
        mm[1] += 1
        k = {'вышла': 2, 'готова': 3, 'в плане': 5}.get(r['state'], 4)
        mm[k] += 1
    rubrics = {}
    for r in rows:
        rubrics[r['card']['rubric']] = rubrics.get(r['card']['rubric'], 0) + 1
    first, last = rows[0]['date'].strftime('%d.%m.%Y'), rows[-1]['date'].strftime('%d.%m.%Y')
    sched = plan['schedule']
    days = ', '.join(DAYS[d] for d in sched['weekdays'])
    yn = lambda v: '' if v is None else ('да' if v else 'нет')  # noqa: E731

    # Markdown: читается в редакторе и на GitHub
    md = ['# Контент-план блога TeacherDesk', '',
          f'Таблица-база всех статей блога. Статусы на {td.strftime("%d.%m.%Y")}. '
          'Собирается командой `python3 blog/zavod.py tablica` и после каждой команды завода, которая меняет статьи, '
          'из `blog/plan.json` и файлов `blog/stati/`. Руками не править: правится план или статья. '
          'Та же таблица с фильтрами и полным содержанием тем: `blog/kontent-plan.xlsx`.', '',
          f'График: с {first}, {days}, {sched.get("per_day", 1)} в день. Тем в плане: {len(rows)}, последняя выходит {last}.', '',
          'Статусы: **вышла** (дата наступила, статья в сборке сайта), **готова** (одобрена, картинки есть, ждет даты), '
          '**ждет картинок**, **на доработке** (критик вернул), **пишется**, **в плане**, **отложена** (решает владелец).', '',
          '| Статус | Статей |', '|---|---|'] + [f'| {s} | {n} |' for s, n in counts.items() if n] + [
          '', '| Месяц | Всего | Вышло | Готово | В работе | В плане |', '|---|---|---|---|---|---|'] + [
          f'| {m[0]} | {m[1]} | {m[2]} | {m[3]} | {m[4]} | {m[5]} |' for m in months] + [
          '', '## План', '',
          '| № | Дата | Статус | Тема | Рубрика | Главный запрос | Вордстат | Ссылки | Проверка | Адрес |',
          '|---|---|---|---|---|---|---|---|---|---|']
    for r in rows:
        c = r['card']
        md.append(f'| {r["n"]} | {DAYS[r["date"].weekday()]} {r["date"].strftime("%d.%m.%Y")} | {r["state"]} | {r["h1"]} | {c["rubric"]} | '
                  f'{c["pk"]} | {"" if c.get("freq") is None else c["freq"]} | {r["n_links"]} | {"да" if c.get("check") else ""} | '
                  f'`/blog/{c["slug"]}/` |')
    md += ['', '## Статьи сайта до завода', '', 'Написаны раньше в `build/content/`. Новые статьи с теми же адресами их заменяют.', '',
           '| Адрес | Тема | Главный запрос | Статус | Что дальше |', '|---|---|---|---|---|']
    md += [f'| `{o["url"]}` | {o["h1"]} | {o["query"]} | {o["state"]} | {o["next"]} |' for o in old]
    (HERE / 'plan.md').write_text('\n'.join(md) + '\n', encoding='utf-8')

    # Excel: фильтры, закрепленная шапка, заливка статусов
    plan_rows, content_rows = [], []
    for r in rows:
        c = r['card']
        fill = FILL.get(r['state'], 'plan')
        plan_rows.append([r['n'], r['date'], DAYS[r['date'].weekday()], month(r['date']), (r['state'], fill), c['rubric'],
                          (r['h1'], 'wrap'), (c['pk'], 'wrap'), (c.get('freq'), 'num'), yn(c.get('suggest')),
                          (r['cta'], 'wrap'), 'нет' if not r['n_links'] else f'до {r["n_links"]}', 'да' if c.get('check') else '',
                          (c.get('season') or '', 'wrap'), f'/blog/{c["slug"]}/', r['words'], r['rounds']])
        outline = '\n'.join(f'{k}. {t}' for k, t in enumerate(c.get('outline', []), 1))
        content_rows.append([r['n'], r['date'], (r['state'], fill), (r['h1'], 'bold'), (c['pk'], 'wrap'),
                             ('\n'.join(c.get('sk', [])), 'wrap'), (c.get('angle', ''), 'wrap'), (outline, 'wrap'),
                             ('\n'.join(r['links']), 'wrap'), (c.get('note', ''), 'wrap')])
    summary = [[(f'Контент-план блога TeacherDesk', 'title')],
               [f'Статусы на {td.strftime("%d.%m.%Y")}. График: с {first}, {days}, {sched.get("per_day", 1)} в день, последняя тема {last}.'],
               [],
               [('Статус', 'head'), ('Статей', 'head')]] + [[(s, FILL.get(s, 'plan')), n] for s, n in counts.items() if n] + [
               [], [('Месяц', 'head'), ('Всего', 'head'), ('Вышло', 'head'), ('Готово', 'head'), ('В работе', 'head'), ('В плане', 'head')]] + [
               list(m) for m in months] + [
               [], [('Рубрика', 'head'), ('Статей', 'head')]] + [[k, v] for k, v in sorted(rubrics.items(), key=lambda x: -x[1])] + [
               [], [('Как читать', 'bold')],
               ['Вышла: дата наступила, статья одобрена и с картинками, она в сборке сайта.'],
               ['Готова: одобрена, картинки есть, выйдет сама в свою дату.'],
               ['Ждет картинок, на доработке, пишется: статья в работе у завода.'],
               ['В плане: текста еще нет. Отложена: решает владелец, в шапке статьи status: hold.'],
               ['Ссылки в тексте: первый месяц без ссылок, дальше до трех ссылок на уже вышедшие страницы.'],
               ['Вордстат: частота из семантического ядра; пусто, если запроса нет в ядре. Подсказки Яндекса: запрос есть в подсказках поиска.']]
    xlsx.write_xlsx(HERE / 'kontent-plan.xlsx', [
        {'name': 'План', 'freeze': True, 'filter': True, 'rows': plan_rows,
         'columns': [('№', 5), ('Дата', 11), ('День', 5), ('Месяц', 13), ('Статус', 14), ('Рубрика', 19), ('Тема (H1)', 58),
                     ('Главный запрос', 30), ('Вордстат', 10), ('Подсказки Яндекса', 11), ('Мост в продукт', 30),
                     ('Ссылки в тексте', 10), ('Проверка фактов', 10), ('Сезон', 34), ('Адрес', 34), ('Слов', 7), ('Кругов критика', 9)]},
        {'name': 'Содержание', 'freeze': True, 'filter': True, 'rows': content_rows,
         'columns': [('№', 5), ('Дата', 11), ('Статус', 14), ('Тема (H1)', 40), ('Главный запрос', 26), ('Доп. запросы', 30),
                     ('О чем статья', 55), ('План разделов', 55), ('Ссылки на', 28), ('Заметка автору', 45)]},
        {'name': 'Сводка', 'header': False, 'rows': summary, 'columns': [('', 26), ('', 10), ('', 10), ('', 10), ('', 10), ('', 10)]},
        {'name': 'До завода', 'freeze': True, 'filter': True,
         'rows': [[o['url'], (o['h1'], 'wrap'), (o['query'], 'wrap'), o['state'], (o['next'], 'wrap')] for o in old],
         'columns': [('Адрес', 36), ('Тема', 60), ('Главный запрос', 30), ('Статус', 20), ('Что дальше', 36)]},
    ])
    print(f'Таблица обновлена: blog/plan.md, blog/kontent-plan.xlsx ({len(rows)} тем, вышло {counts["вышла"]}, готово {counts["готова"]})')


def norm(q):
    return re.sub(r'\s+', ' ', q.lower().replace('ё', 'е')).strip()


def suggest_of(part):
    url = 'https://suggest.yandex.ru/suggest-ff.cgi?' + urllib.parse.urlencode({'part': part, 'uil': 'ru'})
    req = urllib.request.Request(url, headers={'User-Agent': 'teacherdesk-blog-plan'})
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read().decode('utf-8'))
    return [norm(x) for x in data[1]] if len(data) > 1 else []


def cmd_suggest(plan):
    """Главный запрос есть в подсказках Яндекса (те же основы слов в любом порядке): люди так ищут.
    Бесплатная замена частоты для тем вне ядра. Нет в подсказках не значит нет спроса: редкие запросы туда не попадают."""
    redo = '--all' in sys.argv
    changed = 0
    for c in plan['cards']:
        if 'suggest' in c and not redo:
            continue
        pk = norm(c['pk'])
        words = pk.split()
        roots = [w[:5] for w in words if w not in STOP and len(w) > 2]
        same = lambda x: all(any(t.startswith(r) for t in x.split()) for r in roots)  # noqa: E731
        cut = lambda w: w[:max(4, len(w) - 2)]  # noqa: E731  подсказки дополняют начало последнего слова
        sig = [w for w in words if w not in STOP and len(w) > 2]
        parts = [pk, ' '.join(words[:-1] + [cut(words[-1])])]
        if len(sig) >= 2:
            parts.append(' '.join([sig[-1]] + sig[:-2] + [cut(sig[-2])]))  # другой порядок: «репетитор налог»
        parts = list(dict.fromkeys(parts))
        found = ''
        try:
            for part in parts:
                hits = [x for x in suggest_of(part) if same(x)]
                time.sleep(1)
                if hits:
                    found = hits[0]
                    break
        except Exception as e:  # сеть: оставляем поле как было
            print(f'{c["slug"]}: подсказки не ответили ({e.__class__.__name__})')
            continue
        c['suggest'] = bool(found)
        changed += 1
        print(f'{"да " if found else "нет"}  {c["pk"]}' + (f'  [{found}]' if found and found != pk else ''))
    if changed:
        save_plan(plan)
    n = sum(1 for c in plan['cards'] if c.get('suggest'))
    print(f'Проверено: {changed}. В подсказках: {n} из {len(plan["cards"])}')


def cmd_table(plan):
    write_table(plan)


# ---------- проверки ----------


def stems(q):
    return [w[:max(4, len(w) - 2)] if len(w) > 5 else w for w in re.findall(r'[a-zа-я0-9]+', q.lower()) if w not in STOP]


def has_query(text, q):
    t = text.lower()
    return all(s in t for s in stems(q))


def body_of(path):
    head, body = blog_md.split(path.read_text(encoding='utf-8'))
    return head, body


def lint(slug, plan, quiet=False):
    f = STATI / f'{slug}.md'
    if not f.exists():
        return [f'нет файла {f.relative_to(ROOT)}'], []
    E, W = [], []
    try:
        head, body = body_of(f)
        _, c = blog_md.parse(f)
    except ValueError as e:
        return [str(e)], []
    card = next((x for x in plan['cards'] if x['slug'] == slug), None)
    for k in blog_md.REQUIRED + ('toc', 'cover_prompt', 'cover_alt', 'img1_prompt', 'img1_alt', 'img2_prompt', 'img2_alt'):
        if not head.get(k):
            E.append(f'в шапке пусто: {k}')
    if head.get('id') != slug:
        E.append('id в шапке не совпадает с именем файла')
    t, d = head.get('title', ''), head.get('description', '')
    if len(t) > 65:
        E.append(f'title {len(t)} знаков, нужно до 60')
    elif len(t) > 60:
        W.append(f'title {len(t)} знаков, лучше до 60')
    if t and not t.endswith('| TeacherDesk'):
        W.append('title без «| TeacherDesk» в конце')
    if d and not 140 <= len(d) <= 160:
        E.append(f'description {len(d)} знаков, нужно 140-160')
    if len(head.get('nav', '')) > 40:
        W.append('nav длиннее 40 знаков')
    if len(head.get('card', '')) > 60:
        W.append('card длиннее 60 знаков')
    q = head.get('query', '')
    for k in ('title', 'h1', 'description', 'lead'):
        if q and head.get(k) and not has_query(head[k], q):
            W.append(f'в {k} нет слов главного запроса «{q}»')
    secs = c['sections']
    h2s = [blog_md.inline(s['h2']) for s in secs]
    if q and not any(has_query(h, q) for h in h2s):
        W.append('главного запроса нет ни в одном ##')
    if not 4 <= len(secs) <= 10:
        E.append(f'разделов ## {len(secs)}, нужно 5-8')
    elif not 5 <= len(secs) <= 8:
        W.append(f'разделов ## {len(secs)}, норма 5-8')
    ids = [s['id'] for s in secs]
    if len(set(ids)) != len(ids):
        E.append('id разделов повторяются')
    if len(set(h2s)) != len(h2s):
        E.append('заголовки ## повторяются')
    if not secs or secs[-1]['id'] != 'korotko':
        E.append('последний раздел должен быть «## Коротко о главном {#korotko}»')
    if len(c['toc']) != 3:
        E.append('toc: нужно ровно 3 ярлыка')
    for sid, label in c['toc']:
        if sid not in ids:
            E.append(f'toc ведет на неизвестный раздел {sid}')
        if not label:
            E.append(f'toc: нет ярлыка у {sid}')
    text = re.sub(r'<[^>]+>', ' ', ' '.join(s['html'] for s in secs))
    words = len(re.findall(r'[А-Яа-яA-Za-z0-9-]+', text))
    if not 900 <= words <= 2300:
        E.append(f'объем {words} слов, нужно 1 200-1 800')
    elif not 1200 <= words <= 1800:
        W.append(f'объем {words} слов, норма 1 200-1 800')
    raw = body + ' ' + ' '.join(head.get(k, '') for k in ('title', 'description', 'h1', 'lead', 'nav', 'card', 'cover_alt',
                                                          'img1_alt', 'img2_alt', 'img1_caption', 'img2_caption'))
    for ch, name in (('ё', 'буква ё'), ('Ё', 'буква Ё'), ('—', 'длинное тире'), ('–', 'среднее тире'), ('!', 'восклицательный знак'),
                     ('₽', 'знак рубля, пишем руб.'), ('"', 'прямые кавычки, нужны «елочки»'), ('<', 'HTML в тексте')):
        if ch in raw:
            i = raw.index(ch)
            E.append(f'{name}: «{raw[max(0, i - 30):i + 10].strip()}»')
    if re.search('[\U0001F300-\U0001FAFF☀-➿]', raw):
        E.append('эмодзи в тексте')
    low = raw.lower()
    for b in STOP_BRANDS:
        if re.search(r'(?<![а-яa-z])' + re.escape(b) + r'(?![а-яa-z])', low):
            E.append(f'чужой сервис в тексте: {b}')
    for rx, why in STOP_CLAIMS:
        if re.search(rx, low):
            E.append(why)
    if 'импорт' in low:
        W.append('импорт из Excel клиент не подтвердил: пишите осторожно или уберите')
    for cl in CLICHES:
        if cl in low:
            W.append(f'штамп: «{cl.strip()}»')
    if re.search(r'[^.?!:»\n]\s+Вы\b', body):
        W.append('«Вы» с большой буквы посреди предложения')
    if re.search(r'\d\s*(рублей|руб(?!\.)|р\.)', body):
        W.append('деньги пишем «990 руб.»')
    td = body.count('TeacherDesk')
    if td == 0:
        W.append('TeacherDesk в тексте не упоминается')
    elif td > 6:
        W.append(f'TeacherDesk упомянут {td} раз, это уже реклама')
    # ссылки
    md_links = re.findall(r'\[([^\]]+)\]\(([^)\s]+)\)', body)
    promos = re.findall(r'\[\[promo:([\w-]+)\]\]', body)
    n_links = len(md_links) + len(promos)
    limit = int(head.get('links', '0') or 0)
    if limit == 0 and n_links:
        E.append(f'статья первого месяца: ссылок и промоблоков быть не должно, найдено {n_links}')
    elif n_links > limit:
        E.append(f'ссылок {n_links}, можно до {limit}')
    elif limit and not n_links:
        W.append('во втором месяце и дальше нужна хотя бы одна ссылка')
    if n_links and plan:
        ok = allowed_links(plan, head.get('date', '9999'))
        reg = registry()
        for anchor, href in md_links:
            if not href.startswith('/'):
                E.append(f'внешняя ссылка в тексте: {href}')
            elif href.split('#')[0] not in ok:
                E.append(f'ссылка на {href}: адреса нет среди вышедших к дате статьи')
            if href.split('#')[0] == head.get('url'):
                E.append('ссылка на саму себя')
            if anchor.lower() in ('здесь', 'тут', 'по ссылке', 'ссылка'):
                E.append(f'пустой анкор «{anchor}»')
        for pid in promos:
            if pid not in reg or reg[pid]['url'] not in ok:
                E.append(f'[[promo:{pid}]]: страница не опубликована или неизвестна')
    for k in ('cover_prompt', 'img1_prompt', 'img2_prompt'):
        n = len(head.get(k, '').split())
        if head.get(k) and not 15 <= n <= 80:
            W.append(f'{k}: {n} слов, норма 25-60')
        if re.search('[а-яА-Я]', head.get(k, '')):
            W.append(f'{k}: промпт лучше на английском')
    if card and head.get('date') and head['date'] != schedule(plan).get(slug):
        W.append(f'дата в шапке {head["date"]} не совпадает с планом {schedule(plan)[slug]} (python3 blog/zavod.py redate)')
    if not quiet:
        print(f'{slug}: {words} слов, разделов {len(secs)}, ссылок {n_links} из {limit}')
        for e in E:
            print('  ОШИБКА  ' + e)
        for w in W:
            print('  внимание ' + w)
        if not E:
            print('  механика в порядке')
    return E, W


def cmd_text(slug):
    f = STATI / f'{slug}.md'
    head, body = body_of(f)
    print(f'# {head.get("h1")}\n')
    for k in ('title', 'description', 'query', 'links', 'date', 'sources'):
        print(f'{k}: {head.get(k, "")}')
    print(f'\n{head.get("lead", "")}\n')
    print(body.strip())


def cmd_titles(plan):
    """Все статьи блога: вышедшие в реестре и темы плана. Для критика и планировщика: искать дубли."""
    dates = schedule(plan)
    for p in registry().values():
        if p['type'] == 'article' and p['id'] not in dates:
            st = 'вышла     ' if p['status'] == 'published' else 'пример    '
            print(f'{st}{p["url"]}  {p["h1"]}  [{p.get("query", "")}]')
    for c in plan['cards']:
        print(f'{dates[c["slug"]]}  /blog/{c["slug"]}/  {c["h1"]}  [{c["pk"]}]')


def cmd_verdict(plan, slug):
    vf = PROVERKA / f'{slug}.json'
    if not vf.exists():
        sys.exit(f'Нет вердикта {vf.relative_to(ROOT)}')
    v = json.loads(vf.read_text(encoding='utf-8'))
    E, _ = lint(slug, plan, quiet=True)
    f = STATI / f'{slug}.md'
    text = f.read_text(encoding='utf-8')
    if v.get('approved') and not E:
        new = 'approved'
    elif v.get('round', 1) >= 2:
        new = 'hold'
    else:
        print(f'{slug}: на доработку, блокеров {len(v.get("blockers", []))}, ошибок механики {len(E)}')
        return
    text = re.sub(r'(?m)^status: \w+$', f'status: {new}', text, count=1)
    f.write_text(text, encoding='utf-8')
    print(f'{slug}: статус {new}')


# ---------- картинки ----------
def cmd_prompt(plan, slug, n):
    head, _ = body_of(STATI / f'{slug}.md')
    key = 'cover_prompt' if n == 'cover' else f'img{n}_prompt'
    w, h = SIZES[n]
    print(f'{head[key].rstrip(". ")}. {plan["image_style"]}')
    print(f'\nРазмер для генерации: {w}x{h}')


def sips(*args):
    r = subprocess.run(['sips', *map(str, args)], capture_output=True, text=True)
    if r.returncode:
        sys.exit('sips: ' + r.stderr.strip())
    return r.stdout


def dims(f):
    out = sips('-g', 'pixelWidth', '-g', 'pixelHeight', f)
    mw = re.search(r'pixelWidth: (\d+)', out)
    mh = re.search(r'pixelHeight: (\d+)', out)
    if not (mw and mh):
        sys.exit(f'{f}: это не картинка. Скачайте файл заново (ссылка Figma, curl -f)')
    return int(mw.group(1)), int(mh.group(1))


def fit(src, dst, w, h, q=72):
    """Масштаб под размер с запасом, обрезка по центру, JPEG с заданным качеством.
    Больше исходника не растягиваем: если картинка меньше, уменьшаем рамку с теми же пропорциями."""
    sw, sh = dims(src)
    k = max(w / sw, h / sh)
    if k > 1:
        w, h, k = round(w / k), round(h / k), 1
    with tempfile.TemporaryDirectory() as t:
        a, b = Path(t) / 'a.png', Path(t) / 'b.png'
        sips('-s', 'format', 'png', '-z', max(h, round(sh * k)), max(w, round(sw * k)), src, '--out', a)
        sips('-c', h, w, a, '--out', b)
        sips('-s', 'format', 'jpeg', '-s', 'formatOptions', q, b, '--out', dst)
    return w, h


def cmd_img(slug, n, src):
    if n not in SIZES:
        sys.exit('Картинка: cover, 1 или 2')
    out = IMG / slug
    out.mkdir(parents=True, exist_ok=True)
    w, h = fit(src, out / f'{n}.jpg', *SIZES[n])
    fit(out / f'{n}.jpg', out / f'{n}-s.jpg', 800, round(800 * h / w), 70)
    # реальный размер в шапку статьи: шаблон ставит его в width и height, чтобы страница не прыгала
    f = STATI / f'{slug}.md'
    if f.exists():
        key = ('cover' if n == 'cover' else f'img{n}') + '_size'
        text = f.read_text(encoding='utf-8')
        line = f'{key}: {w}x{h}'
        if re.search(rf'(?m)^{key}: .*$', text):
            text = re.sub(rf'(?m)^{key}: .*$', line, text, count=1)
        else:
            text = text.replace('\n---\n', f'\n{line}\n---\n', 1)
        f.write_text(text, encoding='utf-8')
    if n == 'cover':
        fit(out / 'cover.jpg', out / 'og.jpg', 1200, 630, 78)
    sizes = ', '.join(f'{p.name} {p.stat().st_size // 1024} КБ' for p in sorted(out.glob(f'{n}*.jpg')) if p.name.startswith(n))
    print(f'{slug}/{n}: {sizes}' + (', og.jpg' if n == 'cover' else ''))


def cmd_redate(plan):
    dates = schedule(plan)
    today = blog_md.today(sys.argv).isoformat()
    for c in plan['cards']:
        f = STATI / f'{c["slug"]}.md'
        if not f.exists():
            continue
        text = f.read_text(encoding='utf-8')
        m = re.search(r'(?m)^date: (\S+)$', text)
        if m and m.group(1) <= today and 'status: approved' in text:
            continue  # вышедшие статьи не двигаем
        if m and m.group(1) != dates[c['slug']]:
            f.write_text(text.replace(m.group(0), f'date: {dates[c["slug"]]}', 1), encoding='utf-8')
            print(f'{c["slug"]}: {m.group(1)} -> {dates[c["slug"]]}')


def main():
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    if not a:
        sys.exit(__doc__)
    plan = load_plan()
    cmd = a[0]
    if cmd == 'plan':
        cmd_plan(plan)
    elif cmd == 'status':
        cmd_status(plan)
    elif cmd == 'next':
        cmd_next(plan, int(a[1]) if len(a) > 1 else 5, '--json' in sys.argv)
    elif cmd == 'new':
        cmd_new(plan, a[1])
        write_table(plan)
    elif cmd == 'card':
        cmd_card(plan, a[1])
    elif cmd == 'lint':
        slugs = [p.stem for p in sorted(STATI.glob('*.md'))] if '--all' in sys.argv else a[1:]
        bad = sum(bool(lint(s, plan)[0]) for s in slugs)
        sys.exit(1 if bad else 0)
    elif cmd == 'titles':
        cmd_titles(plan)
    elif cmd == 'text':
        cmd_text(a[1])
    elif cmd == 'verdict':
        cmd_verdict(plan, a[1])
        write_table(plan)
    elif cmd == 'prompt':
        cmd_prompt(plan, a[1], a[2])
    elif cmd == 'img':
        cmd_img(a[1], a[2], a[3])
        write_table(plan)
    elif cmd == 'redate':
        cmd_redate(plan)
        write_table(plan)
    elif cmd == 'tablica':
        cmd_table(plan)
    elif cmd == 'podskazki':
        cmd_suggest(plan)
        write_table(plan)
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
