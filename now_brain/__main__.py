"""Start the independent local Brain service; never binds a public interface."""
import argparse
import os
from uuid import uuid4

from .api import create_app
from .provider import OllamaProvider


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--timeout", type=int, default=180, help="generation deadline in seconds, 1–900")
    args = parser.parse_args(argv)
    if not 1 <= args.port <= 65535 or not 1 <= args.timeout <= 900:
        parser.error("invalid port or timeout")
    token = os.getenv("NOW_BRAIN_TOKEN", "")
    if len(token) < 32 or not token.isascii():
        parser.error("set NOW_BRAIN_TOKEN to a private random ASCII process token (at least 32 characters)")
    import uvicorn
    app = create_app(token, instance_id=os.getenv("NOW_BRAIN_INSTANCE", str(uuid4())),
                     provider=OllamaProvider(timeout=args.timeout))
    uvicorn.run(app, host="127.0.0.1", port=args.port, access_log=False,
                log_level="warning", timeout_graceful_shutdown=2)


if __name__ == "__main__":
    main()
