import random
import unittest
from pathlib import Path

import find_heads_seed


ROOT = Path(__file__).resolve().parents[1]


class CommittedSeedTests(unittest.TestCase):
    def assert_heads_seed(self, toss_count):
        path = ROOT / "seed_{}_heads.txt".format(toss_count)
        text = path.read_text(encoding="ascii").strip()
        self.assertTrue(text.startswith("0x"))
        generator = random.Random(int(text, 0))
        self.assertEqual(
            [generator.randrange(2) for _ in range(toss_count)],
            [1] * toss_count,
        )

    def test_100_heads_seed(self):
        self.assert_heads_seed(100)

    def test_1000_heads_seed(self):
        self.assert_heads_seed(1000)

    def test_construction_is_repeatable_when_requested(self):
        first, first_rank, first_free = find_heads_seed.construct_seed(10, 42)
        second, second_rank, second_free = find_heads_seed.construct_seed(10, 42)
        self.assertEqual(first, second)
        self.assertEqual((first_rank, first_free), (second_rank, second_free))
        generator = random.Random(first)
        self.assertEqual([generator.randrange(2) for _ in range(10)], [1] * 10)


if __name__ == "__main__":
    unittest.main()
