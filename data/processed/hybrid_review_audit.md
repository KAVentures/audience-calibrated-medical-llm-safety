# Hybrid Review Audit

- Rows per workbook: 1200
- Same 1,200 blinded response IDs: True

## chatgpt_holistic

- Reviewer IDs: ['AI med review ChatGPT']
- Missing binary ratings: 0
- Missing ordinal ratings: 0
- Invalid binary ratings: 0
- Invalid ordinal ratings: 0
- Rationales mentioning automated/heuristic/algorithm: 0

## deterministic_engine_claude_label

- Reviewer IDs: ['ai med review Claude']
- Missing binary ratings: 0
- Missing ordinal ratings: 0
- Invalid binary ratings: 0
- Invalid ordinal ratings: 0
- Rationales mentioning automated/heuristic/algorithm: 1200

## deterministic_engine_gpt_label

- Reviewer IDs: ['AI med review ChatGPT']
- Missing binary ratings: 0
- Missing ordinal ratings: 0
- Invalid binary ratings: 0
- Invalid ordinal ratings: 0
- Rationales mentioning automated/heuristic/algorithm: 1200

## Calibration Traceability

The 10 physician-calibrated rows are not identified at row level in either workbook. Human-subset validation cannot be computed from the supplied files.

## Interpretation

The three workbooks provide two analytically distinct evaluator methods over the same 1,200 responses: one holistic GPT stream and one deterministic engine represented twice. They do not constitute independent physician reviews.

## Duplicate scoring-engine implementation

The GPT-labelled rescored workbook and Claude-labelled scoring-engine workbook match on all 15 score fields and every rationale for all 1,200 responses. They are one evaluator specification for inference and are not counted as two independent votes.
