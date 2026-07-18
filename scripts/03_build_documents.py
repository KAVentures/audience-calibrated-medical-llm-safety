#!/usr/bin/env python3
from pathlib import Path
import re

import pandas as pd
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "manuscript"
TABLES = ROOT / "results" / "tables"
FIGURES = ROOT / "results" / "figures"
PANEL_TABLES = ROOT / "results" / "llm_judge_panel_tables"
PANEL_FIGURES = ROOT / "results" / "llm_judge_panel_figures"
METHOD_TABLES = ROOT / "results" / "evaluator_method_tables"
METHOD_FIGURES = ROOT / "results" / "evaluator_method_figures"
BLUE = RGBColor(46, 116, 181)
DARK_BLUE = RGBColor(31, 77, 120)
MUTED = RGBColor(90, 101, 111)
DISPLAY_LABELS = {
    "grok_4_3": "Grok 4.3",
    "gpt_5_5": "GPT-5.5",
    "gemini_3_5_flash": "Gemini 3.5 Flash",
    "claude_4_8_opus": "Claude Opus 4.8",
    "clinician_original": "Clinician original",
    "role_only_isolation": "Patient role-only",
    "patient_rewrite": "Patient rewrite",
    "unsafe_binary": "Unsafe response",
    "evidence_sufficiency_failure": "Evidence-sufficiency failure",
}
JAMIA_RUNNING_TITLE = "Evaluator-dependent medical LLM safety"
JAMIA_KEYWORDS = (
    "large language models; artificial intelligence; patient safety; "
    "medical informatics; reproducibility"
)


def set_repeat_table_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def set_table_row_cant_split(row):
    tr_pr = row._tr.get_or_add_trPr()
    cant_split = OxmlElement("w:cantSplit")
    tr_pr.append(cant_split)


def shade(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=80, start=120, bottom=80, end=120):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for margin, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{margin}"))
        if node is None:
            node = OxmlElement(f"w:{margin}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def add_page_field(paragraph):
    run = paragraph.add_run()
    fld_char1 = OxmlElement("w:fldChar")
    fld_char1.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    fld_char2 = OxmlElement("w:fldChar")
    fld_char2.set(qn("w:fldCharType"), "end")
    run._r.extend([fld_char1, instr, fld_char2])


def prevent_hyphen_breaks(text):
    return re.sub(r"(?<=[A-Za-z])-(?=[A-Za-z])", "\u2011", str(text))


def configure_document(doc, running_title):
    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1.2)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)
    section.header_distance = Inches(0.492)
    section.footer_distance = Inches(0.2)

    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(11)
    normal.paragraph_format.space_before = Pt(0)
    normal.paragraph_format.space_after = Pt(8)
    normal.paragraph_format.line_spacing = 1.333
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT

    title = styles["Title"]
    title.font.name = "Calibri"
    title.font.size = Pt(22)
    title.font.bold = True
    title.font.color.rgb = RGBColor(20, 35, 45)
    title.paragraph_format.space_before = Pt(0)
    title.paragraph_format.space_after = Pt(12)
    title.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT

    for name, size, color, before, after in (
        ("Heading 1", 16, BLUE, 18, 10),
        ("Heading 2", 13, BLUE, 12, 6),
        ("Heading 3", 12, DARK_BLUE, 8, 4),
    ):
        style = styles[name]
        style.font.name = "Calibri"
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = color
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(after)
        style.paragraph_format.keep_with_next = True

    for name in ("List Bullet", "List Number"):
        style = styles[name]
        style.font.name = "Calibri"
        style.font.size = Pt(11)
        style.paragraph_format.left_indent = Inches(0.375)
        style.paragraph_format.first_line_indent = Inches(-0.194)
        style.paragraph_format.space_after = Pt(4)
        style.paragraph_format.line_spacing = 1.208

    if "Figure Caption" not in styles:
        cap = styles.add_style("Figure Caption", WD_STYLE_TYPE.PARAGRAPH)
    else:
        cap = styles["Figure Caption"]
    cap.font.name = "Calibri"
    cap.font.size = Pt(9)
    cap.font.color.rgb = MUTED
    cap.paragraph_format.space_before = Pt(4)
    cap.paragraph_format.space_after = Pt(10)
    cap.paragraph_format.keep_with_next = False

    header = section.header.paragraphs[0]
    header.text = running_title
    header.alignment = WD_ALIGN_PARAGRAPH.LEFT
    header.runs[0].font.name = "Calibri"
    header.runs[0].font.size = Pt(8.5)
    header.runs[0].font.color.rgb = MUTED
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = footer.add_run("Page ")
    run.font.name = "Calibri"
    run.font.size = Pt(8.5)
    run.font.color.rgb = MUTED
    add_page_field(footer)


