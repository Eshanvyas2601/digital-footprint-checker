# DigitalTrace — Citizen Digital Footprint & Scam Awareness Tool

Track: Knowledge & Public Interest — SerpApi India Hackathon 2026

## The Problem

Online scams and identity misuse are a growing public safety concern in India, and most citizens have no easy way to check their own digital exposure or verify a suspicious contact before a transaction.

What It Does

DigitalTrace lets users check a name, email, or phone number against public search data — surfacing identity mismatches, duplicate profiles, and inconsistencies in plain, non-technical language. It's built on SerpApi's Google Search API for data retrieval and Google's Gemini AI to synthesize raw search results into a clear, actionable risk summary.

Example: Searching a common name might reveal multiple unrelated people sharing that name across different industries and locations — exactly the kind of confusion that leads to mistaken identity or scam vulnerability. DigitalTrace surfaces this automatically instead of leaving the user to manually cross-check dozens of search results.

Ethical Use

This tool is designed strictly for self-verification and citizen awareness — checking your own digital footprint, or vetting a suspicious contact before you trust them. It is not intended for surveilling others without consent, and stores no data beyond a single search session.

Tech Stack
Python — core logic
Streamlit — web interface
SerpApi (Google Search API) — public data retrieval
Google Gemini API — AI-powered analysis and risk summarization
How It Works (Pipeline)
User input (name/email/phone)
    ↓
SerpApi Google Search — fetches real public search results
    ↓
Gemini AI — analyzes results, flags inconsistencies, assigns risk level
    ↓
Streamlit UI — displays a clean, readable report to the user
Setup Instructions
Clone this repository:
   git clone https://github.com/Eshanvyas2601/digital-footprint-checker.git
   cd digital-footprint-checker
Create and activate a virtual environment:
   python -m venv venv
   venv\Scripts\activate      # Windows
   source venv/bin/activate   # Mac/Linux
Install dependencies:
   pip install streamlit requests python-dotenv google-genai
Create a .env file in the project root with your own API keys:
   SERPAPI_KEY=your_serpapi_key_here
   GEMINI_API_KEY=your_gemini_key_here
Run the app:
   streamlit run app.py
Author

Built by Eshan Vyas for the SerpApi India Hackathon 2026.