import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ScriptSmokeTests(unittest.TestCase):
    """Exercise the command-line workflows without changing the checkout."""

    def setUp(self):
        self.workdir = Path(tempfile.mkdtemp(prefix="point-cloud-registration-"))
        for name in ("bun045.pts", "bun000.pts"):
            source = ROOT / "PLY_PTS" / name
            lines = source.read_text().splitlines(keepends=True)
            (self.workdir / name).write_text("".join(lines[:400]))

    def tearDown(self):
        shutil.rmtree(self.workdir, ignore_errors=True)

    def run_script(self, script, output_dir, filenames):
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(ROOT)
        subprocess.run(
            [
                sys.executable,
                str(ROOT / script),
                "bun045.pts",
                "bun000.pts",
            ],
            cwd=self.workdir,
            env=environment,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for filename in filenames:
            self.assertTrue((self.workdir / output_dir / filename).is_file())

    def test_icp_accepts_missing_transform_files(self):
        self.run_script("icp.py", "output02", ("bun045.pts", "bun045.xf"))

    def test_icp_ply_pts_writes_into_output_directory(self):
        self.run_script(
            "icp_ply_pts.py",
            "output01",
            ("bun045.pts", "bun045.xf", "bun045.txt"),
        )


if __name__ == "__main__":
    unittest.main()
