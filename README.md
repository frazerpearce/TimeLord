# Post-selecting 100 heads

This small CPython demonstration constructs an ordinary integer seed for which
up to 1,000 ordinary `random.Random(seed).randrange(2)` calls all return 1
(HEADS). It
does not use `setstate`, patch `random`, or replace the generator.

For a seed fixed independently in advance, 100 heads has probability
`2^-100`, approximately `7.9e-31` (with Python's exact rejection-sampling
mapping producing an unbiased bit).  Here the seed was *not* independently
chosen: it was constructed conditional on the desired outcome.  The observed
result therefore is not evidence for a `2^-100` random fluctuation.

## How construction works

On this CPython implementation, `_randbelow(2)` calls `getrandbits(2)` until
the value is below 2.  `getrandbits(2)` uses the top two bits of one tempered
MT19937 word.  Requiring those bits to be `01` makes every call return 1
without rejection.

`find_heads_seed.py` expresses the MT19937 twist and temper operations as
linear equations over GF(2), solves two output-bit constraints per toss across
as many MT19937 output blocks as needed, reverses
the second `init_by_array` loop, and constructs the 624 little-endian 32-bit
limbs consumed by CPython's integer-seeding path.  The resulting arbitrarily
large positive Python integer therefore reaches the solved state through
normal `random.Random(seed)` initialization.

This relies on the MT19937 and seed initialization code bundled in CPython's
`Modules/_randommodule.c`; it has no third-party dependencies.  The generated
seed is specific to CPython implementations retaining those details.

The repository includes verified hexadecimal fixtures for 100 and 1,000 heads:
`seed_100_heads.txt` and `seed_1000_heads.txt`.

## Run

```sh
python3 find_heads_seed.py
python3 find_heads_seed.py 500
python3 demo_heads.py 500
python3 find_heads_seed.py 1000 --free-seed 42
python3 demo_heads.py 1000
```

The positional argument selects 1 through 1,000 heads and defaults to 100.
Seeds are written as hexadecimal integers to `seed_<N>_heads.txt`. By default,
unconstrained state bits
come from OS entropy, so the continuation looks like an ordinary MT19937
sequence rather than inheriting long runs caused by zero-filled free state.
Use `--free-seed` to make the free-bit selection exactly repeatable.

The first command writes `seed_100_heads.txt` and verifies the result. The demo
accepts the same optional length (default 100), reads `seed_<N>_heads.txt`, and
runs ordinary seeded coin tosses. Hexadecimal avoids Python 3.11+'s default
4,300-digit limit for decimal integer conversions. Reproducible
output shows only that a computation can be replayed; it does not show that
its seed was randomly selected.  This is the same distinction behind
post-selection and look-elsewhere effects.

## Test

The test suite uses only Python's standard library:

```sh
python3 -m unittest discover -s tests -v
```
