# Памятка для выкладки: сервер, переезд и поисковики

Для клиента, который сам выкладывает сайт на свой сервер. Публичные страницы остаются статическими, прием обращений работает через Python-бэкенд. Запуск сервера, база, панель и резервные копии: [backend.md](backend.md). Готовый пример nginx с проксированием в бэкенд: [../deploy/nginx.conf](../deploy/nginx.conf). Ниже описаны SEO-настройки и карта переезда.

## 1. Перед выкладкой

1. Собрать выкладку: `python3 build/build.py --release`, затем `python3 build/sync_home.py --release`. Примеры, служебный список `/_pages/` и ссылки на неопубликованные страницы уйдут из `site/`.
2. Проверить, что документы открываются в кабинете: `https://app.teacherdesk.ru/privacy`, `/terms`, `/offer`, `/consent`, `/cookies`, `/requisites`. На сайте их копии не публикуются, отдельно остается только `/marketing-consent/`.
3. Запустить `python3 build/seo_audit.py`: последняя строка должна быть «Ошибок нет». Аудит проверяет битые ссылки, canonical, sitemap, микроразметку и вес страниц.
4. Перенести публичную папку `site/` целиком и серверную часть по [backend.md](backend.md). Если используется nginx со статической раздачей из примера ниже, обязательно добавить проксирование `/api/`, `/admin/`, `/register` и `/login` из `deploy/nginx.conf`. Базу SQLite и `.env` хранить вне публичного корня.

## 2. Настройки сервера (пример для nginx)

Основное зеркало: `https://teacherdesk.ru` без www. Все остальные варианты отдают 301 на него.

```nginx
# http и www -> https://teacherdesk.ru
server {
    listen 80;
    server_name teacherdesk.ru www.teacherdesk.ru;
    return 301 https://teacherdesk.ru$request_uri;
}
server {
    listen 443 ssl http2;
    server_name www.teacherdesk.ru;
    # ssl_certificate ... (сертификат должен покрывать и www)
    return 301 https://teacherdesk.ru$request_uri;
}

server {
    listen 443 ssl http2;
    server_name teacherdesk.ru;
    root /var/www/teacherdesk/site;
    index index.html;
    charset utf-8;

    # старые адреса текущего сайта -> новые страницы (301)
    location = /features  { return 301 /features/; }
    location = /pricing   { return 301 /pricing/; }
    location = /tutors    { return 301 /features/; }
    location = /students  { return 301 /features/kabinet-uchenika/; }
    location = /about     { return 301 /about/; }
    location = /contact   { return 301 /kontakty/; }
    location = /careers   { return 301 /about/; }
    location = /blog      { return 301 /; }          # пока блог не опубликован; после публикации: /blog/
    # адреса регистрации и входа берутся бэкендом из REGISTER_URL и LOGIN_URL
    location = /register { proxy_pass http://127.0.0.1:8131; proxy_set_header Host $host; }
    location = /login { proxy_pass http://127.0.0.1:8131; proxy_set_header Host $host; }
    location ^~ /api/ {
        proxy_pass http://127.0.0.1:8131;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $remote_addr;
        client_max_body_size 16k;
        add_header Cache-Control "no-store" always;
    }
    location = /admin { return 302 /admin/; }
    location ^~ /admin/ {
        proxy_pass http://127.0.0.1:8131;
        proxy_set_header Host $host;
        add_header Cache-Control "no-store" always;
    }

    # слэш в конце: /features/raspisanie -> /features/raspisanie/ (адреса без точки, то есть не файлы)
    location ~ ^([^.]*[^/])$ { return 301 $1/$is_args$args; }

    location / {
        try_files $uri $uri/index.html =404;
    }

    error_page 404 /404.html;
    location = /404.html { internal; }

    # долгий кэш для стилей, скриптов, шрифтов и картинок: у CSS и JS в адресе есть версия ?v=...
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, max-age=31536000, immutable";
    }
    # HTML всегда свежий
    location ~* \.html$ {
        add_header Cache-Control "no-cache";
    }

    gzip on;
    gzip_types text/css application/javascript application/json image/svg+xml text/xml application/xml;
    # brotli on; brotli_types ... (если модуль установлен)
}
```

Документы теперь живут в кабинете, поэтому старые адреса ведем туда, правило ставим выше общего правила слэша:

```nginx
location ~ ^/(privacy|terms|offer|consent|cookies|requisites)/?$ { return 301 https://app.teacherdesk.ru/$1; }
```