def configure_submission_document(doc):
    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)
    section.header_distance = Inches(0.5)
    section.footer_distance = Inches(0.5)

    line_numbers = OxmlElement("w:lnNumType")
    line_numbers.set(qn("w:countBy"), "1")
    line_numbers.set(qn("w:start"), "1")
    line_numbers.set(qn("w:restart"), "continuous")
    section._sectPr.append(line_numbers)

    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(12)
    normal.font.color.rgb = RGBColor(0, 0, 0)
    normal.paragraph_format.space_before = Pt(0)
    normal.paragraph_format.space_after = Pt(0)
    normal.paragraph_format.line_spacing = 2.0
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT

    title = styles["Title"]
    title.font.name = "Times New Roman"
    title.font.size = Pt(14)
    title.font.bold = True
    title.font.color.rgb = RGBColor(0, 0, 0)
    title.paragraph_format.space_before = Pt(0)
    title.paragraph_format.space_after = Pt(12)
    title.paragraph_format.line_spacing = 2.0
    title.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_p_pr = title._element.get_or_add_pPr()
    title_border = title_p_pr.find(qn("w:pBdr"))
    if title_border is not None:
        title_p_pr.remove(title_border)

    for name in ("Heading 1", "Heading 2", "Heading 3"):
        style = styles[name]
        style.font.name = "Times New Roman"
        style.font.size = Pt(12)
        style.font.bold = True
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.paragraph_format.space_before = Pt(12)
        style.paragraph_format.space_after = Pt(0)
        style.paragraph_format.line_spacing = 2.0
        style.paragraph_format.keep_with_next = True

    for name in ("List Bullet", "List Number"):
        style = styles[name]
        style.font.name = "Times New Roman"
        style.font.size = Pt(12)
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.paragraph_format.left_indent = Inches(0.5)
        style.paragraph_format.first_line_indent = Inches(-0.25)
        style.paragraph_format.space_after = Pt(0)
        style.paragraph_format.line_spacing = 2.0

    if "Figure Caption" not in styles:
        cap = styles.add_style("Figure Caption", WD_STYLE_TYPE.PARAGRAPH)
    else:
        cap = styles["Figure Caption"]
    cap.font.name = "Times New Roman"
    cap.font.size = Pt(12)
    cap.font.color.rgb = RGBColor(0, 0, 0)
    cap.paragraph_format.space_before = Pt(6)
    cap.paragraph_format.space_after = Pt(0)
    cap.paragraph_format.line_spacing = 2.0

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = footer.add_run("Page ")
    run.font.name = "Times New Roman"
    run.font.size = Pt(10)
    run.font.color.rgb = RGBColor(0, 0, 0)
    add_page_field(footer)


