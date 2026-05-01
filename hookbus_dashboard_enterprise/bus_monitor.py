"""
HookBus Monitor - Background threads for event polling and subscriber probing.

Polls CRE's SQLite for new events and probes subscriber sockets for health.
Feeds events into a queue consumed by the SSE endpoint.
"""

import json
import os
import queue
import signal
import socket
import subprocess
import threading
import time
import urllib.parse
import urllib.request
from pathlib import Path


SUBSCRIBERS_YAML_PATH = os.path.expanduser("~/.hookbus/subscribers.yaml")
# Docker containers use /root/.hookbus but host uses ~/.hookbus
# Map container paths to host paths for socket probing
SOCKET_PATH_MAP = {"/root/.hookbus": os.path.expanduser("~/.hookbus")}
# Display labels for subscriber names (overrides auto-title-case)
LABEL_MAP = {
    "cre": "CRE",
    "CRE-AgentProtect Light": "CRE-AgentProtect Light",
    "cre-agentprotect-light": "CRE-AgentProtect Light",
    "cre-agentprotect-enterprise": "CRE-AgentProtect Enterprise",
    "audit-trail": "Auditor",
    "kb-injector": "KB Injector",
    "dlp-filter": "DLP Filter",
    "session-memory": "Session Memory",
    "cre-light": "CRE Light",
    "hookbus-llm": "HookBus LLM",
}

CONTAINER_ALIASES = {
    "cre-agentprotect-light": ("hookbus-light-cre-agentprotect-1", "cre-agentprotect"),
    "CRE-AgentProtect Light": ("hookbus-light-cre-agentprotect-1", "cre-agentprotect"),
}

KNOWN_UI_PORTS = {
    "cre-agentprotect-enterprise": 8766,
    "auditor": 8877,
    "audit-trail": 8877,
    "agentspend": 8879,
    "hookbus-agentspend": 8879,
    "workflow": 8888,
    "compliance-manager": 8889,
    "compliance-notifier": 8889,
    "hookbus-llm": 8890,
}


def display_label(name: str) -> str:
    """Preserve explicit branded names; prettify only simple slug names."""
    if name in LABEL_MAP:
        return LABEL_MAP[name]
    if any(ch.isupper() for ch in name):
        return name
    return name.replace("-", " ").title()


def known_ui_port(name: str):
    return KNOWN_UI_PORTS.get(name)