Если сервер не nginx, логика та же: 301 с http и www на `https://teacherdesk.ru`, 301 с адреса без слэша на адрес со слэшем, карта старых адресов из таблицы выше, ответ 404 с файлом `/404.html`, долгий кэш для `/assets/`.

## 3. Проверка после выкладки

Каждую строку проверить командой `curl -I адрес`: в ответе нужен код из второй колонки.

| Адрес | Ожидаемый ответ |
|---|---|
| http://teacherdesk.ru/ | 301 на https://teacherdesk.ru/ |
| https://www.teacherdesk.ru/pricing/ | 301 на https://teacherdesk.ru/pricing/ |
| https://teacherdesk.ru/features/raspisanie | 301 на .../features/raspisanie/ |
| https://teacherdesk.ru/tutors | 301 на https://teacherdesk.ru/features/ |
| https://teacherdesk.ru/register | 302 на адрес REGISTER_URL |
| https://teacherdesk.ru/net-takoy-stranicy/ | 404 и страница «Такой страницы нет» |
| https://teacherdesk.ru/sitemap.xml | 200, только опубликованные страницы |
| https://teacherdesk.ru/assets/css/main.css?v=... | 200, Cache-Control с max-age=31536000 |

## 4. Яндекс Вебмастер и Google Search Console

1. Добавить сайт `https://teacherdesk.ru` в оба сервиса и подтвердить права (мета-тег в `<head>` или файл в корне `site/`; файл подтверждения тоже кладется в `site/` и не удаляется).
2. В Вебмастере: «Индексирование» → «Файлы Sitemap» → добавить `https://teacherdesk.ru/sitemap.xml`. В Search Console: «Файлы Sitemap» → тот же адрес.
3. В Вебмастере проверить «Зеркала»: главным должен быть `https://teacherdesk.ru`.
4. «Переобход страниц»: отправить главную, пять посадочных и девять функций в первый день, остальные по мере квоты.
5. «Валидатор микроразметки» Яндекса и Rich Results Test Google: проверить главную, одну посадочную, одну функцию, один инструмент и тарифы.
6. После каждого релиза снова отправлять sitemap и новые страницы на переобход.

## 5. Яндекс Метрика

Счетчик с вебвизором и целями из ТЗ (раздел 9): клик по кнопке регистрации с меткой места, переход на app.teacherdesk.ru, скачивание шаблона, использование инструмента, отправка формы генератора. Код счетчика подключается после согласия на cookies, как на текущем сайте. Номер счетчика в публичный репозиторий не коммитим, если клиент против.

## 6. Позиции

Раз в неделю снимать позиции по 272 запросам ядра (Топвизор или аналог), регион Россия, Яндекс и Google. Первые изменения ждать через 3-6 недель после индексации, сезонный пик спроса с августа по октябрь.

## 7. Ежедневный выход статей блога

Статьи блога выходят по датам: в каждой статье записана дата выхода, сборка в этот день делает ее опубликованной, добавляет в хаб блога и sitemap. Коммит в день выхода не нужен, нужен ежедневный запуск сборки на сервере.

Порядок работы:

1. Студия раз в неделю или две готовит статьи вперед: текст, проверка, картинки. Они попадают в `main` обычным Pull Request после принятия клиентом, сразу пачкой на 1-2 недели вперед.
2. Сервер каждое утро забирает `main`, собирает выкладку и обновляет публичную папку. Статьи, у которых наступила дата, появляются на сайте сами.

Пример для cron пользователя, от которого работает сайт (`crontab -e`), запуск в 10:05 по Москве:

```cron
CRON_TZ=Europe/Moscow
5 10 * * * cd /var/www/teacherdesk/repo && git pull --ff-only origin main && python3 build/build.py --release && python3 build/sync_home.py --release && python3 build/seo_audit.py && rsync -a site/ /var/www/teacherdesk/site/ >> /var/log/teacherdesk-blog.log 2>&1
```

- `/var/www/teacherdesk/repo` - клон публичного репозитория только для сборки, `/var/www/teacherdesk/site` - публичный корень. Сборка идет в клоне, в публичный корень копируется только готовая `site/`.
- Цепочка через `&&`: если сборка или аудит нашли ошибку, сайт не обновляется, причина в логе.
- Сервер должен считать дату по Москве: сборка сама берет московскую дату, переменная `CRON_TZ` нужна только для времени запуска. Если cron не понимает `CRON_TZ`, поставьте время по часовому поясу сервера (10:05 МСК = 07:05 UTC).
- После публикации блога заменить в nginx правило `location = /blog { return 301 /; }` на `location = /blog { return 301 /blog/; }`.
