import os
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
import requests
import cloudinary
import cloudinary.uploader

load_dotenv()

API_KEY = os.getenv("SERPAPI_KEY")
BASE_URL = "https://serpapi.com/search"
REQUEST_TIMEOUT = 15   # seconds per attempt
MAX_ATTEMPTS = 2       # a hung request is retried once

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# In-memory cache: repeating a name search in one session is instant and free.
# Only complete results (no failed sources) are cached.
_SEARCH_CACHE = {}


def search_text(query):
    """General text-based search — works for names, emails, phone numbers."""
    params = {
        "engine": "google",
        "q": query,
        "api_key": API_KEY
    }

    response = requests.get(BASE_URL, params=params, timeout=REQUEST_TIMEOUT)
    return response.json()


def search_reverse_image(image_url):
    """Reverse image search — needs a public image URL, not a local file."""
    params = {
        "engine": "google_reverse_image",
        "image_url": image_url,
        "api_key": API_KEY
    }
    response = requests.get(BASE_URL, params=params, timeout=REQUEST_TIMEOUT)
    return response.json()


def upload_image_temp(image_file):
    """
    Uploads an image file to Cloudinary and returns a public URL.
    image_file: a file-like object (e.g. from Streamlit's file uploader, or an open() file)
    """
    result = cloudinary.uploader.upload(image_file)
    return result.get("secure_url")


def build_targeted_query(value, input_type, platform=None):
    """Builds smarter queries depending on input type, optionally targeting one platform."""
    if input_type == "email":
        return f'"{value}"'
    elif input_type == "phone":
        return f'"{value}"'
    elif input_type == "name":
        if platform and platform != "All platforms":

            site_map = {
                "LinkedIn": "site:linkedin.com",
                "Instagram": "site:instagram.com",
                "Facebook": "site:facebook.com"
            }
            return f'"{value}" {site_map.get(platform, "")}'
        return f'"{value}" site:linkedin.com OR site:facebook.com OR site:instagram.com'
    return value


def _search_with_retry(query):
    """Retries network failures and timeouts once before giving up."""
    last_error = None
    for _ in range(MAX_ATTEMPTS):
        try:
            return search_text(query)
        except requests.exceptions.RequestException as e:
            last_error = e
    raise last_error


def multi_query_search(name, return_status=False):
    """
    Runs multiple targeted searches for a name in parallel, tagging each result
    with which query surfaced it. Results keep a fixed order so clustering stays
    deterministic.

    return_status=False -> returns the list of results
    return_status=True  -> returns (results, failed_source_labels)
    """
    cache_key = name.strip().lower()
    if cache_key in _SEARCH_CACHE:

        cached = _SEARCH_CACHE[cache_key]
        return (cached, []) if return_status else cached

    queries = {
        "LinkedIn": f'"{name}" site:linkedin.com',
        "Instagram": f'"{name}" site:instagram.com',
        "Facebook": f'"{name}" site:facebook.com',
        "News/Articles": f'"{name}" (news OR article OR press)',
        "Other/General": f'"{name}" -site:linkedin.com -site:facebook.com -site:instagram.com',
    }

    def run_query(item):
        label, query = item
        try:
            data = _search_with_retry(query)
        except Exception as e:
            return label, [], e
        error = data.get("error")
        # "No results" is a normal answer; anything else (out of credits, bad key) is a failure.
        if error and "hasn't returned any results" not in error:
            return label, [], RuntimeError(error)
        return label, data.get("organic_results", [])[:5], None

    with ThreadPoolExecutor(max_workers=len(queries)) as pool:
        outcomes = list(pool.map(run_query, queries.items()))

    all_results, failed = [], []
    for label, organic, error in outcomes:
        if error:
            print(f"Query for {label} failed: {error}")
            failed.append(label)
            continue

        for item in organic:
            item["query_source"] = label
            all_results.append(item)

    if all_results and not failed:
        _SEARCH_CACHE[cache_key] = all_results

    return (all_results, failed) if return_status else all_results


if __name__ == "__main__":
    import time

    print("=== MULTI-QUERY SPEED TEST (public figure) ===\n")
    start = time.time()
    results, failed = multi_query_search("Sundar Pichai", return_status=True)
    print(f"Fetched {len(results)} results in {time.time() - start:.1f}s")
    print("Failed sources:", ", ".join(failed) if failed else "none")