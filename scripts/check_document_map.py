#!/usr/bin/env python3
"""Offline guard against manuscript/supplement drift and wrong-study ethics text."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
pairs = [
    ("manuscript/manuscript.md", "PAPER.md"),
    ("SUPPLEMENT.md", "manuscript/supplement.md"),
]
for canonical, mirror in pairs:
    expected = (root / canonical).read_bytes()
    actual = (root / mirror).read_bytes()
    assert expected == actual, f"Mirror drift: {mirror} differs from {canonical}"

ethics = (root / "ETHICS_SELF_ASSESSMENT.md").read_text()
assert "Study-specific" in ethics or "study-specific" in ethics
assert "No ethics approval was requested or obtained" in ethics
for misleading in ("Both studies", "evidence-sufficiency study only", "three blinded physician reviewers"):
    assert misleading.lower() not in ethics.lower(), f"Cross-study ethics statement: {misleading}"
archived = (root / "generation_docs/ethics_irb_note.md").read_text()
assert "superseded" in archived.lower()
readme = (root / "README.md").read_text()
assert "DOCUMENT_MAP.md" in readme
builder = (root / "scripts/03_build_documents.py").read_text()
assert 'MANUSCRIPT / "manuscript.md"' in builder
assert 'MANUSCRIPT / "supplement.md"' in builder
assert 'ROOT / "ETHICS_SELF_ASSESSMENT.md"' in builder
print("PASS: canonical document mirrors, ethics scope, builder inputs and links")
