"""Versioned vector index.

vectorstore/
  CURRENT                 id of the version being served (replaced atomically)
  versions/<id>/          index.faiss, chunks.pkl, meta.json (embedding model, corpus hashes, chunk counts)

A rebuild writes a new version, validates it, and only then moves CURRENT, so a crash half-way leaves the old
index serving. Chunks whose text is unchanged keep their old vector (matched by content hash). The previous
version is kept for rollback. No web or model imports here: the embedding function is passed in.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import pickle
import shutil
from datetime import datetime, timezone
from pathlib import Path

import faiss
import numpy as np

log = logging.getLogger(__name__)

KEEP_VERSIONS = 2


class IndexUnavailable(RuntimeError):
    pass


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def corpus_manifest(sources, root) -> dict:
    """{relative path: content hash}. Content, not mtime: a fresh clone or container must not look changed."""
    out = {}
    for source in sources:
        base = Path(source["path"])
        if base.exists():
            for p in sorted(list(base.rglob("*.pdf")) + list(base.rglob("*.txt"))):
                out[p.relative_to(root).as_posix()] = sha256_file(p)
    return out


def _read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def current_id(store: Path):
    try:
        return (store / "CURRENT").read_text(encoding="utf-8").strip() or None
    except OSError:
        return None


def _set_current(store: Path, version_id: str):
    tmp = store / "CURRENT.tmp"
    tmp.write_text(version_id, encoding="utf-8")
    os.replace(tmp, store / "CURRENT")


def _versions(store: Path) -> list:
    base = store / "versions"
    return sorted((p.name for p in base.iterdir() if p.is_dir()), reverse=True) if base.exists() else []


def load_version(store: Path, version_id: str, embedding_model: str):
    """-> (index, docs, meta). Raises IndexUnavailable if the version is missing, corrupt, or was built with a
    different embedding model (its vectors would be meaningless for our query vectors)."""
    d = store / "versions" / version_id
    meta = _read_json(d / "meta.json")
    if not meta:
        raise IndexUnavailable(f"index {version_id}: meta.json missing or unreadable")
    if meta.get("embedding_model") != embedding_model:
        raise IndexUnavailable(f"index {version_id} was built with {meta.get('embedding_model')}, not {embedding_model}")
    try:
        index = faiss.read_index(str(d / "index.faiss"))
        with open(d / "chunks.pkl", "rb") as fh:      # written by this module only; never load an untrusted file
            docs = pickle.load(fh)
    except Exception as e:
        raise IndexUnavailable(f"index {version_id} is corrupt: {e}") from e
    if index.ntotal != len(docs) or not docs:
        raise IndexUnavailable(f"index {version_id}: {index.ntotal} vectors for {len(docs)} chunks")
    return index, docs, meta


def _reusable_vectors(store: Path, embedding_model: str) -> dict:
    vid = current_id(store)
    if not vid:
        return {}
    try:
        index, docs, _ = load_version(store, vid, embedding_model)
    except IndexUnavailable:
        return {}
    return {sha256_text(d.page_content): index.reconstruct(i) for i, d in enumerate(docs)}


def validate(index, docs, vectors, manifest: dict, previous_meta) -> None:
    """Gate before a new version goes live."""
    if not docs or index.ntotal != len(docs):
        raise IndexUnavailable("new index is empty or does not match its chunks")
    if not np.isfinite(vectors).all() or (np.linalg.norm(vectors, axis=1) < 0.5).any():
        raise IndexUnavailable("new index has invalid vectors")
    step = max(len(docs) // 20, 1)
    for i in range(0, len(docs), step):                   # each sampled chunk must find itself (or a twin)
        score, _ = index.search(vectors[i:i + 1], 1)
        if score[0][0] < 0.99:
            raise IndexUnavailable(f"chunk {i} cannot be retrieved from the new index")
    # a file that used to produce chunks and now produces none means extraction silently failed
    had = set((previous_meta or {}).get("documents", {}))
    now = {d.metadata.get("rel_path") for d in docs}
    lost = sorted(p for p in had if p in manifest and (previous_meta["documents"][p]["chunks"] > 0) and p not in now)
    if lost:
        raise IndexUnavailable(f"no chunks extracted from: {', '.join(lost)}")


def build_version(store: Path, docs: list, embed, embedding_model: str, schema: int, manifest: dict) -> str:
    """Embed (reusing unchanged chunks), validate, publish. Returns the new version id."""
    if not docs:
        raise IndexUnavailable("the corpus produced no chunks")
    store.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    previous_meta = _read_json(store / "versions" / (current_id(store) or "-") / "meta.json")
    cache = _reusable_vectors(store, embedding_model)

    hashes = [sha256_text(d.page_content) for d in docs]
    todo = [i for i, h in enumerate(hashes) if h not in cache]
    fresh = np.asarray(embed([docs[i].page_content for i in todo]), dtype="float32") if todo else None
    new_vectors = dict(zip(todo, fresh)) if todo else {}
    vectors = np.asarray([new_vectors[i] if i in new_vectors else cache[h] for i, h in enumerate(hashes)],
                         dtype="float32")
    log.info("index build: %d chunks, %d embedded, %d reused", len(docs), len(todo), len(docs) - len(todo))

    documents = {p: {"sha256": h, "chunks": 0} for p, h in manifest.items()}
    for i, d in enumerate(docs):
        rel = d.metadata.get("rel_path")
        if rel in documents:
            documents[rel]["chunks"] += 1
        d.metadata.update(chunk_id=f"{hashes[i][:12]}-{i}", content_hash=hashes[i], embedding_model=embedding_model,
                          indexed_at=now.isoformat(timespec="seconds"))

    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)
    validate(index, docs, vectors, manifest, previous_meta)

    version_id = now.strftime("%Y%m%dT%H%M%S%f")
    d = store / "versions" / version_id
    d.mkdir(parents=True)
    faiss.write_index(index, str(d / "index.faiss"))
    with open(d / "chunks.pkl", "wb") as fh:
        pickle.dump(docs, fh)
    meta = {"version": version_id, "built_at": now.isoformat(timespec="seconds"), "embedding_model": embedding_model,
            "schema_version": schema, "chunks": len(docs), "embedded": len(todo), "documents": documents}
    (d / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")    # written last: marks completeness
    _set_current(store, version_id)

    for old in _versions(store)[KEEP_VERSIONS:]:
        shutil.rmtree(store / "versions" / old, ignore_errors=True)
    return version_id


def open_index(store: Path, manifest: dict, schema: int, embedding_model: str, make_docs, embed):
    """-> (index, docs, meta). Serves the current version if the corpus is unchanged, otherwise rebuilds.
    If the rebuild fails, the last good version keeps serving and meta["stale"] says why."""
    vid = current_id(store)
    meta = _read_json(store / "versions" / vid / "meta.json") if vid else None
    wanted = {p: h for p, h in manifest.items()}
    if (meta and meta.get("schema_version") == schema
            and {p: v["sha256"] for p, v in meta.get("documents", {}).items()} == wanted):
        try:
            return load_version(store, vid, embedding_model)
        except IndexUnavailable as e:
            log.error("%s; rebuilding", e)
    try:
        return load_version(store, build_version(store, make_docs(), embed, embedding_model, schema, manifest),
                            embedding_model)
    except Exception as e:
        log.exception("index build failed")
        candidates = [v for v in [current_id(store)] + _versions(store) if v]
        for old in dict.fromkeys(candidates):
            try:
                index, docs, old_meta = load_version(store, old, embedding_model)
                return index, docs, {**old_meta, "stale": str(e)}
            except IndexUnavailable as err:
                log.error("%s", err)
        raise IndexUnavailable(f"no usable index: {e}") from e
