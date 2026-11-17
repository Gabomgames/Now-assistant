"""Run NOW Assistant desktop, or its private owned Engine child."""
import argparse
import os
from pathlib import Path


def default_data_directory():
    if os.name == "nt":
        return Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local"))) / "NOWAssistant"
    return Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share"))) / "now-assistant"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=default_data_directory())
    parser.add_argument("--engine-child", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--port", type=int, help=argparse.SUPPRESS)
    parser.add_argument("--smoke-output", type=Path, help="run actual offline GUI/API checks in temporary storage and capture results")
    parser.add_argument("--legacy-api", action="store_true", help="start with the compatible /v2 client")
    parser.add_argument("--evaluate", action="store_true", help="open the local model evaluation utility")
    parser.add_argument("--evaluate-child", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--evaluation-self-check", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--output", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--models", nargs="+", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.evaluate_child:
        from .evaluation import child_main
        return child_main(args.output, args.models)
    if args.evaluate or args.evaluation_self_check:
        from .evaluation import run
        return run(args.evaluation_self_check)
    if args.engine_child:
        from now_engine.desktop_api import main as engine_main
        if args.port is None:
            parser.error("child Engine requires a port")
        return engine_main(["--port", str(args.port)])
    if args.smoke_output:
        from .smoke import capture
        capture(args.smoke_output)
        return 0
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication
    from .engine_client import EngineClient
    from .runtime import EngineProcess
    from .theme import apply_theme
    from .window import MainWindow

    application = QApplication.instance() or QApplication([])
    application.setApplicationName("NOW Assistant")
    from .version import VERSION
    application.setApplicationVersion(VERSION)
    application.setOrganizationName("NOW")
    apply_theme(application)
    runtime = EngineProcess()
    try:
        runtime.start()
        client = EngineClient(runtime.url, runtime.token, runtime.instance,
                              protocol="v2" if args.legacy_api else "v1", force_protocol=args.legacy_api)
        window = MainWindow(client, args.data_dir)
        window.show()
        QTimer.singleShot(0, client.start)
        application.aboutToQuit.connect(runtime.stop)
        return application.exec()
    finally:
        runtime.stop()


if __name__ == "__main__":
    raise SystemExit(main())
