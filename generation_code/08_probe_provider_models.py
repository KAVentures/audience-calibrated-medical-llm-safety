#!/usr/bin/env python3
from pathlib import Path
import json
import re
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_KEYS = Path("/Users/koyarafrasyab/Documents/Codex/2026-06-27/read/outputs/medrobust/API_KEYS.local.md")
OUT = ROOT / "results"
OUT.mkdir(exist_ok=True)


def load_keys(path: Path = DEFAULT_KEYS) -> dict:
    text = path.read_text()
    keys = {}
    for name in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "XAI_API_KEY"]:
        m = re.search(rf"{name}\s*=\s*([^\s`]+)", text)
        if m:
            keys[name] = m.group(1).strip()
    return keys


def request_json(url: str, headers: dict = None, timeout: int = 30) -> dict:
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def safe_call(name: str, fn):
    try:
        return {"provider": name, "ok": True, "data": fn()}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:2000]
        return {"provider": name, "ok": False, "status": e.code, "error": body}
    except Exception as e:
        return {"provider": name, "ok": False, "error": repr(e)}


def ids_from_openai_style(data: dict) -> list:
    return sorted([item.get("id", "") for item in data.get("data", []) if item.get("id")])


def ids_from_google(data: dict) -> list:
    ids = []
    for item in data.get("models", []):
        name = item.get("name", "")
        if name:
            ids.append(name.replace("models/", ""))
    return sorted(ids)


def main() -> None:
    keys = load_keys()
    probes = []
    if "OPENAI_API_KEY" in keys:
        probes.append(safe_call("openai", lambda: ids_from_openai_style(request_json(
            "https://api.openai.com/v1/models",
            {"Authorization": f"Bearer {keys['OPENAI_API_KEY']}"},
        ))))
    if "XAI_API_KEY" in keys:
        probes.append(safe_call("xai", lambda: ids_from_openai_style(request_json(
            "https://api.x.ai/v1/models",
            {"Authorization": f"Bearer {keys['XAI_API_KEY']}"},
        ))))
    if "ANTHROPIC_API_KEY" in keys:
        probes.append(safe_call("anthropic", lambda: ids_from_openai_style(request_json(
            "https://api.anthropic.com/v1/models",
            {
                "x-api-key": keys["ANTHROPIC_API_KEY"],
                "anthropic-version": "2023-06-01",
            },
        ))))
    if "GOOGLE_API_KEY" in keys:
        url = "https://generativelanguage.googleapis.com/v1beta/models?" + urllib.parse.urlencode({"key": keys["GOOGLE_API_KEY"]})
        probes.append(safe_call("google", lambda: ids_from_google(request_json(url))))

    redacted = []
    for probe in probes:
        if probe.get("ok"):
            ids = probe["data"]
            redacted.append({
                "provider": probe["provider"],
                "ok": True,
                "model_count": len(ids),
                "matching_candidates": [
                    mid for mid in ids
                    if any(term in mid.lower() for term in ["gpt", "claude", "gemini", "grok", "opus", "flash"])
                ],
            })
        else:
            redacted.append(probe)

    (OUT / "provider_model_probe.json").write_text(json.dumps(redacted, indent=2))
    for item in redacted:
        print(f"{item['provider']}: {'ok' if item.get('ok') else 'failed'}")
        if item.get("ok"):
            print(f"  models: {item['model_count']}")
            print("  candidates:")
            for mid in item["matching_candidates"][:40]:
                print(f"    {mid}")
        else:
            print(f"  error/status: {item.get('status', '')} {str(item.get('error', ''))[:200]}")


if __name__ == "__main__":
    main()

