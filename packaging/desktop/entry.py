import os
import sys

# PyInstaller --windowed sets stdio to None on Windows. Uvicorn's logging setup
# expects valid streams even though access logging is disabled.
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

from now_desktop.__main__ import main

if __name__ == "__main__":
    raise SystemExit(main())
