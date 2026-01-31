from __future__ import annotations
from dataclasses import dataclass, field
from collections import deque
import re
import time
import numpy as np

URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)

@dataclass
class UserState:
    timestamps: deque[int] = field(default_factory=lambda: deque(maxlen=50))
    lengths: deque[int] = field(default_factory=lambda: deque(maxlen=50))
    dup_hashes: deque[int] = field(default_factory=lambda: deque(maxlen=50))
    link_flags: deque[int] = field(default_factory=lambda: deque(maxlen=50))
    mention_counts: deque[int] = field(default_factory=lambda: deque(maxlen=50))

def has_link(text: str) -> bool:
    return bool(URL_RE.search(text))

def content_hash(text: str) -> int:
    # simple stable-ish hash for duplicates
    return hash(text.strip().lower())

def extract_features(state: UserState, now_ts: int) -> dict:
    # No features if insufficient history
    ts = list(state.timestamps)
    if len(ts) < 3:
        return {
            "msg_rate_60s": 0.0,
            "avg_inter": 999.0,
            "var_inter": 999.0,
            "avg_len": float(np.mean(state.lengths)) if state.lengths else 0.0,
            "var_len": float(np.var(state.lengths)) if len(state.lengths) > 1 else 0.0,
            "dup_ratio": 0.0,
            "link_rate_60s": 0.0,
            "mention_rate_60s": 0.0,
        }

    # messages in last 60 seconds
    last_60 = [t for t in ts if now_ts - t <= 60]
    msg_rate_60s = len(last_60) / 60.0

    inter = np.diff(ts)
    avg_inter = float(np.mean(inter))
    var_inter = float(np.var(inter)) if len(inter) > 1 else 0.0

    lens = np.array(state.lengths, dtype=float) if state.lengths else np.array([0.0])
    avg_len = float(np.mean(lens))
    var_len = float(np.var(lens)) if len(lens) > 1 else 0.0

    # duplicate ratio in last N
    hashes = list(state.dup_hashes)
    dup_ratio = 0.0
    if len(hashes) >= 5:
        dup_ratio = 1.0 - (len(set(hashes)) / len(hashes))

    # link/mention rate in last 60 seconds
    # approximate by counting flags aligned with timestamps
    link_rate_60s = 0.0
    mention_rate_60s = 0.0
    if len(ts) == len(state.link_flags):
        link_rate_60s = sum(
            f for t, f in zip(ts, state.link_flags) if now_ts - t <= 60
        ) / 60.0
    if len(ts) == len(state.mention_counts):
        mention_rate_60s = sum(
            c for t, c in zip(ts, state.mention_counts) if now_ts - t <= 60
        ) / 60.0

    return {
        "msg_rate_60s": msg_rate_60s,
        "avg_inter": avg_inter,
        "var_inter": var_inter,
        "avg_len": avg_len,
        "var_len": var_len,
        "dup_ratio": dup_ratio,
        "link_rate_60s": link_rate_60s,
        "mention_rate_60s": mention_rate_60s,
    }

def update_state(state: UserState, now_ts: int, content: str, mentions_count: int) -> None:
    state.timestamps.append(now_ts)
    state.lengths.append(len(content))
    state.dup_hashes.append(content_hash(content))
    state.link_flags.append(1 if has_link(content) else 0)
    state.mention_counts.append(mentions_count)
