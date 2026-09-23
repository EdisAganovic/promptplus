"""Category colors stay distinct and safe for template CSS variables."""

import unittest

from app.api import CATEGORY_COLORS, category_color


class CategoryColorTests(unittest.TestCase):
    def test_demo_categories_have_distinct_colors(self):
        self.assertEqual(len(CATEGORY_COLORS), 15)
        self.assertEqual(len(set(CATEGORY_COLORS.values())), 15)
        self.assertEqual(category_color("Writing"), CATEGORY_COLORS["writing"])

    def test_custom_category_is_stable_and_returns_palette_color(self):
        self.assertEqual(category_color("My Category"), category_color(" my category "))
        self.assertIn(category_color("My Category"), CATEGORY_COLORS.values())
        self.assertEqual(category_color(""), "#64748b")


if __name__ == "__main__":
    unittest.main()
