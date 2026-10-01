import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
 
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
 
# Every Gemini request now has a hard time limit (milliseconds). Without this, a stuck
# request waits forever and the whole Streamlit page freezes.
REQUEST_TIMEOUT_MS = 20_000
 
client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options=types.HttpOptions(timeout=REQUEST_TIMEOUT_MS),
)
MODELS_TO_TRY = ["gemini-3.6-flash"]
MAX_ATTEMPTS = 2  # worst case is roughly 2 x 20s + a short pause, then the fallback summary is used
 
 
def _is_retryable(error):
    """Overload, rate-limit and timeout errors are worth one retry. Anything else fails fast."""
    text = str(error).lower()
    return any(
        marker in text
        for marker in ("503", "unavailable", "429", "resource_exhausted", "504", "deadline", "timed out", "timeout")
    )
 
 
def _fallback_narrative(risk):
    """Rule-based summary used whenever Gemini is unavailable, so the report always has text."""
    level, score = risk["level"], risk["score"]
    n_signals = len(risk["signals"])
    if n_signals:
        signal_part = f"{n_signals} signal(s) were flagged for review"
    else:
        signal_part = "no specific signals were flagged"
    return (
        "SUMMARY: The AI explanation is unavailable right now, but the rule-based assessment still applies. "
        f"This identity scores {score}/100 ({level} exposure), with {risk['consistent_count']} consistent "
        f"reference(s) and {risk['ambiguous_count']} result(s) that need verification; {signal_part}.\n"
        "RECOMMENDED ACTIONS:\n"
        "- Verify identity through an independent channel\n"
        "- Avoid sharing sensitive information until verified\n"
        "- Cross-check details against official sources"
    )
 
 
def generate_narrative(input_type, input_value, risk, extra_context=""):
    """
    Gemini's ONLY job: explain the already-calculated score and signals in
    plain language, and suggest verification actions. It never decides the
    score, level, or signals — those come from risk_scorer.py.
    """
    signals_text = "\n".join(
        f"- {s['label']} (+{s['points']} pts): {s['reason']}" for s in risk["signals"]
    ) or "No specific risk signals were triggered."
 
    prompt = f"""
You are a digital footprint analysis assistant. A deterministic rule-based engine has
already analyzed public search results for the {input_type} "{input_value}" and produced
this assessment — do NOT change or second-guess these numbers:
 
Overall exposure score: {risk['score']}/100
Risk level: {risk['level']}
Consistent references: {risk['consistent_count']}
Ambiguous/flagged results: {risk['ambiguous_count']}
 
Triggered signals:
{signals_text}
 
{extra_context}
 
Your task:
1. Write a 2-3 sentence plain-language SUMMARY of what this means for an everyday citizen.
2. Suggest exactly 3 short, practical RECOMMENDED ACTIONS for verifying this identity.
3. Do not mention or invent any score, level, or signal not given above.
4. Keep tone calm and non-alarming — this measures identity confusability/exposure, not danger.
 
Respond in this exact format:
SUMMARY: <text>
RECOMMENDED ACTIONS:
- <action 1>
- <action 2>
- <action 3>
"""
 
    for model_name in MODELS_TO_TRY:
        for attempt in range(MAX_ATTEMPTS):
            try:
                response = client.models.generate_content(model=model_name, contents=prompt)
                if response.text:
                    return response.text
                print(f"Model {model_name}, attempt {attempt + 1} returned an empty response")
            except Exception as e:
                print(f"Model {model_name}, attempt {attempt + 1} failed: {e}")
                if not _is_retryable(e):
                    break
            if attempt < MAX_ATTEMPTS - 1:
                time.sleep(2 * (2 ** attempt))  # short pause before the retry
 
    print("Gemini unavailable, using rule-based fallback summary.")
    return _fallback_narrative(risk)