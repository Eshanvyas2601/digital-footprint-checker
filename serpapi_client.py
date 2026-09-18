import os
from dotenv import load_dotenv
import requests

load_dotenv()

API_KEY = os.getenv("SERPAPI_KEY")
BASE_URL = "https://serpapi.com/search"


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


def build_targeted_query(value, input_type):
    """Builds smarter queries depending on input type."""
    if input_type == "email":
        return f'"{value}"'
    elif input_type == "phone":
        return f'"{value}"'
    elif input_type == "name":
        return f'"{value}" site:linkedin.com OR site:facebook.com OR site:instagram.com'
    return value


if __name__ == "__main__":
    # Test 1: Name search
    test_query = build_targeted_query("Eshan Vyas", "name")
    result = search_text(test_query)
    
    organic_results = result.get("organic_results", [])
    for item in organic_results[:5]:
        print("Title:", item.get("title"))
        print("Link:", item.get("link"))
        print("Snippet:", item.get("snippet"))
        print("---")
    
    # Test 2: Reverse image search
    print("\n=== REVERSE IMAGE TEST ===\n")
    test_image_url = "https://upload.wikimedia.org/wikipedia/commons/8/8d/President_Barack_Obama.jpg"
    image_result = search_reverse_image(test_image_url)
    print(image_result.get("error"))
    image_matches = image_result.get("image_results", [])
    
    if not image_matches:
        print("No image matches found.")
    else:
        for item in image_matches[:3]:
            print("Title:", item.get("title"))
            print("Link:", item.get("link"))
            print("---")