import argparse
import os

from . import main


def cli():
    default_port = int(os.environ.get("HOOKBUS_DASHBOARD_PORT", "8901"))
    parser = argparse.ArgumentParser(description="HookBus Dashboard")
    parser.add_argument("--port", type=int, default=default_port, help=f"HTTP port (default: {default_port})")
    parser.add_argument("--db", default=None, help="Path to CRE SQLite database")
    args = parser.parse_args()
    main(port=args.port, db_path=args.db)


if __name__ == "__main__":
    cli()
