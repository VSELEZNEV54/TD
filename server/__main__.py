"""Local preview only. Use Gunicorn behind HTTPS for deployment."""

import argparse
import logging
import os
from socketserver import ThreadingMixIn
from wsgiref.simple_server import WSGIServer, make_server

from .app import application


class ThreadedServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True


def main():
    parser = argparse.ArgumentParser(description="TeacherDesk local website and API")
    parser.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8131")))
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    print("TeacherDesk: http://%s:%s/" % (args.host, args.port), flush=True)
    print("Admin: /admin/ (ADMIN_TOKEN from .env)", flush=True)
    with make_server(args.host, args.port, application, server_class=ThreadedServer) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
