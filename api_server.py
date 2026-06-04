from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import threading
import urllib.parse
from downloader import YtDownloader
from logger import logger


_handler_ref = None


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _check_origin(self):
        origin = self.headers.get("Origin")
        if origin and (origin.startswith("chrome-extension://") or origin.startswith("moz-extension://")):
            return origin
        return None

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        origin = self._check_origin()
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/status":
            self._send_json({"status": "ok"})
        elif parsed.path == "/formats":
            params = urllib.parse.parse_qs(parsed.query)
            url = params.get("url", [None])[0]
            if not url:
                self._send_json({"error": "Missing url"}, 400)
                return
            try:
                app = self.app
                dl_path = app.get_download_path() if app else os.path.expanduser("~/Downloads")
                dl = YtDownloader(dl_path)
                formats = dl.list_formats(url)
                self._send_json({"formats": formats})
            except Exception as e:
                self._send_json({"error": str(e)})
        else:
            self._send_json({"error": "Not found"}, 404)

    def do_POST(self):
        if self.path == "/download":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode() if length else "{}"
            data = json.loads(body)
            url = data.get("url", "")
            fmt = data.get("format", "best")
            if not url:
                self._send_json({"status": "error", "msg": "Missing url"})
                return
            
            origin = self._check_origin()
            if not origin and self.headers.get("Origin"):
                self._send_json({"error": "Unauthorized origin"}, 403)
                return

            self._send_json({"status": "ok"})
            app = self.app
            if app:
                app.handle_extension_download(url, fmt)
        else:
            self._send_json({"error": "Not found"}, 404)

    def do_OPTIONS(self):
        self.send_response(204)
        origin = self._check_origin()
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


class APIServer:
    def __init__(self, host="127.0.0.1", port=9876):
        self._host = host
        self._port = port
        self._server = None

    def start(self, app_ref):
        class HandlerWithApp(_Handler):
            app = app_ref

        try:
            self._server = HTTPServer((self._host, self._port), HandlerWithApp)
            t = threading.Thread(target=self._server.serve_forever, daemon=True)
            t.start()
        except Exception as e:
            logger.error(f"Failed to start API server: {e}")

    def stop(self):
        if self._server:
            self._server.shutdown()
