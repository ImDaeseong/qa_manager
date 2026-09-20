"""Keep normal-size dashboard text above the WCAG AA contrast threshold."""

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from _style import STYLE  # noqa: E402


def luminance(color: str) -> float:
    """Return relative luminance for a six-digit sRGB color."""
    values = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    channels = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
                for value in values]
    return sum(a * b for a, b in zip(channels, (0.2126, 0.7152, 0.0722)))


def contrast(first: str, second: str) -> float:
    """Return the WCAG contrast ratio between two colors."""
    light, dark = sorted((luminance(first), luminance(second)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


class StyleContrastTests(unittest.TestCase):
    def test_normal_text_tokens_meet_aa_in_both_themes(self):
        themes = re.findall(r":root\s*\{([^}]*)\}", STYLE)
        self.assertEqual(len(themes), 2)
        pairs = (("text", "bg"), ("text-muted", "card-bg"), ("primary", "card-bg"),
                 ("pass-text", "pass-bg"), ("fail-text", "fail-bg"),
                 ("pending-text", "pending-bg"))
        for theme_name, theme in zip(("light", "dark"), themes):
            tokens = dict(re.findall(r"--([\w-]+):\s*(#[0-9A-Fa-f]{6})", theme))
            for foreground, background in pairs:
                with self.subTest(theme=theme_name, foreground=foreground):
                    self.assertGreaterEqual(contrast(tokens[foreground], tokens[background]), 4.5,
                                            f"{theme_name} {foreground}/{background} contrast")


if __name__ == "__main__":
    unittest.main()
