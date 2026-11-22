#!/usr/bin/env python3
"""Deterministic checksum manifest for the *current* submission derivatives.

Never changes historical July 2026 research-freeze manifests.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "ARXIV_RELEASE_MANIFEST.json"
SOURCE_FILES = (
    "manuscript/manuscript.md",
    "PAPER.md",
    "SUPPLEMENT.md",
    "manuscript/supplement.md",
    "ETHICS_SELF_ASSESSMENT.md",
    "CITATION.cff",
    "REPLICATION_AUDIT.md",
    "scripts/03_build_documents.py",
    "scripts/check_arxiv_readiness.py",
)
DERIVED_FILES = (
    "PAPER.pdf",
    "SUPPLEMENT.pdf",
    "manuscript/audience_calibrated_medical_safety_manuscript.docx",
    "manuscript/audience_calibrated_medical_safety_manuscript.pdf",
    "manuscript/audience_calibrated_medical_safety_medrxiv.docx",
    "manuscript/audience_calibrated_medical_safety_medrxiv.pdf",
    "manuscript/audience_calibrated_medical_safety_JAMIA.docx",
    "manuscript/audience_calibrated_medical_safety_JAMIA.pdf",
    "manuscript/audience_calibrated_medical_safety_supplement.docx",
    "manuscript/audience_calibrated_medical_safety_supplement.pdf",
    "ETHICS_SELF_ASSESSMENT.docx",
    "ETHICS_SELF_ASSESSMENT.pdf",
)

def records(paths):
    output = []
    for rel in paths:
        path = ROOT / rel
        if not path.is_file():
            raise FileNotFoundError(rel)
        output.append({"path": rel, "bytes": path.stat().st_size,
                       "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    return output

def main():
    payload = {
        "schema_version": 1,
        "purpose": "current derived submission artifact inventory, not the frozen analysis input manifest",
        "research_analysis_freeze": "2026-07-18",
        "source_files": records(SOURCE_FILES),
        "derived_files": records(DERIVED_FILES),
    }
    content = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    OUTPUT.write_text(content, encoding="utf-8")
    assert OUTPUT.read_text(encoding="utf-8") == content
    print(f"Wrote current arXiv release inventory: {len(SOURCE_FILES)} source + {len(DERIVED_FILES)} derived files")

if __name__ == "__main__":
    main()
