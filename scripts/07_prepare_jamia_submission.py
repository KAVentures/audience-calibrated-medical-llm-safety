#!/usr/bin/env python3
"""Create portal-ready 300-dpi JAMIA figure files and an audit manifest."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "submission" / "JAMIA" / "figures"
FIGURES = (
    (
        "Figure_1_evaluator_method_prevalence.tiff",
        ROOT / "results" / "evaluator_method_figures" / "figure_1_evaluator_method_prevalence.png",
    ),
    (
        "Figure_2_panel_unsafe_rates.tiff",
        ROOT / "results" / "llm_judge_panel_figures" / "figure_2_panel_unsafe_rates.png",
    ),
    (
        "Figure_3_panel_evidence_sufficiency.tiff",
        ROOT / "results" / "llm_judge_panel_figures" / "figure_3_panel_evidence_rates.png",
    ),
    (
        "Figure_4_between_judge_agreement.tiff",
        ROOT / "results" / "llm_judge_panel_figures" / "figure_4_between_judge_agreement.png",
    ),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for filename, source in FIGURES:
        if not source.exists():
            raise FileNotFoundError(source)
        target = OUT / filename
        with Image.open(source) as image:
            converted = image.convert("RGB")
            converted.save(target, format="TIFF", compression="tiff_lzw", dpi=(300, 300))
        with Image.open(target) as check:
            dpi = check.info.get("dpi", (None, None))
            if tuple(round(float(value)) for value in dpi) != (300, 300):
                raise RuntimeError(f"Unexpected DPI metadata for {target}: {dpi}")
            rows.append(
                {
                    "file": filename,
                    "source": source.relative_to(ROOT).as_posix(),
                    "width_px": check.width,
                    "height_px": check.height,
                    "dpi_x": round(float(dpi[0])),
                    "dpi_y": round(float(dpi[1])),
                    "color_mode": check.mode,
                    "compression": "LZW",
                    "sha256": sha256(target),
                }
            )

    manifest = OUT / "figure_upload_manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    readme = OUT / "README.md"
    readme.write_text(
        "# JAMIA figure upload files\n\n"
        "These four RGB TIFF files are exported at 300 dpi with lossless LZW "
        "compression for separate upload to the journal portal. Figure legends "
        "remain in the manuscript after the references. Exact dimensions, DPI "
        "metadata, source paths, and SHA-256 hashes are recorded in "
        "`figure_upload_manifest.csv`.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
