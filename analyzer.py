import os
import time
from dotenv import load_dotenv
from google import genai
from risk_scorer import calculate_risk_score

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

MODELS_TO_TRY = ["gemini-3.6-flash"]


def analyze_results(search_results, input_type, input_value):
    simplified = []
    for item in search_results.get("organic_results", [])[:8]:
        simplified.append({
            "title": item.get("title"),
            "link": item.get("link"),
            "snippet": item.get("snippet")
        })

    score, risk_level, evidence = calculate_risk_score(search_results, input_type, input_value)
    evidence_text = "\n".join(f"- {e}" for e in evidence)

    prompt = f"""
You are a digital footprint analysis assistant helping an everyday citizen understand what's publicly findable about a {input_type}: "{input_value}".

Here are the raw search results:
{simplified}

A rule-based scoring system has already calculated the risk level as {risk_level} (score: {score}) based on this evidence:
{evidence_text}

Your task:
1. Summarize what you find in plain, non-technical language.
2. Explain the flags using the evidence above (plus anything else clearly relevant you notice in the results).
3. Do NOT invent or change the risk level — it has already been calculated by the rules above. Just explain why it makes sense.
4. Keep the tone helpful and non-alarming — this is for citizen awareness, not accusation.

Respond in this format:
SUMMARY: <2-3 sentences>
FLAGS: <bullet list, or "None found">
FOOTPRINT CONFUSABILITY: {risk_level} (evidence-based score: {score})

Important: "Confusability" measures how easy it would be to mix up this identity with others online (e.g. due to shared names, conflicting profiles, or scattered results) — it does NOT mean the searched person is dangerous, suspicious, or "at risk" themselves. Make sure your summary reflects this framing clearly, especially if the level is HIGH.
"""

    for model_name in MODELS_TO_TRY:
        for attempt in range(6):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                return response.text
            except Exception as e:
                print(f"Model {model_name}, attempt {attempt + 1} failed: {e}")
                time.sleep(10)

    return f"Analysis failed after multiple attempts. Rule-based risk level was: {risk_level} (score: {score})\n\nEvidence:\n{evidence_text}"


def analyze_clustered_results(clusters, input_type, input_value):
    """
    Takes identity clusters (from identity_clustering.py) and produces
    a report that explains distinct identities found, using the same
    evidence-based risk scoring as the standard flow.
    """
    all_items = [item for cluster in clusters for item in cluster]
    wrapped = {"organic_results": all_items}

    score, risk_level, evidence = calculate_risk_score(wrapped, input_type, input_value)
    evidence_text = "\n".join(f"- {e}" for e in evidence)

    cluster_summary_lines = []
    for i, cluster in enumerate(clusters, 1):
        top_titles = [item.get("title", "") for item in cluster[:3]]
        cluster_summary_lines.append(f"Cluster {i} ({len(cluster)} result(s)): {top_titles}")
    cluster_summary_text = "\n".join(cluster_summary_lines)

    prompt = f"""
You are a digital footprint analysis assistant. A multi-query OSINT search for the {input_type} "{input_value}" was run, and results were automatically grouped into likely-identity clusters based on shared location/role/profile signals.

Here are the identity clusters found:
{cluster_summary_text}

A rule-based scoring system has already calculated the overall footprint confusability as {risk_level} (score: {score}) based on:
{evidence_text}

Your task:
1. Summarize in plain language how many likely distinct people/identities appear to share this {input_type}, based on the clusters.
2. Briefly describe what each larger cluster (2+ results) seems to represent (e.g. "a US-based finance professional" vs "a student in India").
3. Do NOT invent or change the confusability level — just explain why it makes sense given the clustering.
4. Keep the tone helpful and non-alarming.

Respond in this format:
SUMMARY: <2-3 sentences>
DISTINCT IDENTITIES: <bullet list, one per notable cluster>
FOOTPRINT CONFUSABILITY: {risk_level} (evidence-based score: {score})

Important: "Confusability" measures how easily this identity could be mixed up with others online — it does NOT mean the searched person is dangerous or at risk themselves.
"""

    for model_name in MODELS_TO_TRY:
        for attempt in range(6):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                return response.text
            except Exception as e:
                print(f"Model {model_name}, attempt {attempt + 1} failed: {e}")
                time.sleep(10)

    return f"Analysis failed after multiple attempts. Footprint confusability: {risk_level} (score: {score})"


if __name__ == "__main__":
    dummy_results = {
        "organic_results": [
            {"title": "Eshan Vyas - Financial Analyst @ ServiceNow", "link": "https://linkedin.com/in/eshanvyas", "snippet": "Financial Analyst, Austin & Bay Area"},
            {"title": "Eshan Vyas - Student, Amity University", "link": "https://in.linkedin.com/in/eshan-vyas-390161328", "snippet": "Third Year Engineering Student, Noida"},
            {"title": "Eshan Vyas - Instagram", "link": "https://instagram.com/eshan.vyas", "snippet": "Boxing, Mic, Conversations"},
        ]
    }
    result = analyze_results(dummy_results, "name", "Eshan Vyas")
    print(result)