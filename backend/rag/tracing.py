"""One JSON record per request, with a timed span per stage, so a bad answer can be traced to retrieval
(wrong chunks) or generation (right chunks, wrong answer). Logged on the "rag.trace" logger and, if
RAG_TRACE_FILE is set, appended to that file as JSON lines.

The question text is never recorded, only its hash and length: it can contain personal data.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

log = logging.getLogger("rag.trace")


class Trace:
    def __init__(self, query: str, index_meta: dict = None):
        meta = index_meta or {}
        self.id = uuid.uuid4().hex
        self._start = time.perf_counter()
        self.record = {
            "trace_id": self.id,
            "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "query_sha256": hashlib.sha256(query.encode("utf-8")).hexdigest()[:16],
            "query_chars": len(query),
            "index_version": meta.get("version"),
            "index_built_at": meta.get("built_at"),
            "index_stale": bool(meta.get("stale")),
            "spans": [],
            "errors": [],
        }

    @contextmanager
    def span(self, name: str, **attrs):
        data = {"name": name, **attrs}
        t = time.perf_counter()
        try:
            yield data
        except Exception as e:
            data["error"] = type(e).__name__
            raise
        finally:
            data["ms"] = round((time.perf_counter() - t) * 1000, 1)
            self.record["spans"].append(data)

    def error(self, stage: str, exc: Exception):
        self.record["errors"].append({"stage": stage, "type": type(exc).__name__, "message": str(exc)[:300]})
        log.warning("rag %s failed (trace %s): %s", stage, self.id, exc)

    def finish(self, status: str, **attrs):
        self.record.update(status=status, total_ms=round((time.perf_counter() - self._start) * 1000, 1), **attrs)
        write(self.record)


def write(record: dict):
    """Tracing must never break a request."""
    try:
        line = json.dumps(record, default=str)
        log.info(line)
        path = os.getenv("RAG_TRACE_FILE")
        if path:
            with open(path, "a", encoding="utf-8") as fh:
                fh.write(line + "\n")
    except Exception:
        log.exception("could not write trace")


def chunk_events(items: list) -> list:
    """Which chunks a stage returned, for attribution."""
    out = []
    for it in items:
        m = it["doc"].metadata
        out.append({"chunk_id": m.get("chunk_id"), "file": m.get("file"), "section": m.get("section"),
                    "page": m.get("page"), "score": round(float(it.get("rerank_score", it.get("hybrid_score", 0.0))), 3)})
    return out
