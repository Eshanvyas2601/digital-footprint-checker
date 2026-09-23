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


if __name__ == "__main__":
    print("=== FULL REVERSE IMAGE PIPELINE TEST ===\n")
    with open("test_image.jpg", "rb") as f:
        uploaded_url = upload_image_temp(f)
        print("Uploaded URL:", uploaded_url)

    print("\nSearching for matches...\n")
    image_result = search_reverse_image(uploaded_url)
    image_matches = image_result.get("image_results", [])

    if not image_matches:
        print("No image matches found.")
    else:
        for item in image_matches[:3]:
            print("Title:", item.get("title"))
            print("Link:", item.get("link"))
            print("---")