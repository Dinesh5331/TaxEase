"""Reciprocal rank fusion. Rank-based, so BM25 and cosine scores never need to be put on one scale
(the old min-max blend let one outlier score squash everything else)."""
from __future__ import annotations

RRF_K = 60


def rrf_fuse(rankings, weights=None, k: int = RRF_K) -> dict:
    """rankings: list of ranked lists of hashable keys, best first. Returns {key: score in (0, 1]}.

    The score is divided by the best possible score (first place in every list), so 1.0 means
    "ranked first by every retriever"; the pipeline's score thresholds keep a stable meaning.
    """
    weights = weights or [1.0] * len(rankings)
    if len(weights) != len(rankings):
        raise ValueError("one weight per ranking")
    best = sum(w / (k + 1) for w in weights) or 1.0
    scores = {}
    for ranking, w in zip(rankings, weights):
        seen = set()
        for rank, key in enumerate(ranking, start=1):
            if key in seen:                       # a list repeating a key must not vote twice
                continue
            seen.add(key)
            scores[key] = scores.get(key, 0.0) + w / (k + rank)
    return {key: s / best for key, s in scores.items()}
