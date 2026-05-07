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

    prompt = f"""You are a senior investment analyst at Genesis Financial Asset Management (GFAM), a Toronto-based private investment firm.

GFAM focuses on: Infrastructure, Healthcare Services, Financial Services, Special Situations.
GFAM provides: equity, structured debt, and hybrid capital.
Capital products: Growth Capital, Acquisition Financing, Liquidity Solutions, Special Situations Financing, Stabilization Capital.

You are reviewing: {clean(file_name)}

IMPORTANT: Extract ALL specific numbers, figures, and data points mentioned in the document. Do not say "Unknown" if the information exists in the document. Search carefully through the entire text for financial figures, deal terms, and specific details.

Respond ONLY with a single JSON object. No markdown, no extra text.

Document content:
{cleaned_text}

Return this exact JSON — fill in every field you can find in the document:
{{
  "company_name": "exact company name from document",
  "sector": "Infrastructure, Healthcare Services, Financial Services, Special Situations, or Other",
  "deal_type": "M&A, Growth Equity, Debt Financing, Recapitalization, Distressed, IPO, Other",

  "deal_economics": {{
    "asking_price": "exact valuation or price range from document, e.g. CAD 55-65 million",
    "ev_ebitda_multiple": "exact multiple from document, e.g. 7-8.5x",
    "deal_size": "transaction size from document",
    "structure": "exact deal structure — full share sale, minority stake, debt, hybrid, etc."
  }},

  "financial_snapshot": {{
    "revenue": "exact revenue figure and year, e.g. CAD 38.2M (FY2025)",
    "ebitda": "exact EBITDA figure and year, e.g. CAD 7.6M (FY2025)",
    "ebitda_margin": "exact margin %, e.g. 19.9%",
    "revenue_growth": "exact growth rate, e.g. 18% YoY",
    "net_income": "exact net income if in document",
    "debt": "exact debt figure, e.g. CAD 6.8M term loan",
    "recurring_revenue": "exact % or description of recurring revenue"
  }},

  "financial_quality": "2-3 sentences assessing earnings quality — are margins strong, is growth sustainable, is revenue recurring, any concerns. Reference specific numbers.",

  "value_creation_thesis": "3-4 sentences on HOW GFAM would make money — entry angle, value drivers (organic growth, M&A roll-up, margin expansion), expected return profile. Be specific.",

  "market_context": "2-3 sentences on market size, growth rate, competitive dynamics, tailwinds relevant to this deal.",

  "gfam_fit_score": <integer 1-10>,
  "gfam_fit_reason": "2 sentences on why this fits GFAM mandate. Reference specific deal characteristics.",
  "recommended_capital_product": "Growth Capital, Acquisition Financing, Liquidity Solutions, Special Situations Financing, Stabilization Capital, or None",

  "key_strengths": [
    "specific strength with data point from document",
    "specific strength with data point from document",
    "specific strength with data point from document"
  ],
  "key_risks": [
    "specific risk with context from document",
    "specific risk with context from document",
    "specific risk with context from document"
  ],
  "red_flags": ["serious concern if any — empty array if none"],

  "diligence_checklist": [
    "Specific item to verify or request",
    "Specific item to verify or request",
    "Specific item to verify or request",
    "Specific item to verify or request",
    "Specific item to verify or request"
  ],

  "recommendation": "GO, CONDITIONAL GO, or PASS",
  "recommendation_rationale": "2-3 direct sentences justifying the recommendation with specific numbers and reasons."
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
    return json.loads(raw)
