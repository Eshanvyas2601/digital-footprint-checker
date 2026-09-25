import os
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)
MODELS_TO_TRY = ["gemini-3.6-flash"]


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
        for attempt in range(6):
            try:
                response = client.models.generate_content(model=model_name, contents=prompt)
                return response.text
            except Exception as e:
                print(f"Model {model_name}, attempt {attempt + 1} failed: {e}")
                time.sleep(10)

    return (
        f"SUMMARY: Unable to generate an AI explanation right now, but the evidence-based "
        f"assessment above ({risk['level']}, {risk['score']}/100) still applies.\n"
        "RECOMMENDED ACTIONS:\n"
        "- Verify identity through an independent channel\n"
        "- Avoid sharing sensitive information until verified\n"
        "- Cross-check details against official sources"
    )