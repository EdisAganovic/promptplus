"""Smoke tests for the shared Gallery/List prompt rendering."""

import asyncio
import unittest
from unittest.mock import patch

from starlette.requests import Request

from app.api import app, read_root


class LibraryUITests(unittest.TestCase):
    def render(self, prompts):
        request = Request({"type": "http", "app": app, "method": "GET", "path": "/", "headers": []})
        with patch("app.api.load_prompts", return_value=prompts), patch(
            "app.api.load_settings", return_value={"theme": "dark", "language": "en"}
        ):
            response = asyncio.run(read_root(request))
        return response.body.decode("utf-8")

    def test_prompt_is_available_in_both_views(self):
        html = self.render({":test-brief": {"content": "Explain [topic] clearly", "last_updated": "01.01.2026", "tags": ["Writing"]}})
        self.assertIn('id="galleryView"', html)
        self.assertIn('id="listView"', html)
        self.assertIn('id="listPanel"', html)
        self.assertEqual(html.count('data-keyword=":test-brief"'), 6)
        self.assertIn('src="/static/icon.svg"', html)
        self.assertIn('data-theme', html)
        self.assertNotIn('class="library-breadcrumb"', html)
        self.assertNotIn('data-i18n="library.subtitle"', html)
        self.assertLess(html.index('</nav>'), html.index('class="btn btn-accent library-new"'))
        self.assertLess(html.index('class="library-heading"'), html.index('class="btn btn-accent library-new"'))
        self.assertLess(html.index('class="btn btn-accent library-new"'), html.index('class="library-workspace"'))
        self.assertNotIn('class="library-count"', html)
        self.assertNotIn('id="resultsCount"', html)

    def test_empty_library_keeps_controls_and_empty_state(self):
        html = self.render({})
        self.assertIn('id="galleryView"', html)
        self.assertIn('id="listView"', html)
        self.assertIn('Nema dodanih promptova', html)

    def test_categories_are_in_sidebar_before_library_views(self):
        html = self.render({":test": {"content": "Test", "last_updated": "01.01.2026", "tags": ["Writing"]}})
        self.assertLess(html.index('class="library-sidebar"'), html.index('class="library-content"'))
        self.assertLess(html.index('id="tagFilters"'), html.index('id="galleryView"'))
        self.assertLess(html.index('id="galleryView"'), html.index('id="promptScroll"'))
        self.assertLess(html.index('id="promptScroll"'), html.index('id="promptsContainer"'))
        self.assertIn('tabindex="0" aria-label="Prompt results"', html)
        self.assertIn('data-tag="Writing"', html)


if __name__ == "__main__":
    unittest.main()
