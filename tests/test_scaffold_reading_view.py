import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("reading_view_parser", ROOT / "scripts" / "parse_scaffold_reading_view.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ReadingViewParserTests(unittest.TestCase):
    def setUp(self):
        self.sample = (ROOT / "tests" / "fixtures" / "scaffold-reading-view.sample.txt").read_text()

    def test_scoreboard_rows(self):
        parsed = MODULE.parse_reading_view(self.sample)
        self.assertEqual(parsed["challenge_scores"][0]["case_id"], "WB2S3")
        self.assertEqual(parsed["challenge_scores"][0]["score_text"], "0/20")
        self.assertEqual(parsed["challenge_scores"][2]["score_text"], "0/18")

    def test_tool_input_and_output_are_separated(self):
        parsed = MODULE.parse_reading_view(self.sample)
        self.assertEqual(parsed["used_tools_count"], 1)
        self.assertEqual(len(parsed["tool_calls"]), 1)
        call = parsed["tool_calls"][0]
        self.assertEqual(call["tool_name"], "shopify.get-order-by-id")
        self.assertEqual(call["input"]["orderId"], "REDACTED_ORDER_ID")
        self.assertEqual(call["output"]["order"]["totalPrice"]["amount"], "55.50")
        self.assertIsNone(call["input_parse_error"])
        self.assertIsNone(call["output_parse_error"])

    def test_underscore_tool_identifier(self):
        parsed = MODULE.parse_reading_view('shopify_get-orders\n{\n  "limit": 1\n}\nOUTPUT\n{\n  "orders": []\n}')
        call = parsed["tool_calls"][0]
        self.assertEqual(call["tool_name"], "shopify_get-orders")
        self.assertEqual(call["input"]["limit"], 1)
        self.assertEqual(call["output"]["orders"], [])

    def test_narrative_is_not_side_effect_evidence(self):
        parsed = MODULE.parse_reading_view(self.sample)
        self.assertIn("not independent proof", parsed["final_summary"])
        self.assertNotIn("side_effects", parsed)
        self.assertFalse(parsed["native_scaffold_json_schema_verified"])

    def test_truncated_json_is_reported_not_repaired(self):
        text = 'shopify.get-order-by-id\n{\n "orderId": "123"\nOUTPUT\n{\n "order": {\n'
        parsed = MODULE.parse_reading_view(text)
        self.assertIsNotNone(parsed["tool_calls"][0]["output_parse_error"])
        self.assertIsNone(parsed["tool_calls"][0]["output"])


if __name__ == "__main__":
    unittest.main()
