"""Smoke test for the Electron Quick Search ↔ Python prompt-list contract."""

import asyncio
import unittest

from fastapi import HTTPException
from starlette.requests import Request

from app.api import app, quick_search_prompts


def request_with_token(token=None):
    headers = [] if token is None else [(b"x-promptplus-token", token.encode())]
    return Request({"type": "http", "method": "GET", "path": "/api/prompts",
                    "headers": headers})


class DesktopContractTests(unittest.TestCase):
    def setUp(self):
        app.state.desktop_token = "test-token"

    def tearDown(self):
        del app.state.desktop_token

    def test_rejects_requests_without_desktop_token(self):
        with self.assertRaises(HTTPException) as result:
            asyncio.run(quick_search_prompts(request_with_token()))
        self.assertEqual(result.exception.status_code, 403)

    def test_returns_keyword_and_content_for_picker(self):
        rows = asyncio.run(quick_search_prompts(request_with_token("test-token")))
        self.assertIsInstance(rows, list)
        for row in rows:
            self.assertEqual(set(row), {"keyword", "content"})
            self.assertIsInstance(row["keyword"], str)
            self.assertIsInstance(row["content"], str)


if __name__ == "__main__":
    unittest.main()
