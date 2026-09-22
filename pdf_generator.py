from fpdf import FPDF
from datetime import datetime


def generate_pdf_report(input_type, input_value, report_text, raw_items):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "DigitalTrace - Footprint Report", ln=True)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
    pdf.cell(0, 8, f"Checked {input_type}: {input_value}", ln=True)
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Report", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, report_text.encode("latin-1", "replace").decode("latin-1"), wrapmode="CHAR")
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Raw Search Results", ln=True)
    pdf.set_font("Helvetica", "", 9)

    for item in raw_items:
        title = (item.get("title") or "").encode("latin-1", "replace").decode("latin-1")
        link = (item.get("link") or "").encode("latin-1", "replace").decode("latin-1")
        snippet = (item.get("snippet") or "").encode("latin-1", "replace").decode("latin-1")

        pdf.set_font("Helvetica", "B", 9)
        pdf.multi_cell(0, 5, title, wrapmode="CHAR")
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 5, link, wrapmode="CHAR")
        pdf.multi_cell(0, 5, snippet, wrapmode="CHAR")
        pdf.ln(3)

    return bytes(pdf.output())