class BusMonitor:
    """Background monitor for HookBus events and subscriber health."""

    def __init__(self, db_path=None, config_path=None):
        self.db_path = db_path or os.path.expanduser("~/.hookbus/data/auditor.db")
        self.config_path = config_path or SUBSCRIBERS_YAML_PATH
        self.bus_api_url = self._normalise_bus_api_url()
        self.bus_token = os.environ.get("HOOKBUS_TOKEN", "")
        self.use_auditor_fallback = os.environ.get("HOOKBUS_USE_AUDITOR_FALLBACK", "").lower() in {"1", "true", "yes"}
        self.event_queue = queue.Queue(maxsize=2000)
        self.last_event_id = 0
        self.subscribers = {}  # name -> {label, type, socket, status, pid}
        self.subscriber_enabled = {}  # name -> bool, dashboard/control-plane state
        self.publishers = {}  # source_name -> last_seen_timestamp
        self.stats = {"total": 0, "allow": 0, "deny": 0, "ask": 0, "events_per_min": 0}
        self._recent_events = []  # last 60s of event timestamps for rate calc
        self._lock = threading.Lock()
        self._started = False
        self._start_time = time.time()
        self._config_mtime = 0  # track config file changes

        # Load subscribers from bus config
        self._load_subscribers()

    def _normalise_bus_api_url(self):
        """Return the HookBus HTTP base URL used for live dashboard reads."""
        explicit = os.environ.get("HOOKBUS_API_URL") or os.environ.get("HOOKBUS_BASE_URL")
        raw = explicit or os.environ.get("HOOKBUS_URL") or "http://localhost:18800"
        raw = raw.strip().rstrip("/")
        if raw.endswith("/event"):
            raw = raw[:-6]
        return raw or "http://localhost:18800"

    def _bus_get(self, path, params=None):
        """GET a JSON payload from HookBus, returning None on failure."""
        if not self.bus_api_url:
            return None
        url = self.bus_api_url.rstrip("/") + path
        if params:
            url += "?" + urllib.parse.urlencode(params)
        try:
            req = urllib.request.Request(url)
            if self.bus_token:
                req.add_header("Authorization", f"Bearer {self.bus_token}")
            with urllib.request.urlopen(req, timeout=3) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            print(f"HookBus API read failed {path}: {exc}")
            return None

    def _load_subscribers(self):
        """Load subscribers from the bus's subscribers.yaml config file."""
        try:
            import yaml
        except ImportError:
            # Fall back to basic YAML parsing if PyYAML not available
            self._load_subscribers_basic()
            return

        if not os.path.exists(self.config_path):
            print(f"Warning: subscribers.yaml not found at {self.config_path}")
            return

        try:
            mtime = os.path.getmtime(self.config_path)
            if mtime == self._config_mtime:
                return  # no changes
            self._config_mtime = mtime

            with open(self.config_path) as f:
                config = yaml.safe_load(f)

            subs = config.get("subscribers", [])
            with self._lock:
                self.subscribers.clear()
                for sub in subs:
                    name = sub.get("name", "")
                    if not name:
                        continue
                    sock_path = sub.get("address", "")
                    # Map Docker container paths to host paths
                    for container_prefix, host_prefix in SOCKET_PATH_MAP.items():
                        if sock_path.startswith(container_prefix):
                            sock_path = sock_path.replace(container_prefix, host_prefix, 1)
                            break
                    metadata = sub.get("metadata", {}) or {}
                    ui_port = metadata.get("ui_port") or known_ui_port(name)
                    self.subscribers[name] = {
                        "name": name,
                        "label": display_label(name),
                        "type": sub.get("type", "sync"),
                        "socket": sock_path,
                        "cmd": "",
                        "status": "unknown",
                        "pid": None,
                        "ui_port": ui_port,
                        "has_ui": bool(metadata.get("has_ui", False) or known_ui_port(name)),
                    }
                    self.subscriber_enabled.setdefault(name, True)
        except Exception as e:
            print(f"Error loading subscribers.yaml: {e}")

    def _load_subscribers_basic(self):
        """Parse subscribers.yaml without PyYAML (basic line parsing)."""
        if not os.path.exists(self.config_path):
            return
        try:
            mtime = os.path.getmtime(self.config_path)
            if mtime == self._config_mtime:
                return
            self._config_mtime = mtime

            with open(self.config_path) as f:
                lines = f.readlines()

            current = {}
            subs = []
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("- name:"):
                    if current:
                        subs.append(current)
                    current = {"name": stripped.split(":", 1)[1].strip()}
                elif stripped.startswith("type:") and current:
                    current["type"] = stripped.split(":", 1)[1].strip()
                elif stripped.startswith("transport:") and current:
                    current["transport"] = stripped.split(":", 1)[1].strip()
                elif stripped.startswith("address:") and current:
                    current["address"] = stripped.split(":", 1)[1].strip()
                elif stripped.startswith("ui_port:") and current:
                    try:
                        current["ui_port"] = int(stripped.split(":", 1)[1].strip())
                    except ValueError:
                        pass
                elif stripped.startswith("has_ui:") and current:
                    current["has_ui"] = stripped.split(":", 1)[1].strip().lower() in {"1", "true", "yes"}
            if current:
                subs.append(current)

            with self._lock:
                self.subscribers.clear()
                for sub in subs:
                    name = sub.get("name", "")
                    if not name:
                        continue
                    sock_path = sub.get("address", "")
                    for container_prefix, host_prefix in SOCKET_PATH_MAP.items():
                        if sock_path.startswith(container_prefix):
                            sock_path = sock_path.replace(container_prefix, host_prefix, 1)
                            break
                    self.subscribers[name] = {
                        "name": name,
                        "label": display_label(name),
                        "type": sub.get("type", "sync"),
                        "socket": sock_path,
                        "cmd": "",
                        "status": "unknown",
                        "pid": None,
                        "ui_port": sub.get("ui_port") or known_ui_port(name),
                        "has_ui": bool(sub.get("has_ui", False) or known_ui_port(name)),
                    }
                    self.subscriber_enabled.setdefault(name, True)
        except Exception as e:
            print(f"Error parsing subscribers.yaml: {e}")

    def start(self):
        """Start background monitor threads."""
        if self._started:
            return
        self._started = True
        self._start_time = time.time()

        # Seed last_event_id from current max
        self._seed_event_cursor()

        target = self._poll_bus_events if self.bus_api_url else self._poll_events
        t1 = threading.Thread(target=target, daemon=True, name="event-poller")
        t1.start()

        t2 = threading.Thread(target=self._probe_subscribers, daemon=True, name="sub-prober")
        t2.start()

    def _seed_event_cursor(self):
        """Set cursor to current max event ID so we only stream new events."""
        events = self._fetch_bus_events(limit=500)
        if events:
            try:
                self.last_event_id = max(int(e.get("id") or 0) for e in events)
                return
            except (TypeError, ValueError):
                pass

        if not self.use_auditor_fallback:
            return

        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path, timeout=5)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(id) as max_id FROM audit_log")
            row = cursor.fetchone()
            if row and row["max_id"]:
                self.last_event_id = row["max_id"]
            conn.close()
        except Exception:
            pass

    def _poll_bus_events(self):
        """Poll HookBus live /api/events endpoint and feed SSE."""
        while True:
            events = self._fetch_bus_events(since=self.last_event_id, limit=200)
            now = time.time()
            for event in reversed(events):
                try:
                    event_id = int(event.get("id") or 0)
                except (TypeError, ValueError):
                    event_id = 0
                if event_id <= self.last_event_id:
                    continue
                self.last_event_id = event_id

                decision = (event.get("decision") or "").lower()
                with self._lock:
                    self.stats["total"] += 1
                    if decision in self.stats:
                        self.stats[decision] += 1
                    self._recent_events.append(now)
                    source = event.get("source") or self._extract_publisher(event)
                    if source:
                        self.publishers[source] = now

                try:
                    self.event_queue.put_nowait(event)
                except queue.Full:
                    try:
                        self.event_queue.get_nowait()
                        self.event_queue.put_nowait(event)
                    except queue.Empty:
                        pass

            with self._lock:
                cutoff = time.time() - 60
                self._recent_events = [t for t in self._recent_events if t > cutoff]
                self.stats["events_per_min"] = len(self._recent_events)

            time.sleep(0.5)

    def _poll_events(self):
        """Poll SQLite for new events every 500ms."""
        import sqlite3
        while True:
            try:
                conn = sqlite3.connect(self.db_path, timeout=5)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM audit_log WHERE id > ? ORDER BY id ASC LIMIT 50",
                    (self.last_event_id,),
                )
                rows = cursor.fetchall()
                conn.close()

                now = time.time()
                for row in rows:
                    event = dict(row)
                    self.last_event_id = event["id"]

                    # Update stats
                    with self._lock:
                        self.stats["total"] += 1
                        decision = (event.get("decision") or "").lower()
                        if decision in self.stats:
                            self.stats[decision] += 1
                        self._recent_events.append(now)

                        # Track publisher
                        source = event.get("session_id", "unknown")
                        # Try to extract a friendly name from session_id or layer
                        pub_name = self._extract_publisher(event)
                        self.publishers[pub_name] = now

                    # Push to SSE queue
                    try:
                        sse_event = {
                            "id": event["id"],
                            "tool_name": event.get("tool_name", ""),
                            "command": (event.get("tool_input") or "")[:120],
                            "decision": event.get("decision", ""),
                            "reason": (event.get("reason") or "")[:200],
                            "hook": event.get("hook", ""),
                            "source": event.get("source", "") or self._extract_publisher(event),
                            "timestamp": event.get("timestamp", ""),
                        }
                        self.event_queue.put_nowait(sse_event)
                    except queue.Full:
                        # Drop oldest
                        try:
                            self.event_queue.get_nowait()
                            self.event_queue.put_nowait(sse_event)
                        except queue.Empty:
                            pass

            except Exception:
                pass

            # Clean old rate entries
            with self._lock:
                cutoff = time.time() - 60
                self._recent_events = [t for t in self._recent_events if t > cutoff]
                self.stats["events_per_min"] = len(self._recent_events)

            time.sleep(0.5)

    def _extract_publisher(self, event):
        """Extract a friendly publisher name from event data."""
        source = event.get("source", "")
        session = event.get("session_id", "")

        # Use source field directly if available (auditor schema has it)
        if source:
            name = source.lower()
            if "claude" in name: return "Claude Code"
            if "hookbus-chat" in name: return "HookBus Chat"
            if "amp" in name: return "Amp"
            if "openclaw" in name: return "OpenClaw"
            if "openai" in name or "agents" in name: return "OpenAI Agents SDK"
            if "anthropic" in name: return "Anthropic SDK"
            if "e2e" in name or "test" in name or "verify" in name: return source
            return source[:25]

        if session and session != "default":
            return session[:20]
        return "Agent"

    def _probe_subscribers(self):
        """Probe subscriber sockets every 5 seconds. Also reloads config on changes."""
        while True:
            # Reload config if file changed (picks up new subscribers)
            self._load_subscribers()

            with self._lock:
                for name, sub in self.subscribers.items():
                    sock_path = sub["socket"]
                    if not sock_path or not os.path.exists(sock_path):
                        sub["status"] = "offline"
                        sub["pid"] = None
                        continue

                    # Try connecting to the socket
                    try:
                        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                        s.settimeout(1)
                        s.connect(sock_path)
                        s.close()
                        sub["status"] = "online"
                        # Try to find PID
                        sub["pid"] = self._find_pid_for_socket(sock_path)
                    except (ConnectionRefusedError, FileNotFoundError, OSError):
                        sub["status"] = "offline"
                        sub["pid"] = None

            time.sleep(5)

    def _find_pid_for_socket(self, sock_path):
        """Find PID of process listening on a Unix socket."""
        try:
            result = subprocess.run(
                ["lsof", "-t", sock_path],
                capture_output=True, text=True, timeout=3,
            )
            if result.returncode == 0 and result.stdout.strip():
                return int(result.stdout.strip().split("\n")[0])
        except Exception:
            pass
        return None

    def get_subscribers(self):
        """Return current subscriber states."""
        with self._lock:
            rows = []
            for s in self.subscribers.values():
                controllable = self._is_controllable(s)
                enabled = self.subscriber_enabled.get(s["name"], True)
                status = s["status"]
                if not enabled:
                    status = "disabled"
                if self._docker_container_for(s["name"]):
                    status = "online" if enabled else "disabled"
                rows.append({
                    "name": s["name"],
                    "label": s["label"],
                    "type": s["type"],
                    "status": status,
                    "pid": s["pid"],
                    "ui_port": s.get("ui_port"),
                    "has_ui": bool(s.get("has_ui", False)),
                    "controllable": controllable,
                    "enabled": enabled,
                })
            return rows

    def get_publishers(self):
        """Return recently-seen publishers."""
        bus_publishers = self._fetch_bus_publishers()
        if bus_publishers:
            return bus_publishers

        now = time.time()
        with self._lock:
            return [
                {
                    "name": name,
                    "last_seen": ts,
                    "age_seconds": int(now - ts),
                    "active": (now - ts) < 60,
                }
                for name, ts in sorted(self.publishers.items(), key=lambda x: x[1], reverse=True)
            ]

    def get_stats(self):
        """Return aggregate stats."""
        bus_stats = self._fetch_bus_stats()
        if bus_stats:
            return bus_stats

        with self._lock:
            uptime = int(time.time() - self._start_time)
            return {**self.stats, "uptime_seconds": uptime}

    def get_recent_events(self, limit=100):
        """Get recent events from HookBus, falling back to auditor SQLite only if enabled."""
        bus_events = self._fetch_bus_events(limit=limit)
        if bus_events:
            return bus_events

        if not self.use_auditor_fallback:
            return []

        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path, timeout=5)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,)
            )
            rows = cursor.fetchall()
            conn.close()
            events = []
            for row in rows:
                e = dict(row)
                # Map auditor fields to dashboard fields
                e["command"] = (e.get("tool_input") or "")[:120]
                e["hook"] = e.get("hook", "")
                if not e.get("source"):
                    e["source"] = self._extract_publisher(e)
                events.append(e)
            return events
        except Exception:
            return []

    def _fetch_bus_events(self, since=None, limit=100):
        params = {}
        if since is not None:
            params["since"] = int(since or 0)
        payload = self._bus_get("/api/events", params=params)
        if isinstance(payload, dict):
            events = payload.get("events", [])
        elif isinstance(payload, list):
            events = payload
        else:
            return []

        out = []
        for item in events[:limit]:
            if not isinstance(item, dict):
                continue
            event = dict(item)
            event["hook"] = event.get("hook") or event.get("event_type") or ""
            event["timestamp"] = event.get("timestamp") or event.get("event_timestamp") or ""
            if not event["timestamp"] and event.get("ts"):
                event["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(float(event["ts"])))
            event["source"] = event.get("source") or self._extract_publisher(event)
            tool_input = event.get("tool_input") or ""
            if isinstance(tool_input, (dict, list)):
                tool_input = json.dumps(tool_input, separators=(",", ":"))
            event["command"] = str(tool_input)[:120]
            out.append(event)
        return out

    def _fetch_bus_stats(self):
        payload = self._bus_get("/api/stats")
        if not isinstance(payload, dict):
            return {}
        stats = dict(payload)
        if "uptime_seconds" not in stats:
            stats["uptime_seconds"] = stats.get("uptime_s", 0)
        return stats

    def _fetch_bus_publishers(self):
        payload = self._bus_get("/api/publishers")
        if not isinstance(payload, dict):
            return []
        now = time.time()
        out = []
        for name, last_seen in sorted(payload.items(), key=lambda x: x[1], reverse=True):
            try:
                ts = float(last_seen)
            except (TypeError, ValueError):
                ts = now
            out.append({
                "name": name,
                "last_seen": ts,
                "age_seconds": int(max(0, now - ts)),
                "active": (now - ts) < 60,
            })
        return out


    def _docker_container_for(self, subscriber_name, all_states=False):
        """Return the docker container name if this subscriber maps to one.

        Matches subscriber name to a running container whose name contains the
        subscriber name (e.g. 'kb-injector' -> container 'kb-injector',
        'dlp-filter' -> 'dlp-filter'). Returns None if no match.
        """
        try:
            fmt = "{{.Names}}" if not all_states else "{{.Names}}\t{{.State}}"
            cmd = ["docker", "ps", "--format", fmt]
            if all_states:
                cmd.insert(2, "-a")
            out = subprocess.run(
                cmd,
                capture_output=True, text=True, timeout=3, check=False
            )
            if out.returncode != 0:
                return None
            names = [line.split("\t", 1)[0].strip() for line in out.stdout.splitlines() if line.strip()]
            wanted = [subscriber_name, *CONTAINER_ALIASES.get(subscriber_name, ())]
            # Exact match first
            for candidate in wanted:
                if candidate in names:
                    return candidate
            # Then contains match (e.g. 'hookbus-dlp-filter' contains 'dlp-filter')
            for n in names:
                if any(candidate and (candidate in n or n in candidate) for candidate in wanted):
                    return n
            return None
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return None

    def _is_controllable(self, sub):
        if self._docker_container_for(sub["name"], all_states=True):
            return True
        if sub.get("pid") or sub.get("cmd"):
            return True
        try:
            return bool(sub.get("socket") and self._find_pid_for_socket(sub["socket"]))
        except Exception:
            return False

    def _docker_stop(self, container):
        try:
            r = subprocess.run(["docker", "stop", container],
                               capture_output=True, text=True, timeout=15, check=False)
            return r.returncode == 0, (r.stderr or r.stdout).strip()[:200]
        except Exception as e:
            return False, str(e)[:200]

    def _docker_start(self, container):
        try:
            r = subprocess.run(["docker", "start", container],
                               capture_output=True, text=True, timeout=15, check=False)
            return r.returncode == 0, (r.stderr or r.stdout).strip()[:200]
        except Exception as e:
            return False, str(e)[:200]

    def toggle_subscriber(self, name, action):
        """Enable or disable a subscriber in the dashboard control plane.

        This intentionally does not start/stop containers. Process lifecycle is
        separate from routing policy; the UI toggle is an activation control.
        """
        with self._lock:
            sub = self.subscribers.get(name)
            if not sub:
                return {"ok": False, "error": f"Unknown subscriber: {name}"}

        if action == "stop":
            with self._lock:
                self.subscriber_enabled[name] = False
            return {"ok": True, "action": "disabled", "name": name}
        elif action == "start":
            with self._lock:
                self.subscriber_enabled[name] = True
            return {"ok": True, "action": "enabled", "name": name}
        else:
            return {"ok": False, "error": f"Unknown action: {action}"}

    def _stop_subscriber(self, sub):
        """Stop a subscriber. Prefers docker stop <container>; falls back to SIGTERM."""
        # Docker-first
        container = self._docker_container_for(sub["name"])
        if container:
            ok, msg = self._docker_stop(container)
            if ok:
                with self._lock:
                    sub["status"] = "offline"
                    sub["pid"] = None
                    sub["container"] = container
                return {"ok": True, "action": "docker_stopped", "name": sub["name"], "container": container}
            return {"ok": False, "error": f"docker stop failed: {msg}"}
        # Native-process fallback
        pid = sub.get("pid")
        if not pid:
            # Try to find it
            pid = self._find_pid_for_socket(sub["socket"])

        if not pid:
            return {"ok": False, "error": "Subscriber is not installed or is not managed by this dashboard"}

        try:
            os.kill(pid, signal.SIGTERM)
            # Wait up to 3s for socket to disappear
            for _ in range(6):
                time.sleep(0.5)
                if not os.path.exists(sub["socket"]):
                    break
            with self._lock:
                sub["status"] = "offline"
                sub["pid"] = None
            return {"ok": True, "action": "stopped", "name": sub["name"]}
        except ProcessLookupError:
            with self._lock:
                sub["status"] = "offline"
                sub["pid"] = None
            return {"ok": True, "action": "already_stopped", "name": sub["name"]}
        except PermissionError:
            return {"ok": False, "error": "Permission denied"}

    def _start_subscriber(self, sub):
        """Start a subscriber. Prefers docker start <container>; falls back to Popen."""
        # Docker-first: look for a stopped container matching this subscriber name
        try:
            r = subprocess.run(
                ["docker", "ps", "-a", "--format", "{{.Names}}\t{{.State}}"],
                capture_output=True, text=True, timeout=3, check=False,
            )
            if r.returncode == 0:
                container = self._docker_container_for(sub["name"], all_states=True)
                if container:
                    for line in r.stdout.splitlines():
                        parts = line.strip().split("\t")
                        if len(parts) != 2:
                            continue
                        cname, state = parts
                        if cname == container and state != "running":
                            ok, msg = self._docker_start(cname)
                            if ok:
                                with self._lock:
                                    sub["status"] = "online"
                                    sub["container"] = cname
                                return {"ok": True, "action": "docker_started", "name": sub["name"], "container": cname}
                            return {"ok": False, "error": f"docker start failed: {msg}"}
                        if cname == container and state == "running":
                            return {"ok": True, "action": "already_running", "name": sub["name"], "container": cname}
        except Exception:
            pass
        # Native-process fallback
        cmd = sub.get("cmd")
        if not cmd:
            return {"ok": False, "error": "Subscriber is not installed or has no start command configured"}

        # Check if already running
        if sub["status"] == "online":
            return {"ok": True, "action": "already_running", "name": sub["name"]}

        try:
            # Remove stale socket
            sock_path = sub["socket"]
            if os.path.exists(sock_path):
                os.unlink(sock_path)

            # Launch process
            proc = subprocess.Popen(
                cmd.split(),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )

            # Wait up to 5s for socket to appear
            for _ in range(10):
                time.sleep(0.5)
                if os.path.exists(sock_path):
                    with self._lock:
                        sub["status"] = "online"
                        sub["pid"] = proc.pid
                    return {"ok": True, "action": "started", "name": sub["name"], "pid": proc.pid}

            return {"ok": False, "error": "Process started but socket not created within 5s"}
        except Exception as e:
            return {"ok": False, "error": str(e)[:200]}
