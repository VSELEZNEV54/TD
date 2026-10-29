"""Экспорт Pages меняет копию сайта и проверяет ее до создания выходной папки."""
import contextlib
import importlib.util
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location('teacherdesk_pages', Path(__file__).resolve().parents[1] / 'deploy' / 'pages.py')
pages = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = pages
SPEC.loader.exec_module(pages)


class PagesExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / 'project'
        self.source = self.project / 'site'
        self.source.mkdir(parents=True)
        self.output = self.project / 'pages-preview'
        self.write('index.html', '''<!doctype html><html><head><meta name="robots" content="index,follow">
<meta name="teacherdesk-preview" content="old"><link rel="stylesheet" href="/assets/css/main.css?v=7">
<script src="assets/js/main.js"></script><style>.pic{background:url('/assets/img/a.svg#dot')}</style></head>
<body id="main"><a href="/features/demo/#details">Root</a><a href="features/demo/#details">Relative</a><a href="#main">Local</a>
<a href="https://example.com/page">External</a><a href="mailto:hello@example.com">Mail</a><a href="tel:+79990000000">Phone</a>
<img src="/assets/img/a.svg" srcset="/assets/img/a.svg 1x, /assets/img/b.svg 2x"><img src="//cdn.example.com/image.jpg">
<svg><use href="#i-not-a-page-anchor"/></svg><form action="/api/requests" data-endpoint="/api/requests"></form>
<div style="background:url('/assets/img/b.svg')"></div></body></html>''')
        self.write('features/demo/index.html', '<html><head><title>Demo</title></head><body id="details"><a href="/">Home</a></body></html>')
        self.write('assets/css/main.css', "/* url('/not-a-request') */ @import '/assets/css/extra.css'; .a{background:url('/assets/img/a.svg#dot')} @font-face{src:url('../fonts/demo.woff2')} .b{background:url(data:image/svg+xml,a,b)}")
        self.write('assets/css/extra.css', 'body{color:black}')
        self.write('assets/js/main.js', 'const endpoint = "/api/requests"; const markup = \'<a href="/do-not-rewrite-js">\';')
        self.write('assets/img/a.svg', '<svg id="dot"></svg>')
        self.write('assets/img/b.svg', '<svg/>')
        self.write('assets/fonts/demo.woff2', 'fixture-font')

    def write(self, relative, value):
        path = self.source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding='utf-8')
        return path

    def export(self):
        return pages.export_site(self.source, self.output, '/TD/')

    def test_project_prefix_preserves_relative_external_and_fragment_urls(self):
        original = (self.source / 'index.html').read_text(encoding='utf-8')
        report = self.export()
        html = (self.output / 'index.html').read_text(encoding='utf-8')
        self.assertEqual(report.pages, 2)
        self.assertEqual(report.broken_paths, 0)
        for value in ('href="/TD/features/demo/#details"', 'href="features/demo/#details"',
                      'src="assets/js/main.js"', 'href="#main"', 'href="#i-not-a-page-anchor"',
                      'href="https://example.com/page"', 'href="mailto:hello@example.com"',
                      'href="tel:+79990000000"', 'src="//cdn.example.com/image.jpg"',
                      'action="/TD/api/requests"', 'data-endpoint="/TD/api/requests"',
                      'srcset="/TD/assets/img/a.svg 1x, /TD/assets/img/b.svg 2x"'):
            self.assertIn(value, html)
        css = (self.output / 'assets/css/main.css').read_text(encoding='utf-8')
        self.assertIn("@import '/TD/assets/css/extra.css'", css)
        self.assertIn("url('/TD/assets/img/a.svg#dot')", css)
        self.assertIn("url('../fonts/demo.woff2')", css)
        self.assertIn('url(data:image/svg+xml,a,b)', css)
        self.assertIn("url('/TD/assets/img/a.svg#dot')", html)
        self.assertIn('url(&#x27;/TD/assets/img/b.svg&#x27;)', html)
        self.assertEqual(pages.validate_site(self.output, '/TD/'), [])
        self.assertEqual((self.source / 'index.html').read_text(encoding='utf-8'), original)
        self.assertEqual((self.output / 'assets/js/main.js').read_bytes(), (self.source / 'assets/js/main.js').read_bytes())

    def test_every_page_has_one_static_flag_and_noindex(self):
        self.export()
        for path in self.output.rglob('*.html'):
            document = pages.Markup(path.read_text(encoding='utf-8'))
            metadata = [attrs for _, _, tag, attrs in document.tags if tag == 'meta']
            self.assertEqual([m['content'] for m in metadata if m.get('name') == 'teacherdesk-preview'], ['static'])
            self.assertEqual([m['content'] for m in metadata if m.get('name') == 'robots'], ['noindex,nofollow'])
        self.assertTrue((self.output / '.nojekyll').is_file())
        self.assertEqual((self.output / 'robots.txt').read_text(), 'User-agent: *\nDisallow: /\n')

    def test_refuses_existing_directory_file_and_symlink(self):
        self.output.mkdir()
        sentinel = self.output / 'keep.txt'
        sentinel.write_text('keep')
        with self.assertRaises(pages.ExportError):
            self.export()
        self.assertEqual(sentinel.read_text(), 'keep')
        target = self.project / 'existing-file'
        target.write_text('keep-file')
        with self.assertRaises(pages.ExportError):
            pages.export_site(self.source, target, '/TD/')
        link = self.project / 'dangling-output'
        link.symlink_to(self.project / 'missing')
        with self.assertRaises(pages.ExportError):
            pages.export_site(self.source, link, '/TD/')

    def test_refuses_output_inside_private_or_source_directories(self):
        for relative in ('site/new', 'server/new', 'backend/new', 'data/new', 'deploy/new', 'build/new', 'prototype/new'):
            with self.subTest(relative=relative), self.assertRaises(pages.ExportError):
                pages.export_site(self.source, self.project / relative, '/TD/')
        for value in ('TD', '/TD', '/../TD/', '//TD/', '/TD/?x=1', '/%2e%2e/'):
            with self.subTest(prefix=value), self.assertRaises(pages.ExportError):
                pages.export_site(self.source, self.output, value)
        external = Path(self.temp.name) / 'external-server'
        external.mkdir()
        (self.project / 'server').symlink_to(external, target_is_directory=True)
        with self.assertRaises(pages.ExportError):
            pages.export_site(self.source, self.project / 'server/new', '/TD/')

    def test_excludes_secrets_working_materials_and_symlinks(self):
        for relative in ('.env', '.env.production', 'data/requests.sqlite', 'server/app.py',
                         'backend/settings.js', 'build/generated.html', 'deploy/config.txt',
                         'prototype/index.html', '_pages/index.html', '.git/config',
                         'assets/private.key', 'assets/credentials.json', 'assets/access-token.js',
                         'assets/secrets/config.js'):
            self.write(relative, 'DO-NOT-PUBLISH')
        secret = self.project / 'outside-secret.js'
        secret.write_text('DO-NOT-PUBLISH')
        (self.source / 'assets/link.js').symlink_to(secret)
        (self.source / 'linked-directory').symlink_to(self.project, target_is_directory=True)
        report = self.export()
        self.assertGreater(report.skipped, 0)
        for path in self.output.rglob('*'):
            self.assertFalse(path.is_symlink())
            if path.is_file():
                self.assertNotIn(b'DO-NOT-PUBLISH', path.read_bytes())
        self.assertFalse((self.output / '_pages').exists())
        self.assertFalse((self.output / 'assets/link.js').exists())

    def test_missing_asset_or_page_anchor_fails_before_output_exists(self):
        self.write('broken/index.html', '<html><head></head><body><img src="/missing.png"><a href="/features/demo/#missing">Bad</a></body></html>')
        with self.assertRaisesRegex(pages.ExportError, 'битых путей: 2'):
            self.export()
        self.assertFalse(self.output.exists())
        self.assertFalse(list(self.project.glob('.teacherdesk-pages-*')))

    def test_srcset_data_url_and_css_comments_are_preserved(self):
        value = 'data:image/png;base64,ABC 1x, /assets/img/a.svg 2x'
        self.assertEqual(pages.rewrite_srcset(value, '/TD/'), 'data:image/png;base64,ABC 1x, /TD/assets/img/a.svg 2x')
        self.assertEqual([u for _, _, u in pages.srcset_urls(value)], ['data:image/png;base64,ABC', '/assets/img/a.svg'])
        self.assertEqual(pages.rewrite_css('/* url(/private) */ .a{background:url(#filter)}', '/TD/'), '/* url(/private) */ .a{background:url(#filter)}')

    def test_fragment_only_links_resolve_to_the_same_non_index_document(self):
        self.write('404.html', '<html><head></head><body id="only-here"><a href="#only-here">Here</a></body></html>')
        self.export()
        self.assertEqual(pages.validate_site(self.output, '/TD/'), [])

    def test_cli_reports_counts_and_failure_exit_status(self):
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(pages, 'SITE', self.source), contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            self.assertEqual(pages.main(['--output', str(self.output), '--base-path', '/TD/']), 0)
            self.assertEqual(pages.main(['--output', str(self.output), '--base-path', '/TD/']), 1)
        self.assertIn('Страниц: 2', stdout.getvalue())
        self.assertIn('битых путей: 0', stdout.getvalue())
        self.assertIn('перезапись запрещена', stderr.getvalue())

    def test_cli_accepts_positional_destination_and_rejects_both_forms(self):
        with patch.object(pages, 'SITE', self.source), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as error:
                pages.main([str(self.output), '--output', str(self.project / 'second-output'), '--base-path', '/TD/'])
            self.assertEqual(error.exception.code, 2)
            self.assertFalse(self.output.exists())
            self.assertEqual(pages.main([str(self.output), '--base-path', '/TD/']), 0)
        self.assertTrue((self.output / 'index.html').is_file())


if __name__ == '__main__':
    unittest.main()
