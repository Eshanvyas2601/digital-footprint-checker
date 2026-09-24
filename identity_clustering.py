from urllib.parse import urlparse
import re


def extract_domain(link):
    try:
        return urlparse(link).netloc.replace("www.", "")
    except Exception:
        return ""


def extract_handle(link):
    """Extracts the profile handle/slug from a LinkedIn/Instagram/Facebook URL, if present."""
    match = re.search(r'(?:linkedin\.com/(?:in|pub)|instagram\.com|facebook\.com)/([a-zA-Z0-9_\-.]+)', link)
    return match.group(1).lower() if match else None


def extract_location_hints(text):
    locations = [
        "india", "noida", "delhi", "mumbai", "bangalore", "indore",
        "usa", "united states", "austin", "san francisco", "bay area",
        "uk", "canada", "australia"
    ]
    text_lower = text.lower()
    return {loc for loc in locations if loc in text_lower}


def extract_role_hints(text):
    roles = {
        "finance": ["financial analyst", "accountant", "banker", "investment"],
        "engineering": ["engineer", "developer", "commissioning", "technician"],
        "student": ["student", "university", "college", "vice president", "ambassador"],
        "creative": ["author", "writer", "artist", "actor", "kindle"],
        "other_media": ["imdb", "tiktok"],
    }
    text_lower = text.lower()
    found = set()
    for role, keywords in roles.items():
        if any(keyword in text_lower for keyword in keywords):
            found.add(role)
    return found


def build_identity_signature(item):
    text = f"{item.get('title', '')} {item.get('snippet', '')}"
    return {
        "locations": extract_location_hints(text),
        "roles": extract_role_hints(text),
        "domain": extract_domain(item.get("link", "")),
        "handle": extract_handle(item.get("link", "")),
    }


def signatures_match(sig_a, sig_b):
    """
    Strong match: same handle on the same domain (very reliable — same profile).
    Weak match: same domain AND (shared location OR shared role) — requires
    two matching signals, not just one, to avoid over-merging unrelated results.
    """
    if sig_a["handle"] and sig_b["handle"] and sig_a["handle"] == sig_b["handle"] and sig_a["domain"] == sig_b["domain"]:
        return True

    same_domain = sig_a["domain"] == sig_b["domain"]
    shared_location = sig_a["locations"] & sig_b["locations"]
    shared_role = sig_a["roles"] & sig_b["roles"]

    return same_domain and bool(shared_location or shared_role)


def cluster_identities(results):
    """
    Groups search results into likely-identity clusters.
    Each new result is compared against the ORIGINAL seed item of each cluster
    (not an ever-expanding merged signature) to avoid cluster drift.
    """
    clusters = []

    for item in results:
        sig = build_identity_signature(item)
        placed = False

        for cluster in clusters:
            seed_sig = cluster["seed_signature"]  # never changes after creation
            if signatures_match(sig, seed_sig):
                cluster["items"].append(item)
                placed = True
                break

        if not placed:
            clusters.append({"seed_signature": sig, "items": [item]})

    return [c["items"] for c in clusters]
if __name__ == "__main__":
    from serpapi_client import multi_query_search

    results = multi_query_search("Eshan Vyas")
    clusters = cluster_identities(results)

    for i, cluster in enumerate(clusters, 1):
        print(f"\n=== IDENTITY CLUSTER {i} ({len(cluster)} results) ===")
        for item in cluster:
            print(f"- [{item.get('query_source')}] {item.get('title')}")