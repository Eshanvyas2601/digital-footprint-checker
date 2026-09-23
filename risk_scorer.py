import re
from urllib.parse import urlparse


def extract_domain(link):
    try:
        return urlparse(link).netloc.replace("www.", "")
    except Exception:
        return ""


def has_numeric_heavy_handle(link):
    """Checks if a profile URL's handle/slug contains unusually many digits (common in fake accounts)."""
    match = re.search(r'/(?:in|p|pub)/([a-zA-Z0-9_\-.]+)', link)
    if not match:
        return False
    slug = match.group(1)
    digit_count = sum(c.isdigit() for c in slug)
    return digit_count >= 4  # e.g. "johndoe83920" style handles


def detect_role_conflict(titles):
    """
    Very lightweight heuristic: looks for common job/role keywords across titles
    and flags if multiple clearly different fields appear.
    """
    role_categories = {
        "finance": ["financial analyst", "accountant", "banker", "investment"],
        "engineering": ["engineer", "developer", "commissioning", "technician"],
        "student": ["student", "university", "college", "school"],
        "creative": ["author", "writer", "artist", "designer"],
        "medical": ["doctor", "nurse", "physician", "medical"],
    }
    found_categories = set()
    combined = " ".join(titles).lower()
    for category, keywords in role_categories.items():
        if any(keyword in combined for keyword in keywords):
            found_categories.add(category)
    return found_categories


def calculate_risk_score(search_results, input_type, input_value):
    """
    Analyzes raw search results using fixed rules and returns:
    (score, risk_level, evidence_list)
    No AI involved here — pure counting and pattern-matching.
    """
    organic_results = search_results.get("organic_results", [])
    evidence = []
    score = 0

    if not organic_results:
        evidence.append("No public search results were found for this input.")
        return 0, "LOW", evidence

    titles = [item.get("title", "") for item in organic_results]
    snippets = [item.get("snippet", "") for item in organic_results]
    combined_text = " ".join(titles + snippets).lower()

    # Rule 1: Multiple distinct social/professional profiles found
    profile_links = [
        item for item in organic_results
        if any(domain in item.get("link", "") for domain in ["linkedin.com", "facebook.com", "instagram.com"])
    ]
    if len(profile_links) >= 3:
        score += 2
        evidence.append(
            f"Found {len(profile_links)} distinct social/professional profile links — possible multiple-identity overlap under the same {input_type}."
        )

    # Rule 2: Name/URL mismatch (only meaningful for name searches)
    if input_type == "name":
        name_parts = [p.lower() for p in input_value.split() if len(p) > 2]
        for item in organic_results:
            link = item.get("link", "")
            match = re.search(r'/in/([a-zA-Z0-9\-]+)', link)
            if match:
                slug = re.sub(r'[\d\-]', ' ', match.group(1).lower())
                if name_parts and not any(part in slug for part in name_parts):
                    score += 2
                    evidence.append(
                        f"A profile URL ('{match.group(1)}') doesn't clearly match the searched name — possible identity inconsistency."
                    )
                    break

    # Rule 3: Domain diversity
    domains = {extract_domain(item.get("link", "")) for item in organic_results if item.get("link")}
    domains.discard("")
    if len(domains) >= 4:
        score += 1
        evidence.append(
            f"Results span {len(domains)} different platforms/domains, indicating a broad or scattered digital footprint."
        )

    # Rule 4: Geographic diversity (crude keyword check)
    geo_terms = ["india", "usa", "united states", "uk", "canada", "australia", "noida", "austin", "bay area", "indore"]
    found_geos = {geo for geo in geo_terms if geo in combined_text}
    if len(found_geos) >= 2:
        score += 1
        evidence.append(
            f"Results reference multiple distinct locations ({', '.join(found_geos)}), suggesting different individuals rather than one person."
        )

    # Rule 5: Job/role conflict across results
    role_categories = detect_role_conflict(titles)
    if len(role_categories) >= 2:
        score += 2
        evidence.append(
            f"Results show conflicting professional fields ({', '.join(role_categories)}) under the same {input_type}, suggesting multiple distinct individuals."
        )

    # Rule 6: Numeric-heavy handles (common in fake/bot accounts)
    numeric_handles = [item for item in organic_results if has_numeric_heavy_handle(item.get("link", ""))]
    if numeric_handles:
        score += 1
        evidence.append(
            f"Found {len(numeric_handles)} profile handle(s) with an unusually high number of digits — a pattern more common in fake or bot-generated accounts."
        )

    if score <= 1:
        level = "LOW"
    elif score <= 3:
        level = "MEDIUM"
    else:
        level = "HIGH"

    if not evidence:
        evidence.append("No significant risk indicators were detected in the available public results.")

    return score, level, evidence