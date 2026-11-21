"""Frozen-panel identity regression tests. Run: python -m unittest discover -s tests -v."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "llm_judge_panel" / "code"))
from panel_identity import audit_judge_identities, check_blinding_key


def fixture():
    rows = [{"opaque_id": f"J{i:06d}",
             "response_id": f"R{i if i <= 1200 else i - 1200:06d}",
             "occurrence": "1" if i <= 1200 else "2"}
            for i in range(1, 1321)]
    return rows, [r["opaque_id"] for r in rows]


class PanelIdentityTests(unittest.TestCase):
    def setUp(self):
        rows, self.ids = fixture()
        self.blind = check_blinding_key(rows)

    def test_exact_expected_id_set_passes(self):
        a = audit_judge_identities(self.blind, self.ids, self.ids)
        self.assertTrue(a["complete_expected_1320"])
        self.assertEqual((a["valid_primary"], a["valid_repeats"]), (1200, 120))

    def test_duplicate_with_missing_expected_id_fails(self):
        observed = self.ids[:-1] + [self.ids[0]]
        a = audit_judge_identities(self.blind, observed, observed)
        self.assertFalse(a["complete_expected_1320"])
        self.assertEqual(a["duplicate_ids"], 1)
        self.assertEqual(a["missing_ids"], 1)

    def test_unexpected_replacing_expected_id_fails(self):
        observed = self.ids[:-1] + ["J999999"]
        a = audit_judge_identities(self.blind, observed, observed[:-1])
        self.assertFalse(a["complete_expected_1320"])
        self.assertEqual(a["missing_ids"], 1)
        self.assertEqual(a["unexpected_ids"], 1)

    def test_invalid_rating_is_not_counted_as_valid(self):
        a = audit_judge_identities(self.blind, self.ids, self.ids[:-1])
        self.assertFalse(a["complete_expected_1320"])
        self.assertEqual(a["missing_ids"], 1)

    def test_bad_blinding_key_rejected(self):
        rows, _ = fixture()
        rows[-1]["response_id"] = "R000001"
        with self.assertRaises(ValueError):
            check_blinding_key(rows)


if __name__ == "__main__":
    unittest.main()
