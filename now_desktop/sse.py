"""Bounded incremental UTF-8 SSE decoding, independent of Qt and inference."""
import codecs
import json


class SSEDecoder:
    def __init__(self):
        self._utf8 = codecs.getincrementaldecoder("utf-8")()
        self._buffer = ""
        self._event, self._data = None, []

    def feed(self, data):
        self._buffer += self._utf8.decode(data)
        events = []
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            line = line.rstrip("\r")
            if len(line) > 65536:
                raise ValueError("SSE line limit exceeded")
            if not line:
                if self._event:
                    payload = json.loads("\n".join(self._data))
                    if not isinstance(payload, dict):
                        raise ValueError("invalid SSE object")
                    events.append((self._event, payload))
                self._event, self._data = None, []
            elif line.startswith("event:"):
                self._event = line[6:].strip()
            elif line.startswith("data:"):
                self._data.append(line[5:].lstrip(" "))
                if sum(map(len, self._data)) > 65536:
                    raise ValueError("SSE event limit exceeded")
        if len(self._buffer) > 65536:
            raise ValueError("SSE buffer limit exceeded")
        return events
