import json
import re
import streamlit as st
from groq import Groq


def clean(text):
    if not text:
        return ""
    return text.encode('ascii', 'ignore').decode('ascii')


def truncate(text, max_chars=6000):
    """Truncate text to avoid hitting token limits."""
    if len(text) > max_chars:
        return text[:max_chars] + "\n[Document truncated for analysis...]"
    return text


def analyze_document(text: str, file_name: str) -> dict:
    """
    Sends extracted document text to Groq and returns
    a structured due diligence summary as a dict.
    """
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])

    prompt = f"""You are a senior analyst at Genesis Financial Asset Management (GFAM), a Toronto-based private investment firm.

GFAM focuses on: Infrastructure, Healthcare Services, Financial Services, Special Situations.
GFAM provides: equity, structured debt, and hybrid capital.
Capital products: Growth Capital, Acquisition Financing, Liquidity Solutions, Special Situations Financing, Stabilization Capital.

You are reviewing a document called: {clean(file_name)}

Perform a thorough due diligence analysis and respond ONLY with a single JSON object. No markdown, no extra text.

Document content:
{truncate(clean(text))}

Return exactly this JSON structure:
{{
  "company_name": "Name of the company or entity",
  "company_overview": "3-4 sentences describing what the company does, its size, stage, and business model",
  "sector": "Which GFAM sector this falls under: Infrastructure, Healthcare Services, Financial Services, Special Situations, or Other",
  "deal_type": "Type of deal: M&A, Growth Equity, Debt Financing, Recapitalization, Distressed, IPO, Other",
  "deal_size": "Estimated deal size or valuation if mentioned, otherwise Unknown",
  "financial_highlights": {{
    "revenue": "Revenue figure if mentioned, otherwise Unknown",
    "ebitda": "EBITDA figure if mentioned, otherwise Unknown",
    "margins": "Margin profile if mentioned, otherwise Unknown",
    "debt": "Debt level if mentioned, otherwise Unknown",
    "growth": "Revenue or earnings growth rate if mentioned, otherwise Unknown"
  }},
  "key_strengths": ["strength 1", "strength 2", "strength 3"],
  "key_risks": ["risk 1", "risk 2", "risk 3"],
  "management_team": ["Name and title if mentioned"],
  "gfam_fit_score": <integer 1-10 on how well this fits GFAM's mandate>,
  "gfam_fit_reason": "2-3 sentences on why this does or does not fit GFAM's strategy",
  "recommended_capital_product": "Which GFAM capital product best fits: Growth Capital, Acquisition Financing, Liquidity Solutions, Special Situations Financing, Stabilization Capital, or None",
  "investment_thesis": "3-4 sentences on the investment angle GFAM could pursue — what makes this interesting, what value could be created",
  "red_flags": ["Any serious concerns or deal breakers if present"],
  "next_steps": ["Recommended next steps for GFAM to evaluate this opportunity"]
}}"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1500,
    )

    raw = response.choices[0].message.content.strip()

    # Extract JSON robustly
    start = raw.find('{')
    end = raw.rfind('}') + 1
    if start != -1 and end > start:
        raw = raw[start:end]

    # Remove control characters
    raw = re.sub(r'[\x00-\x1f\x7f]', ' ', raw)

    return json.loads(raw)
