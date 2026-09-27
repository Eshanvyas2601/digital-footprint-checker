DigitalTrace — Citizen Digital Footprint & Scam Awareness Tool

Track: Knowledge & Public Interest — SerpApi India Hackathon 2026

The Problem

Online scams and identity misuse are a growing public safety concern in India, and most citizens have no easy way to check their own digital exposure, verify a suspicious contact, or tell whether a name genuinely belongs to one clear identity before trusting it.

What It Does

DigitalTrace runs a multi-source OSINT (Open Source Intelligence) investigation on a name, email, phone number, or image, and turns the results into a clear, evidence-backed report — not just a list of links, and not just an AI opinion.

The core design principle: the AI never decides the risk score. A deterministic, rule-based engine calculates the score from concrete, countable evidence. Gemini's only job is to explain that score in plain language. This makes every number in a DigitalTrace report reproducible and auditable — if a judge, a user, or a police cyber cell asks "why was this flagged?", the answer is always traceable back to specific evidence, not an AI's opinion.

Key features
Multi-query OSINT search — for names, runs separate targeted searches across LinkedIn, Instagram, Facebook, news/press, and the general web, instead of one mixed query
Evidence engine — converts every raw search result into a structured record: source type (social profile, news, spam-lookup site, data aggregator), detected role, detected location, and whether it's an actual profile page or just a third-party post mentioning the name
Relevance filtering — discards results that don't actually contain the searched name/email/phone, preventing unrelated search noise from being treated as evidence (a real bug found and fixed during validation — see Evaluation below)
Identity clustering — groups evidence into likely-distinct identities using profile handles, locations, and roles, and specifically distinguishes a person's own profile pages from other people's posts that merely mention them
Deterministic risk scoring — a fixed, documented point system (see risk_scorer.py) calculates an exposure score out of 100 from named signals: identity inconsistency, multiple conflicting profiles, contact inconsistency, image reuse, suspicious sources, numeric-heavy handles, and auto-generated spam-lookup sites
Content-based spam detection — recognizes auto-generated phone/data-lookup spam pages by their title pattern (e.g. "9289321, Shared Mobility Syndicate Tmi"), not just by domain, so it generalizes to new spam sites automatically
Evidence-to-conclusion drill-down — every flagged signal in the dashboard expands to show exactly which evidence triggered it and why
Reverse image search — via Cloudinary (temporary public hosting) + SerpApi, checks where else an uploaded photo appears online
PDF export — a full downloadable report including the score, signals, evidence, sources, and recommended actions
Framing: "Footprint Confusability," not a danger score

DigitalTrace's exposure score measures how easily an identity could be confused with others online — not whether a person is dangerous. This distinction is stated explicitly on every report:

"DigitalTrace does not determine whether a person is a scammer or a threat. It identifies publicly observable signals — such as conflicting profiles or reused images — that may warrant further verification. Always confirm identity through an independent, trusted channel before acting on this report."

Architecture
User input (name / email / phone / image)
    ↓
SerpApi multi-query search — separate targeted searches across
LinkedIn, Instagram, Facebook, news, and the general web
    ↓
Evidence engine — extracts structured facts from each result,
filters out irrelevant matches, and clusters likely-distinct identities
    ↓
Deterministic risk scoring — fixed, weighted, reproducible signals
(no AI involved in this step)
    ↓
Gemini AI — explains the pre-calculated score and signals in
plain language; cannot change the score itself
    ↓
Dashboard + PDF report — exposure score, findings with evidence
drill-down, sources, and recommended verification actions
Why SerpApi is essential

SerpApi is not a peripheral feature — it is the sole source of real-world evidence the entire system reasons over. Every signal in the risk-scoring engine, every identity cluster, and every piece of evidence shown to the user originates from a SerpApi call (google search engine for multi-query text search, google_reverse_image for photo matching). Remove SerpApi, and the evidence engine, clustering, and scoring engine all have nothing to process — there is no fallback data source. Gemini is downstream of SerpApi's data; it never searches on its own.

How the risk scoring works

Scoring methodology (documented in full in risk_scorer.py):

Signal	Points	What it detects
Identity inconsistency	+25	Same name, conflicting professional fields, across the person's own profile pages only
Multiple conflicting profiles	+15	3+ distinct genuine profile-page clusters under one identity
Contact inconsistency	+20	Same email/phone tied to differing names
Image reuse	+25	Uploaded photo found on 3+ unrelated domains
Suspicious/low-context source	+10	Result from a data-aggregator style site
Numeric-heavy handle	+5	Profile handle with an unusually high digit count
Low-quality lookup sites	+5	Contact appears mainly on auto-generated spam directories

Score is capped at 100. Risk level thresholds: 0–25 LOW, 26–55 MEDIUM, 56+ HIGH.

Evaluation

Rather than claim the tool "just works," it was tested against 10 real-world cases spanning three categories, using live search data:

