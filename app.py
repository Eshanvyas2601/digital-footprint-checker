import streamlit as st
from serpapi_client import search_text, search_reverse_image, build_targeted_query, upload_image_temp, multi_query_search
from evidence_engine import build_evidence_list
from identity_clustering import cluster_identities
from risk_scorer import calculate_risk
from analyzer import generate_narrative
from pdf_generator import generate_pdf_report

st.set_page_config(page_title="DigitalTrace - Footprint Checker", page_icon="🔍")


def parse_narrative(narrative_text):
    summary, actions = narrative_text, []
    if "RECOMMENDED ACTIONS:" in narrative_text:
        parts = narrative_text.split("RECOMMENDED ACTIONS:")
        summary = parts[0].replace("SUMMARY:", "").strip()
        actions = [line.strip("- ").strip() for line in parts[1].strip().split("\n") if line.strip()]
    else:
        summary = narrative_text.replace("SUMMARY:", "").strip()
    return summary, actions


def render_dashboard(input_type, input_value, risk, narrative, evidence_list):
    summary, actions = parse_narrative(narrative)

    st.title("DigitalTrace")
    st.caption("Digital Identity Verification Report")
    st.write(f"**Input:** {input_value}")
    st.divider()

    level_icon = {"LOW": "🟢", "MEDIUM": "🟠", "HIGH": "🔴"}
    st.subheader("Overall exposure")
    st.markdown(f"### {level_icon.get(risk['level'], '')} {risk['level']} — {risk['score']} / 100")
    st.progress(min(risk['score'], 100) / 100)
    st.caption(
        "This score measures how easily this identity could be confused with others online, "
        "or how exposed its public information is — it is not a judgment of danger or wrongdoing."
    )
    st.divider()

    c1, c2, c3 = st.columns(3)
    c1.metric("⚠ Signals detected", len(risk["signals"]))
    c2.metric("✓ Consistent references", risk["consistent_count"])
    c3.metric("ℹ Ambiguous results", risk["ambiguous_count"])
    st.divider()

    st.subheader("Summary")
    st.write(summary)
    st.divider()

    st.subheader("Findings")
    if not risk["signals"]:
        st.write("No specific risk signals were detected in the available public results.")
    else:
        for signal in risk["signals"]:
            with st.expander(f"⚠ {signal['label']} — {signal['points']} points ({len(signal['evidence'])} supporting source(s))"):
                st.write(f"**Why was this flagged?** {signal['reason']}")
                st.write("**Evidence:**")
                for i, ev in enumerate(signal["evidence"], 1):
                    st.markdown(f"*Evidence {i}* — [{ev['source_type']}] {ev['title']}")
                    st.write(ev["url"])
    st.divider()

    st.subheader("Sources")
    seen = set()
    for ev in evidence_list[:15]:
        if ev["url"] and ev["url"] not in seen:
            st.write(f"- [{ev['title']}]({ev['url']})")
            seen.add(ev["url"])
    st.divider()

    st.subheader("Recommended actions")
    for a in (actions or ["Verify identity through an independent channel before trusting it."]):
        st.write(f"- {a}")

    pdf_bytes = generate_pdf_report(
        input_type, input_value,
        f"SUMMARY: {summary}\n\nRISK LEVEL: {risk['level']} (score: {risk['score']}/100)",
        [{"title": ev["title"], "link": ev["url"], "snippet": ev["snippet"]} for ev in evidence_list[:15]]
    )
    st.download_button(
        label="📄 Download DigitalTrace Report (PDF)",
        data=pdf_bytes,
        file_name=f"digitaltrace_report_{input_type}.pdf",
        mime="application/pdf"
    )


st.title("🔍 DigitalTrace")
st.caption("Check your public digital footprint — for self-verification and citizen awareness only.")

input_type = st.selectbox("What are you checking?", ["name", "email", "phone", "image"])

if input_type == "image":
    uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
else:
    input_value = st.text_input(f"Enter the {input_type}:")

if st.button("Check Footprint"):
    if input_type == "image":
        if uploaded_file is None:
            st.warning("Please upload an image first.")
        else:
            with st.spinner("Uploading image..."):
                public_url = upload_image_temp(uploaded_file)
            if not public_url:
                st.error("Image upload failed. Please try again.")
            else:
                with st.spinner("Searching for matches..."):
                    results = search_reverse_image(public_url)
                image_matches = results.get("image_results", [])
                evidence_list = build_evidence_list(image_matches)

                with st.spinner("Scoring evidence..."):
                    risk = calculate_risk(evidence_list, "image", clusters=None, image_matches=image_matches)
                with st.spinner("Generating explanation..."):
                    narrative = generate_narrative("image", "uploaded photo", risk)

                render_dashboard("image", "Uploaded photo", risk, narrative, evidence_list)

    elif input_type == "name":
        if not input_value.strip():
            st.warning("Please enter a name first.")
        else:
            with st.spinner("Running multi-query OSINT search..."):
                results = multi_query_search(input_value)
            with st.spinner("Extracting evidence..."):
                evidence_list = build_evidence_list(results)
            with st.spinner("Clustering into likely identities..."):
                clusters = cluster_identities(evidence_list)
            with st.spinner("Scoring evidence..."):
                risk = calculate_risk(evidence_list, "name", clusters=clusters)
            with st.spinner("Generating explanation..."):
                narrative = generate_narrative(
                    input_type, input_value, risk,
                    extra_context=f"There are {len(clusters)} likely distinct identity clusters found."
                )
            render_dashboard(input_type, input_value, risk, narrative, evidence_list)

    else:
        if not input_value.strip():
            st.warning("Please enter a value first.")
        else:
            with st.spinner("Searching public records..."):
                query = build_targeted_query(input_value, input_type)
                results = search_text(query)
            with st.spinner("Extracting evidence..."):
                evidence_list = build_evidence_list(results.get("organic_results", []))
            with st.spinner("Scoring evidence..."):
                risk = calculate_risk(evidence_list, input_type, clusters=None)
            with st.spinner("Generating explanation..."):
                narrative = generate_narrative(input_type, input_value, risk)
            render_dashboard(input_type, input_value, risk, narrative, evidence_list)