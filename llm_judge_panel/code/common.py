#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import re
import urllib.error
import urllib.request
import uuid


PANEL_ROOT = Path(__file__).resolve().parents[1]
STUDY_ROOT = PANEL_ROOT.parent
SOURCE_CSV = STUDY_ROOT / "data" / "source" / "model_responses.csv"
INSTRUMENT_DIR = PANEL_ROOT / "instrument"
INPUT_DIR = PANEL_ROOT / "batch_inputs"
RAW_DIR = PANEL_ROOT / "raw_provider_outputs"
AUDIT_DIR = PANEL_ROOT / "audit"
STATE_DIR = PANEL_ROOT / "state"
DEFAULT_KEYS = Path("/Users/koyarafrasyab/Documents/Codex/2026-06-27/read/outputs/medrobust/API_KEYS.local.md")

MODEL_CONFIG = {
    "grok_4_3": {
        "provider": "xai",
        "model_id": "grok-4.3",
        "key_name": "XAI_API_KEY",
        "batch_discount": 0.20,
        "reasoning": "high",
    },
    "gpt_5_5": {
        "provider": "openai",
        "model_id": "gpt-5.5",
        "key_name": "OPENAI_API_KEY",
        "batch_discount": 0.50,
        "reasoning": "high",
    },
    "gemini_3_5_flash": {
        "provider": "google",
        "model_id": "gemini-3.5-flash",
        "key_name": "GOOGLE_API_KEY",
        "batch_discount": 0.50,
        "reasoning": "HIGH",
    },
    "claude_4_8_opus": {
        "provider": "anthropic",
        "model_id": "claude-opus-4-8",
        "key_name": "ANTHROPIC_API_KEY",
        "batch_discount": 0.50,
        "reasoning": "high",
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_keys(path: Path = DEFAULT_KEYS) -> dict[str, str]:
    keys = dict(os.environ)
    if path.exists():
        text = path.read_text(encoding="utf-8")
        for name in {cfg["key_name"] for cfg in MODEL_CONFIG.values()}:
            match = re.search(rf"{name}\s*=\s*([^\s`]+)", text)
            if match and name not in keys:
                keys[name] = match.group(1).strip()
    return keys


def load_schema() -> dict:
    return json.loads((INSTRUMENT_DIR / "judge_schema.json").read_text(encoding="utf-8"))


def provider_schema() -> dict:
    """Return a conservative JSON-Schema subset accepted across all four APIs."""
    schema = load_schema()

    def clean(value):
        if isinstance(value, list):
            return [clean(item) for item in value]
        if not isinstance(value, dict):
            return value
        out = {}
        for key, item in value.items():
            if key in {"$schema", "title", "minimum", "maximum"}:
                continue
            if key == "const":
                out["enum"] = [item]
            else:
                out[key] = clean(item)
        if value.get("type") == "integer" and "minimum" in value and "maximum" in value:
            out["enum"] = list(range(value["minimum"], value["maximum"] + 1))
        return out

    return clean(schema)


def model_visible_user_text(question: str, response: str) -> str:
    return (
        "MEDICAL QUESTION\n"
        + question.strip()
        + "\n\nCANDIDATE RESPONSE\n"
        + response.strip()
    )


def post_json(url: str, headers: dict[str, str], payload: dict, timeout: int = 180) -> dict:
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={**headers, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from {url}: {detail[:2000]}") from exc


def get_json(url: str, headers: dict[str, str], timeout: int = 180) -> dict:
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from {url}: {detail[:2000]}") from exc


def multipart_upload(url: str, headers: dict[str, str], path: Path, fields: dict[str, str] | None = None) -> dict:
    boundary = "----CodexBoundary" + uuid.uuid4().hex
    parts: list[bytes] = []
    for name, value in (fields or {}).items():
        parts.extend([
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
            value.encode(),
            b"\r\n",
        ])
    parts.extend([
        f"--{boundary}\r\n".encode(),
        f'Content-Disposition: form-data; name="file"; filename="{path.name}"\r\n'.encode(),
        b"Content-Type: application/jsonl\r\n\r\n",
        path.read_bytes(),
        b"\r\n",
        f"--{boundary}--\r\n".encode(),
    ])
    body = b"".join(parts)
    request = urllib.request.Request(
        url,
        data=body,
        headers={**headers, "Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from {url}: {detail[:2000]}") from exc


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")

