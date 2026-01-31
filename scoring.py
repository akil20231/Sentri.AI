import re
from typing import Tuple, List

BULLET_RE = re.compile(r"(^|\n)\s*([-*]|\d+\.)\s+", re.MULTILINE)
STRUCTURE_RE = re.compile(r"\b(here are|in summary|overall|step-by-step|bullet points)\b", re.IGNORECASE)

def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))

def agent_score(features: dict, content: str) -> Tuple[float, List[str]]:
    reasons: List[str] = []
    score = 0.0

    # Behavioral: high message rate suggests automation
    if features["msg_rate_60s"] > 0.15:  # >9/min
        score += 0.25
        reasons.append(f"High message rate (~{features['msg_rate_60s']*60:.0f}/min)")

    # Behavioral: very low variance in inter-message timing
    if features["avg_inter"] < 8 and features["var_inter"] < 10:
        score += 0.20
        reasons.append("Low response-time variance")

    # Formatting: bullets/structured templates
    if BULLET_RE.search(content):
        score += 0.15
        reasons.append("Structured bullet/number formatting")

    if STRUCTURE_RE.search(content):
        score += 0.10
        reasons.append("Template-like phrasing")

    # Low length variance + consistently long
    if features["avg_len"] > 250 and features["var_len"] < 2000:
        score += 0.15
        reasons.append("Consistently long, uniform messages")

    # Duplicates
    if features["dup_ratio"] > 0.25:
        score += 0.20
        reasons.append("Repeated/duplicate messages")

    return clamp(score), reasons or ["No strong automation signals"]

def harm_score(features: dict) -> Tuple[float, List[str]]:
    reasons: List[str] = []
    score = 0.0

    # Link spam
    if features["link_rate_60s"] > 0.05:  # >3 links/min
        score += 0.35
        reasons.append("High link posting rate")

    # Mention spam
    if features["mention_rate_60s"] > 0.10:
        score += 0.20
        reasons.append("High @mention rate")

    # Burst posting
    if features["msg_rate_60s"] > 0.20:  # >12/min
        score += 0.25
        reasons.append("Burst posting behavior")

    # Repetition
    if features["dup_ratio"] > 0.30:
        score += 0.30
        reasons.append("High repetition/duplication")

    return clamp(score), reasons or ["No strong harm signals"]

def final_risk(a: float, h: float) -> float:
    return clamp(a * (0.4 + 0.6*h))  # harm amplifies agent-ness modestly
