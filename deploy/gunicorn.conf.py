"""One process keeps the request limiter shared by all four threads."""
import os

bind = os.environ.get("BIND", "127.0.0.1:8131")
workers = 1
worker_class = "gthread"
threads = 4
timeout = 30
graceful_timeout = 30
keepalive = 5
worker_tmp_dir = "/tmp"
control_socket_disable = True
accesslog = "-"
errorlog = "-"
# Do not write query strings or Authorization headers to the access log.
access_log_format = '%(h)s %(t)s "%(m)s %(U)s" %(s)s %(b)s'
