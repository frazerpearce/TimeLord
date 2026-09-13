#!/usr/bin/env python3
import argparse
import random

parser = argparse.ArgumentParser()
parser.add_argument("tosses", nargs="?", type=int, default=100)
args = parser.parse_args()
if not 1 <= args.tosses <= 1000:
    parser.error("tosses must be between 1 and 1000")

seed_file = "seed_{}_heads.txt".format(args.tosses)
with open(seed_file, encoding="ascii") as handle:
    seed = int(handle.read().strip(), 0)

r = random.Random(seed)
tosses = ["H" if r.randrange(2) else "T" for _ in range(args.tosses)]

print("Seed file:", seed_file)
print("".join(tosses))
print("Heads:", tosses.count("H"))
print("Tails:", tosses.count("T"))

assert tosses == ["H"] * args.tosses
