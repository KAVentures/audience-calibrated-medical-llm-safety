#!/usr/bin/env python3
"""Offline source and optional generated-PDF preflight for the arXiv-facing paper.

Does not rerun generators, judges, or statistics; the numerical integrity checks
remain in scripts/check_research_integrity.py.
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF_TITLES = {
    "2607.18086": "Judge-dependent safety gains and model-specific helpfulness costs of evidence-sufficiency prompting in clinical LLMs",
    "2607.18828": "Evaluating medical AI under missing information: same-provider judges and human raters change apparent safety",
}

def source_checks():
    paper = (ROOT / "manuscript/manuscript.md").read_text(encoding="utf-8")
    mirror = (ROOT / "PAPER.md").read_text(encoding="utf-8")
    assert paper == mirror, "PAPER.md must mirror canonical manuscript"
    assert "Koyar Afrasyab, M.D.^1^" in paper, "author credentials should match prior preprints"
    assert "ORCID: 0009-0009-3530-4606" in paper
    assert "koyar@kinvectum.com" in paper
    assert "**Keywords:**" in paper and "LLM-as-judge" in paper
    assert "holistic GPT scoring calibrated on physician examples" not in paper, "obsolete calibration provenance"
    assert "incompletely documented calibration" in paper
    assert "independent replications" in paper
    for identifier, title in REF_TITLES.items():
        assert paper.count("doi:10.48550/arXiv." + identifier) == 1
        assert paper.count(title) == 1, f"missing correct citation title {identifier}"
        assert "arXiv:" + identifier in paper
    heading_order = ["## Abstract", "## Introduction", "## Methods",
                     "## Results", "## Discussion", "## Declarations", "## References"]
    offsets = [paper.index("\n" + h + "\n") for h in heading_order]
    assert offsets == sorted(offsets), "core paper sections out of order"
    reference_numbers = [int(v) for v in re.findall(r"^([0-9]+)\. [^\n]+$", paper.split("## References", 1)[1], re.M)]
    assert reference_numbers == list(range(1, 19)), "expected contiguous 1–18 references"
    summary = json.loads((ROOT / "results/llm_judge_panel_analysis_summary.json").read_text(encoding="utf-8"))
    assert summary["primary_ratings"] == 4800
    assert summary["unique_responses"] == 1200
    tests = {x["outcome"]: x for x in summary["primary_tests"]}
    assert tests["unsafe_binary"]["events"] == 25
    assert tests["evidence_sufficiency_failure"]["events"] == 102
    assert "25/4,800" in paper and "102/4,800" in paper
    builder = (ROOT / "scripts/03_build_documents.py").read_text(encoding="utf-8")
    assert '"Koyar Afrasyab, M.D."' in builder
    assert 'normal.font.name = "Times New Roman"' in builder
    assert "add_result_tables(doc, plain=True)" in builder
    print("PASS: arXiv manuscript structure, related-work attribution, authorship and source numerics")

def pdf_checks():
    path = ROOT / "PAPER.pdf"
    assert path.is_file() and path.stat().st_size > 20000, "regenerate paper PDF"
    info = subprocess.check_output(["pdfinfo", str(path)], text=True)
    match = re.search(r"^Pages:\s+(\d+)", info, re.M)
    assert match and int(match.group(1)) >= 5, "unexpectedly short manuscript PDF"
    rendered = subprocess.check_output(["pdftotext", str(path), "-"], text=True)
    normalized = " ".join(rendered.split())
    for token in ("Koyar Afrasyab, M.D.", "2607.18086", "2607.18828", "Keywords:",
                  "Figure 1.", "Figure 2.", "Figure 3.", "Figure 4."):
        assert token in normalized, f"PDF extraction missing {token}; verify source/binary sync"
    fonts = subprocess.check_output(["pdffonts", str(path)], text=True)
    font_lines = fonts.strip().splitlines()[2:]
    assert font_lines, "cannot inspect fonts embedded in PDF"
    for font in font_lines:
        assert "Type 3" not in font, f"unsupported Type 3 font: {font}"
        match = re.search(r"\s+(yes|no)\s+(yes|no)\s+(yes|no)\s+\d+\s+\d+\s*$", font)
        assert match and match.group(1) == "yes", f"font not embedded: {font}"
    print(f"PASS: {len(font_lines)} embedded fonts; machine-readable PDF, title page and four figures")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", action="store_true", help="also inspect regenerated PAPER.pdf using poppler utilities")
    args = ap.parse_args()
    source_checks()
    if args.pdf:
        pdf_checks()
