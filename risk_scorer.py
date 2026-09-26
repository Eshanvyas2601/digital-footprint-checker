"""
Deterministic, evidence-based risk scoring engine for DigitalTrace.

Design: each "signal" is a specific, explainable pattern found in the evidence,
with a fixed point weight. Signals sum into a total score (capped at 100),
which maps to a risk level via fixed thresholds. Gemini never decides the
score — it only explains signals already calculated here.

Scoring methodology (out of 100):
  Identity inconsistency (conflicting roles, same name, own profiles only) +25
  Multiple conflicting profiles (3+ distinct profile clusters)             +15
  Contact inconsistency (email/phone tied to differing names)             +20
  Image reuse (photo found on 3+ unrelated domains)                        +25
  Suspicious / low-context source (data-aggregator domains)                +10
  Numeric-heavy handle (pattern common in fake accounts)                    +5
  Low-quality lookup sites (auto-generated spam directories)                +5

Note: role and profile-count signals only consider actual profile pages
(e.g. linkedin.com/in/..., a person's own Instagram/Facebook page), not
third-party posts or articles that merely mention the name — this avoids
miscounting commentary about a person as a separate conflicting identity.

Risk level thresholds: 0-25 LOW | 26-55 MEDIUM | 56+ HIGH
"""

import re
from evidence_engine import build_evidence_list


def _name_candidates(text):
    return set(re.findall(r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)?\b', text or ""))



def _has_numeric_heavy_handle(evidence):
    handle = evidence.get("handle")
    if not handle:
        return False
    return sum(c.isdigit() for c in handle) >= 4


def signal_identity_inconsistency(clusters):
    if not clusters or len(clusters) < 2:
        return None
    role_sets = []
    for cluster in clusters:
        roles = set()
        for ev in cluster:
            if ev.get("is_profile"):
                roles |= ev.get("detected_roles", set())
        if roles:
            role_sets.append((cluster, roles))
    if len(role_sets) < 2:
        return None
    for i in range(len(role_sets)):
        for j in range(i + 1, len(role_sets)):
            cluster_a, roles_a = role_sets[i]
            cluster_b, roles_b = role_sets[j]
            if roles_a and roles_b and not (roles_a & roles_b):
                return {
                    "id": "identity_inconsistency",
                    "label": "Identity inconsistency",
                    "points": 25,
                    "evidence": [cluster_a[0], cluster_b[0]],
                    "reason": (

                        f"Results tied to the same identity show conflicting professional fields "
                        f"({', '.join(roles_a)} vs {', '.join(roles_b)}), suggesting these are likely "
                        f"different individuals sharing the same name, not one person."
                    ),
                }
    return None


def signal_multiple_conflicting_profiles(clusters):
    profile_clusters = [
        c for c in clusters if any(e.get("is_profile") for e in c)
    ] if clusters else []
    if len(profile_clusters) >= 3:
        return {
            "id": "multiple_profiles",
            "label": "Multiple conflicting profiles",
            "points": 15,
            "evidence": [c[0] for c in profile_clusters[:3]],
            "reason": (
                f"Found {len(profile_clusters)} distinct profile clusters across social/professional "
                f"platforms under the same identity, increasing the chance of mistaking one person for another."
            ),
        }
    return None


def signal_contact_inconsistency(evidence_list, input_type):
    if input_type not in ("email", "phone"):
        return None
    name_sets = []
    for ev in evidence_list:
        if ev.get("source_type") == "spam_lookup":

            continue
        names = _name_candidates(f"{ev['title']} {ev['snippet']}")
        if names:
            name_sets.append((ev, names))
    if len(name_sets) < 2:
        return None
    for i in range(len(name_sets)):
        for j in range(i + 1, len(name_sets)):
            ev_a, names_a = name_sets[i]
            ev_b, names_b = name_sets[j]
            if not (names_a & names_b):
                return {
                    "id": "contact_inconsistency",
                    "label": "Contact inconsistency",
                    "points": 20,
                    "evidence": [ev_a, ev_b],
                    "reason": (
                        "The same contact detail appears in results referencing different names, "
                        "which may indicate it is shared, reused, or tied to more than one identity."
                    ),
                }
    return None


def signal_image_reuse(image_matches):
    if not image_matches:
        return None
    evidence = build_evidence_list(image_matches)
    domains = {e["domain"] for e in evidence}
    domains.discard("")
    if len(domains) >= 3:
        return {

            "id": "image_reuse",
            "label": "Image reuse",
            "points": 25,
            "evidence": evidence[:2],
            "reason": (
                f"This image appears on {len(domains)} unrelated domains, which can indicate a stolen "
                f"or reused photo — a common pattern in fake profiles."
            ),
        }
    return None


def signal_suspicious_source(evidence_list):
    flagged = [e for e in evidence_list if e["source_type"] == "data_aggregator"]
    if flagged:
        return {
            "id": "suspicious_source",
            "label": "Suspicious or low-context source",
            "points": 10,
            "evidence": flagged[:2],
            "reason": (
                "One or more results come from data-aggregator style sites that compile contact "
                "information from public sources — verify these independently before trusting them."
            ),
        }
    return None


def signal_numeric_handle(evidence_list):
    flagged = [e for e in evidence_list if _has_numeric_heavy_handle(e)]
    if flagged:
        return {

            "id": "numeric_handle",
            "label": "Numeric-heavy handle",
            "points": 5,
            "evidence": flagged[:2],
            "reason": (
                "One or more profile handles contain an unusually high number of digits, a pattern "
                "more common in fake or auto-generated accounts."
            ),
        }
    return None


def signal_spam_lookup_sources(evidence_list):
    flagged = [e for e in evidence_list if e.get("source_type") == "spam_lookup"]
    if len(flagged) >= 2:
        return {
            "id": "spam_lookup",
            "label": "Low-quality lookup sites",
            "points": 5,
            "evidence": flagged[:2],
            "reason": (
                f"This contact appears mainly on {len(flagged)} auto-generated phone/data-lookup sites "
                f"rather than genuine profiles — these often display fabricated or randomized names and "
                f"should not be treated as reliable identity information."
            ),
        }
    return None


def _level_from_score(score):
    if score <= 25:
        return "LOW"

    elif score <= 55:
        return "MEDIUM"
    return "HIGH"


def calculate_risk(evidence_list, input_type, clusters=None, image_matches=None):
    """
    Runs every signal check and returns a structured, reproducible risk assessment:
    {score, level, signals: [...], consistent_count, ambiguous_count}
    """
    signals = []
    for check in [
        lambda: signal_identity_inconsistency(clusters),
        lambda: signal_multiple_conflicting_profiles(clusters),
        lambda: signal_contact_inconsistency(evidence_list, input_type),
        lambda: signal_image_reuse(image_matches),
        lambda: signal_suspicious_source(evidence_list),
        lambda: signal_numeric_handle(evidence_list),
        lambda: signal_spam_lookup_sources(evidence_list),
    ]:
        result = check()
        if result:
            signals.append(result)

    score = min(sum(s["points"] for s in signals), 100)
    level = _level_from_score(score)

    flagged_urls = {ev.get("url") for s in signals for ev in s["evidence"]}
    total_items = len(evidence_list) if evidence_list else 0
    consistent_count = max(total_items - len(flagged_urls), 0)
    ambiguous_count = len(flagged_urls)


    return {
        "score": score,
        "level": level,
        "signals": signals,
        "consistent_count": consistent_count,
        "ambiguous_count": ambiguous_count,
    }