import argparse

from . import main


def cli():
    parser = argparse.ArgumentParser(description="HookBus Dashboard")
    parser.add_argument("--port", type=int, default=8900, help="HTTP port (default: 8900)")
    parser.add_argument("--db", default=None, help="Path to CRE SQLite database")
    args = parser.parse_args()
    main(port=args.port, db_path=args.db)


if __name__ == "__main__":
    cli()
