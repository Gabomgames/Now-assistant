"""Inspect real capabilities or route typed text; no default audio backend is installed."""
import argparse
from dataclasses import asdict, replace
import getpass
import json
import os

from now_engine.assistant import LocalAssistant

from .contracts import VoicePermissions, VoiceSettings
from .errors import VoiceError
from .session import VoiceSession


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text")
    parser.add_argument("--language", choices=("pt-BR", "en-US"))
    parser.add_argument("--capabilities", action="store_true")
    parser.add_argument("--speak", action="store_true", help="requires installed and authorized TTS/output adapters")
    parser.add_argument("--memory-directory")
    parser.add_argument("--memory-password-env")
    args = parser.parse_args(argv)
    if not args.capabilities and args.text is None:
        parser.error("provide --text or --capabilities")
    settings = VoiceSettings()
    try:
        if args.memory_directory:
            from now_memory import MemoryStore
            from now_memory.store import MemoryErrorBase
            password = os.environ.get(args.memory_password_env) if args.memory_password_env else getpass.getpass("Memory passphrase: ")
            if password is None:
                raise ValueError("the named memory password variable is not set")
            try:
                with MemoryStore.open(args.memory_directory, password) as memory:
                    settings = VoiceSettings.from_preferences(memory.get_preferences())
            except MemoryErrorBase as error:
                print(json.dumps({"status": "error", "code": "MEMORY_LOCKED_OR_DISABLED", "message": str(error)}))
                return 2
        if args.language:
            settings = replace(settings, language=args.language)
        session = VoiceSession(LocalAssistant(), settings=settings)
        if args.capabilities:
            print(json.dumps(session.capabilities))
            return 0
        session.enable(VoicePermissions(playback=args.speak))
        result = session.respond_text(args.text, speak=args.speak)
        print(json.dumps({"mode": "audio" if result.playback_completed else "text", **asdict(result)}, ensure_ascii=False))
        return 0
    except (EOFError, KeyboardInterrupt):
        print(json.dumps({"status": "cancelled"}))
        return 130
    except VoiceError as error:
        print(json.dumps({"status": "error", "code": error.code, "message": str(error)}))
        return 2
    except (ValueError, OSError) as error:
        print(json.dumps({"status": "error", "code": "INVALID_CONFIGURATION", "message": str(error)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
