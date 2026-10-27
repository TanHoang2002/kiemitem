import json
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

LOGGER = logging.getLogger(__name__)


class LocalApiHandler(BaseHTTPRequestHandler):
    handler_instance = None

    def log_message(self, format, *args):
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

        parsed_url = urlparse(self.path)
        path = parsed_url.path.rstrip("/")
        query = parse_qs(parsed_url.query)
        account_id = query.get("account_id", [None])[0]

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            data = json.loads(body)
        except Exception:
            data = {}

        target_acc = data.get("game_account") or account_id or "GoldenDich#1856 / July"
        request_id = data.get("request_id")

        if path in ("/scan", "/trigger/f4"):
            LOGGER.info("Local API: Received scan trigger (F4) for account=%s, request_id=%s", target_acc, request_id)
            threading.Thread(
                target=self.handler_instance.capture_stash_full,
                kwargs={"account_id": target_acc, "request_id": request_id},
                daemon=True,
            ).start()
            self._send_json(200, {"ok": True, "action": "scan_started", "game_account": target_acc, "request_id": request_id})
        elif path == "/trigger/f6":
            LOGGER.info("Local API: Received currency trigger (F6) for account=%s, request_id=%s", target_acc, request_id)
            threading.Thread(
                target=self.handler_instance.capture_currency,
                kwargs={"account_id": target_acc, "request_id": request_id},
                daemon=True,
            ).start()
            self._send_json(200, {"ok": True, "action": "currency_scan_started", "game_account": target_acc, "request_id": request_id})
        elif path == "/trigger/f5":
            LOGGER.info("Local API: Triggering F5 (trigger_affix_search)")
            threading.Thread(target=self.handler_instance.trigger_affix_search, daemon=True).start()
            self._send_json(200, {"ok": True, "triggered": "F5"})
        elif path in ("/health", "/health/"):
            self._send_json(200, {"ok": True, "status": "online", "account": "GoldenDich#1856 / July"})
        elif path == "/trigger/f11":
            LOGGER.info("Local API: Triggering F11 (filter_items)")
            threading.Thread(target=self.handler_instance.filter_items, daemon=True).start()
            self._send_json(200, {"ok": True, "triggered": "F11"})
        else:
            self._send_json(404, {"ok": False, "error": "Not Found"})

    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path.rstrip("/")
        if path in ("/health", "/health/"):
            self._send_json(200, {"ok": True, "status": "online", "account": "GoldenDich#1856 / July"})
        else:
            self.do_POST()


def start_local_api(handler) -> None:
    LocalApiHandler.handler_instance = handler
    try:
        server = HTTPServer(("0.0.0.0", 18080), LocalApiHandler)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True, name="giaoit-local-api")
        server_thread.start()
        LOGGER.info("GiaoIT Local API listening on http://0.0.0.0:18080")
    except Exception:
        LOGGER.exception("Failed to start GiaoIT Local API server")

    try:
        from bridge.config import load_config
        from bridge.dispatcher import Dispatcher
        from bridge.retry_queue import RetryQueue
        from bridge.watcher import build_watcher
        cfg = load_config()
        for p in (cfg.pending_dir, cfg.sent_dir, cfg.failed_dir, cfg.received_dir, cfg.logs_dir, cfg.state_dir):
            p.mkdir(parents=True, exist_ok=True)
        retry_q = RetryQueue(cfg.retry_queue_file)
        disp = Dispatcher(config=cfg, retry_queue=retry_q, confirm_fn=None)
        watcher = build_watcher(cfg, disp.handle)
        watcher.start()
        LOGGER.info("GiaoIT Bridge PollingWatcher started automatically")
    except Exception:
        LOGGER.exception("Failed to start GiaoIT Bridge watcher")
