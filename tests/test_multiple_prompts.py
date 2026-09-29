"""Tests for multiple prompts sharing the same keyword and picker triggering."""

import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from starlette.requests import Request
from fastapi import UploadFile

from app import utils
from app.api import app, read_root, add_prompt, update_prompt, delete_prompt, quick_search_prompts
from app.replacer import RealtimeTextReplacer


class MultiplePromptsTests(unittest.TestCase):
    def test_add_multiple_prompts_with_same_keyword(self):
        with tempfile.TemporaryDirectory() as directory:
            prompts_path = Path(directory) / "prompts.json"
            prompts_path.write_text("[]", encoding="utf-8")
            with patch.object(utils, "PROMPTS_FILE", str(prompts_path)), patch.object(utils, "DEMO_FILE", str(Path(directory) / "no_demo.json")):
                asyncio.run(add_prompt(keyword="test", content="Prompt 1", tags="Writing"))
                asyncio.run(add_prompt(keyword="test", content="Prompt 2", tags="Editing"))

                prompts = utils.load_prompts()
                self.assertEqual(len(prompts), 2)
                self.assertEqual(prompts[0]["keyword"], ":test")
                self.assertEqual(prompts[0]["content"], "Prompt 1")
                self.assertEqual(prompts[1]["keyword"], ":test")
                self.assertEqual(prompts[1]["content"], "Prompt 2")
                self.assertNotEqual(prompts[0]["id"], prompts[1]["id"])

    def test_update_and_delete_specific_prompt_by_id(self):
        with tempfile.TemporaryDirectory() as directory:
            prompts_path = Path(directory) / "prompts.json"
            prompts_path.write_text("[]", encoding="utf-8")
            with patch.object(utils, "PROMPTS_FILE", str(prompts_path)), patch.object(utils, "DEMO_FILE", str(Path(directory) / "no_demo.json")):
                asyncio.run(add_prompt(keyword="email", content="Email 1", tags="Email"))
                asyncio.run(add_prompt(keyword="email", content="Email 2", tags="Email"))

                prompts = utils.load_prompts()
                p1_id = prompts[0]["id"]
                p2_id = prompts[1]["id"]

                # Update first prompt only
                asyncio.run(update_prompt(prompt_id=p1_id, keyword="email", content="Email 1 Updated", tags="Work"))
                prompts = utils.load_prompts()
                self.assertEqual(prompts[0]["content"], "Email 1 Updated")
                self.assertEqual(prompts[1]["content"], "Email 2")

                # Delete second prompt only
                asyncio.run(delete_prompt(prompt_id=p2_id))
                prompts = utils.load_prompts()
                self.assertEqual(len(prompts), 1)
                self.assertEqual(prompts[0]["id"], p1_id)

    def test_replacer_single_match_triggers_single_replace(self):
        with tempfile.TemporaryDirectory() as directory:
            prompts_path = Path(directory) / "prompts.json"
            prompts_path.write_text("[]", encoding="utf-8")
            with patch.object(utils, "PROMPTS_FILE", str(prompts_path)), patch.object(utils, "DEMO_FILE", str(Path(directory) / "no_demo.json")):
                utils.save_prompts([{"id": "1", "keyword": ":single", "content": "Single content", "tags": []}])
                replacer = RealtimeTextReplacer()

                single_mock = MagicMock()
                replacer._replace_keyword_single = single_mock
                picker_mock = MagicMock()
                replacer._trigger_multiple_matches = picker_mock

                # Simulate typing ":single "
                for char in ":single ":
                    event = MagicMock()
                    event.event_type = "down"
                    event.name = "space" if char == " " else char
                    replacer.on_key_event(event)

                single_mock.assert_called_once_with(":single", "Single content")
                picker_mock.assert_not_called()

    def test_replacer_multiple_matches_triggers_picker(self):
        with tempfile.TemporaryDirectory() as directory:
            prompts_path = Path(directory) / "prompts.json"
            prompts_path.write_text("[]", encoding="utf-8")
            with patch.object(utils, "PROMPTS_FILE", str(prompts_path)), patch.object(utils, "DEMO_FILE", str(Path(directory) / "no_demo.json")):
                p1 = {"id": "1", "keyword": ":multi", "content": "Choice 1", "tags": []}
                p2 = {"id": "2", "keyword": ":multi", "content": "Choice 2", "tags": []}
                utils.save_prompts([p1, p2])
                replacer = RealtimeTextReplacer()

                single_mock = MagicMock()
                replacer._replace_keyword_single = single_mock
                picker_mock = MagicMock()
                replacer._trigger_multiple_matches = picker_mock

                # Simulate typing ":multi "
                for char in ":multi ":
                    event = MagicMock()
                    event.event_type = "down"
                    event.name = "space" if char == " " else char
                    replacer.on_key_event(event)

                single_mock.assert_not_called()
                picker_mock.assert_called_once()
                args, _ = picker_mock.call_args
                self.assertEqual(args[0], ":multi")
                self.assertEqual(len(args[1]), 2)
                self.assertEqual(args[1][0]["content"], "Choice 1")
                self.assertEqual(args[1][1]["content"], "Choice 2")


if __name__ == "__main__":
    unittest.main()
