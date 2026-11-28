import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ocr.parser import mask_pans


class MaskPans(unittest.TestCase):
    def test_every_pan_is_masked(self):
        out = mask_pans("PAN of the Employee: ABCDE1234F\nDeductor pan pqrst6789z")
        self.assertEqual(out, "PAN of the Employee: AB******4F\nDeductor pan PQ******9Z")

    def test_tan_and_other_text_untouched(self):
        text = "TAN MUMA12345B, amount 14,50,000, ref XABCDE1234FZ"
        self.assertEqual(mask_pans(text), text)


if __name__ == "__main__":
    unittest.main()
