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

    prompt = f"""You are a senior investment analyst at Genesis Financial Asset Management (GFAM).
GFAM provides equity, structured debt, and hybrid capital for Healthcare Services, Infrastructure, Financial Services, and Special Situations deals.
Capital products: Growth Capital, Acquisition Financing, Liquidity Solutions, Special Situations Financing, Stabilization Capital.

Document: {clean(file_name)}

Read every word of this document and extract ALL specific numbers and details. Never write "Unknown" if the number appears anywhere in the text.

{cleaned_text}

Now respond ONLY with this JSON. No markdown. Fill every single field using the exact numbers from the document above:

{{
  "company_name": "company name",
  "sector": "Healthcare Services",
  "deal_type": "M&A",
  "asking_price": "CAD 55-65 million",
  "ev_ebitda_multiple": "7.2x - 8.5x",
  "deal_size": "CAD 55-65 million",
  "deal_structure": "Full share sale",
  "revenue": "CAD 38.2M (FY2025)",
  "ebitda": "CAD 7.6M (FY2025)",
  "ebitda_margin": "19.9%",
  "revenue_growth": "18% YoY",
  "net_income": "net income figure or Unknown",
  "debt": "CAD 6.8M term loan (BMO)",
  "recurring_revenue": "65% from insurance contracts",
  "financial_quality": "2-3 sentences on earnings quality referencing the specific numbers above",
  "value_creation_thesis": "3-4 sentences on how GFAM makes money — roll-up strategy, margin expansion, exit multiple. Be specific.",
  "market_context": "2-3 sentences on market size, growth drivers, competition",
  "gfam_fit_score": 8,
  "gfam_fit_reason": "2 sentences on fit with GFAM mandate referencing specific deal characteristics",
  "recommended_capital_product": "Acquisition Financing",
  "key_strengths": ["strength with specific data", "strength with specific data", "strength with specific data"],
  "key_risks": ["risk with context", "risk with context", "risk with context"],
  "red_flags": ["red flag if any, else leave empty array"],
  "diligence_checklist": ["item 1", "item 2", "item 3", "item 4", "item 5"],
  "recommendation": "GO",
  "recommendation_rationale": "2-3 direct sentences with specific numbers justifying the decision"
}}"""

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000,
    )

    raw = response.choices[0].message.content.strip()
    start = raw.find('{')
    end = raw.rfind('}') + 1
    if start != -1 and end > start:
        raw = raw[start:end]

    raw = re.sub(r'[\x00-\x1f\x7f]', ' ', raw)
    result = json.loads(raw)

    # Reshape flat response into nested structure app.py expects
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
