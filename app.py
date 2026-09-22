import streamlit as st
from serpapi_client import search_text, search_reverse_image, build_targeted_query, upload_image_temp
from analyzer import analyze_results
from pdf_generator import generate_pdf_report

st.set_page_config(page_title="DigitalTrace - Footprint Checker", page_icon="🔍")

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

                st.subheader("Report")
                if not image_matches:
                    st.write("No matches found for this image elsewhere online.")
                else:
                    st.write(f"This image appears in **{len(image_matches)}** other public locations online. Review below for anything unexpected.")
                    with st.expander("See matches"):
                        for item in image_matches[:8]:
                            st.markdown(f"**{item.get('title')}**")
                            st.write(item.get("link"))
                            st.divider()
    else:
        if not input_value.strip():
            st.warning("Please enter a value first.")
        else:
            with st.spinner("Searching public records..."):
                query = build_targeted_query(input_value, input_type)
                results = search_text(query)

            with st.spinner("Analyzing results..."):
                report = analyze_results(results, input_type, input_value)

            st.subheader("Report")
            st.write(report)

            with st.expander("See raw search results"):
                for item in results.get("organic_results", [])[:8]:
                    st.markdown(f"**{item.get('title')}**")
                    st.write(item.get("link"))
                    st.write(item.get("snippet"))
                    st.divider()

            pdf_bytes = generate_pdf_report(
                input_type, input_value, report,
                results.get("organic_results", [])[:8]
            )
            st.download_button(
                label="📄 Download Report as PDF",
                data=pdf_bytes,
                file_name=f"digitaltrace_report_{input_type}.pdf",
                mime="application/pdf"
            )