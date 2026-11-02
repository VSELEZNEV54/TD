#!/usr/bin/env python3
"""Экспорт публичного site/ для просмотра на GitHub Pages.

    python3 deploy/pages.py /tmp/teacherdesk-pages --base-path /TD/

Исходный сайт не меняется. Выходная папка должна быть новой; backend и рабочие
материалы не попадают в экспорт. Проверка ссылок выполняется до публикации папки.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from html import escape, unescape
from html.parser import HTMLParser
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'
URL_ATTRS = {'href', 'xlink:href', 'src', 'action', 'data-endpoint'}
EXCLUDED_DIRS = {'_pages', 'backend', 'server', 'data', 'build', 'deploy',
                 'prototype', 'node_modules', '__pycache__'}
PUBLIC_SUFFIXES = {'.html', '.css', '.js', '.svg', '.png', '.jpg', '.jpeg',
                   '.webp', '.gif', '.avif', '.ico', '.woff', '.woff2', '.ttf',
                   '.otf', '.eot', '.txt', '.xml', '.webmanifest', '.pdf',
                   '.docx', '.xlsx', '.csv', '.mp4', '.webm', '.mp3', '.ogg'}
SECRET_NAME = re.compile(r'(?:^|[._-])(?:secrets?|credentials?|tokens?|passwords?|private)(?:[._-]|$)', re.I)
ATTR = re.compile(r'''(?P<name>[^\s<>/=]+)(?P<eq>\s*=\s*)(?:(?P<quote>["'])(?P<quoted>.*?)(?P=quote)|(?P<plain>[^\s>]+))''', re.S)
CSS_URL = re.compile(r'''url\(\s*(?:(?P<quote>["'])(?P<quoted>.*?)(?P=quote)|(?P<plain>[^)]*?))\s*\)''', re.I | re.S)
CSS_IMPORT = re.compile(r'''@import\s+(?P<quote>["'])(?P<url>.*?)(?P=quote)''', re.I | re.S)


class ExportError(ValueError):
    """Экспорт не создан, потому что путь или содержимое не прошли проверку."""


@dataclass(frozen=True)
class ExportReport:
    pages: int
    files: int
    skipped: int
    broken_paths: int = 0


def base_path(value: str) -> str:
    """Принимаем явный путь проекта, без URL, traversal и неоднозначных escape."""
    if not re.fullmatch(r'/(?:[A-Za-z0-9._~-]+/)*', value):
        raise ExportError('Префикс должен иметь вид /TD/ или /.')
    if any(part in {'.', '..'} for part in value.split('/')):
        raise ExportError('Префикс не может содержать . или ...')
    return value


def rewrite_url(value: str, prefix: str) -> str:
    """Относительные URL остаются относительными к скопированному документу."""
    text = value.strip()
    if text.startswith('/') and not text.startswith('//'):
        return prefix + text[1:]
    return value


def srcset_urls(value: str):
    """Позиции URL в srcset; запятые внутри data: URL не разделяют кандидаты."""
    pos, size = 0, len(value)
    while pos < size:
        while pos < size and (value[pos].isspace() or value[pos] == ','):
            pos += 1
        start = pos
        while pos < size and not value[pos].isspace():
            pos += 1
        end = pos
        while end > start and value[end - 1] == ',':
            end -= 1
        if end > start:
            yield start, end, value[start:end]
        if end != pos:
            continue
        # Дескрипторы 1x / 480w могут содержать скобки; URL уже прочитан.
        depth = 0
        while pos < size:
            char = value[pos]
            pos += 1
            if char == '(':
                depth += 1
            elif char == ')':
                depth = max(0, depth - 1)
            elif char == ',' and depth == 0:
                break


def _replace_ranges(text: str, replacements) -> str:
    for start, end, value in sorted(replacements, reverse=True):
        text = text[:start] + value + text[end:]
    return text


def rewrite_srcset(value: str, prefix: str) -> str:
    return _replace_ranges(value, [(start, end, rewrite_url(url, prefix))
                                   for start, end, url in srcset_urls(value)])


def css_urls(text: str):
    # Комментарии не являются запросами браузера. Сохраняем позиции символов.
    masked = re.sub(r'/\*.*?\*/', lambda m: ' ' * len(m.group()), text, flags=re.S)
    for match in CSS_URL.finditer(masked):
        group = 'quoted' if match.group('quote') else 'plain'
        start, end = match.span(group)
        yield start, end, text[start:end].strip()
    for match in CSS_IMPORT.finditer(masked):
        start, end = match.span('url')
        yield start, end, text[start:end]


def rewrite_css(text: str, prefix: str) -> str:
    return _replace_ranges(text, [(start, end, rewrite_url(url, prefix))
                                  for start, end, url in css_urls(text)])


class Markup(HTMLParser):
    """Собирает только реальные теги, не HTML-подобные строки внутри JS."""
    def __init__(self, text: str):
        super().__init__(convert_charrefs=False)
        self.text = text
        self.offsets = [0]
        self.offsets.extend(match.end() for match in re.finditer('\n', text))
        self.tags = []
        self.styles = []
        self.ids = set()
        self.in_style = False
        self.feed(text)
        self.close()

    def position_offset(self):
        line, column = self.getpos()
        return self.offsets[line - 1] + column

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append((self.position_offset(), self.get_starttag_text(), tag, attrs))
        if attrs.get('id'):
            self.ids.add(attrs['id'])
        if tag == 'a' and attrs.get('name'):
            self.ids.add(attrs['name'])
        if tag == 'style':
            self.in_style = True

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag == 'style':
            self.in_style = False

    def handle_endtag(self, tag):
        if tag == 'style':
            self.in_style = False

    def handle_data(self, data):
        if self.in_style:
            self.styles.append((self.position_offset(), data))


def rewrite_html(text: str, prefix: str) -> str:
    document = Markup(text)
    replacements = []
    head_end = None
    for start, raw, tag, attrs in document.tags:
        if tag == 'head':
            head_end = start + len(raw)
        if tag == 'meta' and (attrs.get('name') or '').lower() in {'robots', 'teacherdesk-preview'}:
            replacements.append((start, start + len(raw), ''))
            continue

        def attribute(match):
            name = match.group('name').lower()
            value = unescape(match.group('quoted') if match.group('quote') else match.group('plain'))
            if name in URL_ATTRS:
                result = rewrite_url(value, prefix)
            elif name == 'srcset':
                result = rewrite_srcset(value, prefix)
            elif name == 'style':
                result = rewrite_css(value, prefix)
            else:
                return match.group()
            if value == result:
                return match.group()
            quote = match.group('quote') or '"'
            return match.group('name') + match.group('eq') + quote + escape(result, quote=True) + quote

        changed = ATTR.sub(attribute, raw)
        if changed != raw:
            replacements.append((start, start + len(raw), changed))
    if head_end is None:
        raise ExportError('В HTML нет <head>, невозможно добавить флаг статического просмотра.')
    replacements.append((head_end, head_end, '\n<meta name="teacherdesk-preview" content="static">\n<meta name="robots" content="noindex,nofollow">'))
    for start, style in document.styles:
        changed = rewrite_css(style, prefix)
        if changed != style:
            replacements.append((start, start + len(style), changed))
    return _replace_ranges(text, replacements)


def _public_files(source: Path):
    files = []
    skipped = 0
    for folder, dirs, names in os.walk(source, followlinks=False):
        directory = Path(folder)
        for name in list(dirs):
            entry = directory / name
            if entry.is_symlink() or name.startswith('.') or name.lower() in EXCLUDED_DIRS or SECRET_NAME.search(name):
                dirs.remove(name)
                skipped += 1
        for name in names:
            entry = directory / name
            if entry.is_symlink() or name.startswith('.') or SECRET_NAME.search(name) or entry.suffix.lower() not in PUBLIC_SUFFIXES:
                skipped += 1
                continue
            if not entry.is_file():
                skipped += 1
                continue
            files.append(entry)
    return sorted(files), skipped


def _target(root: Path, document: Path, url: str, prefix: str):
    text = url.strip()
    if not text or text.startswith('//'):
        return None
    try:
        parsed = urlsplit(text)
    except ValueError as exc:
        raise ExportError(f'Некорректный URL {url!r}: {exc}') from exc
    if parsed.scheme or parsed.netloc:
        return None
    path = unquote(parsed.path)
    if not path:
        target = document
    elif path.startswith('/'):
        if not path.startswith(prefix):
            raise ExportError(f'Внутренний URL вышел за префикс {prefix}: {url}')
        relative = path[len(prefix):]
        target = root / relative
    else:
        target = document.parent / path
    if path.startswith(prefix + 'api/') or path == prefix + 'api':
        return None
    resolved = target.resolve()
    if resolved != root and root not in resolved.parents:
        raise ExportError(f'URL вышел за публичный каталог: {url}')
    if resolved.is_dir():
        resolved /= 'index.html'
    return resolved, unquote(parsed.fragment)


def validate_site(root: Path, prefix: str):
    """Ссылки, ресурсы, формы и CSS проверяются по готовому дереву экспорта."""
    root = root.resolve()
    errors = []
    html = {path: Markup(path.read_text(encoding='utf-8')) for path in root.rglob('*')
            if path.is_file() and path.suffix.lower() == '.html'}

    def check(document, url, *, anchor=False):
        try:
            target = _target(root, document, url, prefix)
            if target is None:
                return
            path, fragment = target
            if not path.is_file():
                errors.append(f'{document.relative_to(root)}: нет пути {url}')
            elif anchor and fragment and path.suffix.lower() == '.html' and fragment not in html[path].ids:
                errors.append(f'{document.relative_to(root)}: нет якоря {url}')
        except ExportError as exc:
            errors.append(f'{document.relative_to(root)}: {exc}')

    for path, document in html.items():
        for _, _, tag, attrs in document.tags:
            for name in URL_ATTRS:
                if attrs.get(name):
                    check(path, attrs[name], anchor=tag in {'a', 'area'} and name == 'href')
            if attrs.get('srcset'):
                for _, _, url in srcset_urls(attrs['srcset']):
                    check(path, url)
            if attrs.get('style'):
                for _, _, url in css_urls(attrs['style']):
                    check(path, url)
        for _, style in document.styles:
            for _, _, url in css_urls(style):
                check(path, url)
    for path in root.rglob('*'):
        if not path.is_file() or path.suffix.lower() != '.css':
            continue
        for _, _, url in css_urls(path.read_text(encoding='utf-8')):
            check(path, url)
    return sorted(set(errors))


def export_site(source: Path, output: Path, prefix: str) -> ExportReport:
    prefix = base_path(prefix)
    source = Path(source).absolute()
    output = Path(output).absolute()
    if source.is_symlink() or not source.is_dir():
        raise ExportError('Публичный site/ не найден или является символической ссылкой.')
    source = source.resolve()
    project = source.parent
    forbidden = [source] + [(project / name).resolve() for name in ('server', 'backend', 'data', 'deploy', 'build', 'prototype')]
    resolved_output = output.resolve()
    if any(resolved_output == folder or folder in resolved_output.parents for folder in forbidden):
        raise ExportError('Выходная папка не может находиться внутри site/server/backend/data/deploy/build/prototype.')
    if output.exists() or output.is_symlink():
        raise ExportError(f'Выходная папка уже существует, перезапись запрещена: {output}')
    files, skipped = _public_files(source)
    pages = sum(path.suffix.lower() == '.html' for path in files)
    if not pages:
        raise ExportError('В site/ нет публичных HTML-страниц.')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.teacherdesk-pages-', dir=output.parent) as folder:
        stage = Path(folder).resolve()
        for path in files:
            target = stage / path.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            if path.suffix.lower() == '.html':
                target.write_text(rewrite_html(path.read_text(encoding='utf-8'), prefix), encoding='utf-8')
            elif path.suffix.lower() == '.css':
                target.write_text(rewrite_css(path.read_text(encoding='utf-8'), prefix), encoding='utf-8')
            else:
                shutil.copyfile(path, target)
        (stage / '.nojekyll').touch()
        (stage / 'robots.txt').write_text('User-agent: *\nDisallow: /\n', encoding='utf-8')
        errors = validate_site(stage, prefix)
        if errors:
            raise ExportError(f'Страниц: {pages}; битых путей: {len(errors)}\n' + '\n'.join(errors))
        # mkdir(exist_ok=False) запрещает перезапись даже при появлении папки после проверки.
        try:
            output.mkdir()
        except FileExistsError as exc:
            raise ExportError(f'Выходная папка уже существует, перезапись запрещена: {output}') from exc
        for child in stage.iterdir():
            shutil.move(str(child), output / child.name)
    return ExportReport(pages, len(files) + (0 if any(p.name == 'robots.txt' and p.parent == source for p in files) else 1) + 1, skipped)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('destination', type=Path, nargs='?', help='Новая папка для статического просмотра')
    parser.add_argument('--output', type=Path, help='Альтернатива позиционному пути, не вместе с ним')
    parser.add_argument('--base-path', default='/TD/', help='Префикс проекта GitHub Pages, например /TD/')
    args = parser.parse_args(argv)
    if args.destination is not None and args.output is not None:
        parser.error('Укажите папку одним способом: позиционный путь или --output.')
    output = args.destination if args.destination is not None else args.output
    if output is None:
        parser.error('Укажите новую выходную папку позиционным путем или --output.')
    try:
        report = export_site(SITE, output, args.base_path)
    except (ExportError, OSError, UnicodeError) as exc:
        print(f'Ошибка экспорта: {exc}', file=sys.stderr)
        return 1
    print(f'Страниц: {report.pages}; файлов: {report.files}; битых путей: {report.broken_paths}; пропущено служебных: {report.skipped}')
    print(f'Экспорт: {output.resolve()}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
