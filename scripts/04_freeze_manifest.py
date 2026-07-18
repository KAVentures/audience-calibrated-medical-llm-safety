#!/usr/bin/env python3
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "REPRODUCIBILITY_MANIFEST.json"
EXCLUDED_PARTS = {"qa", ".cache", ".matplotlib-cache"}


def digest(path: Path) -> str:
    hasher = sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def main() -> None:
    records = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path == OUTPUT:
            continue
        relative = path.relative_to(ROOT)
        if EXCLUDED_PARTS.intersection(relative.parts):
            continue
        records.append({
            "path": relative.as_posix(),
            "bytes": path.stat().st_size,
            "sha256": digest(path),
        })
    payload = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "hash_algorithm": "SHA-256",
        "file_count": len(records),
        "files": records,
    }
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT} with {len(records)} file hashes")


if __name__ == "__main__":
    main()
