#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
export MPLCONFIGDIR="${MPLCONFIGDIR:-$ROOT/.matplotlib-cache}"
export MPLBACKEND="${MPLBACKEND:-Agg}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-$ROOT/.cache}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
DOCX_PYTHON_BIN="${DOCX_PYTHON_BIN:-$PYTHON_BIN}"
mkdir -p "$MPLCONFIGDIR"
mkdir -p "$XDG_CACHE_HOME"

"$PYTHON_BIN" "$ROOT/llm_judge_panel/code/04_validate_merge_judge_results.py"
"$PYTHON_BIN" "$ROOT/scripts/01_audit_hybrid_reviews.py"
"$PYTHON_BIN" "$ROOT/scripts/02_analyze_hybrid_ratings.py"
"$PYTHON_BIN" "$ROOT/scripts/05_analyze_llm_judge_panel.py"
"$PYTHON_BIN" "$ROOT/scripts/06_analyze_evaluator_methods.py"
"$DOCX_PYTHON_BIN" "$ROOT/scripts/03_build_documents.py"
"$DOCX_PYTHON_BIN" "$ROOT/scripts/07_prepare_jamia_submission.py"

echo "Panel validation, evaluator-method audit, analyses, figures, Word documents, and JAMIA upload files rebuilt successfully."
