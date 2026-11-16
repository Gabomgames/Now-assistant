"""Capture a real running Qt application with actual deterministic Engine replies."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="new, non-existing output directory")
    args = parser.parse_args()
    from now_desktop.smoke import capture
    report = capture(args.output)
    print(f"Actual GUI + HTTP Engine: {len(report['offline_commands'])} offline commands; {report['qt_platform']}")
    print("Captures and results:", args.output.resolve())
    print("This does not test model inference, microphone, speech, wake word or a Windows build.")


if __name__ == "__main__":
    main()
