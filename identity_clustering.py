def build_identity_signature(evidence):
    return {
        "locations": evidence["detected_locations"],
        "roles": evidence["detected_roles"],
        "domain": evidence["domain"],
        "handle": evidence["handle"],
    }


def signatures_match(sig_a, sig_b):
    if sig_a["handle"] and sig_b["handle"] and sig_a["handle"] == sig_b["handle"] and sig_a["domain"] == sig_b["domain"]:
        return True
    same_domain = sig_a["domain"] == sig_b["domain"]
    shared_location = sig_a["locations"] & sig_b["locations"]
    shared_role = sig_a["roles"] & sig_b["roles"]
    return same_domain and bool(shared_location or shared_role)


def cluster_identities(evidence_list):
    """
    Groups Evidence objects into likely-identity clusters.
    Each cluster is locked to its first (seed) item's signature to avoid drift.
    """
    clusters = []
    for ev in evidence_list:
        sig = build_identity_signature(ev)
        placed = False
        for cluster in clusters:
            seed_sig = cluster["seed_signature"]
            if signatures_match(sig, seed_sig):
                cluster["items"].append(ev)
                placed = True
                break
        if not placed:
            clusters.append({"seed_signature": sig, "items": [ev]})
    return [c["items"] for c in clusters]