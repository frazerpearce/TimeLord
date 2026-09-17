import ast
from pathlib import Path
import random
import string
import subprocess
import sys
import tempfile
import unittest

from find_text_seed import TERMINATOR, construct_seed
from timelord_mt import ConstraintError, solve_gf2

ROOT = Path(__file__).resolve().parents[1]


class TextTests(unittest.TestCase):
    def verify(self, target):
        seed, rank, free = construct_seed(target, 42)
        self.assertGreater(seed, 0)
        r = random.Random(seed)
        self.assertEqual(bytes(r.randrange(128) for _ in target), target)
        self.assertEqual(bytes(r.randrange(128) for _ in TERMINATOR), TERMINATOR)
        # Direct outputs also establish no rejection and MSB-first ordering.
        r = random.Random(seed)
        self.assertEqual(bytes(r.getrandbits(32) >> 24 for _ in target), target)
        self.assertEqual(rank + free, 19936)
        return seed

    def test_targets(self):
        for target in [b'A', b'HELLO', b'HELLO WORLD', b'TimeLord',
                       b'The future is already written.',
                       string.punctuation.encode('ascii'), bytes(reversed(range(128))),
                       b'\x00\x01\x02\x03\x7f', b'a\r\nb\n', b'']:
            with self.subTest(target=target):
                self.verify(target)

    def test_reserved_pair(self):
        with self.assertRaisesRegex(ValueError, 'reserved terminator'):
            construct_seed(b'before' + TERMINATOR + b'after', 42)

    def test_demo_termination_edges(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            for target in [b'', b'A', b'\x1e', b'\x1f', b'a\x1e\x1eb\x1fc\x1e']:
                seed = self.verify(target)
                (tmp / 'seed_text.txt').write_text(hex(seed) + '\n')
                demo = subprocess.run([sys.executable, str(ROOT / 'demo_text.py')],
                                      cwd=tmp, capture_output=True, timeout=10)
                self.assertEqual(demo.returncode, 0, demo.stderr)
                self.assertEqual(demo.stdout, target + b'\n')

    def test_repeatable_and_string(self):
        self.assertEqual(construct_seed('TimeLord', 42), construct_seed(b'TimeLord', 42))
        self.assertNotEqual(construct_seed('TimeLord', 42)[0], construct_seed('TimeLord', 43)[0])

    def test_non_ascii(self):
        for target in ['caf\u00e9', b'\x80', b'\xff']:
            with self.assertRaisesRegex(ValueError, 'ASCII'):
                construct_seed(target)

    def test_installed_cpython_bits(self):
        a, b = random.Random(7), random.Random(7)
        for _ in range(1300):
            self.assertEqual(a.getrandbits(8), b.getrandbits(32) >> 24)
        # Observe the installed _randbelow's request width and rejection loop.
        class Probe(random.Random):
            def getrandbits(self, k):
                self.widths.append(k)
                return next(self.values)
        p = Probe()
        p.widths, p.values = [], iter([255, 128, 65])
        self.assertEqual(p.randrange(128), 65)
        self.assertEqual(p.widths, [8, 8, 8])

    def test_dependent_constraints(self):
        self.assertEqual(solve_gf2([1, 1], [1, 1], 0), (1, 1))
        with self.assertRaises(ConstraintError) as caught:
            solve_gf2([1, 1], [0, 1], 0)
        self.assertEqual(caught.exception.rank, 1)

    def test_long_prefix(self):
        self.verify((b'The future is already written. ' * 65)[:2000])

    def test_measured_capacity(self):
        target = (b'The future is already written. ' * 81)
        self.verify(target[:2490])
        with self.assertRaises(ConstraintError) as caught:
            construct_seed(target[:2491], 42)
        self.assertEqual(caught.exception.rank, 19936)

    def test_cli_rejects_non_ascii_cleanly(self):
        done = subprocess.run([sys.executable, str(ROOT / 'find_text_seed.py'),
                               'caf\u00e9'], capture_output=True)
        self.assertEqual(done.returncode, 2)
        self.assertIn(b'ASCII', done.stderr)
        self.assertNotIn(b'Traceback', done.stderr)

    def test_file_and_standalone_demo(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            target = b'\x00\x01A\r\nB\n\x7f'
            source = tmp / 'input.bin'
            source.write_bytes(target)
            done = subprocess.run([sys.executable, str(ROOT / 'find_text_seed.py'),
                                   '--file', str(source), '--free-seed', '42'],
                                  cwd=tmp, capture_output=True)
            self.assertEqual(done.returncode, 0, done.stderr)
            seed_text = (tmp / 'seed_text.txt').read_text().strip()
            self.assertTrue(seed_text.startswith('0x'))
            self.assertGreater(int(seed_text, 0), 0)
            self.assertNotIn('=', seed_text)
            source.unlink()
            (tmp / 'demo_text.py').write_bytes((ROOT / 'demo_text.py').read_bytes())
            demo = subprocess.run([sys.executable, 'demo_text.py'], cwd=tmp,
                                  capture_output=True)
            self.assertEqual(demo.returncode, 0, demo.stderr)
            self.assertEqual(demo.stdout, target + b'\n')

    def test_demo_is_simple(self):
        source = (ROOT / 'demo_text.py').read_text()
        tree = ast.parse(source)
        self.assertNotIn('THE FUTURE IS ALREADY WRITTEN.', source)
        self.assertFalse(any(isinstance(n, ast.Attribute) and n.attr == 'setstate'
                             for n in ast.walk(tree)))
        opens = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Name) and n.func.id == 'open']
        self.assertEqual(len(opens), 1)
        self.assertEqual(opens[0].args[0].value, 'seed_text.txt')
