"""Сжатие CSS и JS для выкладки: убираем комментарии и лишние пробелы, код не переписываем.

Исходники остаются в site/assets/{css,js} и правятся как раньше. Рядом лежат сжатые копии
main.min.css, home.min.js и т. д., страницы подключают их. Копии пересобирают build.py
и sync_home.py вместе с версиями ?v=, так что отдельный шаг запускать не нужно.

    python3 build/minify.py   пересобрать все сжатые копии и показать экономию

JS: переносы строк сохраняются (автоматическая точка с запятой работает как в исходнике),
строки, шаблоны `...` и регулярные выражения копируются как есть.
"""
import hashlib
import re
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / 'site'


# ---------- CSS ----------

def _css_tokens(src):
    """Строки, url(...) без кавычек и комментарии отделяем от остального текста."""
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if c in '"\'':
            j = i + 1
            while j < n and src[j] != c:
                j += 2 if src[j] == '\\' else 1
            yield 'raw', src[i:j + 1]
            i = j + 1
        elif src.startswith('/*', i):
            j = src.find('*/', i + 2)
            i = n if j < 0 else j + 2
            yield 'ws', ' '
        elif c.isspace():
            j = i
            while j < n and src[j].isspace():
                j += 1
            yield 'ws', ' '
            i = j
        elif src[i:i + 4].lower() == 'url(' and src[i + 4:i + 5] not in ('"', "'"):
            j = src.find(')', i)
            j = n if j < 0 else j + 1
            yield 'raw', src[i:j]
            i = j
        else:
            j = i
            while j < n and not src[j].isspace() and src[j] not in '"\'' and not src.startswith('/*', j) \
                    and src[j:j + 4].lower() != 'url(':
                j += 1
            if j == i:  # url( с кавычкой: слово url( отдельно, строка дальше
                j = i + 4
            yield 'txt', src[i:j]
            i = j


# пробел рядом с этими знаками не нужен; двоеточие и скобки разбираем отдельно,
# плюс и минус не трогаем (в calc() пробелы вокруг них обязательны)
_CSS_BOTH = set('{};,>~')


def _css_tight(text):
    """Пробелы внутри куска без строк и комментариев."""
    text = re.sub(r'\s*([{};,>~])\s*', r'\1', text)
    text = re.sub(r':\s+', ':', text)          # после двоеточия; перед ним пробел значим (a :hover)
    text = re.sub(r'\(\s+', '(', text)
    text = re.sub(r'\s+\)', ')', text)
    text = re.sub(r'\s+!', '!', text)
    text = re.sub(r';+}', '}', text)
    return text


def minify_css(src):
    parts = []
    for kind, val in _css_tokens(src):
        parts.append((kind, val))
    out = []
    buf = ''
    for kind, val in parts:
        if kind == 'raw':
            out.append(_css_tight(buf))
            buf = ''
            out.append('\0' + val)  # метка «не трогать»
        else:
            buf += val
    out.append(_css_tight(buf))
    # склейка: пробел на стыке со строкой оставляем, только если он нужен
    res = ''
    for chunk in out:
        if chunk.startswith('\0'):
            raw = chunk[1:]
            if res.endswith(' ') and res[-2:-1] in _CSS_BOTH | {':', '('}:
                res = res[:-1]
            res += raw
        else:
            if res and chunk.startswith(' ') and (chunk[1:2] in _CSS_BOTH | {')', '!'} or res[-1:] in _CSS_BOTH | {'('}):
                chunk = chunk[1:]
            res += chunk
    return res.strip() + '\n'


# ---------- JS ----------

_ID = re.compile(r'[A-Za-z0-9_$\u0080-￿]')
_REGEX_AFTER_WORD = {'return', 'typeof', 'instanceof', 'in', 'of', 'new', 'delete', 'void', 'throw',
                     'case', 'do', 'else', 'yield', 'await'}


def _skip_string(src, i):
    q, j, n = src[i], i + 1, len(src)
    while j < n and src[j] != q:
        if src[j] == '\\':
            j += 1
        elif src[j] == '\n':
            raise ValueError('строка без закрывающей кавычки')
        j += 1
    return j + 1


def _skip_template(src, i):
    """`...${ выражение }...`: выражения проходим с учетом строк, вложенных шаблонов и скобок."""
    j, n = i + 1, len(src)
    while j < n:
        c = src[j]
        if c == '\\':
            j += 2
        elif c == '`':
            return j + 1
        elif src.startswith('${', j):
            j = _skip_expr(src, j + 2)
        else:
            j += 1
    raise ValueError('шаблон без закрывающей кавычки')


def _skip_expr(src, j):
    depth, n = 1, len(src)
    while j < n:
        c = src[j]
        if c in '"\'':
            j = _skip_string(src, j)
        elif c == '`':
            j = _skip_template(src, j)
        elif src.startswith('//', j):
            j = src.find('\n', j)
            if j < 0:
                raise ValueError('комментарий в шаблоне без конца')
        elif src.startswith('/*', j):
            j = src.index('*/', j) + 2
        elif c == '{':
            depth += 1
            j += 1
        elif c == '}':
            depth -= 1
            j += 1
            if not depth:
                return j
        else:
            j += 1
    raise ValueError('незакрытое выражение в шаблоне')


