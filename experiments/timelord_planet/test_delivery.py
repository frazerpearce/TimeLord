"""Exercise the recipient's two-file package with real CPython random output."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]


class DeliveryTests(unittest.TestCase):
    def test_two_file_clean_delivery(self):
        with tempfile.TemporaryDirectory() as directory:
            clean = Path(directory)
            for name in ('timelord_planet.py', 'seed_planet.txt'):
                (clean / name).write_bytes((REPO / name).read_bytes())
            subprocess.run([sys.executable, '-I', '-S', str(clean / 'timelord_planet.py'),
                            '--no-open', '--output', str(clean / 'planet.html')],
                           cwd='/', check=True, capture_output=True)
            self.assertEqual((clean / 'planet.html').read_bytes(),
                             (ROOT / 'artifacts/planet.html').read_bytes())

    def test_archive_contents_and_launch(self):
        self.assertEqual((ROOT / 'artifacts/magrathea.zip').read_bytes(),
                         (ROOT / 'artifacts/timelord-planet.zip').read_bytes())
        with tempfile.TemporaryDirectory() as directory:
            clean = Path(directory)
            with zipfile.ZipFile(ROOT / 'artifacts/timelord-planet.zip') as archive:
                self.assertEqual(set(archive.namelist()),
                                 {'README.md', 'world.json', 'timelord_planet.py', 'seed_planet.txt'})
                archive.extractall(clean)
            subprocess.run([sys.executable, '-I', '-S', 'timelord_planet.py',
                            '--no-open', '--output', 'planet.html'],
                           cwd=clean, check=True, capture_output=True)
            self.assertEqual((clean / 'planet.html').read_bytes(),
                             (ROOT / 'artifacts/planet.html').read_bytes())

    def test_stripped_archive_reconstructs_and_runs(self):
        with tempfile.TemporaryDirectory() as directory:
            clean = Path(directory)
            with zipfile.ZipFile(ROOT / 'artifacts/magrathea-stripped.zip') as archive:
                self.assertEqual(set(archive.namelist()), {'timelord_planet.py', 'seed_planet.txt'})
                archive.extractall(clean)
            # Observe browser launching without opening a GUI during an automated test.
            observe = (
                "import runpy,webbrowser;from pathlib import Path;"
                "webbrowser.open=lambda url:Path('opened-url.txt').write_text(url);"
                "runpy.run_path('timelord_planet.py',run_name='__main__')"
            )
            result = subprocess.run([sys.executable, '-I', '-S', '-c', observe],
                                    cwd=clean, check=True, capture_output=True)
            self.assertEqual(result.stdout, b'')
            self.assertEqual(result.stderr, b'')
            self.assertEqual((clean / 'planet.html').read_bytes(),
                             (ROOT / 'artifacts/planet.html').read_bytes())
            self.assertEqual((clean / 'opened-url.txt').read_text(),
                             (clean / 'planet.html').resolve().as_uri())

    def test_invalid_seed_fails_without_output(self):
        with tempfile.TemporaryDirectory() as directory:
            clean = Path(directory)
            (clean / 'bad.seed').write_text('-1\n')
            result = subprocess.run([sys.executable, str(REPO / 'timelord_planet.py'),
                                     str(clean / 'bad.seed'), '--no-open',
                                     '--output', str(clean / 'planet.html')], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((clean / 'planet.html').exists())


if __name__ == '__main__':
    unittest.main()
