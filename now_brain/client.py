"""Small native Python client for the local v1 contract; no embedded credentials."""
from contextlib import contextmanager
import json
from urllib.parse import urlsplit
from urllib.request import Request

from now_engine.providers import local_open

PREFIX = "/api/now/v1"


class Client:
    def __init__(self, url, token, *, timeout=190):
        parsed = urlsplit(url)
        if (parsed.scheme != "http" or parsed.hostname != "127.0.0.1" or not parsed.port
                or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment):
            raise ValueError("client accepts only its local Brain API")
        self.url, self.token, self.timeout = url, token, timeout

    def request(self, path, payload=None):
        return Request(self.url + PREFIX + path,
                       data=json.dumps(payload, ensure_ascii=False).encode() if payload is not None else None,
                       headers={"Authorization": "Bearer " + self.token, "Content-Type": "application/json"})

    def json(self, path, payload=None):
        with local_open(self.request(path, payload), timeout=self.timeout) as response:
            return json.load(response)

    @contextmanager
    def stream(self, payload):
        with local_open(self.request("/chat/stream", payload), timeout=self.timeout) as response:
            yield self.events(response)

    @staticmethod
    def events(response):
        event, data = None, []
        while True:
            raw = response.readline(131073)
            if not raw:
                break
            if len(raw) > 131072:
                raise ValueError("SSE line exceeds the local response contract")
            line = raw.decode("utf-8").rstrip("\r\n")
            if not line:
                if event:
                    yield event, json.loads("\n".join(data))
                event, data = None, []
            elif line.startswith("event: "):
                event = line[7:]
            elif line.startswith("data: "):
                data.append(line[6:])
