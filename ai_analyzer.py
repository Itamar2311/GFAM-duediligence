import json
import re
import streamlit as st
from groq import Groq


def clean(text):
    if not text:
        return ""
    return text.encode('ascii', 'ignore').decode('ascii')


def truncate(text, max_chars=10000):
    if len(text) > max_chars:
        return text[:max_chars] + "\n[Document truncated...]"
    return text


def analyze_document(text: str, file_name: str) -> dict:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    cleaned_text = truncate(clean(text))

    prompt = f"""Read this document carefully and extract the specific values listed below.

{cleaned_text}

From the document above, find and return ONLY this JSON with the real values — no placeholders, no "Unknown" if the value exists in the text:

{{
  "company_name": "exact company name",
  "sector": "exact sector",
  "deal_type": "exact deal type",
  "asking_price": "exact EV or price range",
  "ev_ebitda_multiple": "exact multiple",
  "deal_size": "exact deal size",
  "deal_structure": "exact structure e.g. full share sale",
  "revenue": "exact revenue with year",
  "ebitda": "exact EBITDA with year",
  "ebitda_margin": "exact margin %",
  "revenue_growth": "exact growth rate",
  "net_income": "exact net income",
  "debt": "exact debt amount",
  "recurring_revenue": "% or description of recurring revenue",
  "financial_quality": "write 2-3 sentences assessing earnings quality using the numbers you found",
  "value_creation_thesis": "write 3-4 sentences on how an investor makes money here — roll-up, growth, margin expansion, exit",
  "market_context": "write 2-3 sentences on the market opportunity",
  "gfam_fit_score": 8,
  "gfam_fit_reason": "write 2 sentences on investment fit",
  "recommended_capital_product": "one of: Growth Capital, Acquisition Financing, Liquidity Solutions, Special Situations Financing, Stabilization Capital",
  "key_strengths": ["specific strength 1", "specific strength 2", "specific strength 3"],
  "key_risks": ["specific risk 1", "specific risk 2", "specific risk 3"],
  "red_flags": [],
  "diligence_checklist": ["item 1", "item 2", "item 3", "item 4", "item 5"],
  "recommendation": "GO or CONDITIONAL GO or PASS",
  "recommendation_rationale": "write 2-3 sentences justifying the recommendation with specific numbers"
}}"""

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000,
        temperature=0.1,
    )

    raw = response.choices[0].message.content.strip()

    # Show raw response in app for debugging
    st.expander("🔧 Raw AI response (debug)").write(raw)

    start = raw.find('{')
    end = raw.rfind('}') + 1
    if start != -1 and end > start:
        raw = raw[start:end]

    raw = re.sub(r'[\x00-\x1f\x7f]', ' ', raw)
    result = json.loads(raw)

    return {
        "company_name": result.get("company_name", "Unknown"),
        "sector": result.get("sector", "Unknown"),
        "deal_type": result.get("deal_type", "Unknown"),
        "deal_economics": {
            "asking_price": result.get("asking_price", "Unknown"),
            "ev_ebitda_multiple": result.get("ev_ebitda_multiple", "Unknown"),
            "deal_size": result.get("deal_size", "Unknown"),
            "structure": result.get("deal_structure", "Unknown"),
        },
        "financial_snapshot": {
            "revenue": result.get("revenue", "Unknown"),
            "ebitda": result.get("ebitda", "Unknown"),
            "ebitda_margin": result.get("ebitda_margin", "Unknown"),
            "revenue_growth": result.get("revenue_growth", "Unknown"),
            "net_income": result.get("net_income", "Unknown"),
            "debt": result.get("debt", "Unknown"),
            "recurring_revenue": result.get("recurring_revenue", "Unknown"),
        },
        "financial_quality": result.get("financial_quality", ""),
        "value_creation_thesis": result.get("value_creation_thesis", ""),
        "market_context": result.get("market_context", ""),
        "gfam_fit_score": result.get("gfam_fit_score", 5),
        "gfam_fit_reason": result.get("gfam_fit_reason", ""),
        "recommended_capital_product": result.get("recommended_capital_product", "None"),
        "key_strengths": result.get("key_strengths", []),
        "key_risks": result.get("key_risks", []),
        "red_flags": result.get("red_flags", []),
        "diligence_checklist": result.get("diligence_checklist", []),
        "recommendation": result.get("recommendation", "CONDITIONAL GO"),
        "recommendation_rationale": result.get("recommendation_rationale", ""),
    }
