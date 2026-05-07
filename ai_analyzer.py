import json
import re
import streamlit as st
from groq import Groq


def clean(text):
    if not text:
        return ""
    return text.encode('ascii', 'ignore').decode('ascii')


def truncate(text, max_chars=6000):
    if len(text) > max_chars:
        return text[:max_chars] + "\n[Document truncated...]"
    return text


def analyze_document(text: str, file_name: str) -> dict:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])

    prompt = f"""You are a senior investment analyst at Genesis Financial Asset Management (GFAM), a Toronto-based private investment firm.

GFAM focuses on: Infrastructure, Healthcare Services, Financial Services, Special Situations.
GFAM provides: equity, structured debt, and hybrid capital.
Capital products: Growth Capital, Acquisition Financing, Liquidity Solutions, Special Situations Financing, Stabilization Capital.

You are reviewing a deal document: {clean(file_name)}

Your job is to produce a concise, senior-level investment analysis focused on the DECISION — should GFAM pursue this? What are the key numbers? What is the value creation angle? What are the risks?

Respond ONLY with a single JSON object. No markdown, no extra text.

Document:
{truncate(clean(text))}

Return exactly this JSON:
{{
  "company_name": "Company name",
  "sector": "Infrastructure, Healthcare Services, Financial Services, Special Situations, or Other",
  "deal_type": "M&A, Growth Equity, Debt Financing, Recapitalization, Distressed, IPO, Other",

  "deal_economics": {{
    "asking_price": "Valuation or price if mentioned, else Unknown",
    "ev_ebitda_multiple": "EV/EBITDA multiple if mentioned, else Unknown",
    "deal_size": "Transaction size if mentioned, else Unknown",
    "structure": "How the deal is structured — equity, debt, hybrid, full sale, minority, etc."
  }},

  "financial_snapshot": {{
    "revenue": "Revenue figure and year",
    "ebitda": "EBITDA figure and year",
    "ebitda_margin": "EBITDA margin %",
    "revenue_growth": "YoY revenue growth rate",
    "net_income": "Net income if mentioned",
    "debt": "Existing debt level",
    "recurring_revenue": "% or description of recurring revenue if mentioned"
  }},

  "financial_quality": "2-3 sentences assessing the quality of earnings — are margins strong, is growth sustainable, is revenue recurring or lumpy, any accounting concerns",

  "value_creation_thesis": "3-4 sentences on HOW GFAM would make money — what is the entry angle, what drives value (organic growth, M&A roll-up, margin expansion, refinancing, exit), what is the expected return profile",

  "market_context": "2-3 sentences on the market — size, growth rate, competitive dynamics, tailwinds or headwinds relevant to this deal",

  "gfam_fit_score": <integer 1-10>,
  "gfam_fit_reason": "2 sentences on why this fits or does not fit GFAM mandate",
  "recommended_capital_product": "Growth Capital, Acquisition Financing, Liquidity Solutions, Special Situations Financing, Stabilization Capital, or None",

  "key_strengths": ["strength 1", "strength 2", "strength 3"],
  "key_risks": ["risk 1", "risk 2", "risk 3"],
  "red_flags": ["serious concern 1 if any — leave empty array if none"],

  "diligence_checklist": [
    "Item that needs to be verified or requested before proceeding"
  ],

  "recommendation": "GO, CONDITIONAL GO, or PASS",
  "recommendation_rationale": "2-3 sentences justifying the recommendation — be direct and specific"
}}"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1800,
    )

    raw = response.choices[0].message.content.strip()
    start = raw.find('{')
    end = raw.rfind('}') + 1
    if start != -1 and end > start:
        raw = raw[start:end]

    raw = re.sub(r'[\x00-\x1f\x7f]', ' ', raw)
    return json.loads(raw)
