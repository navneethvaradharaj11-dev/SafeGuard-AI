from pathlib import Path
import sys
from urllib.parse import urlparse, unquote

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from web_dashboard import DashboardRequestHandler, TEMPLATES_DIR, STATIC_DIR, CONTROLLER

class handler(DashboardRequestHandler):
    def _normalize_path(self) -> str:
        for header_key in ("x-forwarded-uri", "x-vercel-sc-path", "x-invoke-path", "x-original-uri"):
            val = self.headers.get(header_key)
            if val:
                p = unquote(urlparse(val).path)
                if p and not p.startswith("/api/index.py"):
                    return p

        parsed = urlparse(self.path)
        p = unquote(parsed.path)

        if p == "/api/index.py" or p == "/api/index.py/":
            return "/"
        if p.startswith("/api/index.py/"):
            return p[len("/api/index.py"):]

        return p or "/"

    def do_GET(self) -> None:
        norm_path = self._normalize_path()
        self.path = norm_path

        if norm_path == "/" or norm_path == "":
            self._send_file(TEMPLATES_DIR / "index.html", "text/html; charset=utf-8")
            return
        if norm_path == "/service-bay":
            self._send_file(TEMPLATES_DIR / "service_bay.html", "text/html; charset=utf-8")
            return
        if norm_path == "/garage-setup":
            self._send_file(TEMPLATES_DIR / "garage_setup.html", "text/html; charset=utf-8")
            return
        if norm_path == "/api/state":
            self._send_json(CONTROLLER.get_state())
            return
        if norm_path in {"/favicon.ico", "/favicon.png", "/apple-touch-icon.png"}:
            target = (STATIC_DIR / norm_path.lstrip("/")).resolve()
            if target.exists() and target.is_file():
                self._send_file(target)
                return
        if norm_path.startswith("/static/"):
            relative = norm_path.removeprefix("/static/")
            target = (STATIC_DIR / relative).resolve()
            if target.exists() and target.is_file():
                self._send_file(target)
                return

        super().do_GET()

    def do_POST(self) -> None:
        norm_path = self._normalize_path()
        self.path = norm_path
        super().do_POST()
