#!/usr/bin/env python3
import random

with open("seed_text.txt", encoding="ascii") as handle:
    seed = int(handle.read().strip(), 0)
r = random.Random(seed)
pending = ""
while True:
    character = chr(r.randrange(128))
    if pending + character == "\x1e\x1f":
        break
    print(pending, end="")
    pending = character
print()
