"""Build NOW Assistant on real Windows. See tools/windows_build.py for the implementation."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.windows_build import main

if __name__ == "__main__":
    raise SystemExit(main())