def add_inline_markup(paragraph, text):
    text = text.replace("  ", " ").strip()
    pattern = re.compile(r"(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*)")
    pos = 0
    for match in pattern.finditer(text):
        if match.start() > pos:
            paragraph.add_run(prevent_hyphen_breaks(text[pos:match.start()]))
        token = match.group(0)
        if token.startswith("`"):
            run = paragraph.add_run(token[1:-1])
            run.font.name = "Courier New"
            run.font.size = Pt(9.5)
        elif token.startswith("**"):
            run = paragraph.add_run(prevent_hyphen_breaks(token[2:-2]))
            run.bold = True
        else:
            run = paragraph.add_run(prevent_hyphen_breaks(token[1:-1]))
            run.italic = True
        pos = match.end()
    if pos < len(text):
        paragraph.add_run(prevent_hyphen_breaks(text[pos:]))


def add_markdown_table(doc, lines):
    rows = []
    for line in lines:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", cell or "") for cell in cells):
            continue
        rows.append(cells)
    if not rows:
        return
    table = doc.add_table(rows=len(rows), cols=max(map(len, rows)))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.style = "Table Grid"
    width = 6.5 / len(table.columns)
    for r, values in enumerate(rows):
        for c, value in enumerate(values):
            cell = table.cell(r, c)
            cell.width = Inches(width)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_cell_margins(cell)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.0
            add_inline_markup(p, value)
            for run in p.runs:
                run.font.name = "Calibri"
                run.font.size = Pt(8.5)
                if r == 0:
                    run.bold = True
                    run.font.color.rgb = RGBColor(255, 255, 255)
            if r == 0:
                shade(cell, "2E74B5")
            elif r % 2 == 0:
                shade(cell, "F4F6F9")
    set_repeat_table_header(table.rows[0])
    doc.add_paragraph()


def append_markdown(doc, markdown_path=None, skip_title=False, lines=None, marker_callback=None):
    if lines is None:
        lines = markdown_path.read_text().splitlines()
    buffer = []
    i = 0

    def flush():
        nonlocal buffer
        text = " ".join(part.strip() for part in buffer).strip()
        if text:
            p = doc.add_paragraph()
            add_inline_markup(p, text)
        buffer = []

    while i < len(lines):
        line = lines[i].rstrip()
        marker = re.fullmatch(r"<!--\s*([A-Z0-9_]+)\s*-->", line.strip())
        if marker:
            flush()
            if marker_callback is not None:
                marker_callback(doc, marker.group(1))
            i += 1
            continue
        if line.startswith("|"):
            flush()
            table_lines = []
            while i < len(lines) and lines[i].rstrip().startswith("|"):
                table_lines.append(lines[i].rstrip())
                i += 1
            add_markdown_table(doc, table_lines)
            continue
        if not line.strip():
            flush()
            i += 1
            continue
        heading = re.match(r"^(#{1,4})\s+(.*)$", line)
        if heading:
            flush()
            level = len(heading.group(1))
            text = heading.group(2).strip()
            if skip_title and level == 1:
                i += 1
                continue
            p = doc.add_paragraph(style="Title" if level == 1 else f"Heading {level - 1}")
            add_inline_markup(p, text)
            i += 1
            continue
        bullet = re.match(r"^-\s+(.*)$", line)
        number = re.match(r"^\d+\.\s+(.*)$", line)
        if bullet or number:
            flush()
            p = doc.add_paragraph(style="List Bullet" if bullet else "List Number")
            add_inline_markup(p, (bullet or number).group(1))
            i += 1
            continue
        buffer.append(line)
        i += 1
    flush()


def add_title_block(doc):
    lines = (MANUSCRIPT / "manuscript.md").read_text().splitlines()
    title = lines[0].removeprefix("# ")
    p = doc.add_paragraph(style="Title")
    add_inline_markup(p, title)
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(3)
    run = p.add_run("Koyar Afrasyab, MD")
    run.bold = True
    run.font.size = Pt(12)
    p = doc.add_paragraph("Kinvectum AB, Sweden")
    p.paragraph_format.space_after = Pt(3)
    p = doc.add_paragraph("Correspondence: Koyar Afrasyab | koyar@kinvectum.com | ORCID 0009-0009-3530-4606")
    p.paragraph_format.space_after = Pt(14)
    p.runs[0].font.color.rgb = MUTED
    p.runs[0].font.size = Pt(9.5)


