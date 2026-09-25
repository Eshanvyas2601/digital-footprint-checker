import re
from urllib.parse import urlparse

SOCIAL_DOMAINS = ["linkedin.com", "instagram.com", "facebook.com", "tiktok.com", "twitter.com", "x.com"]
NEWS_KEYWORDS = ["news", "times", "hindustantimes", "bbc.", "cnn.", "reuters", "press"]
AGGREGATOR_DOMAINS = ["unifers.ai", "bebee.com", "scribd.com", "internshala.com"]
SPAM_LOOKUP_PATTERNS = ["blob.core.windows.net", "s3.us-east-1.amazonaws.com", "web.core.windows.net", "z-dqehpjab", ".z7.", ".z48."]

ROLE_KEYWORDS = {
    "finance": ["financial analyst", "accountant", "banker", "investment"],
    "engineering": ["engineer", "developer", "commissioning", "technician"],
    "student": ["student", "university", "college", "ambassador"],
    "creative": ["author", "writer", "artist", "actor", "kindle", "singer"],
    "consultant": ["consultant", "advisor"],
    "other_media": ["imdb", "tiktok"],
}

LOCATION_KEYWORDS = [
    "india", "noida", "delhi", "mumbai", "bangalore", "indore",
    "usa", "united states", "austin", "san francisco", "bay area",
    "uk", "canada", "australia", "dubai", "perth"
]


def extract_domain(link):
    try:
        return urlparse(link).netloc.replace("www.", "")
    except Exception:
        return ""


def extract_handle(link):
    match = re.search(r'(?:linkedin\.com/(?:in|pub)|instagram\.com|facebook\.com)/([a-zA-Z0-9_\-.]+)', link or "")
    return match.group(1).lower() if match else None


def classify_source_type(domain):
    if any(p in domain for p in SPAM_LOOKUP_PATTERNS):
        return "spam_lookup"
    if any(s in domain for s in SOCIAL_DOMAINS):
        return "social_media"
    if any(n in domain for n in NEWS_KEYWORDS):
        return "news_or_press"
    if any(a in domain for a in AGGREGATOR_DOMAINS):
        return "data_aggregator"
    if "imdb.com" in domain:
        return "media_database"
    return "general_web"


def detect_roles(text):
    text_lower = text.lower()
    found = set()
    for role, keywords in ROLE_KEYWORDS.items():
        if any(k in text_lower for k in keywords):
            found.add(role)
    return found


def detect_locations(text):
    text_lower = text.lower()
    return {loc for loc in LOCATION_KEYWORDS if loc in text_lower}


def build_evidence(item):
    """Converts one raw SerpApi result into a structured Evidence object."""
    title = item.get("title", "") or ""
    link = item.get("link", "") or ""
    snippet = item.get("snippet", "") or ""
    domain = extract_domain(link)
    text = f"{title} {snippet}"

    return {
        "title": title,
        "url": link,
        "domain": domain,
        "snippet": snippet,
        "source_type": classify_source_type(domain),
        "handle": extract_handle(link),
        "detected_roles": detect_roles(text),
        "detected_locations": detect_locations(text),
        "query_source": item.get("query_source", "General"),
    }


def build_evidence_list(raw_results):
    """Converts a list of raw SerpApi results into structured Evidence objects."""
    return [build_evidence(item) for item in raw_results]