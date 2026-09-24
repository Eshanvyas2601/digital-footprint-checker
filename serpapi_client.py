import os
from dotenv import load_dotenv
import requests
import cloudinary
import cloudinary.uploader

load_dotenv()

API_KEY = os.getenv("SERPAPI_KEY")
BASE_URL = "https://serpapi.com/search"

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)


def search_text(query):
    """General text-based search — works for names, emails, phone numbers."""
    params = {
        "engine": "google",
        "q": query,
        "api_key": API_KEY
    }
    response = requests.get(BASE_URL, params=params)
    return response.json()


def search_reverse_image(image_url):
    """Reverse image search — needs a public image URL, not a local file (yet)."""
    params = {
        "engine": "google_reverse_image",
        "image_url": image_url,
        "api_key": API_KEY
    }
    response = requests.get(BASE_URL, params=params)
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


def multi_query_search(name):
    """
    Runs multiple targeted searches for a name instead of one broad search,
    tagging each result with which query surfaced it. This gives cleaner,
    more distinguishable signal per platform/category than one mixed search.
    """
    queries = {
        "LinkedIn": f'"{name}" site:linkedin.com',
        "Instagram": f'"{name}" site:instagram.com',
        "Facebook": f'"{name}" site:facebook.com',
        "News/Articles": f'"{name}" (news OR article OR press)',
        "Other/General": f'"{name}" -site:linkedin.com -site:facebook.com -site:instagram.com',
    }

    all_results = []
    for source_label, query in queries.items():
        try:
            data = search_text(query)
            organic = data.get("organic_results", [])[:5]  # top 5 per query, keeps it manageable
            for item in organic:
                item["query_source"] = source_label  # tag which search found this
                all_results.append(item)
        except Exception as e:
            print(f"Query for {source_label} failed: {e}")

    return all_results


if __name__ == "__main__":
    print("=== MULTI-QUERY TEST ===\n")
    results = multi_query_search("Eshan Vyas")
    for item in results:
        print(f"[{item['query_source']}]", item.get("title"))
        print(item.get("link"))
        print("---")