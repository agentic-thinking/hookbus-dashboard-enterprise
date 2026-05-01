"""HookBus Dashboard HTTP handler - GET/POST API routes + SSE event stream."""

import json
import queue
import time
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse

from .template import HTML_TEMPLATE


# Global reference to bus monitor (set by __init__.py)
_monitor = None


def set_monitor(monitor):
    global _monitor
    _monitor = monitor


class HookBusDashboardHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the HookBus Dashboard."""

    def log_message(self, format, *args):
        pass  # Suppress default logging

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _send_html(self, html):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode())

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length).decode() if length else ""

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/" or path == "":
            self._send_html(HTML_TEMPLATE)

        elif path == "/api/subscribers":
            if _monitor:
                self._send_json({"subscribers": _monitor.get_subscribers()})
            else:
                self._send_json({"subscribers": []})

        elif path == "/api/publishers":
            if _monitor:
                self._send_json({"publishers": _monitor.get_publishers()})
            else:
                self._send_json({"publishers": []})

        elif path == "/api/events":
            if _monitor:
                events = _monitor.get_recent_events(limit=100)
                self._send_json({"events": events})
            else:
                self._send_json({"events": []})

        elif path == "/api/stats":
            if _monitor:
                self._send_json(_monitor.get_stats())
            else:
                self._send_json({})

        elif path == "/api/events/stream":
            self._handle_sse()

        else:
            self.send_response(404)
            self.end_headers()

    def _is_local_request(self):
        """True if the request came from 127.0.0.0/8 or ::1."""
        host = self.client_address[0] if self.client_address else ""
        return host.startswith("127.") or host == "::1" or host.startswith("192.168.") or host.startswith("10.") or host.startswith("172.16.") or host.startswith("172.17.") or host.startswith("172.18.") or host.startswith("172.19.") or host.startswith("172.2") or host.startswith("172.3")

    def do_POST(self):
        path = urlparse(self.path).path
        body = self._read_body()

        if path == "/api/subscribers/toggle":
            # Auth: localhost only (127.0.0.0/8 or ::1). Prevents lateral network takeover.
            if not self._is_local_request():
                self._send_json({"ok": False, "error": "Toggle requires localhost"}, 403)
                return
            if not _monitor:
                self._send_json({"ok": False, "error": "Monitor not running"}, 500)
                return
            try:
                data = json.loads(body)
                name = data.get("name", "")
                action = data.get("action", "")
                if not name or not action:
                    self._send_json({"ok": False, "error": "name and action required"}, 400)
                    return
                result = _monitor.toggle_subscriber(name, action)
                self._send_json(result)
            except json.JSONDecodeError:
                self._send_json({"ok": False, "error": "Invalid JSON"}, 400)
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)[:200]}, 500)

        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _handle_sse(self):
        """Server-Sent Events stream for real-time event delivery."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        if not _monitor:
            return

        try:
            while True:
                try:
                    event = _monitor.event_queue.get(timeout=15)
                    data = json.dumps(event)
                    self.wfile.write(f"data: {data}\n\n".encode())
                    self.wfile.flush()
                except queue.Empty:
                    # Send keepalive comment
                    self.wfile.write(b": keepalive\n\n")
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
