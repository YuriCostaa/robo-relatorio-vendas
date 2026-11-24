"""Servidor local do portal de demonstração (portal_demo/), usado em testes e na demo."""

import functools
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PASTA_PORTAL = Path(__file__).resolve().parent.parent / "portal_demo"


class _SemLog(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def iniciar(porta: int = 8765) -> ThreadingHTTPServer:
    handler = functools.partial(_SemLog, directory=str(PASTA_PORTAL))
    servidor = ThreadingHTTPServer(("127.0.0.1", porta), handler)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    return servidor