def add_submission_title_block(doc):
    lines = (MANUSCRIPT / "manuscript.md").read_text().splitlines()
    title = lines[0].removeprefix("# ")
    p = doc.add_paragraph(style="Title")
    add_inline_markup(p, title)
    for text, bold in (
        ("Koyar Afrasyab, MD", True),
        ("Affiliation: Kinvectum AB, Sweden", False),
        ("Correspondence: Koyar Afrasyab, Kinvectum AB; koyar@kinvectum.com", False),
        ("ORCID: 0009-0009-3530-4606", False),
        (f"Running title: {JAMIA_RUNNING_TITLE}", False),
        ("Main-text word count: 3,732", False),
        (f"Keywords: {JAMIA_KEYWORDS}", False),
    ):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(text)
        run.bold = bold


def add_result_tables(doc, plain=False):
    doc.add_page_break()
    doc.add_paragraph("Tables", style="Heading 1")
    tests = pd.read_csv(PANEL_TABLES / "table_primary_interaction_tests.csv")
    tests = tests[["outcome", "events", "panel_model_prompt_chi2", "panel_model_prompt_df", "holm_p"]]
    tests["outcome"] = tests["outcome"].map(DISPLAY_LABELS)
    tests.columns = ["Outcome", "Events", "Wald chi-square", "Effective df", "Holm p"]
    add_dataframe_table(doc, tests.round(4), "Table 1. Co-primary generator-by-prompt interaction tests. Both reported tests use post hoc identity-link generalized estimating equations after the planned logistic models were not estimable.", plain=plain)

    rates = pd.read_csv(PANEL_TABLES / "table_panel_standardized_rates.csv")
    rates = rates[rates.outcome.eq("unsafe_binary")].copy()
    rates["rate_ci"] = rates.apply(lambda r: f"{100*r.rate:.2f}% ({100*r.ci_low:.2f}-{100*r.ci_high:.2f})", axis=1)
    rates = rates[["model_key", "prompt_version", "events", "judge_ratings", "rate_ci"]]
    rates["model_key"] = rates["model_key"].map(DISPLAY_LABELS)
    rates["prompt_version"] = rates["prompt_version"].map(DISPLAY_LABELS)
    rates.columns = ["Generator", "Prompt", "Positive ratings", "Judge ratings", "Panel rate (95% CI)"]
    add_dataframe_table(doc, rates, "Table 2. Evaluator-assigned unsafe rates. Panel estimates weight four fixed LLM judges equally; confidence intervals resample complete topics.", plain=plain)

    doc.add_page_break()
    methods = pd.read_csv(METHOD_TABLES / "table_evaluator_method_overall_rates.csv")
    methods["rate_ci"] = methods.apply(
        lambda r: f"{100*r.rate:.2f}% ({100*r.ci_low:.2f}-{100*r.ci_high:.2f})", axis=1
    )
    methods = methods[["method_label", "outcome_label", "events", "n", "rate_ci"]]
    methods.columns = ["Evaluator specification", "Outcome", "Events", "Ratings", "Rate (95% CI)"]
    add_dataframe_table(
        doc,
        methods,
        "Table 3. Evaluator-method comparison. Nominally matched outcomes are measurement outputs, not physician-validated endpoints; the deterministic engine is counted once.",
        plain=plain,
    )

    doc.add_page_break()
    sensitivity = pd.read_csv(PANEL_TABLES / "table_leave_one_judge_interaction_tests.csv")
    sensitivity = sensitivity[sensitivity.outcome.eq("unsafe_binary")].copy()
    sensitivity["omitted_judge"] = sensitivity["omitted_judge"].map({
        "grok_4_3": "Grok 4.3", "gpt_5_5": "GPT-5.5",
        "gemini_3_5_flash": "Gemini 3.5 Flash", "claude_4_8_opus": "Claude Opus 4.8",
    })
    sensitivity = sensitivity[[
        "omitted_judge", "events", "model_prompt_chi2", "effective_df", "raw_p",
        "holm_p_within_omission", "holm_p_all_8_sensitivity_tests",
    ]]
    sensitivity.columns = [
        "Omitted judge", "Events", "Wald chi-square", "Effective df", "Raw p",
        "Holm p within omission", "Holm p across 8 tests",
    ]
    add_dataframe_table(
        doc,
        sensitivity.round(4),
        "Table 4. Leave-one-judge-out sensitivity analysis for evaluator-assigned unsafe response. All rows use the same post hoc identity-link risk-difference model as the full-panel fallback.",
        plain=plain,
    )


