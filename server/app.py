"""Small WSGI service for the public website. Runtime: Python 3.9+, SQLite."""

import csv
import hashlib
import hmac
import io
import json
import logging
import mimetypes
import os
import re
import sqlite3
import threading
import time
import uuid
from collections import OrderedDict, deque
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, quote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
MAX_BODY = 16 * 1024
CONSENT_VERSION = "2026-10-28"
KINDS = {"question", "consultation"}
STATUSES = {"new", "in_progress", "closed"}
CONTACT_METHODS = {"any", "email", "phone"}
EMAIL_RE = re.compile(r"^[^\s@<>]+@[^\s@<>]+\.[^\s@<>.]+$")
LOG = logging.getLogger("teacherdesk")


def load_env(path=ROOT / ".env"):
    """Read literal KEY=value lines; no shell execution or interpolation."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition("=")
        if not sep or not re.fullmatch(r"[A-Z][A-Z0-9_]*", key.strip()):
            raise ValueError("Invalid .env line")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ.setdefault(key.strip(), value)


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


class HTTPError(Exception):
    def __init__(self, status, error, message, fields=None, headers=None):
        self.status, self.error, self.message = status, error, message
        self.fields, self.headers = fields, headers or []


def json_body(environ):
    if environ.get("CONTENT_TYPE", "").split(";", 1)[0].strip().lower() != "application/json":
        raise HTTPError(415, "unsupported_media_type", "Нужен запрос в формате JSON.")
    try:
        length = int(environ.get("CONTENT_LENGTH") or "0")
    except ValueError:
        raise HTTPError(400, "invalid_body", "Некорректная длина запроса.")
    if length < 0 or length > MAX_BODY:
        raise HTTPError(413, "payload_too_large", "Слишком большой запрос.")
    if not length:
        raise HTTPError(400, "invalid_body", "Тело запроса пустое.")
    try:
        body = json.loads(environ["wsgi.input"].read(length).decode("utf-8"))
    except (ValueError, UnicodeError, RecursionError):
        raise HTTPError(400, "invalid_json", "Не удалось прочитать JSON.")
    if not isinstance(body, dict):
        raise HTTPError(400, "invalid_body", "Тело запроса должно быть объектом.")
    return body


def normalize_request(body):
    fields = {}

    def text_field(name, maximum, required=False):
        value = body.get(name, "")
        if not isinstance(value, str):
            fields[name] = "Введите текст."
            return ""
        value = value.strip()
        if "\x00" in value or len(value) > maximum:
            fields[name] = "Слишком длинное или некорректное значение."
        elif required and not value:
            fields[name] = "Заполните это поле."
        return value

    name = text_field("name", 100, True)
    if name and len(name) < 2:
        fields["name"] = "Введите имя, хотя бы 2 символа."
    phone = text_field("phone", 40)
    email = text_field("email", 254)
    question = text_field("question", 4000)
    source_path = text_field("source_path", 500)
    source_tag = text_field("source_tag", 100)
    website = text_field("website", 200)
    kind = body.get("kind", "question")
    if not isinstance(kind, str) or kind not in KINDS:
        fields["kind"] = "Выберите тип обращения."
    preferred = body.get("preferred_contact", "any")
    if not isinstance(preferred, str) or preferred not in CONTACT_METHODS:
        fields["preferred_contact"] = "Выберите способ связи."
    if phone and (not re.fullmatch(r"[+\d\s().-]+", phone) or not 10 <= len(re.sub(r"\D", "", phone)) <= 15):
        fields["phone"] = "Введите телефон, от 10 до 15 цифр."
    if email and not EMAIL_RE.fullmatch(email):
        fields["email"] = "Проверьте адрес электронной почты."
    if not phone and not email:
        fields["phone"] = fields["email"] = "Укажите телефон или email для ответа."
    if preferred == "phone" and not phone:
        fields["phone"] = "Укажите телефон для звонка."
    if preferred == "email" and not email:
        fields["email"] = "Укажите email для ответа."
    if kind == "question" and not question:
        fields["question"] = "Напишите ваш вопрос."
    if body.get("consent") is not True:
        fields["consent"] = "Нужно согласие на обработку данных."
    if not isinstance(body.get("news", False), bool):
        fields["news"] = "Некорректное согласие на рассылку."
    if source_path and (not source_path.startswith("/") or source_path.startswith("//") or "\\" in source_path or any(ord(char) < 32 for char in source_path)):
        fields["source_path"] = "Некорректный адрес страницы."
    if website:
        fields["website"] = "Не удалось принять обращение."
    if fields:
        raise HTTPError(422, "validation_error", "Проверьте поля формы.", fields)
    return {
        "kind": kind, "name": name, "phone": phone, "email": email,
        "question": question, "preferred_contact": preferred,
        "consent": True, "news": body.get("news", False),
        "source_path": source_path, "source_tag": source_tag,
    }


class RateLimiter:
    """Bounded memory; a single worker keeps one shared limiter across threads."""
    def __init__(self, maximum=5, window=600, capacity=10000):
        self.maximum, self.window, self.capacity = maximum, window, capacity
        self.lock, self.entries = threading.Lock(), OrderedDict()

    def check(self, key):
        now = time.monotonic()
        with self.lock:
            # Global cleanup plus LRU eviction caps even a stream of distinct IPs.
            while self.entries:
                first = next(iter(self.entries))
                if self.entries[first] and now - self.entries[first][-1] < self.window:
                    break
                self.entries.pop(first)
            hits = self.entries.pop(key, deque())
            while hits and now - hits[0] >= self.window:
                hits.popleft()
            if len(hits) >= self.maximum:
                self.entries[key] = hits
                retry = max(1, int(self.window - (now - hits[0])) + 1)
                raise HTTPError(429, "rate_limited", "Слишком много обращений. Попробуйте позже.", headers=[("Retry-After", str(retry))])
            hits.append(now)
            self.entries[key] = hits
            while len(self.entries) > self.capacity:
                self.entries.popitem(last=False)


def config_from_env(overrides=None):
    load_env()
    config = {
        "SITE_DIR": str(ROOT / "site"), "DATA_DIR": str(ROOT / "server" / "data"),
        "ADMIN_TOKEN": "", "PUBLIC_ORIGIN": "", "TRUST_PROXY": "false",
        "REGISTER_URL": "https://app.teacherdesk.ru/register",
        "LOGIN_URL": "https://app.teacherdesk.ru/login", "RATE_LIMIT": "5", "RATE_WINDOW": "600",
    }
    for key in config:
        if key in os.environ:
            config[key] = os.environ[key]
    config.update(overrides or {})
    for key in ("SITE_DIR", "DATA_DIR"):
        config[key] = Path(config[key]).expanduser().resolve()
    if config["SITE_DIR"] == config["DATA_DIR"] or config["SITE_DIR"] in config["DATA_DIR"].parents:
        raise ValueError("DATA_DIR must be outside SITE_DIR")
    for key in ("REGISTER_URL", "LOGIN_URL"):
        target = urlsplit(config[key])
        if target.scheme not in {"http", "https"} or not target.netloc or target.username or target.password or any(c in config[key] for c in "\r\n"):
            raise ValueError(key + " must be an absolute http(s) URL")
    if config["PUBLIC_ORIGIN"]:
        origin = urlsplit(config["PUBLIC_ORIGIN"])
        if origin.scheme not in {"http", "https"} or not origin.netloc or origin.path not in {"", "/"} or origin.query or origin.fragment or origin.username:
            raise ValueError("PUBLIC_ORIGIN must contain only scheme and host")
        config["PUBLIC_ORIGIN"] = config["PUBLIC_ORIGIN"].rstrip("/")
    config["TRUST_PROXY"] = str(config["TRUST_PROXY"]).lower() in {"true", "1", "yes"}
    config["RATE_LIMIT"], config["RATE_WINDOW"] = int(config["RATE_LIMIT"]), int(config["RATE_WINDOW"])
    if config["RATE_LIMIT"] < 1 or config["RATE_WINDOW"] < 1:
        raise ValueError("Rate limits must be positive")
    if config["ADMIN_TOKEN"] and len(config["ADMIN_TOKEN"]) < 32:
        raise ValueError("ADMIN_TOKEN must contain at least 32 characters")
    return config


class Application:
    def __init__(self, config):
        self.config = config
        self.database = config["DATA_DIR"] / "requests.sqlite3"
        config["DATA_DIR"].mkdir(parents=True, exist_ok=True, mode=0o700)
        self.limiter = RateLimiter(config["RATE_LIMIT"], config["RATE_WINDOW"])
        self.admin_limiter = RateLimiter(15, 600)
        self._initialize()

    def connect(self):
        connection = sqlite3.connect(str(self.database), timeout=10)
        connection.row_factory = sqlite3.Row
        connection.create_function("CASEFOLD", 1, lambda value: value.casefold() if isinstance(value, str) else value, deterministic=True)
        connection.execute("PRAGMA busy_timeout=10000")
        return connection

    @contextmanager
    def session(self):
        connection = self.connect()
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _initialize(self):
        with self.session() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS requests (
                    id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL CHECK(kind IN ('question','consultation')),
                    name TEXT NOT NULL, phone TEXT NOT NULL, email TEXT NOT NULL,
                    question TEXT NOT NULL, preferred_contact TEXT NOT NULL,
                    source_path TEXT NOT NULL, source_tag TEXT NOT NULL,
                    consent_at TEXT NOT NULL, consent_version TEXT NOT NULL,
                    news INTEGER NOT NULL CHECK(news IN (0,1)),
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'new' CHECK(status IN ('new','in_progress','closed')),
                    note TEXT NOT NULL DEFAULT '',
                    idempotency_key TEXT UNIQUE, payload_hash TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS requests_created ON requests(created_at DESC);
                CREATE INDEX IF NOT EXISTS requests_status ON requests(status,created_at DESC);
            """)
        try:
            self.database.chmod(0o600)
        except OSError:
            pass

    @staticmethod
    def _json(status, payload, headers=None):
        data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        return status, [("Content-Type", "application/json; charset=utf-8")] + (headers or []), data

    def __call__(self, environ, start_response):
        try:
            status, headers, data = self.dispatch(environ)
        except HTTPError as exc:
            payload = {"ok": False, "error": exc.error, "message": exc.message}
            if exc.fields:
                payload["fields"] = exc.fields
            status, headers, data = self._json(exc.status, payload, exc.headers)
        except (sqlite3.Error, OSError):
            LOG.exception("Storage or filesystem error")
            status, headers, data = self._json(503, {"ok": False, "error": "unavailable", "message": "Сервис временно недоступен. Попробуйте позже."})
        except Exception:
            LOG.exception("Unexpected service error")
            status, headers, data = self._json(500, {"ok": False, "error": "internal_error", "message": "Не удалось обработать запрос. Попробуйте позже."})
        reasons = {200: "OK", 201: "Created", 301: "Moved Permanently", 302: "Found", 400: "Bad Request", 401: "Unauthorized", 403: "Forbidden", 404: "Not Found", 405: "Method Not Allowed", 409: "Conflict", 413: "Content Too Large", 415: "Unsupported Media Type", 422: "Unprocessable Content", 429: "Too Many Requests", 500: "Internal Server Error", 503: "Service Unavailable"}
        path = environ.get("PATH_INFO", "/")
        headers.extend([
            ("X-Content-Type-Options", "nosniff"), ("Referrer-Policy", "strict-origin-when-cross-origin"),
            ("X-Frame-Options", "SAMEORIGIN"), ("Content-Length", str(len(data))),
        ])
        if path.startswith(("/api/", "/admin")):
            headers.extend([("Cache-Control", "no-store"), ("X-Robots-Tag", "noindex, nofollow")])
        else:
            headers.append(("Cache-Control", "no-cache"))
        start_response(str(status) + " " + reasons.get(status, "Error"), headers)
        return [b"" if environ.get("REQUEST_METHOD") == "HEAD" else data]

    def _ip(self, environ):
        if self.config["TRUST_PROXY"]:
            # The reverse proxy must REPLACE X-Forwarded-For, not append user input.
            forwarded = environ.get("HTTP_X_FORWARDED_FOR", "").strip()
            if forwarded:
                return forwarded.split(",")[-1].strip()[:100]
        return environ.get("REMOTE_ADDR", "unknown")[:100]

    def _check_origin(self, environ):
        origin = environ.get("HTTP_ORIGIN")
        if origin is None:
            return  # Non-browser API clients do not need a CORS preflight.
        expected = self.config["PUBLIC_ORIGIN"]
        if not expected:
            scheme = environ.get("wsgi.url_scheme", "http")
            if self.config["TRUST_PROXY"]:
                scheme = environ.get("HTTP_X_FORWARDED_PROTO", scheme).split(",")[-1].strip()
            expected = scheme + "://" + environ.get("HTTP_HOST", environ.get("SERVER_NAME", "localhost"))
        if origin.rstrip("/") != expected:
            raise HTTPError(403, "origin_denied", "Отправьте форму со страницы сайта.")

    def _admin_auth(self, environ):
        token = self.config["ADMIN_TOKEN"]
        if not token:
            raise HTTPError(503, "admin_disabled", "Доступ к панели пока не настроен.")
        header = environ.get("HTTP_AUTHORIZATION", "")
        candidate = header[7:] if header.startswith("Bearer ") else ""
        if not hmac.compare_digest(candidate.encode("utf-8"), token.encode("utf-8")):
            self.admin_limiter.check(self._ip(environ))
            raise HTTPError(401, "unauthorized", "Неверный ключ доступа.", headers=[("WWW-Authenticate", "Bearer")])

    def dispatch(self, environ):
        method, path = environ.get("REQUEST_METHOD", "GET"), environ.get("PATH_INFO", "/")
        if path.startswith("/api/"):
            if method not in {"GET", "HEAD"}:
                self._check_origin(environ)
            if path == "/api/health":
                self._method(method, {"GET", "HEAD"})
                with self.session() as connection:
                    connection.execute("SELECT 1 FROM requests LIMIT 1")
                return self._json(200, {"ok": True})
            if path == "/api/public-config":
                self._method(method, {"GET", "HEAD"})
                return self._json(200, {"register_url": self.config["REGISTER_URL"], "login_url": self.config["LOGIN_URL"]})
            if path == "/api/requests":
                self._method(method, {"POST"})
                return self.create_request(environ)
            if path.startswith("/api/admin/"):
                self._admin_auth(environ)
                if path == "/api/admin/requests/export.csv":
                    self._method(method, {"GET"})
                    return self.list_requests(environ, export=True)
                if path == "/api/admin/requests":
                    self._method(method, {"GET"})
                    return self.list_requests(environ)
                if re.fullmatch(r"/api/admin/requests/[0-9a-f-]{36}", path):
                    self._method(method, {"PATCH"})
                    return self.update_request(environ, path.rsplit("/", 1)[-1])
            raise HTTPError(404, "not_found", "Адрес не найден.")
        self._method(method, {"GET", "HEAD"})
        if path.rstrip("/") in {"/register", "/login"}:
            key = "REGISTER_URL" if path.rstrip("/") == "/register" else "LOGIN_URL"
            return 302, [("Location", self.config[key])], b""
        return self.serve_static(environ)

    @staticmethod
    def _method(method, allowed):
        if method not in allowed:
            raise HTTPError(405, "method_not_allowed", "Этот метод не поддерживается.", headers=[("Allow", ", ".join(sorted(allowed)))])

    def create_request(self, environ):
        body = normalize_request(json_body(environ))
        key = environ.get("HTTP_IDEMPOTENCY_KEY") or None
        if key:
            try:
                parsed = uuid.UUID(key)
                if str(parsed) != key.lower():
                    raise ValueError()
                key = str(parsed)
            except (ValueError, AttributeError):
                raise HTTPError(400, "invalid_idempotency_key", "Некорректный идентификатор отправки.")
        payload_hash = hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
        connection = self.connect()
        try:
            # The short write lock makes simultaneous retries atomic across processes.
            connection.execute("BEGIN IMMEDIATE")
            if key:
                existing = connection.execute("SELECT id,payload_hash FROM requests WHERE idempotency_key=?", (key,)).fetchone()
                if existing:
                    if existing["payload_hash"] != payload_hash:
                        raise HTTPError(409, "idempotency_conflict", "Данные формы изменились. Повторите отправку с новым идентификатором.")
                    connection.commit()
                    return self._json(200, {"ok": True, "id": existing["id"]})
            self.limiter.check(self._ip(environ))
            request_id, now = str(uuid.uuid4()), utc_now()
            connection.execute("""INSERT INTO requests
                (id,kind,name,phone,email,question,preferred_contact,source_path,source_tag,
                 consent_at,consent_version,news,created_at,updated_at,idempotency_key,payload_hash)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
                    request_id, body["kind"], body["name"], body["phone"], body["email"], body["question"],
                    body["preferred_contact"], body["source_path"], body["source_tag"], now, CONSENT_VERSION,
                    int(body["news"]), now, now, key, payload_hash,
                ))
            connection.commit()
            return self._json(201, {"ok": True, "id": request_id})
        finally:
            connection.close()

    def _filters(self, environ):
        query = parse_qs(environ.get("QUERY_STRING", ""), keep_blank_values=True)
        clauses, params = [], []
        for key, allowed in (("status", STATUSES), ("kind", KINDS)):
            value = query.get(key, [""])[0]
            if value:
                if value not in allowed:
                    raise HTTPError(400, "invalid_filter", "Некорректный фильтр.")
                clauses.append(key + "=?")
                params.append(value)
        search = query.get("q", [""])[0].strip()
        if len(search) > 200:
            raise HTTPError(400, "invalid_filter", "Поисковый запрос слишком длинный.")
        if search:
            escaped = search.casefold().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            clauses.append("(" + " OR ".join("CASEFOLD(" + key + ") LIKE ? ESCAPE '\\'" for key in ("name", "phone", "email", "question", "note")) + ")")
            params.extend(["%" + escaped + "%"] * 5)
        return (" WHERE " + " AND ".join(clauses) if clauses else ""), params, query

    @staticmethod
    def record(row):
        item = {key: row[key] for key in row.keys() if key not in {"payload_hash", "idempotency_key"}}
        item["news"] = bool(item["news"])
        return item

    def list_requests(self, environ, export=False):
        where, params, query = self._filters(environ)
        try:
            limit, offset = int(query.get("limit", ["50"])[0]), int(query.get("offset", ["0"])[0])
            if not 1 <= limit <= 100 or offset < 0:
                raise ValueError()
        except ValueError:
            raise HTTPError(400, "invalid_pagination", "Некорректный номер страницы.")
        with self.session() as connection:
            if export:
                rows = connection.execute("SELECT * FROM requests" + where + " ORDER BY created_at DESC,id DESC", params)
                output = io.StringIO(newline="")
                writer = csv.writer(output)
                columns = ["id", "created_at", "kind", "status", "name", "phone", "email", "preferred_contact", "question", "note", "source_path", "source_tag", "consent_at", "consent_version", "news"]
                writer.writerow(columns)
                for row in rows:
                    writer.writerow([self.csv_safe(row[key]) for key in columns])
                data = ("\ufeff" + output.getvalue()).encode("utf-8")
                return 200, [("Content-Type", "text/csv; charset=utf-8"), ("Content-Disposition", 'attachment; filename="teacherdesk-requests.csv"')], data
            total = connection.execute("SELECT count(*) FROM requests" + where, params).fetchone()[0]
            rows = connection.execute("SELECT * FROM requests" + where + " ORDER BY created_at DESC,id DESC LIMIT ? OFFSET ?", params + [limit, offset]).fetchall()
        return self._json(200, {"ok": True, "items": [self.record(row) for row in rows], "total": total, "limit": limit, "offset": offset})

    @staticmethod
    def csv_safe(value):
        if isinstance(value, str) and value.lstrip(" \t\r\n").startswith(("=", "+", "-", "@")):
            return "'" + value
        return value

    def update_request(self, environ, request_id):
        body = json_body(environ)
        if not body or any(key not in {"status", "note"} for key in body):
            raise HTTPError(422, "validation_error", "Можно изменить только статус и заметку.")
        fields = {}
        if "status" in body and (not isinstance(body["status"], str) or body["status"] not in STATUSES):
            fields["status"] = "Некорректный статус."
        if "note" in body and (not isinstance(body["note"], str) or len(body["note"]) > 4000 or "\x00" in body["note"]):
            fields["note"] = "Заметка должна быть текстом до 4000 символов."
        if fields:
            raise HTTPError(422, "validation_error", "Проверьте поля.", fields)
        with self.session() as connection:
            row = connection.execute("SELECT * FROM requests WHERE id=?", (request_id,)).fetchone()
            if not row:
                raise HTTPError(404, "not_found", "Обращение не найдено.")
            assignments, values = ["updated_at=?"], [utc_now()]
            for key in ("status", "note"):
                if key in body:
                    assignments.append(key + "=?")
                    values.append(body[key].strip())
            connection.execute("UPDATE requests SET " + ",".join(assignments) + " WHERE id=?", values + [request_id])
            updated = connection.execute("SELECT * FROM requests WHERE id=?", (request_id,)).fetchone()
        return self._json(200, {"ok": True, "item": self.record(updated)})

    def serve_static(self, environ):
        path = environ.get("PATH_INFO", "/")
        if path.startswith("//") or "\\" in path or "\x00" in path or any(part.startswith(".") for part in path.split("/") if part):
            raise HTTPError(404, "not_found", "Адрес не найден.")
        if path.rstrip("/") == "/admin":
            if path == "/admin":
                return self.redirect_directory(environ)
            target = Path(__file__).with_name("admin.html")
        else:
            site = self.config["SITE_DIR"]
            target = (site / path.lstrip("/")).resolve()
            if target != site and site not in target.parents:
                raise HTTPError(404, "not_found", "Адрес не найден.")
            if target.is_dir():
                if not path.endswith("/"):
                    return self.redirect_directory(environ)
                target = (target / "index.html").resolve()
                if site not in target.parents:
                    raise HTTPError(404, "not_found", "Адрес не найден.")
        status = 200
        if not target.is_file():
            status, target = 404, self.config["SITE_DIR"] / "404.html"
            if not target.is_file():
                raise HTTPError(404, "not_found", "Адрес не найден.")
        mime = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        if mime.startswith("text/") or mime in {"application/javascript", "image/svg+xml"}:
            mime += "; charset=utf-8"
        return status, [("Content-Type", mime)], target.read_bytes()

    @staticmethod
    def redirect_directory(environ):
        path = environ.get("PATH_INFO", "/")
        location = quote(path, safe="/" ) + "/"
        query = environ.get("QUERY_STRING", "")
        if query:
            location += "?" + query
        return 301, [("Location", location)], b""


def make_app(overrides=None):
    return Application(config_from_env(overrides))


application = make_app()
