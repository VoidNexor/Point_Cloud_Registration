import tempfile
import unittest
from pathlib import Path

from lib.utils import load_pts, load_xf


class ParserTests(unittest.TestCase):
    def test_pts_accepts_tabs_and_repeated_spaces(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.pts"
            path.write_text("1\t  2 3\t0 0 1\n")
            point = load_pts(str(path))[0]
        self.assertEqual(point.s, [1.0, 2.0, 3.0])
        self.assertEqual(point.n, [0.0, 0.0, 1.0])

    def test_xf_accepts_tabs_and_repeated_spaces(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.xf"
            path.write_text("1\t 0 0 0\n0  1 0 0\n0 0\t1 0\n0 0 0 1\n")
            matrix = load_xf(str(path))
        self.assertEqual(matrix.tolist(), [[1.0, 0.0, 0.0, 0.0],
                                           [0.0, 1.0, 0.0, 0.0],
                                           [0.0, 0.0, 1.0, 0.0],
                                           [0.0, 0.0, 0.0, 1.0]])


if __name__ == "__main__":
    unittest.main()
