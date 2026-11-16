"""Local memory controls; passphrases are read from a terminal or named environment variable."""
import argparse
import getpass
import json
import os
from pathlib import Path
import sqlite3

from .store import ConsentRequired, MemoryErrorBase, MemoryStore


def default_directory():
    if os.name == "nt":
        return Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local"))) / "NOWAI/memory"
    return Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share"))) / "now-ai/memory"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=default_directory())
    parser.add_argument("--password-env", help="name of an existing variable; never pass a password as an argument")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("init", "enable"):
        commands.add_parser(name).add_argument("--consent", action="store_true")
    for name in ("status", "get", "disable", "clear"):
        commands.add_parser(name)
    setter = commands.add_parser("set")
    setter.add_argument("name")
    setter.add_argument("value")
    commands.add_parser("delete").add_argument("name")
    commands.add_parser("export").add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "status":
            print(json.dumps(MemoryStore.status(args.directory)))
            return 0
        if args.command in {"init", "enable"} and not args.consent:
            raise ConsentRequired("pass --consent to explicitly enable local preferences")
        if args.password_env:
            passphrase = os.environ.get(args.password_env)
            if passphrase is None:
                raise ValueError("the named password variable is not set")
        else:
            passphrase = getpass.getpass("Memory passphrase: ")
            if args.command == "init" and getpass.getpass("Confirm passphrase: ") != passphrase:
                raise ValueError("passphrases do not match")
        if args.command == "init":
            with MemoryStore.create(args.directory, passphrase, consent=args.consent):
                pass
        else:
            with MemoryStore.open(args.directory, passphrase) as store:
                if args.command == "set":
                    try:
                        value = json.loads(args.value)
                    except json.JSONDecodeError:
                        value = args.value
                    store.set_preferences({args.name: value})
                elif args.command == "get":
                    print(json.dumps(store.get_preferences(), ensure_ascii=False))
                    return 0
                elif args.command == "disable":
                    store.disable()
                elif args.command == "enable":
                    store.enable(consent=args.consent)
                elif args.command == "delete":
                    store.delete(args.name)
                elif args.command == "clear":
                    store.clear()
                elif args.command == "export":
                    payload = json.dumps(store.export_preferences(), ensure_ascii=False, indent=2) + "\n"
                    descriptor = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                    with os.fdopen(descriptor, "w", encoding="utf-8") as target:
                        target.write(payload)
        print(json.dumps({"status": "ok", "operation": args.command}))
        return 0
    except (EOFError, KeyboardInterrupt):
        print(json.dumps({"status": "cancelled"}))
        return 130
    except (MemoryErrorBase, ValueError, OSError, sqlite3.Error) as error:
        print(json.dumps({"status": "error", "error": str(error)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
