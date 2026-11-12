"""로컬 대시보드 서버.  python3 server.py  →  http://127.0.0.1:8765"""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import db

INDEX = Path(__file__).with_name("index.html")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/":
            self.reply(INDEX.read_bytes(), "text/html; charset=utf-8")
        elif url.path == "/api/data":
            asof = parse_qs(url.query).get("asof", [None])[0]
            con = db.connect()
            try:
                body = json.dumps(db.snapshot(con, asof)).encode()
            finally:
                con.close()
            self.reply(body, "application/json")
        else:
            self.send_error(404)

    def reply(self, body, ctype):
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    print("http://127.0.0.1:8765")
    ThreadingHTTPServer(("127.0.0.1", 8765), Handler).serve_forever()
