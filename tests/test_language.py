"""Tests for language settings persistence and update endpoint."""

import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from app.api import update_language
from app.utils import load_settings, save_settings


class LanguageTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.settings_patch = patch("app.utils.SETTINGS_FILE", str(Path(self.temp_dir.name) / "settings.json"))
        self.settings_patch.start()

    def tearDown(self):
        self.settings_patch.stop()
        self.temp_dir.cleanup()

    def test_update_language_endpoint(self):
        result = asyncio.run(update_language(language="en"))
        self.assertEqual(result, {"status": "success", "language": "en"})
        
        settings = load_settings()
        self.assertEqual(settings.get("language"), "en")

        result = asyncio.run(update_language(language="bs"))
        self.assertEqual(result, {"status": "success", "language": "bs"})
        
        settings = load_settings()
        self.assertEqual(settings.get("language"), "bs")

    def test_rejects_unsupported_language(self):
        from fastapi import HTTPException
        with self.assertRaises(HTTPException) as error:
            asyncio.run(update_language(language="fr"))
        self.assertEqual(error.exception.status_code, 400)
        self.assertFalse(Path(self.temp_dir.name, "settings.json").exists())


if __name__ == "__main__":
    unittest.main()