def add_dataframe_table(doc, frame, caption, plain=False):
    p = doc.add_paragraph()
    p.paragraph_format.keep_with_next = True
    run = p.add_run(prevent_hyphen_breaks(caption))
    run.bold = True
    run.font.size = Pt(9.5)
    table = doc.add_table(rows=1, cols=len(frame.columns))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True
    for c, name in enumerate(frame.columns):
        cell = table.rows[0].cells[c]
        cell.text = prevent_hyphen_breaks(name)
        set_cell_margins(cell)
        for run in cell.paragraphs[0].runs:
            run.bold = True
            run.font.color.rgb = RGBColor(0, 0, 0) if plain else RGBColor(255, 255, 255)
            run.font.name = "Times New Roman" if plain else "Calibri"
            run.font.size = Pt(9 if plain else 7.5)
        if not plain:
            shade(cell, "2E74B5")
    set_repeat_table_header(table.rows[0])
    set_table_row_cant_split(table.rows[0])
    for ri, (_, row) in enumerate(frame.iterrows(), start=1):
        cells = table.add_row().cells
        for c, value in enumerate(row):
            cells[c].text = prevent_hyphen_breaks(value)
            cells[c].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_cell_margins(cells[c], top=55, bottom=55)
            if ri % 2 == 0 and not plain:
                shade(cells[c], "F4F6F9")
            for run in cells[c].paragraphs[0].runs:
                run.font.name = "Times New Roman" if plain else "Calibri"
                run.font.size = Pt(9 if plain else 7.2)
        for cell in cells:
            cell.paragraphs[0].paragraph_format.space_after = Pt(0)
            cell.paragraphs[0].paragraph_format.line_spacing = 1.0
        set_table_row_cant_split(table.rows[-1])
    doc.add_paragraph()


FIGURE_SPECS = {
    "FIGURE_1": (
        METHOD_FIGURES / "figure_1_evaluator_method_prevalence.png",
        "Figure 1. Positive prevalence across six evaluator specifications applied to the same 1,200 responses. The unsafe panel uses a symmetric-log scale, linear from 0% to 0.1%, so low-prevalence evaluators remain distinguishable from the deterministic engine. Each point is one complete evaluator stream with a 95% complete-topic bootstrap confidence interval. The deterministic engine is shown once because its GPT- and Claude-labelled workbooks were exact duplicates. Outcomes are not a physician reference standard.",
    ),
    "FIGURE_2": (
        PANEL_FIGURES / "figure_2_panel_unsafe_rates.png",
        "Figure 2. Panel-average evaluator-assigned unsafe rates by generator and prompt version. Points average the four fixed LLM judges equally; error bars are 95% complete-topic bootstrap confidence intervals.",
    ),
    "FIGURE_3": (
        PANEL_FIGURES / "figure_3_panel_evidence_rates.png",
        "Figure 3. Panel-average evidence-sufficiency failure by generator and prompt version. Points average the four fixed LLM judges equally; error bars are 95% complete-topic bootstrap confidence intervals.",
    ),
    "FIGURE_4": (
        PANEL_FIGURES / "figure_4_between_judge_agreement.png",
        "Figure 4. Pairwise Cohen kappa across judges. Diagonal cells are suppressed because self-agreement is uninformative. Rare unsafe events produce high exact agreement but low chance-corrected agreement.",
    ),
}


