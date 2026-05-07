import streamlit as st
from datetime import datetime
from document_reader import extract_text
from ai_analyzer import analyze_document
from report_generator import generate_report

st.set_page_config(page_title="GFAM Due Diligence", page_icon="📋", layout="wide")

st.title("📋 GFAM Due Diligence Analyzer")
st.caption("AI-powered document analysis for Genesis Financial Asset Management")
st.divider()

SCORE_COLOR = {
    range(8, 11): "🟢",
    range(5, 8): "🟡",
    range(1, 5): "🔴",
}

def score_color(score):
    if score >= 8: return "🟢"
    if score >= 5: return "🟡"
    return "🔴"

# ── File upload ───────────────────────────────────────────────
st.subheader("Upload Deal Document")
st.write("Upload a CIM, pitch deck, financial statement, or any deal document.")

uploaded_file = st.file_uploader(
    "Drop your file here",
    type=["pdf", "docx", "xlsx", "xls"],
    help="Supported formats: PDF, Word (.docx), Excel (.xlsx)"
)

if uploaded_file:
    st.success(f"Uploaded: {uploaded_file.name}")

    if st.button("🔍 Run Due Diligence Analysis", use_container_width=True):

        # Step 1 — Extract text
        with st.spinner("Reading document..."):
            try:
                text, file_type = extract_text(uploaded_file)
                st.info(f"Extracted {len(text):,} characters from {file_type} document")
            except Exception as e:
                st.error(f"Could not read document: {e}")
                st.stop()

        if not text.strip():
            st.error("Could not extract any text from this document. Try a different file.")
            st.stop()

        # Step 2 — AI analysis
        with st.spinner("Running AI analysis... this may take 20-30 seconds"):
            try:
                analysis = analyze_document(text, uploaded_file.name)
            except Exception as e:
                st.error(f"AI analysis failed: {e}")
                st.stop()

        st.success("Analysis complete!")
        st.divider()

        # ── Deal snapshot ─────────────────────────────────────
        score = analysis.get("gfam_fit_score", 5)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Company", analysis.get("company_name", "Unknown"))
        col2.metric("Sector", analysis.get("sector", "Unknown"))
        col3.metric("Deal Type", analysis.get("deal_type", "Unknown"))
        col4.metric("GFAM Fit", f"{score_color(score)} {score}/10")

        st.divider()

        # ── Two column layout ─────────────────────────────────
        left, right = st.columns([3, 2])

        with left:
            st.subheader("Company Overview")
            st.write(analysis.get("company_overview", "N/A"))

            st.subheader("💡 Investment Thesis")
            st.info(analysis.get("investment_thesis", "N/A"))

            st.subheader("GFAM Fit Assessment")
            st.write(analysis.get("gfam_fit_reason", "N/A"))

            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("✅ Key Strengths")
                for s in analysis.get("key_strengths", []):
                    st.write(f"• {s}")

            with col_b:
                st.subheader("⚠️ Key Risks")
                for r in analysis.get("key_risks", []):
                    st.write(f"• {r}")

            red_flags = analysis.get("red_flags", [])
            if red_flags:
                st.subheader("🚨 Red Flags")
                for f in red_flags:
                    st.error(f)

        with right:
            st.subheader("Deal Snapshot")
            st.markdown(f"**Deal Size:** {analysis.get('deal_size', 'Unknown')}")
            st.markdown(f"**Capital Fit:** {analysis.get('recommended_capital_product', 'Unknown')}")

            st.subheader("Financial Highlights")
            fin = analysis.get("financial_highlights", {})
            fin_items = [
                ("Revenue", fin.get("revenue", "Unknown")),
                ("EBITDA", fin.get("ebitda", "Unknown")),
                ("Margins", fin.get("margins", "Unknown")),
                ("Debt", fin.get("debt", "Unknown")),
                ("Growth", fin.get("growth", "Unknown")),
            ]
            for label, value in fin_items:
                st.markdown(f"**{label}:** {value}")

            team = analysis.get("management_team", [])
            if team:
                st.subheader("Management Team")
                for member in team:
                    st.write(f"• {member}")

            st.subheader("Recommended Next Steps")
            for i, step in enumerate(analysis.get("next_steps", []), 1):
                st.write(f"{i}. {step}")

        st.divider()

        # ── Export ────────────────────────────────────────────
        try:
            report_bytes = generate_report(analysis, uploaded_file.name)
            st.download_button(
                label="📄 Download Due Diligence Report (.docx)",
                data=report_bytes,
                file_name=f"GFAM_DD_{analysis.get('company_name', 'Report').replace(' ', '_')}_{datetime.now().strftime('%Y-%m-%d')}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"Report generation failed: {e}")

else:
    st.info("👆 Upload a document above to get started.")

    st.divider()
    st.subheader("What this tool analyzes")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**📊 Financials**")
        st.write("Revenue, EBITDA, margins, debt levels, growth rates")
    with col2:
        st.markdown("**🏢 Company**")
        st.write("Business overview, management team, deal structure")
    with col3:
        st.markdown("**🎯 GFAM Fit**")
        st.write("Fit score, capital product recommendation, investment thesis")
