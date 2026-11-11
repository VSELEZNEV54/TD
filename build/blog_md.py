# -*- coding: utf-8 -*-
"""Статьи контент-завода: один файл blog/stati/<slug>.md = запись реестра + контент статьи.

Шапка файла между строками --- (ключ: значение), дальше текст в Markdown:
## Заголовок {#id}, ### подзаголовок, абзацы, списки - и 1., > цитата, таблицы |...|,
**жирный**, [текст](/адрес/), [[promo:id]] на отдельной строке.

Статус в шапке: draft (черновик), approved (одобрена), hold (отложена). На сайт статья
выходит сама, когда она одобрена, дата выхода наступила и лежат три картинки. Остальные
собираются для просмотра у студии с noindex, как страницы-примеры.
"""
import datetime
import re
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATI = ROOT / 'blog' / 'stati'
IMG = ROOT / 'site' / 'assets' / 'img' / 'blog'
MSK = datetime.timezone(datetime.timedelta(hours=3))
IMAGES = ('cover', '1', '2')
REQUIRED = ('id', 'status', 'date', 'links', 'rubric', 'icon', 'nav', 'card', 'query', 'title', 'description', 'h1', 'lead')
MONTHS = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']

CONTENT, MODIFIED = {}, {}


def today(argv=()):
    """Сегодня по Москве; --date=ГГГГ-ММ-ДД показывает сайт на другой день."""
    for a in argv:
        if a.startswith('--date='):
            return datetime.date.fromisoformat(a.split('=', 1)[1])
    return datetime.datetime.now(MSK).date()


def split(text):
    m = re.match(r'---\n(.*?)\n---\n(.*)', text.replace('\r\n', '\n'), re.S)
    if not m:
        raise ValueError('нет шапки между строками ---')
    head = {}
    for line in m.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        k, sep, v = line.partition(':')
        if not sep:
            raise ValueError(f'строка шапки без двоеточия: {line[:40]}')
        head[k.strip()] = v.strip()
    return head, m.group(2)


def inline(t):
    t = escape(t, quote=False)
    t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
    # внутренние ссылки всегда с data-opt: в выкладке ссылка на невышедшую страницу станет текстом
    t = re.sub(r'\[([^\]]+)\]\((/[^)\s]*)\)', r'<a href="\2" data-opt>\1</a>', t)
    t = re.sub(r'\[([^\]]+)\]\((https?://[^)\s]+)\)', r'<a href="\2" rel="nofollow noopener" target="_blank">\1</a>', t)
    return t


