import re
from urllib.parse import urlparse


def extract_domain(link):
    try:
        return urlparse(link).netloc.replace("www.", "")
    except Exception:
        return ""


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
                    break  # only count this once

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

    # Determine final level from total score
    if score <= 1:
        level = "LOW"
    elif score <= 3:
        level = "MEDIUM"
    else:
        level = "HIGH"

    if not evidence:
        evidence.append("No significant risk indicators were detected in the available public results.")

    return score, level, evidence