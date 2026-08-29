from __future__ import annotations

import argparse
import sys
from pathlib import Path

from models.schemas import AnalysisPack

from .pipeline import ReceiverPipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cybersec")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan", help="Scan a repository with the analysis server")
    scan_parser.add_argument("pack", choices=[pack.value for pack in AnalysisPack])
    scan_parser.add_argument("workspace", nargs="?", default=".")

    watch_parser = subparsers.add_parser("watch", help="Scan and sync a repository with the analysis server")
    watch_parser.add_argument("pack", choices=[pack.value for pack in AnalysisPack])
    watch_parser.add_argument("workspace", nargs="?", default=".")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command not in ("scan", "watch"):
        parser.error("unsupported command")

    pack = AnalysisPack(args.pack)
    workspace = Path(args.workspace).resolve()

    pipeline = ReceiverPipeline()
    
    if args.command == "watch":
        session = pipeline.run_watch(workspace_path=str(workspace), pack=pack)
    else:
        session = pipeline.run(workspace_path=str(workspace), pack=pack)

    if args.command == "scan":
        print(f"Scanned {workspace}")
        print(f"Pack: {pack.value}")
        print(f"Status: {session.status}")
        print(f"Findings: {session.finding_count}")
        if session.error:
            print(f"Error: {session.error}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
