"""
ブラウザで条件を選んで実行する画面（ローカル専用）

起動: python3 app.py  →  http://localhost:8765 を開く
"""
from __future__ import annotations

import csv
import io
import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import scraper
from options import CATEGORIES, PREFECTURES, fetch_cities

PORT = 8765
INDEX = Path(__file__).with_name("static") / "index.html"


class Job:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.running = False
        self.stop_requested = False
        self.logs: list[str] = []
        self.results: list[scraper.Place] = []

    def log(self, message: str) -> None:
        with self.lock:
            self.logs.append(message)
            del self.logs[:-300]

    def start(self, cond: scraper.Condition, headless: bool) -> bool:
        with self.lock:
            if self.running:
                return False
            self.running, self.stop_requested = True, False
            self.logs, self.results = [], []
        threading.Thread(target=self._run, args=(cond, headless), daemon=True).start()
        return True

    def _run(self, cond: scraper.Condition, headless: bool) -> None:
        try:
            scraper.run(cond, on_log=self.log, on_match=self.results.append,
                        should_stop=lambda: self.stop_requested, headless=headless)
        except Exception as exc:
            self.log(f"エラー: {exc}")
        finally:
            self.running = False

    def status(self) -> dict:
        with self.lock:
            return {
                "running": self.running,
                "logs": self.logs[-80:],
                "results": [p.to_row() for p in self.results],
            }

    def csv_bytes(self) -> bytes:
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow([label for _, label in scraper.CSV_COLUMNS])
        for place in list(self.results):
            row = place.to_row()
            writer.writerow([row[key] for key, _ in scraper.CSV_COLUMNS])
        return buf.getvalue().encode("utf-8-sig")


JOB = Job()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args) -> None:  # アクセスログは出さない
        pass

    def _send(self, body: bytes, content_type: str, status: int = 200, extra: dict | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, data, status: int = 200) -> None:
        self._send(json.dumps(data, ensure_ascii=False).encode(), "application/json; charset=utf-8", status)

    def do_GET(self) -> None:
        url = urlparse(self.path)
        if url.path == "/":
            self._send(INDEX.read_bytes(), "text/html; charset=utf-8")
        elif url.path == "/api/options":
            self._json({"prefectures": PREFECTURES, "categories": CATEGORIES})
        elif url.path == "/api/cities":
            self._json(fetch_cities(parse_qs(url.query).get("pref", [""])[0]))
        elif url.path == "/api/status":
            self._json(JOB.status())
        elif url.path == "/api/download.csv":
            self._send(JOB.csv_bytes(), "text/csv; charset=utf-8",
                       extra={"Content-Disposition": 'attachment; filename="gmaps_no_ubereats.csv"'})
        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        body = json.loads(self.rfile.read(length) or b"{}")
        if self.path == "/api/start":
            if body.get("prefecture") not in PREFECTURES or not body.get("category"):
                return self._json({"error": "都道府県と業種を選んでください"}, 400)
            cond = scraper.Condition(
                prefecture=body["prefecture"],
                city=(body.get("city") or "").strip(),
                category=body["category"].strip(),
                phone=body.get("phone", scraper.PHONE_ANY),
                mode=body.get("mode", scraper.MODE_ORDER_NO_UBER),
                limit=max(1, min(int(body.get("limit") or 100), 500)),
                strict_area=bool(body.get("strict_area", True)),
            )
            if not JOB.start(cond, headless=not body.get("headed")):
                return self._json({"error": "実行中です"}, 409)
            self._json({"ok": True})
        elif self.path == "/api/stop":
            JOB.stop_requested = True
            self._json({"ok": True})
        else:
            self._json({"error": "not found"}, 404)


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"http://localhost:{PORT} を開いてください（終了は Ctrl+C）")
    try:
        webbrowser.open(f"http://localhost:{PORT}")
    except Exception:
        pass
    server.serve_forever()


if __name__ == "__main__":
    main()
