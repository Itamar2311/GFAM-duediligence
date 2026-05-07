import streamlit as st
from datetime import datetime
from document_reader import extract_text
from ai_analyzer import analyze_document
from report_generator import generate_report

st.set_page_config(page_title="GFAM Due Diligence", page_icon="📋", layout="wide")

st.title("📋 GFAM Due Diligence Analyzer")
st.caption("AI-powered investment analysis for Genesis Financial Asset Management")
st.divider()

def score_color(score):
    if score >= 8: return "🟢"
    if score >= 5: return "🟡"
    return "🔴"

def rec_color(rec):
    if rec == "GO": return "success"
    if rec == "CONDITIONAL GO": return "warning"
    return "error"

uploaded_file = st.file_uploader(
    "Upload a CIM, pitch deck, financial statement, or any deal document",
    type=["pdf", "docx", "xlsx", "xls"],
    help="Supported: PDF, Word (.docx), Excel (.xlsx)"
)

if uploaded_file:
    st.success(f"Uploaded: {uploaded_file.name}")

    if st.button("🔍 Run Investment Analysis", use_container_width=True):

        with st.spinner("Reading document..."):
            try:
                text, file_type = extract_text(uploaded_file)
            except Exception as e:
                st.error(f"Could not read document: {e}")
                st.stop()

        if not text.strip():
            st.error("Could not extract any text from this document.")
            st.stop()

        with st.spinner("Running AI analysis..."):
            try:
                analysis = analyze_document(text, uploaded_file.name)
            except Exception as e:
                st.error(f"AI analysis failed: {e}")
                st.stop()

        st.divider()

        # ── Recommendation banner ─────────────────────────────
        rec = analysis.get("recommendation", "CONDITIONAL GO")
        getattr(st, rec_color(rec))(f"**{rec}** — {analysis.get('recommendation_rationale', '')}")

        st.divider()

        # ── Top metrics ───────────────────────────────────────
        econ = analysis.get("deal_economics", {})
        fin = analysis.get("financial_snapshot", {})
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Company", analysis.get("company_name", "Unknown"))
        col2.metric("Sector", analysis.get("sector", "Unknown"))
        col3.metric("Asking Price", econ.get("asking_price", "Unknown"))
        col4.metric("EV/EBITDA", econ.get("ev_ebitda_multiple", "Unknown"))
        col5.metric("GFAM Fit", f"{score_color(analysis.get('gfam_fit_score', 5))} {analysis.get('gfam_fit_score', 5)}/10")

        st.divider()

        left, right = st.columns([3, 2])

        with left:
            st.subheader("💡 Value Creation Thesis")
            st.info(analysis.get("value_creation_thesis", ""))

            st.subheader("Financial Quality")
            st.write(analysis.get("financial_quality", ""))

            st.subheader("Market Context")
            st.write(analysis.get("market_context", ""))

            st.subheader("GFAM Fit")
            st.write(analysis.get("gfam_fit_reason", ""))

            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("✅ Strengths")
                for s in analysis.get("key_strengths", []):
                    st.write(f"• {s}")
            with col_b:
                st.subheader("⚠️ Risks")
                for r in analysis.get("key_risks", []):
                    st.write(f"• {r}")

            red_flags = analysis.get("red_flags", [])
            if red_flags:
                st.subheader("🚨 Red Flags")
                for f in red_flags:
                    st.error(f)

        with right:
            st.subheader("Deal Economics")
            st.markdown(f"**Deal Type:** {analysis.get('deal_type', 'Unknown')}")
            st.markdown(f"**Structure:** {econ.get('structure', 'Unknown')}")
            st.markdown(f"**Deal Size:** {econ.get('deal_size', 'Unknown')}")
            st.markdown(f"**Capital Product:** {analysis.get('recommended_capital_product', 'Unknown')}")

            st.subheader("Financials")
            for label, key in [
                ("Revenue", "revenue"), ("EBITDA", "ebitda"),
                ("Margin", "ebitda_margin"), ("Growth", "revenue_growth"),
                ("Net Income", "net_income"), ("Debt", "debt"),
                ("Recurring Rev.", "recurring_revenue")
            ]:
                val = fin.get(key, "Unknown")
                if val and val != "Unknown":
                    st.markdown(f"**{label}:** {val}")

            st.subheader("📋 Diligence Checklist")
            for i, item in enumerate(analysis.get("diligence_checklist", []), 1):
                st.write(f"{i}. {item}")

        st.divider()

        try:
            report_bytes = generate_report(analysis, uploaded_file.name)
            st.download_button(
                label="📄 Download Investment Analysis (.docx)",
                data=report_bytes,
                file_name=f"GFAM_Analysis_{analysis.get('company_name','Report').replace(' ','_')}_{datetime.now().strftime('%Y-%m-%d')}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"Report generation failed: {e}")

else:
    st.info("👆 Upload a deal document to get started.")
    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**📊 Deal Economics**")
        st.write("Asking price, EV/EBITDA multiple, deal structure, capital fit")
    with col2:
        st.markdown("**💰 Financial Analysis**")
        st.write("Revenue, EBITDA, margins, debt, growth, earnings quality")
    with col3:
        st.markdown("**🎯 Investment Decision**")
        st.write("GO / PASS recommendation, value creation thesis, diligence checklist")
