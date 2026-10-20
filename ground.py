"""Ground station: talks to sat.py over TCP, serves the dashboard on http://localhost:8000"""
import json, socket, threading, time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SAT = ("127.0.0.1", 9000)
history, acks, conn = deque(maxlen=600), deque(maxlen=20), [None]


def link():
    while True:
        try:
            s = socket.create_connection(SAT)
            conn[0] = s
            for line in s.makefile():
                m = json.loads(line)
                (history if m["type"] == "tm" else acks).append(m)
        except OSError:
            pass
        conn[0] = None
        time.sleep(1)


class H(BaseHTTPRequestHandler):
    def reply(self, body, ctype="application/json", code=200):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.end_headers()
        self.wfile.write(body if isinstance(body, bytes) else json.dumps(body).encode())

    def do_GET(self):
        if self.path == "/api":
            self.reply({"linked": conn[0] is not None, "history": list(history), "acks": list(acks)})
        else:
            name = self.path.lstrip("/")
            name = name if name in ("dashboard.html", "index.html") else "app.html"
            self.reply((Path(__file__).parent / name).read_bytes(), "text/html")

    def do_POST(self):
        cmd = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if conn[0] is None:
            return self.reply({"error": "no link"}, code=503)
        conn[0].sendall((json.dumps(cmd) + "\n").encode())
        self.reply({"sent": cmd})

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    threading.Thread(target=link, daemon=True).start()
    print("dashboard: http://localhost:8000")
    ThreadingHTTPServer(("127.0.0.1", 8000), H).serve_forever()
