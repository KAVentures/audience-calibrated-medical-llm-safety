#!/usr/bin/env python3
from pathlib import Path
import hashlib
import json
import platform
import subprocess
from datetime import datetime, timezone

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs"
PROCESSED = ROOT / "data" / "processed"
BATCHES = ROOT / "api_batches"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def git_commit_or_none() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "not_a_git_repository_or_unavailable"


def main() -> None:
    prompts_path = PROCESSED / "prompt_families.csv"
    if not prompts_path.exists():
        raise SystemExit("Missing prompt_families.csv. Run scripts/02_build_prompt_families.py first.")
    prompts = pd.read_csv(prompts_path)
    prompts["prompt_sha256"] = prompts["prompt_text"].map(sha256_text)
    prompts["system_prompt_sha256"] = sha256_file(ROOT / "prompts" / "system_prompt.txt")
    frozen_cols = [
        "prompt_id",
        "topic_id",
        "question_id",
        "specialty",
        "specialty_risk",
        "decision_type",
        "prompt_version",
        "audience",
        "red_flag_stratum",
        "prompt_sha256",
        "system_prompt_sha256",
        "prompt_text",
    ]
    frozen = prompts[frozen_cols].sort_values("prompt_id")
    frozen.to_csv(OUT / "frozen_prompt_manifest.csv", index=False)

    files = []
    for path in sorted(ROOT.rglob("*")):
        if path.is_file() and ".DS_Store" not in path.name:
            rel = path.relative_to(ROOT).as_posix()
            if rel.startswith("responses/") or rel.startswith("reviews/"):
                continue
            files.append({
                "path": rel,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            })

    manifest = {
        "study": "audience_calibrated_medical_safety",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "git_commit": git_commit_or_none(),
        "n_topics": int(prompts["topic_id"].nunique()),
        "n_prompts": int(len(prompts)),
        "n_prompt_versions": int(prompts["prompt_version"].nunique()),
        "planned_models": ["grok_4_3", "gpt_5_5", "gemini_3_5_flash", "claude_4_8_opus"],
        "generation_stop_status": "pre_api_until_explicit_approval",
        "file_manifest": files,
    }
    (OUT / "study_reproducibility_manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"wrote {OUT / 'frozen_prompt_manifest.csv'}")
    print(f"wrote {OUT / 'study_reproducibility_manifest.json'}")


if __name__ == "__main__":
    main()