def table(rows):
    cells = [[c.strip() for c in r.strip().strip('|').split('|')] for r in rows]
    head, body = cells[0], [r for r in cells[2:]] if len(cells) > 2 and set(''.join(cells[1])) <= set('-: ') else cells[1:]
    th = ''.join(f'<th>{inline(c)}</th>' for c in head)
    tb = ''.join('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in r) + '</tr>' for r in body)
    return f'<div class="tbl"><table>\n<thead><tr>{th}</tr></thead>\n<tbody>{tb}</tbody></table></div>'


def blocks_html(lines):
    """Тело одного раздела: абзацы, списки, цитаты, таблицы, подзаголовки, промоблоки."""
    out, buf, kind = [], [], None

    def flush():
        nonlocal buf, kind
        if not buf:
            return
        if kind == 'p':
            out.append(f'<p>{inline(" ".join(buf))}</p>')
        elif kind in ('ul', 'ol'):
            out.append(f'<{kind}>\n' + '\n'.join(f'<li>{inline(i)}</li>' for i in buf) + f'\n</{kind}>')
        elif kind == 'q':
            out.append(f'<blockquote>{inline(" ".join(buf))}</blockquote>')
        elif kind == 't':
            out.append(table(buf))
        buf, kind = [], None

    for raw in lines:
        s = raw.strip()
        if not s:
            flush()
            continue
        if s.startswith('### '):
            flush()
            out.append(f'<h3>{inline(s[4:])}</h3>')
            continue
        if re.fullmatch(r'\[\[promo:[\w-]+\]\]', s):
            flush()
            out.append(s)
            continue
        m_ul, m_ol = re.match(r'[-*] (.+)', s), re.match(r'\d+[.)] (.+)', s)
        k = 'ul' if m_ul else 'ol' if m_ol else 'q' if s.startswith('>') else 't' if s.startswith('|') else 'p'
        if k != kind:
            flush()
            kind = k
        if k in ('ul', 'ol'):
            buf.append((m_ul or m_ol).group(1))
        elif k == 'q':
            buf.append(s.lstrip('> ').strip())
        else:
            buf.append(s)
    flush()
    return '\n'.join(out)


def parse(path):
    """Возвращает (шапка, контент статьи в формате article_page)."""
    head, body = split(Path(path).read_text(encoding='utf-8'))
    secs, cur = [], None
    for line in body.splitlines():
        m = re.match(r'## (.+?)(?:\s*\{#([\w-]+)\})?\s*$', line)
        if m:
            cur = {'h2': m.group(1).strip(), 'id': m.group(2) or f's{len(secs) + 1}', 'lines': []}
            secs.append(cur)
        elif cur is not None:
            cur['lines'].append(line)
    toc = []
    for item in filter(None, (x.strip() for x in head.get('toc', '').split(';'))):
        sid, _, label = item.partition('=')
        toc.append((sid.strip(), label.strip()))
    sections = [{'h2': inline(s['h2']), 'id': s['id'], 'html': blocks_html(s['lines'])} for s in secs]
    second = None
    if head.get('cta_second') and '|' in head['cta_second']:
        a, b = head['cta_second'].split('|', 1)
        second = (a.strip(), b.strip())
    c = {'toc': toc, 'lead': head.get('lead', ''), 'author': head.get('author', 'Редакция TeacherDesk'),
         'published': head.get('date'), 'updated': head.get('updated') or head.get('date'),
         'sections': sections, 'related': [x.strip() for x in head.get('related', '').split(',') if x.strip()],
         'cta': {'title': head.get('cta_title') or None, 'second': second},
         'links': int(head.get('links', '0') or 0), 'images': images(head), 'factory': True}
    return head, c


def images(head):
    """Картинки статьи: site/assets/img/blog/<id>/<cover|1|2>.jpg и уменьшенная копия -s.jpg."""
    pid = head.get('id', '')
    out = {}
    for n in IMAGES:
        f = IMG / pid / f'{n}.jpg'
        key = 'cover' if n == 'cover' else 'img' + n
        out[n] = {'src': f'/assets/img/blog/{pid}/{n}.jpg', 'small': f'/assets/img/blog/{pid}/{n}-s.jpg',
                  'exists': f.exists(), 'alt': head.get(key + '_alt', ''), 'caption': head.get(key + '_caption', ''),
                  'size': head.get(key + '_size', '1600x900' if n == 'cover' else '1200x800')}
    return out


def human(d):
    return f'{d.day} {MONTHS[d.month - 1]}'


def registry(argv=()):
    """Записи реестра для статей завода. Статус для сборки вычисляется по шапке, дате и картинкам."""
    if not STATI.exists():
        return [], []
    day = today(argv)
    entries, problems = [], []
    for f in sorted(STATI.glob('*.md')):
        try:
            head, c = parse(f)
        except ValueError as e:
            problems.append(f'{f.name}: {e}')
            continue
        miss = [k for k in REQUIRED if not head.get(k)]
        if miss:
            # черновик в работе: писатель еще не заполнил шапку, в сборку не берем
            problems.append(f'{f.name}: в шапке не заполнено {", ".join(miss)}')
            continue
        pid = head['id']
        if f.stem != pid:
            problems.append(f'{f.name}: имя файла не совпадает с id {pid}')
            continue
        date = datetime.date.fromisoformat(head['date'])
        imgs_ok = all(v['exists'] for v in c['images'].values())
        st = head['status']
        if st == 'approved' and date <= day and imgs_ok:
            status, note = 'published', ''
        elif st == 'approved' and not imgs_ok:
            status, note = 'example', 'Статья одобрена, но иллюстрации еще не готовы.'
            if date <= day:
                problems.append(f'{pid}: дата выхода {head["date"]} наступила, а картинок нет')
        elif st == 'approved':
            status, note = 'example', f'Статья одобрена и выйдет {human(date)}.'
        elif st == 'hold':
            status, note = 'example', 'Статья отложена редакцией.'
        else:
            status, note = 'example', 'Черновик статьи: текст еще проверяет редакция.'
        anchors = [a.strip() for a in head.get('anchors', '').split(';') if a.strip()]
        e = {'id': pid, 'url': head.get('url') or f'/blog/{pid}/', 'type': 'article', 'section': 'blog', 'status': status,
             'nav': head['nav'], 'icon': head['icon'], 'rubric': head['rubric'], 'card': head['card'],
             'title': head['title'], 'description': head['description'], 'h1': head['h1'], 'query': head['query'],
             'anchors': anchors or [head['query']], 'date': head['date'], '_note': note, '_factory': True}
        if imgs_ok:
            e['og'] = f'blog/{pid}/og.jpg' if (IMG / pid / 'og.jpg').exists() else 'og-home.jpg'
        entries.append(e)
        CONTENT[pid] = c
        MODIFIED[pid] = c['updated']
    # новые статьи в хабе и в «Читайте также» идут первыми, свежие сверху
    entries.sort(key=lambda e: e['date'], reverse=True)
    return entries, problems
