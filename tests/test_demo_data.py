"""Demo data and temporary prompt-source switching."""

import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

from app import utils
from app.replacer import RealtimeTextReplacer


class DemoDataTests(unittest.TestCase):
    def test_sample_has_150_prompts_in_15_categories(self):
        demo = json.loads((Path(__file__).resolve().parents[1] / "demo.json").read_text(encoding="utf-8"))
        self.assertEqual(len(demo), 150)
        categories = Counter()
        for keyword, prompt in demo.items():
            self.assertTrue(keyword.startswith(":demo-"))
            self.assertIsInstance(prompt["content"], str)
            self.assertTrue(prompt["content"].strip())
            self.assertEqual(len(prompt["tags"]), 1)
            categories[prompt["tags"][0]] += 1
        self.assertEqual(len(categories), 15)
        self.assertEqual(set(categories.values()), {10})

    def test_demo_temporarily_replaces_personal_prompts(self):
        with tempfile.TemporaryDirectory() as directory:
            personal = Path(directory) / "prompts.json"
            demo = Path(directory) / "demo.json"
            personal.write_text(json.dumps({":personal": {"content": "private"}}), encoding="utf-8")
            original_personal = personal.read_bytes()
            with patch.object(utils, "PROMPTS_FILE", str(personal)), patch.object(utils, "DEMO_FILE", str(demo)):
                self.assertEqual(set(utils.load_prompts()), {":personal"})
                demo.write_text(json.dumps({":demo-test": {"content": "sample", "tags": ["Writing"]}}), encoding="utf-8")
                self.assertEqual(set(utils.load_prompts()), {":demo-test"})
                replacer = RealtimeTextReplacer()
                self.assertEqual(replacer.prompts, {":demo-test": "sample"})
                utils.save_prompts({":demo-edited": {"content": "edited", "tags": ["Writing"]}})
                self.assertEqual(personal.read_bytes(), original_personal)
                self.assertEqual(set(utils.load_prompts()), {":demo-edited"})
                demo.unlink()
                self.assertEqual(set(utils.load_prompts()), {":personal"})
                replacer.reload_prompts_if_needed()
                self.assertEqual(replacer.prompts, {":personal": "private"})


if __name__ == "__main__":
    unittest.main()
