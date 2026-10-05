DigitalTrace

Check your public digital footprint, for self-verification and citizen awareness.

DigitalTrace is an OSINT-style digital footprint and scam-awareness checker. Give it a name, email, phone number or photo and it shows where that identity appears in public search results, whether it could be confused with other people, and whether any publicly observable signals (such as conflicting profiles or reused images) deserve a second look.

Built for the SerpApi India Hackathon 2026, under the Knowledge & Public Interest track.

Important: DigitalTrace does not decide whether a person is a scammer or a threat. It surfaces public signals that may warrant further verification. Always confirm identity through an independent, trusted channel before acting on a report.

Features
Multi-platform search: runs several targeted queries covering LinkedIn, Instagram, Facebook, news and the wider web (Google Search via SerpApi).
Reverse image search: upload a photo to see where else it appears (Google Reverse Image Search via SerpApi, with temporary image hosting on Cloudinary).
Evidence engine: every search result is normalised into a structured evidence item with its source, title, URL and snippet.
Identity clustering: groups results into likely-distinct people who share the same name, based on their own profile pages.
Deterministic risk scoring: the 0-100 exposure score is rule-based and fully traceable. It is not an AI guess.
Gemini explains, never decides: Google Gemini turns the computed score and evidence into a plain-language summary and recommended actions.
Evidence drill-down: each flagged signal expands to show why it was raised and the exact sources behind it.
Platform presence view: shows which platforms returned results for a name search.
PDF export: download the full report as a PDF.
Privacy-first demo mode: generates entirely fabricated results so the tool can be demonstrated without exposing any real person's identity.
Partial-evidence warnings: if a search source times out, the report says so instead of pretending to be complete.
Dark glass UI: a landing page with a search bar and input-type pills, and a report dashboard with score ring, metric cards and session search history.
How it works
Input (name / email / phone / image)
        |
        v
SerpApi searches (multi-query text search, or reverse image search)
        |
        v
Evidence engine  ->  structured evidence list
        |
        v
Identity clustering (name searches)
        |
        v
Rule-based risk scorer  ->  score, level, signals, counts
        |
        v
Gemini narrative (explains the result only)
        |
        v
Dashboard + PDF report
Tech stack
Area	Tools
Language / UI	Python, Streamlit
Search	SerpApi (Google Search, Google Reverse Image Search)
Explanation	Google Gemini API (gemini-3.6-flash)
Image hosting	Cloudinary (temporary URLs for reverse image search)
Reports	fpdf2
Project structure
digital-footprint-checker/
├── app.py                  # Streamlit UI: landing page, dashboard, flow control
├── serpapi_client.py       # SerpApi text / reverse-image search, image upload
├── evidence_engine.py      # Builds structured evidence from raw results
├── identity_clustering.py  # Groups evidence into likely-distinct identities
├── risk_scorer.py          # Deterministic, rule-based exposure scoring
├── analyzer.py             # Gemini narrative (summary + recommended actions)
├── pdf_generator.py        # PDF report export
├── demo_data.py            # Fabricated sample results for demo mode
├── assets/                 # Banner and images
├── .streamlit/config.toml  # Dark theme settings
├── requirements.txt
├── .env.example
└── LICENSE
Setup

1. Clone the repository

bash
git clone https://github.com/Eshanvyas2601/digital-footprint-checker.git
cd digital-footprint-checker

2. Create and activate a virtual environment

powershell
python -m venv venv
venv\Scripts\activate

On macOS / Linux: source venv/bin/activate

3. Install dependencies

bash
pip install -r requirements.txt

4. Add your API keys

Copy .env.example to .env and fill in the values for SerpApi, Google Gemini and Cloudinary. The .env file is git-ignored, so never commit it.

5. Run the app

bash
streamlit run app.py

Open the address Streamlit prints (usually http://localhost:8501).

Usage
Choose what you are checking: Name, Email, Phone or Image.
Enter the value (or upload a photo) and click START SCAN.
Read the report: exposure score, signals, identity clusters, sources and recommended next steps.
Download the PDF report if you need a copy.
Demo mode

Real identities should not be shown in public demonstrations. Turn on Demo mode (name searches only) to use entirely fabricated sample data. Try a fictional name such as Aarav Testwala. The names, profiles and links in a demo report are fabricated, and the report is clearly labelled as such. Any resemblance to a real person is coincidental.

Privacy and ethics
Only publicly available search results are used.
The tool is designed for self-verification and citizen awareness, not for profiling or targeting individuals.
The score measures how easily an identity could be confused with others, or how exposed public information is. It is not a judgment of danger or wrongdoing.
Every flag links back to its source so a human can check it.
Session search history is kept only in the current browser session.
Limitations
Public data only: private profiles and pages not indexed by search engines are invisible to DigitalTrace.
Search coverage varies: results depend on what SerpApi and Google return at that moment. A source can time out, in which case the report is marked as based on partial evidence.
Common names are ambiguous: clustering reduces identity confusion but cannot fully resolve it.
Not a verdict: a low or high score is a signal to verify further, not proof of anything.
Rule-based scoring: the rules are transparent but deliberately simple, so they can miss subtle cases.
API dependence: live searches need working SerpApi, Gemini and Cloudinary keys and are subject to their usage limits.
Demo mode is name-only: email, phone and image searches always use live data.
Validation

DigitalTrace was tested on 10 cases covering public figures, common names, an empty case, an image, and a phone number.

#	Test input	Case type	Result	Behaved as expected?
1	Sundar Pichai	Consistent public figure	LOW (20/100)	Yes
2	Satya Nadella	Consistent public figure	LOW (0/100)	Yes
3	Ravi Kumar	Ambiguous, very common name	MEDIUM (45/100)	Yes
4	Fabricated email address	Empty/negative case	LOW (0/100)	Yes, no hallucinated findings
5	Common Indian Name A	Ambiguous name	LOW (0/100)	Yes, given live search data at test time
6	Common Indian Name B	Ambiguous name	MEDIUM (45/100)	Yes
7	Uploaded photo	Reverse image search	LOW (25/100)	Partially: correct detection, revealed a scope limitation
8	Phone number	Contact + spam detection	LOW (25/100)	Partially: correct, one documented false positive
9	Common Indian Name C	Common name + historical figure	MEDIUM (30/100)	Yes: cleanly separated living professionals from war-hero tribute content
10	Uncommon Indian Name D	Initially broken, then fixed	LOW (0/100)	Yes, after the relevance-filter fix
Bugs found and fixed during evaluation

Two real bugs were caught by this testing and fixed, not found beforehand:

Found in	Problem	Fix
Cases 1 and 2	Third-party posts about a person (for example, someone else's LinkedIn post praising a CEO) were miscounted as separate, conflicting identities.	The evidence engine now distinguishes genuine profile pages from posts and other content.
Case 10	An uncommon name returned completely unrelated people's profiles.	A relevance filter now discards any result that does not actually contain the searched name, email or phone before scoring.

This is included deliberately: an evaluation that only shows successes is less credible than one that shows a real testing process catching and fixing real issues.

Future work
Deploy as a public web app.
Add more platform-specific queries (for example a dedicated GitHub query).
Expand the scoring rules and the validation set.
License

See LICENSE.

Author

Built by Eshan Vyas — github.com/Eshanvyas2601