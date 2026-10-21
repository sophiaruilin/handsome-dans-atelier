"""Problem 12: the audit trail is append-only, valid JSON, and privacy-safe.

Run from backend/:  python -m pytest -q
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import audit  # noqa: E402


def test_appends_keep_valid_json_and_never_lose_entries(tmp_path):
    path = tmp_path / "audit_trail.json"
    for i in range(3):
        audit.record({"run_id": "r1", "event": "tool_call", "n": i}, path)
    first = json.loads(path.read_text(encoding="utf-8"))
    assert [e["n"] for e in first] == [0, 1, 2]
    before = path.read_bytes()

    audit.record({"run_id": "r2", "event": "run_end", "stop_reason": "final_answer"}, path)
    after = json.loads(path.read_text(encoding="utf-8"))
    assert len(after) == 4 and after[:3] == first  # earlier entries untouched
    # Truly appended: the old bytes (minus the closing bracket) are a prefix of the new file.
    assert path.read_bytes().startswith(before[: before.rfind(b"]")])
    assert all("at" in e for e in after)


def test_never_wipes_an_existing_file_it_cannot_read(tmp_path):
    path = tmp_path / "audit_trail.json"
    path.write_text("not json at all", encoding="utf-8")
    audit.record({"event": "run_start"}, path)
    assert json.loads(path.read_text(encoding="utf-8"))[0]["event"] == "run_start"
    kept = list(tmp_path.glob("audit_trail.unreadable-*.json"))
    assert len(kept) == 1 and kept[0].read_text(encoding="utf-8") == "not json at all"


def test_short_masks_private_data_and_truncates():
    text = audit.short({"email": "handsome.dan@campuscustoms.yale.edu", "note": "card 4111 1111 1111 1111"})
    assert "handsome.dan@" not in text and "h***@campuscustoms.yale.edu" in text
    assert "4111 1111 1111 1111" not in text
    assert len(audit.short("x" * 1000)) == audit.MAX_TEXT
