import os
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

MODELS_TO_TRY = ["gemini-3.6-flash", "gemini-2.0-flash-001"]


def analyze_results(search_results, input_type, input_value):
    simplified = []
    for item in search_results.get("organic_results", [])[:8]:
        simplified.append({
            "title": item.get("title"),
            "link": item.get("link"),
            "snippet": item.get("snippet")
        })

    prompt = f"""
You are a digital footprint analysis assistant helping an everyday citizen understand what's publicly findable about a {input_type}: "{input_value}".

Here are the raw search results:
{simplified}

Your task:
1. Summarize what you find in plain, non-technical language.
2. Flag any inconsistencies — e.g. same name/photo linked to very different jobs, locations, or unrelated profiles.
3. Give a simple risk indicator: LOW, MEDIUM, or HIGH — based on how confusing or suspicious the footprint looks (e.g. many unrelated people sharing the same name = MEDIUM, since it could cause mistaken identity when verifying someone).
4. Keep the tone helpful and non-alarming — this is for citizen awareness, not accusation.

Respond in this format:
SUMMARY: <2-3 sentences>
FLAGS: <bullet list, or "None found">
RISK LEVEL: <LOW/MEDIUM/HIGH>
"""

    for model_name in MODELS_TO_TRY:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                return response.text
            except Exception as e:
                print(f"Model {model_name}, attempt {attempt + 1} failed: {e}")
                time.sleep(5)

    return "Analysis failed after multiple attempts across models. Please try again later."


if __name__ == "__main__":
    dummy_results = {
        "organic_results": [
            {"title": "Eshan Vyas - Financial Analyst @ ServiceNow", "link": "https://linkedin.com/in/eshanvyas", "snippet": "Financial Analyst, Austin & Bay Area"},
            {"title": "Eshan Vyas - Student, Amity University", "link": "https://in.linkedin.com/in/eshan-vyas-390161328", "snippet": "Third Year Engineering Student, Noida"},
        ]
    }
    result = analyze_results(dummy_results, "name", "Eshan Vyas")
    print(result)