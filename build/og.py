#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Картинки для соцсетей и мессенджеров (og:image 1200 x 630) для каждой страницы.

    python3 build/og.py              все страницы, кроме документов и служебных
    python3 build/og.py --only=crm   одна или несколько страниц

Рисует карточку в стиле главной: логотип, кикер раздела, h1 страницы с антиквой, наклейка с оффером
и знак T из трех деталей. Снимок делает установленный Google Chrome без окна, JPEG сжимает sips (macOS).
Результат: site/assets/img/og/<id>.jpg и общая site/assets/img/og-home.jpg. build.py берет картинку
страницы сам, если файл есть. Запускать после правки h1 в реестре, затем обычную сборку."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

BUILD = Path(__file__).resolve().parent
SITE = BUILD.parent / 'site'
OUT = SITE / 'assets' / 'img' / 'og'
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
ONLY = next((a.split('=', 1)[1].split(',') for a in sys.argv if a.startswith('--only=')), None)

KICK = {'product': 'Платформа для репетиторов', 'features': 'Возможности', 'tools': 'Бесплатный инструмент',
        'blog': 'Блог для репетиторов', 'kb': 'База знаний', 'trust': 'О сервисе'}
PILL = {'tools': 'Бесплатно, без регистрации', 'blog': 'Читать на teacherdesk.ru', 'kb': 'Инструкция по шагам'}
SKIP = {'legal', 'notfound'}
HOME_H1 = 'Платформа для репетиторов в <em class="em">одном окне</em>'


def card(p, f):
    sec = p.get('section', 'product')
    h1 = HOME_H1 if p['id'] == 'home' else p['h1']
    kick = 'Онлайн-платформа' if p['id'] == 'home' else KICK.get(sec, 'TeacherDesk')
    if p['type'] == 'hub' and sec != 'product':
        kick = 'TeacherDesk'
    pill = PILL.get(sec, '14 дней бесплатно, без карты')
    size = 76 if len(h1) < 60 else 66 if len(h1) < 90 else 58
    return f'''<!doctype html><html lang="ru"><head><meta charset="utf-8"><style>
@font-face{{font-family:Geist;src:url({f}/geist-600.woff2) format("woff2");font-weight:600}}
@font-face{{font-family:Geist;src:url({f}/geist-500.woff2) format("woff2");font-weight:500}}
@font-face{{font-family:Playfair;src:url({f}/playfair-display-italic-500.woff) format("woff");font-style:italic;font-weight:500}}
*{{margin:0;box-sizing:border-box}}
html,body{{width:1200px;height:630px;overflow:hidden}}
body{{position:relative;font-family:Geist,sans-serif;color:#1B1D2E;background:#fff}}
.bg{{position:absolute;inset:0;background:radial-gradient(520px 360px at 82% 18%,rgba(124,108,255,.22),transparent 70%),radial-gradient(420px 320px at 96% 92%,rgba(68,91,246,.18),transparent 70%);}}
.dots{{position:absolute;inset:0 0 0 46%;background-image:radial-gradient(rgba(40,48,110,.12) 1px,transparent 1.4px);background-size:22px 22px;-webkit-mask-image:linear-gradient(90deg,transparent,#000 30%)}}
.logo{{position:absolute;left:72px;top:62px;height:36px}}
.in{{position:absolute;left:72px;top:150px;width:700px}}
.k{{display:flex;align-items:center;gap:12px;font-size:24px;font-weight:500;color:#3548DB}}
.k i{{width:16px;height:16px;border-radius:0 16px 0 0;background:#445BF6}}
h1{{margin-top:22px;font-size:{size}px;font-weight:600;line-height:1.06;letter-spacing:-.035em;text-wrap:balance}}
.em{{font-family:Playfair,serif;font-style:italic;font-weight:500;color:#445BF6;letter-spacing:-.01em}}
.pill{{position:absolute;left:72px;bottom:64px;display:inline-flex;align-items:center;gap:10px;height:54px;padding:0 24px;border-radius:999px;background:#F4EA00;font-size:23px;font-weight:600;box-shadow:4px 4px 0 #1B1D2E;transform:rotate(-2deg)}}
.t{{position:absolute;right:48px;bottom:0;width:374px;height:262px}}
.t b{{position:absolute;display:block}}
.t .a{{left:0;top:0;width:222px;height:96px;background:#445BF6;border-radius:0 96px 0 0}}
.t .y{{left:222px;top:0;width:152px;height:96px;background:#F4EA00}}
.t .s{{left:126px;top:96px;width:96px;height:166px;background:#445BF6;border-radius:96px 0 0 0}}
</style></head><body><div class="bg"></div><div class="dots"></div>
<img class="logo" src="{SITE.as_uri()}/assets/img/logo.svg" alt="">
<div class="in"><p class="k"><i></i>{kick}</p><h1>{h1}</h1></div>
<p class="pill">{pill}</p>
<div class="t"><b class="a"></b><b class="y"></b><b class="s"></b></div>
</body></html>'''


def shoot(html, dest, tmp):
    src = tmp / 'og.html'
    png = tmp / 'og.png'
    src.write_text(html, encoding='utf-8')
    png.unlink(missing_ok=True)
    # свой профиль, чтобы не задеть открытый Chrome; код выхода не смотрим: Chrome пишет снимок и иногда
    # завершается с ошибкой на закрытии, поэтому проверяем сам файл
    subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=1',
                    f'--user-data-dir={tmp / "profile"}', '--no-first-run', '--no-default-browser-check',
                    '--allow-file-access-from-files', '--window-size=1200,630', f'--screenshot={png}', src.as_uri()],
                   capture_output=True, timeout=90)
    if not png.exists():
        sys.exit(f'Chrome не сделал снимок для {dest.name}')
    subprocess.run(['sips', '-s', 'format', 'jpeg', '-s', 'formatOptions', '82', str(png), '--out', str(dest)],
                   check=True, capture_output=True)


def main():
    if not Path(CHROME).exists():
        sys.exit('Нужен Google Chrome в /Applications')
    pages = json.loads((BUILD / 'pages.json').read_text(encoding='utf-8'))
    OUT.mkdir(parents=True, exist_ok=True)
    fonts = (SITE / 'assets' / 'fonts').as_uri()
    n = 0
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        for p in pages:
            if p['type'] in SKIP or (ONLY and p['id'] not in ONLY):
                continue
            dest = SITE / 'assets' / 'img' / 'og-home.jpg' if p['id'] == 'home' else OUT / f'{p["id"]}.jpg'
            shoot(card(p, fonts), dest, tmp)
            n += 1
    print(f'Картинок для соцсетей: {n}')


if __name__ == '__main__':
    main()
