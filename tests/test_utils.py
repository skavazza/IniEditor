import unittest
from PyQt6.QtGui import QColor
from utils import safe_int, safe_float, parse_color

class TestUtils(unittest.TestCase):
    def test_safe_int(self):
        self.assertEqual(safe_int("10"), 10)
        self.assertEqual(safe_int("10.5"), 10)
        self.assertEqual(safe_int("invalid", default=5), 5)
        self.assertEqual(safe_int(None, default=0), 0)

    def test_safe_float(self):
        self.assertEqual(safe_float("10.5"), 10.5)
        self.assertEqual(safe_float("invalid", default=5.5), 5.5)
        self.assertEqual(safe_float(None, default=0.0), 0.0)

    def test_parse_color(self):
        # RGB
        c = parse_color("255,128,0")
        self.assertEqual(c.red(), 255)
        self.assertEqual(c.green(), 128)
        self.assertEqual(c.blue(), 0)
        self.assertEqual(c.alpha(), 255)
        
        # RGBA
        c = parse_color("255,0,0,100")
        self.assertEqual(c.alpha(), 100)
        
        # Invalid
        self.assertIsNone(parse_color("invalid"))
        self.assertIsNone(parse_color("255,0")) # Missing blue
        
        # Default
        default_c = QColor("white")
        self.assertEqual(parse_color("invalid", default=default_c), default_c)

if __name__ == '__main__':
    unittest.main()