def _skip_regex(src, i):
    j, n, cls = i + 1, len(src), False
    while j < n:
        c = src[j]
        if c == '\\':
            j += 2
            continue
        if c == '\n':
            raise ValueError('регулярное выражение без конца строки')
        if c == '[':
            cls = True
        elif c == ']':
            cls = False
        elif c == '/' and not cls:
            j += 1
            while j < n and _ID.match(src[j]):
                j += 1
            return j
        j += 1
    raise ValueError('регулярное выражение без конца')


def _js_tokens(src):
    """Пары (вид, текст). Пробелы и комментарии отдаем как 'ws' с отметкой, был ли перенос строки."""
    i, n = 0, len(src)
    prev = None  # последний значимый токен: (вид, текст)
    while i < n:
        c = src[i]
        if c.isspace() or src.startswith('//', i) or src.startswith('/*', i):
            nl = False
            while i < n:
                if src[i].isspace():
                    nl = nl or src[i] == '\n'
                    i += 1
                elif src.startswith('//', i):
                    j = src.find('\n', i)
                    i = n if j < 0 else j
                elif src.startswith('/*', i):
                    j = src.find('*/', i + 2)
                    if j < 0:
                        raise ValueError('комментарий без конца')
                    nl = nl or '\n' in src[i:j]
                    i = j + 2
                else:
                    break
            yield 'ws', '\n' if nl else ' '
            continue
        if c in '"\'':
            j = _skip_string(src, i)
            tok = ('str', src[i:j])
        elif c == '`':
            j = _skip_template(src, i)
            tok = ('str', src[i:j])
        elif c == '/':
            regex = (prev is None
                     or (prev[0] == 'punct' and prev[1][-1] not in ')]}')
                     or (prev[0] == 'word' and prev[1] in _REGEX_AFTER_WORD))
            if regex:
                j = _skip_regex(src, i)
                tok = ('re', src[i:j])
            else:
                j = i + 1
                tok = ('punct', '/')
        elif _ID.match(c):
            j = i
            while j < n and (_ID.match(src[j]) or (src[j] == '.' and src[i].isdigit())):
                j += 1
            tok = ('word', src[i:j])
        else:
            j = i + 1
            tok = ('punct', c)
        prev = tok
        yield tok
        i = j


def _need_space(a, b):
    """Нужен ли пробел между концом a и началом b, чтобы токены не склеились."""
    x, y = a[-1], b[0]
    if _ID.match(x) and _ID.match(y):
        return True
    if (x, y) in (('+', '+'), ('-', '-'), ('+', '-'), ('-', '+'), ('/', '/'), ('/', '*')):
        return True
    if x.isdigit() and y == '.':
        return True
    return False


def minify_js(src):
    out = []
    pend = None  # пропущенный пробел: ' ' или '\n'
    for kind, val in _js_tokens(src):
        if kind == 'ws':
            if pend != '\n':
                pend = val
            continue
        if out:
            if pend == '\n':
                out.append('\n')
            elif pend == ' ' and _need_space(out[-1], val):
                out.append(' ')
        pend = None
        out.append(val)
    return ''.join(out).strip() + '\n'


# ---------- сжатые копии рядом с исходниками ----------

def min_path(rel):
    p = Path(rel)
    return str(p.with_name(p.stem + '.min' + p.suffix))


def asset(rel, site=SITE):
    """Пересобирает сжатую копию файла и отдает адрес для страницы: 'assets/css/main.min.css?v=1a2b3c4d'.
    Если сжать не вышло, подключаем исходник: страница работает, просто весит больше."""
    src_f = site / rel
    text = src_f.read_text(encoding='utf-8')
    try:
        small = minify_css(text) if rel.endswith('.css') else minify_js(text)
    except ValueError as e:
        print(f'  сжатие {rel} пропущено: {e}')
        return rel + '?v=' + hashlib.md5(src_f.read_bytes()).hexdigest()[:8]
    out_rel = min_path(rel)
    out_f = site / out_rel
    data = small.encode('utf-8')
    if not out_f.exists() or out_f.read_bytes() != data:
        out_f.write_bytes(data)
    return out_rel + '?v=' + hashlib.md5(data).hexdigest()[:8]


if __name__ == '__main__':
    import gzip
    for f in sorted((SITE / 'assets').glob('*/*')):
        if f.suffix not in ('.css', '.js') or f.stem.endswith('.min'):
            continue
        rel = str(f.relative_to(SITE))
        served = asset(rel).split('?')[0]
        a, b = f.read_bytes(), (SITE / served).read_bytes()
        print(f'{rel:42} {len(a):>7} -> {len(b):>7}   gzip {len(gzip.compress(a)):>6} -> {len(gzip.compress(b)):>6}')