def add_figure_block(doc, marker, page_break=False):
    if page_break:
        doc.add_page_break()
    image_path, caption = FIGURE_SPECS[marker]
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(image_path), width=Inches(6.35))
    cp = doc.add_paragraph(style="Figure Caption")
    cp.add_run(prevent_hyphen_breaks(caption))


def add_figures(doc):
    doc.add_page_break()
    doc.add_paragraph("Figures", style="Heading 1")
    for idx, marker in enumerate(FIGURE_SPECS):
        add_figure_block(doc, marker, page_break=idx > 0)


def build_main():
    doc = Document()
    configure_document(doc, "Evaluator-dependent medical LLM safety")
    add_title_block(doc)
    lines = (MANUSCRIPT / "manuscript.md").read_text().splitlines()
    body_start = next(i for i, line in enumerate(lines) if line == "## Abstract")
    append_markdown(doc, lines=lines[body_start:], marker_callback=lambda target, marker: add_figure_block(target, marker))
    add_result_tables(doc)
    doc.core_properties.title = "Evaluator-dependent conclusions in audience-calibrated medical LLM safety assessment"
    doc.core_properties.author = "Koyar Afrasyab"
    doc.core_properties.subject = "Paired medical LLM benchmark study"
    doc.save(MANUSCRIPT / "audience_calibrated_medical_safety_manuscript.docx")
    doc.save(MANUSCRIPT / "audience_calibrated_medical_safety_medrxiv.docx")


def build_jamia_submission():
    doc = Document()
    configure_submission_document(doc)
    add_submission_title_block(doc)
    doc.add_page_break()
    append_markdown(doc, MANUSCRIPT / "jamia_abstract.md")
    lines = (MANUSCRIPT / "manuscript.md").read_text().splitlines()
    body_start = next(i for i, line in enumerate(lines) if line == "## Introduction")
    jamia_lines = lines[body_start:]
    jamia_lines[0] = "## Background and Significance"
    append_markdown(doc, lines=jamia_lines)
    add_result_tables(doc, plain=True)
    add_figures(doc)
    doc.core_properties.title = "Evaluator-dependent conclusions in audience-calibrated medical LLM safety assessment"
    doc.core_properties.author = "Koyar Afrasyab"
    doc.core_properties.subject = "JAMIA submission manuscript"
    doc.save(MANUSCRIPT / "audience_calibrated_medical_safety_JAMIA.docx")


def build_supplement():
    doc = Document()
    configure_document(doc, "Evaluator-dependent medical LLM safety | Supplement")
    append_markdown(doc, MANUSCRIPT / "supplement.md")
    doc.core_properties.title = "Supplementary appendix: evaluator-dependent medical LLM safety study"
    doc.core_properties.author = "Koyar Afrasyab"
    doc.save(MANUSCRIPT / "audience_calibrated_medical_safety_supplement.docx")


def build_ethics_self_assessment():
    doc = Document()
    configure_document(doc, "Ethics self-assessment | Kinvectum AB")
    append_markdown(doc, ROOT / "ETHICS_SELF_ASSESSMENT.md")
    for paragraph in doc.paragraphs:
        if paragraph.text.startswith("5. Clinician raters"):
            paragraph.paragraph_format.keep_together = True
    doc.core_properties.title = "Ethics Self-Assessment: Research Ethics Determination"
    doc.core_properties.author = "Koyar Afrasyab"
    doc.core_properties.subject = "Swedish Ethical Review Act research ethics determination"
    doc.save(ROOT / "ETHICS_SELF_ASSESSMENT.docx")


if __name__ == "__main__":
    build_main()
    build_jamia_submission()
    build_supplement()
    build_ethics_self_assessment()
