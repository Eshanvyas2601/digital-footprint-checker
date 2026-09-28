from fpdf import FPDF
from datetime import datetime

DISCLAIMER = (
    "DigitalTrace does not determine whether a person is a scammer or a threat. "
    "It identifies publicly observable signals - such as conflicting profiles or "
    "reused images - that may warrant further verification. Always confirm identity "
    "through an independent, trusted channel before acting on this report."
)

DEMO_NOTICE = (
    "DEMO REPORT - FABRICATED SAMPLE DATA. The names, profiles, and links in this report are "
    "entirely fabricated. Real identities cannot be shown in this demonstration for privacy "
    "reasons. Any resemblance to a real person is coincidental."
)


def _clean(text):
    return (text or "").encode("latin-1", "replace").decode("latin-1")


def generate_pdf_report(input_type, input_value, risk, summary, actions, evidence_list, demo_mode=False):
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "DigitalTrace - Digital Identity Verification Report", ln=True)

    if demo_mode:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(180, 0, 0)
        pdf.multi_cell(0, 6, _clean(DEMO_NOTICE), wrapmode="CHAR")
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
    pdf.cell(0, 8, f"Search type: {input_type}", ln=True)
    input_label = f"{_clean(input_value)} (fabricated demo name)" if demo_mode else _clean(input_value)
    pdf.cell(0, 8, f"Input: {input_label}", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 10, f"Overall Exposure: {risk['level']}  ({risk['score']} / 100)", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 7, f"Signals detected: {len(risk['signals'])}", ln=True)
    pdf.cell(0, 7, f"Consistent references: {risk['consistent_count']}", ln=True)
    pdf.cell(0, 7, f"Ambiguous results: {risk['ambiguous_count']}", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Summary", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, _clean(summary), wrapmode="CHAR")
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Findings", ln=True)
    if not risk["signals"]:
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 6, "No specific risk signals were detected.", wrapmode="CHAR")
    else:
        for signal in risk["signals"]:
            pdf.set_font("Helvetica", "B", 10)
            pdf.multi_cell(0, 6, _clean(f"- {signal['label']} (+{signal['points']} pts)"), wrapmode="CHAR")
            pdf.set_font("Helvetica", "", 9)
            pdf.multi_cell(0, 5, _clean(f"  Reason: {signal['reason']}"), wrapmode="CHAR")
            for i, ev in enumerate(signal["evidence"], 1):
                pdf.multi_cell(0, 5, _clean(f"  Evidence {i}: {ev.get('title', '')}"), wrapmode="CHAR")
                pdf.multi_cell(0, 5, _clean(f"  {ev.get('url', '')}"), wrapmode="CHAR")
            pdf.ln(2)
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Sources (fictional placeholders)" if demo_mode else "Sources", ln=True)
    pdf.set_font("Helvetica", "", 9)
    seen = set()
    for ev in evidence_list[:15]:
        url = ev.get("url", "")
        if url and url not in seen:
            pdf.multi_cell(0, 5, _clean(f"- {ev.get('title', '')}: {url}"), wrapmode="CHAR")
            seen.add(url)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Recommended Actions", ln=True)
    pdf.set_font("Helvetica", "", 10)
    for a in actions:
        pdf.multi_cell(0, 6, _clean(f"- {a}"), wrapmode="CHAR")
    pdf.ln(4)

    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 5, _clean(DISCLAIMER), wrapmode="CHAR")

    return bytes(pdf.output())