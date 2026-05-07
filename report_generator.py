from datetime import datetime
from io import BytesIO
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


def clean(text):
    if not text:
        return ""
    return str(text).encode('ascii', 'ignore').decode('ascii')


def set_cell_bg(cell, hex_color):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)


def add_cell_text(cell, text, bold=False, font_size=10, color=None):
    para = cell.paragraphs[0]
    run = para.add_run(clean(str(text or "")))
    run.bold = bold
    run.font.size = Pt(font_size)
    run.font.name = "Arial"
    if color:
        run.font.color.rgb = RGBColor.from_string(color)


def add_section_heading(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(4)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '4')
    bottom.set(qn('w:space'), '1')
    bottom.set(qn('w:color'), 'CCCCCC')
    pBdr.append(bottom)
    pPr.append(pBdr)
    run = p.add_run(clean(text).upper())
    run.bold = True
    run.font.size = Pt(11)
    run.font.name = "Arial"
    run.font.color.rgb = RGBColor.from_string("1F3864")


def add_body(doc, text, italic=False, color=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run(clean(str(text or "")))
    run.font.size = Pt(10)
    run.font.name = "Arial"
    run.italic = italic
    if color:
        run.font.color.rgb = RGBColor.from_string(color)
    return p


def add_bullet(doc, text):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_after = Pt(2)
    run = p.runs[0] if p.runs else p.add_run()
    run.text = clean(str(text or ""))
    run.font.size = Pt(10)
    run.font.name = "Arial"


def generate_report(analysis: dict, file_name: str) -> bytes:
    today = datetime.now().strftime("%B %d, %Y")
    doc = Document()

    for section in doc.sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    # ── Header ───────────────────────────────────────────────
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '12')
    bottom.set(qn('w:space'), '1')
    bottom.set(qn('w:color'), '1F3864')
    pBdr.append(bottom)
    pPr.append(pBdr)
    r1 = p.add_run("GFAM DUE DILIGENCE SUMMARY")
    r1.bold = True
    r1.font.size = Pt(16)
    r1.font.name = "Arial"
    r1.font.color.rgb = RGBColor.from_string("1F3864")
    r2 = p.add_run(f"    {today}")
    r2.font.size = Pt(10)
    r2.font.name = "Arial"
    r2.font.color.rgb = RGBColor.from_string("888888")

    doc.add_paragraph()

    # ── Snapshot table ────────────────────────────────────────
    add_section_heading(doc, "Deal Snapshot")
    doc.add_paragraph()

    snap = doc.add_table(rows=0, cols=2)
    snap.style = 'Table Grid'
    snap.autofit = False
    snap.columns[0].width = Inches(2)
    snap.columns[1].width = Inches(4.5)

    snapshot_fields = [
        ("Company", analysis.get("company_name", "Unknown")),
        ("Source Document", file_name),
        ("Sector", analysis.get("sector", "Unknown")),
        ("Deal Type", analysis.get("deal_type", "Unknown")),
        ("Deal Size", analysis.get("deal_size", "Unknown")),
        ("Capital Fit", analysis.get("recommended_capital_product", "Unknown")),
        ("GFAM Fit Score", f"{analysis.get('gfam_fit_score', 'N/A')}/10"),
    ]

    for label, value in snapshot_fields:
        row = snap.add_row()
        set_cell_bg(row.cells[0], "DCE6F1")
        add_cell_text(row.cells[0], label, bold=True, font_size=10)
        add_cell_text(row.cells[1], value, font_size=10)

    doc.add_paragraph()

    # ── Company overview ──────────────────────────────────────
    add_section_heading(doc, "Company Overview")
    add_body(doc, analysis.get("company_overview", ""))

    # ── Financial highlights ──────────────────────────────────
    add_section_heading(doc, "Financial Highlights")
    fin = analysis.get("financial_highlights", {})
    doc.add_paragraph()

    ftable = doc.add_table(rows=0, cols=2)
    ftable.style = 'Table Grid'
    ftable.autofit = False
    ftable.columns[0].width = Inches(2)
    ftable.columns[1].width = Inches(4.5)

    for label, key in [("Revenue", "revenue"), ("EBITDA", "ebitda"),
                        ("Margins", "margins"), ("Debt", "debt"), ("Growth", "growth")]:
        row = ftable.add_row()
        set_cell_bg(row.cells[0], "EEF3FB")
        add_cell_text(row.cells[0], label, bold=True, font_size=10)
        add_cell_text(row.cells[1], fin.get(key, "Unknown"), font_size=10)

    doc.add_paragraph()

    # ── Investment thesis ─────────────────────────────────────
    add_section_heading(doc, "Investment Thesis")
    add_body(doc, analysis.get("investment_thesis", ""), italic=True, color="1F3864")

    # ── GFAM fit ──────────────────────────────────────────────
    add_section_heading(doc, "GFAM Fit Assessment")
    add_body(doc, analysis.get("gfam_fit_reason", ""))

    # ── Key strengths ─────────────────────────────────────────
    add_section_heading(doc, "Key Strengths")
    for s in analysis.get("key_strengths", []):
        add_bullet(doc, s)

    # ── Key risks ─────────────────────────────────────────────
    add_section_heading(doc, "Key Risks")
    for r in analysis.get("key_risks", []):
        add_bullet(doc, r)

    # ── Red flags ─────────────────────────────────────────────
    red_flags = analysis.get("red_flags", [])
    if red_flags:
        add_section_heading(doc, "Red Flags")
        for f in red_flags:
            p = doc.add_paragraph(style='List Bullet')
            p.paragraph_format.space_after = Pt(2)
            run = p.runs[0] if p.runs else p.add_run()
            run.text = clean(str(f or ""))
            run.font.size = Pt(10)
            run.font.name = "Arial"
            run.font.color.rgb = RGBColor.from_string("A32D2D")

    # ── Management team ───────────────────────────────────────
    team = analysis.get("management_team", [])
    if team:
        add_section_heading(doc, "Management Team")
        for member in team:
            add_bullet(doc, member)

    # ── Next steps ────────────────────────────────────────────
    add_section_heading(doc, "Recommended Next Steps")
    for step in analysis.get("next_steps", []):
        add_bullet(doc, step)

    # ── Footer ────────────────────────────────────────────────
    footer = doc.sections[0].footer
    fp = footer.paragraphs[0]
    fr = fp.add_run(f"GFAM Due Diligence  |  Confidential  |  {today}")
    fr.font.size = Pt(8)
    fr.font.name = "Arial"
    fr.font.color.rgb = RGBColor.from_string("999999")

    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.read()