#	Case	Category	Result	Correct?
1	Sundar Pichai	Consistent public figure	LOW (20/100)	Yes
2	Satya Nadella	Consistent public figure	LOW (0/100)	Yes
3	Ravi Kumar	Ambiguous — very common name	MEDIUM (45/100)	Yes
4	Fabricated email address	Empty/negative case	LOW (0/100)	Yes — no hallucinated findings
5	Eshan Vyas	Ambiguous name	LOW (0/100)	Yes, given live search data at test time
6	Ansh Tiwari	Ambiguous name	MEDIUM (45/100)	Yes
7	Uploaded photo	Reverse image search	LOW (25/100)	Partially — correct detection, revealed a scope limitation
8	Phone number	Contact + spam detection	LOW (25/100)	Partially — correct, one documented false positive
9	Manoj Kumar Pandey	Common name + historical figure	MEDIUM (30/100)	Yes — cleanly separated living professionals from war-hero tribute content
10	Balwinder Shukla	Initially broken, then fixed	LOW (0/100)	Yes, after the relevance-filter fix (see below)

Two real bugs were found and fixed during this evaluation, not before it:

Early testing (cases 1 and 2) revealed that third-party posts about a person (e.g., someone else's LinkedIn post praising a CEO) were being miscounted as separate conflicting identities. Fixed by distinguishing genuine profile pages from posts/content in the evidence engine.
Case 10 initially returned completely unrelated people's profiles for an uncommon name. Fixed by adding a relevance filter that discards any result not actually containing the searched name/email/phone before scoring.

This is included deliberately: an evaluation that only shows successes is less credible than one that shows a real testing process catching and fixing real issues.

Known limitations
Search results change over time. Since DigitalTrace queries live search engines rather than a static database, the same search can return different results — and therefore a different score — on different days, as case 5 showed.
No facial recognition. Reverse image search relies on Google's visual similarity matching, not facial recognition. It reliably detects exact photo reuse but can match on incidental visual elements (clothing, background) rather than the person's identity for non-public figures, and cannot yet distinguish suspicious reuse (a stolen profile picture) from benign reuse (a stock/product photo). True facial-recognition-based matching was deliberately excluded due to privacy and ethical concerns beyond this project's scope.
Name-detection uses lightweight pattern matching, not full NLP, so it can occasionally misidentify an unrelated capitalized phrase (e.g., a news headline) as a conflicting name. This trade-off was made deliberately for speed and simplicity.
Spam-lookup detection is pattern-based and may not catch every low-quality source, particularly ones using unrelated legitimate-looking domains (e.g., CDN hosts) rather than known spam patterns.
AI explanations depend on Gemini's availability. During periods of high demand, the app falls back to a raw evidence-based summary rather than a natural-language explanation, so the tool remains functional even if the AI layer is temporarily unavailable.
Ethical Use

This tool is designed strictly for self-verification and citizen awareness — checking your own digital footprint, or vetting a suspicious contact before you trust them. It is not intended for surveilling others without consent, and stores no data beyond a single search session.

Tech Stack
Python — core logic
Streamlit — web interface
SerpApi — Google Search API (multi-query text search) and Google Reverse Image Search API
Google Gemini API — AI-generated, evidence-grounded report explanations
Cloudinary — temporary public image hosting to enable reverse image search on user uploads
fpdf2 — PDF report generation
Project Structure
app.py                   # Streamlit UI, dashboard, and main flow
serpapi_client.py        # SerpApi search, multi-query search, reverse image, Cloudinary upload
evidence_engine.py       # Converts raw results into structured, classified evidence
identity_clustering.py   # Groups evidence into likely-distinct identities
risk_scorer.py           # Deterministic, weighted, documented risk scoring (no AI)
analyzer.py              # Gemini AI narrative generation, grounded in the calculated score
pdf_generator.py         # PDF report export
Setup Instructions
Clone this repository:
   git clone https://github.com/Eshanvyas2601/digital-footprint-checker.git
   cd digital-footprint-checker
Create and activate a virtual environment:
   python -m venv venv
   venv\Scripts\activate
   source venv/bin/activate
Install dependencies:
   pip install streamlit requests python-dotenv google-genai cloudinary fpdf2
Create a .env file in the project root with your own API keys:
   SERPAPI_KEY=your_serpapi_key_here
   GEMINI_API_KEY=your_gemini_key_here
   CLOUDINARY_CLOUD_NAME=your_cloud_name_here
   CLOUDINARY_API_KEY=your_cloudinary_api_key_here
   CLOUDINARY_API_SECRET=your_cloudinary_api_secret_here
Run the app:
   streamlit run app.py
Future Scope
Distinguishing suspicious image reuse from benign stock-photo reuse (e.g., checking whether matches appear on social/dating platforms specifically)
Heavier NLP for name/role detection to reduce false positives from headline-style text
A confidence interval alongside the point score, reflecting evidence volume and quality
Deployment as a public web app with rate-limited free usage
Author

Built by Eshan Vyas for the SerpApi India Hackathon 2026.