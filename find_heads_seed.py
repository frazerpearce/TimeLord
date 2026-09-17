#!/usr/bin/env python3
"""Construct an integer seed making CPython's first N coin tosses heads.

This targets CPython's MT19937 and init_by_array implementation. Twist and
temper are linear over GF(2), so two equations per toss force getrandbits(2)
to return 1. The seeding loops are reversed to obtain an ordinary integer.
Unconstrained state bits are randomized rather than set to zero.
"""

import argparse
import random
import sys
import time

# Re-export the original helpers for existing callers.
from timelord_mt import (N, M, UPPER, LOWER, MATRIX_A, MASK, VARIABLE_COUNT,
                         twist_words, temper, twist_symbolic, temper_symbolic,
                         symbolic_output_rows, fixed_word_outputs, solve_gf2,
                         init_genrand, reverse_second_seed_loop,
                         key_for_first_seed_loop, construct_output_seed)


def construct_seed(toss_count, free_seed=None):
    return construct_output_seed([1] * toss_count, 2, free_seed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tosses", nargs="?", type=int, default=100,
                        help="number of initial HEADS to construct (1..1000)")
    parser.add_argument("--free-seed", type=int,
                        help="repeatable seed for free bits; default uses OS entropy")
    parser.add_argument("--output",
                        help="output path (default: seed_<N>_heads.txt)")
    args = parser.parse_args()
    if not 1 <= args.tosses <= 1000:
        parser.error("tosses must be between 1 and 1000")

    started = time.perf_counter()
    seed, rank, free_count = construct_seed(args.tosses, args.free_seed)
    r = random.Random(seed)
    tosses = [r.randrange(2) for _ in range(args.tosses)]
    assert tosses == [1] * args.tosses
    continuation = [r.randrange(2) for _ in range(100)]
    output = args.output or "seed_{}_heads.txt".format(args.tosses)
    with open(output, "w", encoding="ascii") as handle:
        handle.write(hex(seed) + "\n")

    elapsed = time.perf_counter() - started
    print("Python:", sys.version.replace("\n", " "))
    print("Seed bit length:", seed.bit_length())
    print("Constraints / free state bits: {} / {}".format(rank, free_count))
    print("Construction time: {:.3f} s".format(elapsed))
    print("Verification: {} HEADS, 0 TAILS (passed)".format(args.tosses))
    print("Next 100: {} HEADS, {} TAILS".format(sum(continuation),
                                                     100 - sum(continuation)))
    print("Saved:", output)
    print("Seed:", hex(seed))


if __name__ == "__main__":
    main()
