import json
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

LOGGER = logging.getLogger(__name__)


class LocalApiHandler(BaseHTTPRequestHandler):
    handler_instance = None

    def log_message(self, format, *args):
        # Prevent default stdout logging to keep console clean
        LOGGER.debug(format % args)

    def _send_json(self, status_code: int, data: dict):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_POST(self):
        if self.handler_instance is None:
            self._send_json(500, {"ok": False, "error": "Handler not initialized"})
            return

        path = self.path.rstrip("/")
        if path == "/trigger/f6":
            LOGGER.info("Local API: Triggering F6 (capture_currency)")
            self.handler_instance.capture_currency()
            self._send_json(200, {"ok": True, "triggered": "F6"})
        elif path == "/trigger/f4":
            LOGGER.info("Local API: Triggering F4 (capture_stash_full)")
            self.handler_instance.capture_stash_full()
            self._send_json(200, {"ok": True, "triggered": "F4"})
        elif path == "/trigger/f5":
            LOGGER.info("Local API: Triggering F5 (trigger_affix_search)")
            self.handler_instance.trigger_affix_search()
            self._send_json(200, {"ok": True, "triggered": "F5"})
        elif path == "/trigger/f11":
            LOGGER.info("Local API: Triggering F11 (filter_items)")
            self.handler_instance.filter_items()
            self._send_json(200, {"ok": True, "triggered": "F11"})
        else:
            self._send_json(404, {"ok": False, "error": "Not Found"})

    def do_GET(self):
        self.do_POST()


def start_local_api(handler) -> None:
    LocalApiHandler.handler_instance = handler
    try:
        server = HTTPServer(("127.0.0.1", 18080), LocalApiHandler)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True, name="giaoit-local-api")
        server_thread.start()
        LOGGER.info("GiaoIT Local API listening on http://127.0.0.1:18080")
    except Exception:
        LOGGER.exception("Failed to start GiaoIT Local API server")
