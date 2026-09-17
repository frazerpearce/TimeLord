#!/usr/bin/env python3
"""Construct an ordinary CPython integer seed for predetermined 7-bit ASCII."""
import argparse
from pathlib import Path
import random
import sys
import time

from timelord_mt import construct_output_seed

TERMINATOR = b"\x1e\x1f"  # ASCII record separator, unit separator


def construct_seed(target, free_seed=None):
    """Accept ASCII str or raw bytes, including every ASCII control character."""
    if isinstance(target, str):
        try:
            target = target.encode("ascii")
        except UnicodeEncodeError as exc:
            raise ValueError("target must contain only ASCII values 0..127") from exc
    if not isinstance(target, bytes):
        raise TypeError("target must be str or bytes")
    if any(value > 127 for value in target):
        raise ValueError("target must contain only ASCII values 0..127")
    if TERMINATOR in target:
        raise ValueError("target contains reserved terminator pair ASCII 30, 31")
    return construct_output_seed(target + TERMINATOR, 8, free_seed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("text", nargs="?", help="desired ASCII text")
    parser.add_argument("--file", type=Path, help="read raw ASCII bytes")
    parser.add_argument("--free-seed", type=int, help="reproducible free state bits")
    parser.add_argument("--show-seed", action="store_true")
    args = parser.parse_args()
    if (args.text is None) == (args.file is None):
        parser.error("provide either text or --file, exclusively")
    started = time.perf_counter()
    try:
        target = args.file.read_bytes() if args.file is not None else args.text.encode("ascii")
        seed, rank, free = construct_seed(target, args.free_seed)
    except (ValueError, RuntimeError, OSError) as exc:
        parser.error("cannot construct ASCII seed: " + str(exc))
    elapsed = time.perf_counter() - started
    r = random.Random(seed)
    result = bytes(r.randrange(128) for _ in range(len(target) + len(TERMINATOR)))
    assert result == target + TERMINATOR, "fresh standard Random verification failed"
    output = Path("seed_text.txt")
    output.write_text(hex(seed) + "\n", encoding="ascii")
    print("Python:", sys.version.replace("\n", " "))
    print("Target text:", repr(target.decode("ascii")))
    print("Target length:", len(target))
    print("Constraints:", (len(target) + len(TERMINATOR)) * 8)
    print("Constraint rank:", rank)
    print("Free state bits:", free)
    print("Seed bit length:", seed.bit_length())
    print(f"Construction time: {elapsed:.3f} s")
    print("Verification: passed (fresh standard random.Random)")
    print("Saved:", output)
    if args.show_seed:
        print("Seed:", hex(seed))


if __name__ == "__main__":
    main()
