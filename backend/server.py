import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


PORT = int(os.environ.get("PORT", "8000"))
DATA_DIRECTORY = Path(os.environ.get("DATA_DIRECTORY", "/data"))
VISITS_FILE = DATA_DIRECTORY / "visits.txt"


class RequestHandler(BaseHTTPRequestHandler):
    def send_json(self, status_code: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/health/":
            self.send_json(200, {"service": "api", "status": "ok"})
            return

        if self.path == "/visits/":
            DATA_DIRECTORY.mkdir(parents=True, exist_ok=True)
            visits = int(VISITS_FILE.read_text() if VISITS_FILE.exists() else "0") + 1
            VISITS_FILE.write_text(str(visits))
            self.send_json(200, {"visits": visits})
            return

        self.send_json(404, {"detail": "Not found"})

    def log_message(self, message: str, *args: object) -> None:
        print(f"api: {message % args}", flush=True)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", PORT), RequestHandler)
    print(f"api listening on port {PORT}", flush=True)
    server.serve_forever()
