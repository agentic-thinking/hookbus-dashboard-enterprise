"""
HookBus Dashboard - Live visual dashboard for the HookBus event bus.

Shows publishers, the bus, subscribers, and a real-time event log.
Matches the agenticthinking.uk website visual style.

Usage:
    python3 -m cre.hookbus_dashboard              # Default port 8900
    python3 -m cre.hookbus_dashboard --port 8900   # Custom port
    python3 -m cre.hookbus_dashboard --db /path/to/cre.db
"""

import argparse
import os
import sys
from http.server import ThreadingHTTPServer

from .api import HookBusDashboardHandler, set_monitor
from .bus_monitor import BusMonitor


def main(port=8900, db_path=None):
    """Start the HookBus Dashboard server."""
    db_path = db_path or os.path.expanduser("~/.hookbus/data/auditor.db")
    bus_api_url = (
        os.environ.get("HOOKBUS_API_URL")
        or os.environ.get("HOOKBUS_BASE_URL")
        or os.environ.get("HOOKBUS_URL")
        or "http://localhost:18800"
    )

    if not os.path.exists(db_path):
        print(f"Auditor database not found at {db_path}; auditor fallback disabled by default.")
    print(f"HookBus API: {bus_api_url}")

    # Start bus monitor
    monitor = BusMonitor(db_path=db_path)
    set_monitor(monitor)
    monitor.start()

    # Start HTTP server
    server = ThreadingHTTPServer(("0.0.0.0", port), HookBusDashboardHandler)

    print(f"HookBus Dashboard running on http://0.0.0.0:{port}")
    print(f"Database fallback: {db_path}")
    print(f"Registry: {monitor.subscribers}")
    print("Press Ctrl+C to stop.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.shutdown()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HookBus Dashboard")
    parser.add_argument("--port", type=int, default=8900, help="HTTP port (default: 8900)")
    parser.add_argument("--db", default=None, help="Path to CRE SQLite database")
    args = parser.parse_args()
    main(port=args.port, db_path=args.db)
