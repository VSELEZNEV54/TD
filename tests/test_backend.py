"""Integration tests using temporary real SQLite files and WSGI requests."""

import csv
import io
import json
import tempfile
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlencode
from wsgiref.util import setup_testing_defaults

from server.app import MAX_BODY, make_app


class BackendTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.site = self.root / "site"
        self.site.mkdir()
        (self.site / "index.html").write_text("<h1>TeacherDesk</h1>", encoding="utf-8")
        (self.site / "404.html").write_text("<h1>Missing</h1>", encoding="utf-8")
        (self.site / "features").mkdir()
        (self.site / "features" / "index.html").write_text("Features", encoding="utf-8")
        self.token = "test-admin-key-" + "x" * 32
        self.config = {
            "SITE_DIR": self.site, "DATA_DIR": self.root / "data", "ADMIN_TOKEN": self.token,
            "PUBLIC_ORIGIN": "", "TRUST_PROXY": False, "RATE_LIMIT": 100, "RATE_WINDOW": 600,
        }
        self.app = make_app(self.config)
        self.body = {"kind": "question", "name": "Анна", "phone": "", "email": "anna@example.test", "question": "Как начать?", "preferred_contact": "any", "consent": True, "news": False, "website": "", "source_path": "/features/", "source_tag": "faq"}

    def tearDown(self):
        self.temporary.cleanup()

    def call(self, method="GET", path="/api/health", payload=None, headers=None, raw=None, content_type="application/json", query="", app=None, ip="127.0.0.1", content_length=None):
        environment = {}
        setup_testing_defaults(environment)
        data = raw if raw is not None else (json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else b"")
        environment.update({"REQUEST_METHOD": method, "PATH_INFO": path, "QUERY_STRING": query, "REMOTE_ADDR": ip, "HTTP_HOST": "localhost", "wsgi.input": io.BytesIO(data), "CONTENT_TYPE": content_type, "CONTENT_LENGTH": str(len(data)) if content_length is None else content_length})
        for key, value in (headers or {}).items():
            environment["HTTP_" + key.upper().replace("-", "_")] = value
        captured = {}

        def start_response(status, response_headers):
            captured["status"] = int(status.split()[0])
            captured["headers"] = dict(response_headers)

        result = b"".join((app or self.app)(environment, start_response))
        captured["body"] = result
        captured["json"] = json.loads(result) if result and captured["headers"].get("Content-Type", "").startswith("application/json") else None
        return captured

    def submit(self, body=None, headers=None, app=None, **kwargs):
        return self.call("POST", "/api/requests", payload=self.body if body is None else body, headers=headers, app=app, **kwargs)

    def admin(self, method="GET", path="/api/admin/requests", payload=None, query="", token=None):
        return self.call(method, path, payload, {"Authorization": "Bearer " + (self.token if token is None else token)}, query=query)

    def create(self, **updates):
        body = dict(self.body, **updates)
        response = self.submit(body)
        self.assertEqual(response["status"], 201, response["body"])
        return response["json"]["id"]

    def test_question_is_durable_after_restart(self):
        request_id = self.create()
        restarted = make_app(self.config)
        response = self.call("GET", "/api/admin/requests", headers={"Authorization": "Bearer " + self.token}, app=restarted)
        self.assertEqual(response["json"]["total"], 1)
        item = response["json"]["items"][0]
        self.assertEqual(item["id"], request_id)
        self.assertEqual(item["status"], "new")
        self.assertEqual(item["source_tag"], "faq")
        self.assertEqual(item["consent_at"], item["created_at"])
        self.assertTrue(item["consent_at"].endswith("Z"))
        self.assertFalse(item["news"])
        self.assertNotIn("payload_hash", item)

    def test_consultation_question_is_optional(self):
        request_id = self.create(kind="consultation", question="", preferred_contact="phone", phone="+7 (999) 123-45-67")
        self.assertEqual(self.admin()["json"]["items"][0]["id"], request_id)

    def test_required_question_and_contact(self):
        for changes, expected in (({"question": ""}, "question"), ({"phone": "", "email": ""}, "email"), ({"name": "А"}, "name"), ({"consent": False}, "consent")):
            with self.subTest(changes=changes):
                response = self.submit(dict(self.body, **changes))
                self.assertEqual(response["status"], 422)
                self.assertIn(expected, response["json"]["fields"])
        self.assertEqual(self.admin()["json"]["total"], 0)

    def test_malformed_field_types_rejected(self):
        for key, value in (("name", True), ("phone", 79991234567), ("email", []), ("question", {}), ("kind", []), ("preferred_contact", {}), ("consent", "true"), ("news", "false"), ("source_path", 123), ("website", True)):
            with self.subTest(key=key):
                response = self.submit(dict(self.body, **{key: value}))
                self.assertEqual(response["status"], 422)
                self.assertIn(key, response["json"]["fields"])

    def test_invalid_contacts_and_preferred_contact(self):
        for changes, key in (({"phone": "+7ABC9991234567"}, "phone"), ({"phone": "1234567"}, "phone"), ({"email": "a@b"}, "email"), ({"preferred_contact": "phone"}, "phone"), ({"preferred_contact": "email", "email": "", "phone": "+79991234567"}, "email"), ({"preferred_contact": "telegram"}, "preferred_contact")):
            with self.subTest(changes=changes):
                response = self.submit(dict(self.body, **changes))
                self.assertEqual(response["status"], 422)
                self.assertIn(key, response["json"]["fields"])

    def test_honeypot_and_lengths(self):
        for key, value in (("website", "spam"), ("name", "a" * 101), ("question", "a" * 4001), ("source_path", "//external.test"), ("source_path", "/\\external.test"), ("source_tag", "a" * 101)):
            with self.subTest(key=key, length=len(value)):
                response = self.submit(dict(self.body, **{key: value}))
                self.assertEqual(response["status"], 422)
                self.assertIn(key, response["json"]["fields"])

    def test_bad_json_and_non_object(self):
        for raw in (b"{bad", b"[]", b"null", b"\xff", b""):
            with self.subTest(raw=raw):
                self.assertEqual(self.call("POST", "/api/requests", raw=raw)["status"], 400)
        self.assertEqual(self.call("POST", "/api/requests", raw=b"{}", content_length="invalid")["status"], 400)

    def test_payload_and_content_type_limits(self):
        self.assertEqual(self.call("POST", "/api/requests", raw=b" " * (MAX_BODY + 1))["status"], 413)
        self.assertEqual(self.call("POST", "/api/requests", payload=self.body, content_type="text/plain")["status"], 415)

    def test_idempotency_returns_existing_id(self):
        headers = {"Idempotency-Key": str(uuid.uuid4())}
        first, second = self.submit(headers=headers), self.submit(headers=headers)
        self.assertEqual((first["status"], second["status"]), (201, 200))
        self.assertEqual(first["json"]["id"], second["json"]["id"])
        self.assertEqual(self.admin()["json"]["total"], 1)

    def test_idempotency_conflict_and_invalid_key(self):
        headers = {"Idempotency-Key": str(uuid.uuid4())}
        self.submit(headers=headers)
        self.assertEqual(self.submit(dict(self.body, question="Другой вопрос"), headers=headers)["status"], 409)
        self.assertEqual(self.submit(headers={"Idempotency-Key": "bad"})["status"], 400)

    def test_idempotency_is_atomic_for_concurrent_requests(self):
        headers = {"Idempotency-Key": str(uuid.uuid4())}
        with ThreadPoolExecutor(max_workers=6) as pool:
            responses = list(pool.map(lambda _: self.submit(headers=headers), range(6)))
        self.assertEqual(sorted(response["status"] for response in responses), [200, 200, 200, 200, 200, 201])
        self.assertEqual(len({response["json"]["id"] for response in responses}), 1)
        self.assertEqual(self.admin()["json"]["total"], 1)

    def test_admin_auth_and_disabled_admin(self):
        self.create()
        self.assertEqual(self.call("GET", "/api/admin/requests")["status"], 401)
        self.assertEqual(self.admin(token="wrong")["status"], 401)
        self.assertEqual(self.call("GET", "/api/admin/requests/export.csv")["status"], 401)
        disabled = make_app(dict(self.config, ADMIN_TOKEN=""))
        self.assertEqual(self.call("GET", "/api/admin/requests", app=disabled)["status"], 503)
        with self.assertRaises(ValueError):
            make_app(dict(self.config, ADMIN_TOKEN="short"))

    def test_public_routes_do_not_expose_records_or_token(self):
        self.create()
        for path in ("/api/health", "/api/public-config", "/api/requests", "/api/requests/any", "/data/requests.sqlite3", "/server/data/requests.sqlite3"):
            with self.subTest(path=path):
                response = self.call("GET", path)
                self.assertNotIn(self.token.encode(), response["body"])
                self.assertNotIn(b"anna@example.test", response["body"])
        self.assertEqual(self.call()["json"], {"ok": True})
        self.assertEqual(self.call(path="/api/requests")["status"], 405)

    def test_admin_filters_unicode_search_and_pagination(self):
        question = self.create()
        consultation = self.create(name="Борис", kind="consultation", question="", email="boris@example.test")
        self.admin("PATCH", "/api/admin/requests/" + question, {"status": "closed"})
        for query, expected in (({"kind": "consultation"}, consultation), ({"status": "closed"}, question), ({"q": "анна"}, question), ({"q": "БОРИС"}, consultation)):
            with self.subTest(query=query):
                result = self.admin(query=urlencode(query))["json"]
                self.assertEqual(result["total"], 1)
                self.assertEqual(result["items"][0]["id"], expected)
        page = self.admin(query="limit=1&offset=1")["json"]
        self.assertEqual(page["total"], 2)
        self.assertEqual(len(page["items"]), 1)
        self.assertEqual(page["offset"], 1)
        self.assertEqual(self.admin(query=urlencode({"q": "%"}))["json"]["total"], 0)
        self.assertEqual(self.admin(query=urlencode({"q": "' OR 1=1--"}))["json"]["total"], 0)

    def test_invalid_filters_and_pagination(self):
        for query in ("status=unknown", "kind=unknown", "limit=0", "limit=101", "offset=-1", "limit=oops", "q=" + "a" * 201):
            with self.subTest(query=query):
                self.assertEqual(self.admin(query=query)["status"], 400)

    def test_patch_status_and_note_persist(self):
        request_id = self.create()
        path = "/api/admin/requests/" + request_id
        response = self.admin("PATCH", path, {"status": "in_progress", "note": "  Назначен звонок  "})
        self.assertEqual(response["status"], 200)
        self.assertEqual(response["json"]["item"]["note"], "Назначен звонок")
        self.assertEqual(response["json"]["item"]["status"], "in_progress")
        self.assertEqual(self.admin("PATCH", path, {"status": "closed"})["status"], 200)
        self.assertEqual(self.admin()["json"]["items"][0]["status"], "closed")

    def test_patch_rejects_invalid_updates(self):
        request_id = self.create()
        path = "/api/admin/requests/" + request_id
        for body in ({}, {"id": "other"}, {"status": "bad"}, {"status": []}, {"note": True}, {"note": "a" * 4001}):
            with self.subTest(body_keys=list(body)):
                self.assertEqual(self.admin("PATCH", path, body)["status"], 422)
        self.assertEqual(self.admin("PATCH", "/api/admin/requests/" + str(uuid.uuid4()), {"status": "closed"})["status"], 404)
        self.assertEqual(self.call("DELETE", path, headers={"Authorization": "Bearer " + self.token})["status"], 405)

    def test_csv_is_authenticated_filtered_and_formula_safe(self):
        self.create(name="=HYPERLINK(1)", question="\t@SUM(A1)", phone="+79991234567")
        self.create(name="Другое", kind="consultation", question="")
        response = self.admin(path="/api/admin/requests/export.csv", query="kind=question")
        self.assertEqual(response["status"], 200)
        self.assertTrue(response["body"].startswith(b"\xef\xbb\xbf"))
        rows = list(csv.DictReader(io.StringIO(response["body"].decode("utf-8-sig"))))
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]["name"].startswith("'="))
        self.assertTrue(rows[0]["question"].startswith("'@"))
        self.assertTrue(rows[0]["phone"].startswith("'+"))
        self.assertEqual(response["headers"]["Cache-Control"], "no-store")

    def test_public_rate_limit_and_retry_header(self):
        limited = make_app(dict(self.config, RATE_LIMIT=1))
        self.assertEqual(self.submit(app=limited)["status"], 201)
        response = self.submit(app=limited)
        self.assertEqual(response["status"], 429)
        self.assertGreater(int(response["headers"]["Retry-After"]), 0)

    def test_retry_does_not_consume_rate_limit(self):
        limited = make_app(dict(self.config, RATE_LIMIT=1))
        headers = {"Idempotency-Key": str(uuid.uuid4())}
        self.assertEqual(self.submit(app=limited, headers=headers)["status"], 201)
        self.assertEqual(self.submit(app=limited, headers=headers)["status"], 200)
        self.assertEqual(self.submit(app=limited)["status"], 429)

    def test_forwarded_header_ignored_unless_proxy_is_trusted(self):
        limited = make_app(dict(self.config, RATE_LIMIT=1))
        self.assertEqual(self.submit(app=limited, headers={"X-Forwarded-For": "10.0.0.1"})["status"], 201)
        self.assertEqual(self.submit(app=limited, headers={"X-Forwarded-For": "10.0.0.2"})["status"], 429)
        trusted = make_app(dict(self.config, RATE_LIMIT=1, TRUST_PROXY=True))
        self.assertEqual(self.submit(app=trusted, headers={"X-Forwarded-For": "10.0.0.1"})["status"], 201)
        self.assertEqual(self.submit(app=trusted, headers={"X-Forwarded-For": "10.0.0.2"})["status"], 201)
        self.assertEqual(self.submit(app=trusted, headers={"X-Forwarded-For": "spoofed, 10.0.0.1"})["status"], 429)

    def test_origin_rejection_and_same_origin(self):
        self.assertEqual(self.submit(headers={"Origin": "https://external.test"})["status"], 403)
        self.assertEqual(self.submit(headers={"Origin": "http://localhost"})["status"], 201)
        configured = make_app(dict(self.config, PUBLIC_ORIGIN="https://teacherdesk.test"))
        self.assertEqual(self.submit(app=configured, headers={"Origin": "http://localhost"})["status"], 403)
        self.assertEqual(self.submit(app=configured, headers={"Origin": "https://teacherdesk.test"})["status"], 201)
        self.assertEqual(self.call("OPTIONS", "/api/requests")["status"], 405)

    def test_static_paths_and_symlink_escape_are_denied(self):
        secret = self.root / "secret.txt"
        secret.write_text("private-content", encoding="utf-8")
        (self.site / "escape.txt").symlink_to(secret)
        for path in ("/../secret.txt", "/.env", "/.git/config", "/escape.txt", "/\\secret.txt", "//features", "/%2e%2e/secret.txt"):
            with self.subTest(path=path):
                response = self.call("GET", path)
                self.assertEqual(response["status"], 404)
                self.assertNotIn(b"private-content", response["body"])
        with self.assertRaises(ValueError):
            make_app(dict(self.config, DATA_DIR=self.site / "data"))

    def test_static_redirect_head_404_and_security_headers(self):
        response = self.call("GET", "/features", query="from=menu")
        self.assertEqual(response["status"], 301)
        self.assertEqual(response["headers"]["Location"], "/features/?from=menu")
        self.assertEqual(self.call("GET", "/features/")["body"], b"Features")
        self.assertEqual(self.call("HEAD", "/")["body"], b"")
        missing = self.call("GET", "/missing/")
        self.assertEqual(missing["status"], 404)
        self.assertIn(b"Missing", missing["body"])
        self.assertEqual(missing["headers"]["X-Content-Type-Options"], "nosniff")
        self.assertEqual(self.call()["headers"]["Cache-Control"], "no-store")

    def test_registration_configuration_and_safe_redirects(self):
        app = make_app(dict(self.config, REGISTER_URL="https://register.test/new", LOGIN_URL="https://login.test/auth"))
        public = self.call("GET", "/api/public-config", app=app)["json"]
        self.assertEqual(public, {"register_url": "https://register.test/new", "login_url": "https://login.test/auth"})
        self.assertEqual(self.call("GET", "/register", app=app)["headers"]["Location"], public["register_url"])
        self.assertEqual(self.call("GET", "/login/", app=app)["headers"]["Location"], public["login_url"])
        for url in ("javascript:alert(1)", "//example.test", "https://x.test/\r\nX-Test: bad"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                make_app(dict(self.config, REGISTER_URL=url))


if __name__ == "__main__":
    unittest.main()
