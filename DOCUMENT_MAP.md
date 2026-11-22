# Canonical document map — audience-calibrated clinical LLM safety

This repository deliberately contains original research inputs, dated protocol/audit records, **two public Markdown aliases**, and several journal-specific generated document formats. Different filenames are not evidence of multiple independent studies or ethics determinations.

| Purpose | Authoritative editable source | Compatible mirror or generated derivative |
|---|---|---|
| Main article | `manuscript/manuscript.md` | `PAPER.md` is an **exact mirror**; `PAPER.pdf` and `manuscript/*manuscript*.docx/.pdf` are generated renderings |
| Supplement | `SUPPLEMENT.md` | `manuscript/supplement.md` is an **exact mirror**, used by the existing document builder; `SUPPLEMENT.pdf`, `manuscript/*supplement*.docx/.pdf` are generated |
| Current research ethics | `ETHICS_SELF_ASSESSMENT.md` | `ETHICS_SELF_ASSESSMENT.docx` and `ETHICS_SELF_ASSESSMENT.pdf` are **format derivatives of one self-assessment**, not distinct ethics approvals |
| Dated historical ethics note | `generation_docs/ethics_irb_note.md` | Preserved as archival provenance. The current self-assessment above supersedes its wording; neither constitutes an external authority decision |
| Frozen study protocol and analysis plans | `protocol/` and `generation_docs/` | Earlier planned methods are retained even where later technical execution differs; check dated audit logs |
| Reproducibility evidence | `data/`, `llm_judge_panel/`, `results/`, `scripts/` | Original data, blinding material, provider outputs, scripts and result tables are **not** cosmetic duplicates; do not delete or move casually |
| Journal submission package | `manuscript/jamia_abstract.md` and `submission/JAMIA/` | Venue-specific exports retain historical filenames and links |

## How to make changes safely

1. Edit `manuscript/manuscript.md`, then mirror the same bytes to `PAPER.md`. Edit `SUPPLEMENT.md`, then mirror to `manuscript/supplement.md`.
2. Update only `ETHICS_SELF_ASSESSMENT.md` for the **current** ethics statement. Do not rewrite the original dated note to resemble an externally approved determination.
3. Run `python scripts/check_document_map.py`, `python -m unittest discover -s tests -v`, and `python scripts/check_research_integrity.py`.
4. Regenerate the Word/PDF files with `python scripts/03_build_documents.py` plus the repository PDF-conversion workflow. The existing root links are deliberately maintained; do not hand-edit binary derivatives as if they were independent manuscripts.
5. Visually inspect the generated PDFs and check final manuscript content before publication. A passing source check does not establish PDF freshness or scientific validity.

No scientific data or primary analysis code should be deleted as part of this document-organization cleanup.

## arXiv-facing presentation release

The principal PDF `PAPER.pdf` is derived from `manuscript/manuscript.md`; the JAMIA-specific submission remains a distinct format. `ARXIV_RELEASE_MANIFEST.json` is a deterministic, up-to-date source/derivative checksum list generated after the latest build. The older `PUBLIC_RELEASE_MANIFEST.sha256` and `REPRODUCIBILITY_MANIFEST.json` are preserved as **historical research freezes**, not overwritten or represented as new provenance records.
