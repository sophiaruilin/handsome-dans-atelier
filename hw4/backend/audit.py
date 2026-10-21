"""Append-only audit trail of the agent loop: output/audit_trail.json (Problem 12).

Every chat turn writes events in order:
  run_start   - who (guest / logged in, never the email), page, the shopper's message (masked, truncated)
  model_step  - one per model response: step number, finish reason, the tool calls it asked for
  tool_call   - tool name + short arguments
  tool_result - tool name + short result
  retry       - a tool or the price fact-checker sent the model back to try again (and why)
  run_end     - stop reason, model requests, tokens, seconds, tools used

The file is a JSON array that only ever grows: a new event is written over the closing "]" and
the "]" is put back after it. Earlier entries are never rewritten, and the file is never cleared
between runs or server restarts. If the file is ever unreadable it's set aside (renamed), not deleted.
"""

from __future__ import annotations

import json
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import tools

AUDIT_PATH = Path(__file__).resolve().parent.parent / "output" / "audit_trail.json"
MAX_TEXT = 240  # characters kept from any argument, result or message

_lock = threading.Lock()
_EMAIL = re.compile(r"([A-Za-z0-9._%+-])[A-Za-z0-9._%+-]*@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")


def short(value: Any, limit: int = MAX_TEXT) -> str:
    """Compact, privacy-safe text for the log: JSON-ish, emails and card numbers masked, truncated."""
    if hasattr(value, "model_dump"):
        value = value.model_dump()
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, default=str, separators=(",", ":"))
    text, _ = tools.redact_card_numbers(text)
    text = _EMAIL.sub(r"\1***@\2", text)
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def record(event: dict[str, Any], path: Path | None = None) -> None:
    """Append one event (a timestamp is added) to the JSON array at `path`."""
    path = path or AUDIT_PATH
    entry = {"at": datetime.now(timezone.utc).isoformat(timespec="milliseconds"), **event}
    data = json.dumps(entry, ensure_ascii=False, default=str).encode("utf-8")
    with _lock:
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists() or path.stat().st_size == 0:
            path.write_bytes(b"[\n" + data + b"\n]\n")
            return
        with path.open("r+b") as f:
            f.seek(0, 2)
            size = f.tell()
            f.seek(max(0, size - 64))
            tail = f.read()
            close = tail.rfind(b"]")
            if close == -1:
                # Not a JSON array we wrote: keep it (renamed) and start a fresh file beside it.
                f.close()
                path.rename(path.with_suffix(f".unreadable-{datetime.now():%Y%m%d%H%M%S}.json"))
                path.write_bytes(b"[\n" + data + b"\n]\n")
                return
            f.seek(size - len(tail) + close)
            f.truncate()
            f.write(b",\n" + data + b"\n]\n")
