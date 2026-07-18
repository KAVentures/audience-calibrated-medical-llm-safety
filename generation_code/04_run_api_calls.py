#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import csv
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
BATCHES = ROOT / "api_batches"
RESPONSES = ROOT / "responses"
RESPONSES.mkdir(exist_ok=True)
RUN_DIR = Path(os.getenv("RESPONSE_RUN_DIR", str(RESPONSES)))
RUN_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR = RUN_DIR / "raw_provider_responses"
RAW_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_KEYS = Path("/Users/koyarafrasyab/Documents/Codex/2026-06-27/read/outputs/medrobust/API_KEYS.local.md")
MAX_OUTPUT_TOKENS = int(os.getenv("GENERATION_MAX_OUTPUT_TOKENS", "8192"))
PRESERVE_ORIGINAL_REASONING_SETTINGS = os.getenv("PRESERVE_ORIGINAL_REASONING_SETTINGS") == "YES"

MODEL_CONFIG = {
    "grok_4_3": {
        "provider": "xai",
        "env_key": "XAI_API_KEY",
        "model_id_env": "MODEL_ID_GROK_4_3",
        "model_id": "TO_CONFIRM",
    },
    "gpt_5_5": {
        "provider": "openai",
        "env_key": "OPENAI_API_KEY",
        "model_id_env": "MODEL_ID_GPT_5_5",
        "model_id": "TO_CONFIRM",
    },
    "gemini_3_5_flash": {
        "provider": "google",
        "env_key": "GOOGLE_API_KEY",
        "model_id_env": "MODEL_ID_GEMINI_3_5_FLASH",
        "model_id": "TO_CONFIRM",
    },
    "claude_4_8_opus": {
        "provider": "anthropic",
        "env_key": "ANTHROPIC_API_KEY",
        "model_id_env": "MODEL_ID_CLAUDE_4_8_OPUS",
        "model_id": "TO_CONFIRM",
    },
}


def load_keys(path: Path = DEFAULT_KEYS) -> dict:
    keys = dict(os.environ)
    if path.exists():
        text = path.read_text()
        for name in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "XAI_API_KEY"]:
            m = re.search(rf"{name}\s*=\s*([^\s`]+)", text)
            if m and name not in keys:
                keys[name] = m.group(1).strip()
    return keys


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def post_json(url: str, headers: dict, payload: dict, timeout: int = 180) -> dict:
    timeout = int(os.getenv("PROVIDER_TIMEOUT_SECONDS", str(timeout)))
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={**headers, "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def extract_openai_text(data: dict) -> str:
    if "output_text" in data:
        return data["output_text"]
    pieces = []
    for item in data.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"}:
                pieces.append(content.get("text", ""))
    if pieces:
        return "\n".join(pieces).strip()
    return ""


def nested_int(data: dict, *path: str) -> int:
    value = data
    for key in path:
        if not isinstance(value, dict):
            return 0
        value = value.get(key)
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def call_openai(model_id: str, key: str, request: dict) -> dict:
    payload = {
        "model": model_id,
        "input": request["messages"],
        "max_output_tokens": request["generation"]["max_output_tokens"],
    }
    if request["generation"].get("reasoning_effort") == "high_where_available":
        payload["reasoning"] = {"effort": "high"}
    data = post_json("https://api.openai.com/v1/responses", {"Authorization": f"Bearer {key}"}, payload)
    return {
        "provider_response_id": data.get("id", ""),
        "response_text": extract_openai_text(data),
        "usage": data.get("usage", {}),
        "provider_model_id_returned": data.get("model", ""),
        "provider_status": data.get("status", ""),
        "finish_reason": (data.get("incomplete_details") or {}).get("reason", "") or data.get("status", ""),
        "is_complete": data.get("status") == "completed",
        "raw": data,
    }


def call_xai(model_id: str, key: str, request: dict) -> dict:
    payload = {
        "model": model_id,
        "messages": request["messages"],
        "temperature": 0,
        "max_tokens": request["generation"]["max_output_tokens"],
    }
    if not PRESERVE_ORIGINAL_REASONING_SETTINGS:
        payload["reasoning_effort"] = "high"
    data = post_json("https://api.x.ai/v1/chat/completions", {"Authorization": f"Bearer {key}"}, payload)
    choice = data.get("choices", [{}])[0]
    text = choice.get("message", {}).get("content", "")
    finish_reason = choice.get("finish_reason", "")
    return {
        "provider_response_id": data.get("id", ""),
        "response_text": text,
        "usage": data.get("usage", {}),
        "provider_model_id_returned": data.get("model", ""),
        "provider_status": "completed" if finish_reason == "stop" else "incomplete",
        "finish_reason": finish_reason,
        "is_complete": finish_reason == "stop",
        "raw": data,
    }


def call_anthropic(model_id: str, key: str, request: dict) -> dict:
    system = "\n".join([m["content"] for m in request["messages"] if m["role"] == "system"])
    messages = [m for m in request["messages"] if m["role"] != "system"]
    payload = {
        "model": model_id,
        "system": system,
        "messages": messages,
        "max_tokens": request["generation"]["max_output_tokens"],
    }
    if not PRESERVE_ORIGINAL_REASONING_SETTINGS:
        payload["thinking"] = {"type": "adaptive", "display": "omitted"}
        payload["output_config"] = {"effort": "high"}
    data = post_json(
        "https://api.anthropic.com/v1/messages",
        {"x-api-key": key, "anthropic-version": "2023-06-01"},
        payload,
    )
    text = "\n".join([c.get("text", "") for c in data.get("content", []) if c.get("type") == "text"]).strip()
    return {
        "provider_response_id": data.get("id", ""),
        "response_text": text,
        "usage": data.get("usage", {}),
        "provider_model_id_returned": data.get("model", ""),
        "provider_status": "completed" if data.get("stop_reason") in {"end_turn", "stop_sequence"} else "incomplete",
        "finish_reason": data.get("stop_reason", ""),
        "is_complete": data.get("stop_reason") in {"end_turn", "stop_sequence"},
        "raw": data,
    }


def call_google(model_id: str, key: str, request: dict) -> dict:
    system = "\n".join([m["content"] for m in request["messages"] if m["role"] == "system"])
    user = "\n".join([m["content"] for m in request["messages"] if m["role"] == "user"])
    payload = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {
            "temperature": 0,
            "maxOutputTokens": request["generation"]["max_output_tokens"],
        },
    }
    if not PRESERVE_ORIGINAL_REASONING_SETTINGS:
        payload["generationConfig"]["thinkingConfig"] = {"thinkingLevel": "HIGH", "includeThoughts": False}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={key}"
    data = post_json(url, {}, payload)
    candidate = data.get("candidates", [{}])[0]
    parts = candidate.get("content", {}).get("parts", [])
    text = "\n".join([p.get("text", "") for p in parts]).strip()
    finish_reason = candidate.get("finishReason", "")
    return {
        "provider_response_id": "",
        "response_text": text,
        "usage": data.get("usageMetadata", {}),
        "provider_model_id_returned": data.get("modelVersion", ""),
        "provider_status": "completed" if finish_reason == "STOP" else "incomplete",
        "finish_reason": finish_reason,
        "is_complete": finish_reason == "STOP",
        "raw": data,
    }


