"""Additive Windows launcher; preserve the original NOW CLI and API modules."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

SOURCE_ROOT = Path(__file__).resolve().parents[2]
if not getattr(sys, "frozen", False):
    sys.path.insert(0, str(SOURCE_ROOT))


def main(argv=None):
    # Keep emoji/pt-BR output usable both in a Windows console and when captured by tests.
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="NOW AI 0.2 — terminal ou API local")
    parser.add_argument("--api", action="store_true", help="iniciar API local em 127.0.0.1")
    parser.add_argument("--port", type=int, default=8000, help="porta da API (padrão: 8000)")
    args = parser.parse_args(argv)
    if not 1 <= args.port <= 65535:
        parser.error("a porta deve estar entre 1 e 65535")

    from dotenv import load_dotenv

    directory = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else SOURCE_ROOT
    load_dotenv(directory / ".env", override=False)
    os.environ.setdefault("ENABLE_GEMINI_FALLBACK", "false")
    if args.api:
        import uvicorn
        from now_engine.api import app

        uvicorn.run(app, host="127.0.0.1", port=args.port)
    else:
        from main import main as original_cli

        original_cli()


if __name__ == "__main__":
    main()
