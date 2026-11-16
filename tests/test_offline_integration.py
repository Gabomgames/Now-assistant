"""Run actual CLI/API code with outbound connections denied; no model replies are mocked."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from now_engine.processes import stop_owned_process

ROOT = Path(__file__).resolve().parents[1]
ENVIRONMENT = {**os.environ, "ENABLE_GEMINI_FALLBACK": "false", "PYTHONIOENCODING": "utf-8"}


class OfflineIntegrationTests(unittest.TestCase):
    def test_terminal_with_all_connections_denied(self):
        code = '''
import atexit,json,runpy,sys
attempts=[]
def deny(event,args):
    if event == "socket.connect":
        attempts.append(args[1])
        raise PermissionError("outbound network disabled by regression test")
sys.addaudithook(deny)
atexit.register(lambda: print("OFFLINE_AUDIT="+json.dumps({"attempts":len(attempts),"only_local_ollama":all(a[0]=="127.0.0.1" and a[1]==11434 for a in attempts)}),file=sys.stderr))
runpy.run_path("main.py",run_name="__main__")
'''
        result = subprocess.run(
            [sys.executable, "-c", code], cwd=ROOT, env=ENVIRONMENT,
            input="ajuda\nhoras\ndata\nExplique uma variável.\nsair\n",
            text=True, encoding="utf-8", capture_output=True, timeout=20, check=True,
        )
        self.assertEqual(result.stdout.count("NOW [offline]:"), 3)
        self.assertIn("NOW [unavailable]:", result.stdout)
        self.assertIn("Agora são", result.stdout)
        self.assertIn("Hoje é", result.stdout)
        audit = json.loads(result.stderr.split("OFFLINE_AUDIT=", 1)[1].strip())
        self.assertEqual(audit, {"attempts": 1, "only_local_ollama": True})

    def test_fastapi_with_all_outbound_connections_denied(self):
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        code = '''
import asyncio,sys
# On Windows the event loop creates an internal socketpair using a loopback
# connect. Bootstrap only that OS control pipe before denying every application
# connection, including during imports and all subsequent API/model requests.
loop=asyncio.new_event_loop()
def deny(event,args):
    if event == "socket.connect":
        raise PermissionError("outbound network disabled by regression test")
sys.addaudithook(deny)
import uvicorn
from now_engine.api import app
try:
    config=uvicorn.Config(app,host="127.0.0.1",port=int(sys.argv[1]),log_level="warning")
    loop.run_until_complete(uvicorn.Server(config).serve())
finally:
    loop.close()
'''
        with tempfile.TemporaryDirectory() as temporary, (Path(temporary) / "server.log").open("w") as log:
            server = subprocess.Popen([sys.executable, "-c", code, str(port)], cwd=ROOT, env=ENVIRONMENT, stdout=log, stderr=log)
            try:
                base = f"http://127.0.0.1:{port}"

                def request(path, payload=None):
                    data = None if payload is None else json.dumps(payload).encode("utf-8")
                    req = Request(base + path, data=data, headers={"Content-Type": "application/json"})
                    try:
                        with urlopen(req, timeout=3) as response:
                            return response.status, json.load(response)
                    except HTTPError as error:
                        return error.code, json.load(error)

                for _ in range(100):
                    if server.poll() is not None:
                        detail = Path(log.name).read_text(encoding="utf-8", errors="replace")[-500:].replace("\n", " | ")
                        self.fail("offline API exited before becoming ready: " + detail)
                    try:
                        status, health = request("/health")
                        break
                    except URLError:
                        time.sleep(0.1)
                else:
                    self.fail("offline API startup timed out")
                self.assertEqual(status, 200)
                self.assertEqual(health["version"], "0.2.0")
                for message in ("oi", "ajuda", "horas", "data"):
                    status, answer = request("/v1/chat", {"message": message})
                    self.assertEqual(status, 200)
                    self.assertEqual(answer["provider"], "offline")
                for message in ("", "x" * 4001):
                    self.assertEqual(request("/v1/chat", {"message": message})[0], 422)
                status, answer = request("/v1/chat", {"message": "Explain a variable."})
                self.assertEqual(status, 200)
                self.assertEqual(answer["provider"], "unavailable")
            finally:
                stop_owned_process(server)


if __name__ == "__main__":
    unittest.main()