CALLERS = {
    "openai": call_openai,
    "xai": call_xai,
    "anthropic": call_anthropic,
    "google": call_google,
}


def get_model_id(model_key: str) -> str:
    cfg = MODEL_CONFIG[model_key]
    return os.getenv(cfg["model_id_env"], cfg["model_id"]).strip()


def usage_field(usage: dict, *names: str) -> int:
    for name in names:
        if name in usage and usage[name] is not None:
            return int(usage[name])
    return 0


def main() -> None:
    approved = os.getenv("API_CALLS_APPROVED") == "YES"
    acknowledged = os.getenv("COST_ACKNOWLEDGED") == "YES"
    if not (approved and acknowledged):
        raise SystemExit(
            "Live API calls are blocked. Set API_CALLS_APPROVED=YES and COST_ACKNOWLEDGED=YES after cost approval."
        )

    keys = load_keys()
    rows = []
    jsonl_path = RUN_DIR / "model_responses.jsonl"
    csv_path = RUN_DIR / "model_responses.csv"
    error_path = RUN_DIR / "generation_errors.jsonl"
    max_requests_per_model = int(os.getenv("MAX_REQUESTS_PER_MODEL", "0") or "0")
    only_model_key = os.getenv("ONLY_MODEL_KEY", "").strip()
    request_id_allowlist_path = os.getenv("REQUEST_ID_ALLOWLIST", "").strip()
    request_id_allowlist = None
    if request_id_allowlist_path:
        request_id_allowlist = {
            value.strip()
            for value in Path(request_id_allowlist_path).read_text().splitlines()
            if value.strip()
        }
    existing_ids = set()
    if jsonl_path.exists():
        for line in jsonl_path.read_text().splitlines():
            if line.strip():
                existing_ids.add(json.loads(line)["response_id"])
    if csv_path.exists():
        try:
            with csv_path.open(newline="") as f:
                for row in csv.DictReader(f):
                    existing_ids.add(row["response_id"])
        except Exception:
            pass

    for model_key, cfg in MODEL_CONFIG.items():
        if only_model_key and model_key != only_model_key:
            continue
        model_id = get_model_id(model_key)
        if not model_id or model_id == "TO_CONFIRM":
            raise SystemExit(
                f"Model ID for {model_key} is not confirmed. Set {cfg['model_id_env']} before live calls."
            )
        key = keys.get(cfg["env_key"])
        if not key:
            raise SystemExit(f"Missing API key for {model_key}: {cfg['env_key']}")
        batch_path = BATCHES / f"{model_key}_requests.jsonl"
        caller = CALLERS[cfg["provider"]]
        completed_for_model = 0
        for line in batch_path.read_text().splitlines():
            request = json.loads(line)
            if request_id_allowlist is not None and request["request_id"] not in request_id_allowlist:
                continue
            request["generation"]["max_output_tokens"] = MAX_OUTPUT_TOKENS
            response_id = f"R_{request['request_id']}"
            if response_id in existing_ids:
                continue
            if max_requests_per_model and completed_for_model >= max_requests_per_model:
                break
            started = datetime.now(timezone.utc).isoformat()
            try:
                result = caller(model_id, key, request)
                raw_path = RAW_DIR / f"{response_id}.json"
                raw_path.write_text(json.dumps(result["raw"], ensure_ascii=False, indent=2))
                usage = result["usage"]
                response_text = result["response_text"]
                if not result["is_complete"] or not response_text.strip():
                    raise RuntimeError(
                        f"Incomplete provider response: status={result['provider_status']!r} "
                        f"finish_reason={result['finish_reason']!r} text_length={len(response_text.strip())}"
                    )
                provider = cfg["provider"]
                temperature_parameter_sent = "omitted_unsupported_or_deprecated" if provider in {"openai", "anthropic"} else "0"
                if PRESERVE_ORIGINAL_REASONING_SETTINGS and provider != "openai":
                    reasoning_parameter_sent = "omitted_or_provider_default"
                else:
                    reasoning_parameter_sent = {
                        "openai": "reasoning.effort=high",
                        "xai": "reasoning_effort=high",
                        "google": "thinkingConfig.thinkingLevel=HIGH",
                        "anthropic": "thinking.type=adaptive; output_config.effort=high",
                    }[provider]
                reasoning_tokens = usage_field(usage, "reasoning_tokens", "thoughtsTokenCount")
                reasoning_tokens = reasoning_tokens or nested_int(usage, "output_tokens_details", "reasoning_tokens")
                reasoning_tokens = reasoning_tokens or nested_int(usage, "completion_tokens_details", "reasoning_tokens")
                reasoning_tokens = reasoning_tokens or nested_int(usage, "output_tokens_details", "thinking_tokens")
                record = {
                    "response_id": response_id,
                    "request_id": request["request_id"],
                    "model_key": model_key,
                    "provider": cfg["provider"],
                    "provider_model_id": model_id,
                    "provider_model_id_returned": result["provider_model_id_returned"],
                    "provider_response_id": result["provider_response_id"],
                    "provider_status": result["provider_status"],
                    "finish_reason": result["finish_reason"],
                    "created_at_utc": started,
                    "topic_id": request["topic_id"],
                    "prompt_id": request["prompt_id"],
                    "prompt_version": request["prompt_version"],
                    "audience": request["audience"],
                    "specialty": request["specialty"],
                    "prompt_sha256": request["prompt_sha256"],
                    "system_prompt_sha256": request["system_prompt_sha256"],
                    "temperature_requested": 0,
                    "temperature_parameter_sent": temperature_parameter_sent,
                    "reasoning_effort_requested": request["generation"]["reasoning_effort"],
                    "reasoning_effort_parameter_sent": reasoning_parameter_sent,
                    "max_output_tokens": request["generation"]["max_output_tokens"],
                    "input_tokens": usage_field(usage, "input_tokens", "prompt_tokens", "promptTokenCount"),
                    "output_tokens": usage_field(usage, "output_tokens", "completion_tokens", "candidatesTokenCount"),
                    "reasoning_tokens": reasoning_tokens,
                    "generation_status": "complete",
                    "technical_regeneration": "true" if request_id_allowlist is not None else "false",
                    "error_message": "",
                    "prompt_text": request["messages"][1]["content"],
                    "response_text": response_text,
                    "response_sha256": sha256_text(response_text),
                }
                rows.append(record)
                existing_ids.add(response_id)
                completed_for_model += 1
                with jsonl_path.open("a") as f:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                print(f"ok {response_id}")
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", errors="replace")
                err = {"request_id": request["request_id"], "model_key": model_key, "status": e.code, "error": body[:4000]}
                with error_path.open("a") as f:
                    f.write(json.dumps(err, ensure_ascii=False) + "\n")
                print(f"error {request['request_id']} status={e.code}")
                completed_for_model += 1
                time.sleep(2)
            except Exception as e:
                err = {"request_id": request["request_id"], "model_key": model_key, "error": repr(e)}
                with error_path.open("a") as f:
                    f.write(json.dumps(err, ensure_ascii=False) + "\n")
                print(f"error {request['request_id']}")
                completed_for_model += 1
                time.sleep(2)

    if rows:
        existing_rows = []
        if csv_path.exists():
            with csv_path.open(newline="") as f:
                existing_rows = list(csv.DictReader(f))
        all_rows = existing_rows + rows
        fieldnames = []
        for row in all_rows:
            for key in row.keys():
                if key not in fieldnames:
                    fieldnames.append(key)
        with csv_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(all_rows)
    print(f"wrote {len(rows)} responses")


if __name__ == "__main__":
    main()
