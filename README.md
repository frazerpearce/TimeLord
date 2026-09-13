# TimeLord

**Choose the random future you want, then construct the seed that produces it.**

TimeLord is a small Python demonstration showing that a spectacularly unlikely sequence from a pseudorandom number generator does not necessarily imply spectacular luck.

The program constructs an ordinary Python integer seed such that normal code like

```python
import random

r = random.Random(seed)

for _ in range(100):
    print("H" if r.randrange(2) else "T")
```

produces:

```text
HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH
```

That is **100 consecutive heads**.

TimeLord can construct seeds for runs of up to **1,000 consecutive heads**.

There is no modified random-number generator, no `setstate()`, no monkey-patching and no hidden intervention after the seed has been supplied. The demonstration uses an ordinary integer passed directly to:

```python
random.Random(seed)
```

The trick is that the seed is chosen **after the desired future has been specified**.

---

## Why is this interesting?

If a fair coin is tossed 100 times, the probability of obtaining 100 heads is

$$
2^{-100} \approx 7.9\times10^{-31}.
$$

For 1,000 heads it is

$$
2^{-1000} \approx 9.3\times10^{-302}.
$$

If the seed had been selected independently beforehand, either result would therefore be extraordinary.

But that is not what TimeLord does.

Instead, we first decide:

> I want the next 100 random coin tosses to be heads.

TimeLord then works backwards and constructs an initial seed that makes Python's pseudorandom number generator produce exactly that future.

The resulting sequence is completely reproducible. Anyone given the seed can run ordinary Python and obtain the same 100 heads.

But reproducibility does **not** establish that the seed itself was independently or randomly selected.

That is the point of the demonstration.

---

## The underlying lesson

A pseudorandom generator is deterministic.

Once its internal state is fixed, its future output is fixed too.

Normally we work in the forward direction:

```text
seed
  ↓
internal state
  ↓
random-looking outputs
```

TimeLord solves the inverse problem:

```text
desired future outputs
        ↓
compatible internal state
        ↓
integer seed
```

The desired result is therefore not predicted.

It is **selected**.

This is closely related to statistical ideas such as **post-selection**, the **look-elsewhere effect**, and selection bias. An outcome can appear extraordinarily improbable if we calculate its probability as though the conditions that produced it had been fixed independently in advance.

They were not.

---

# How does TimeLord do it?

Python's standard `random` module in CPython uses the **MT19937 Mersenne Twister** pseudorandom number generator.

For the coin toss used here,

```python
r.randrange(2)
```

CPython ultimately calls:

```python
getrandbits(2)
```

and repeats if the resulting value is not below 2.

`getrandbits(2)` takes the top two bits from a tempered 32-bit MT19937 output word.

To force the result to be `1`, corresponding here to HEADS, those two bits can simply be constrained to:

```text
01
```

Because `01` is already below 2, no rejection occurs.

So each required head gives TimeLord just **two bit constraints** on the MT19937 output.

For 100 heads there are 200 constraints.

For 1,000 heads there are 2,000.

MT19937 has a state containing roughly 20,000 bits, leaving enormous freedom even after those constraints have been imposed.

---

## Solving for a state

The important property exploited here is that the MT19937 **twist** and **temper** transformations can be represented as linear operations over the two-element field \(GF(2)\).

In other words, at the bit level they can be expressed using systems of XOR-based linear equations.

TimeLord:

1. symbolically represents the relevant MT19937 state bits;
2. propagates them through the MT twist and temper operations;
3. constructs equations requiring the appropriate output bits to be `01`;
4. solves those equations over \(GF(2)\);
5. chooses the remaining unconstrained state bits freely.

This produces an MT19937 state whose future outputs begin with the requested sequence of heads.

The program works across multiple MT19937 output blocks, which is why runs longer than the generator's 624-word state array can also be constructed.

---

# But Python accepts a seed, not an MT state

This is the more interesting part.

It would be easy to construct the required MT state and then use:

```python
random.setstate(...)
```

But that would weaken the demonstration.

TimeLord does **not** do that.

Instead, it reverses CPython's MT19937 integer-seeding procedure.

CPython turns an arbitrary-size Python integer into a series of 32-bit words and feeds them through the MT19937 `init_by_array` initialisation algorithm.

TimeLord works backwards through those mixing operations to find the 624 little-endian 32-bit seed words that generate the state it has just constructed.

Those words are then combined into one ordinary, although very large, positive Python integer.

The final result is simply:

```python
seed = <very large integer>

r = random.Random(seed)
```

From that point onwards everything is completely standard Python.

---

# Running TimeLord

No third-party packages are required.

Generate a seed producing the default **100 heads**:

```bash
python3 find_heads_seed.py
```

Generate a seed for 500 heads:

```bash
python3 find_heads_seed.py 500
```

Generate one for 1,000 heads:

```bash
python3 find_heads_seed.py 1000
```

The supported range is currently:

```text
1–1000 heads
```

The generated seed is written to:

```text
seed_<N>_heads.txt
```

For example:

```text
seed_100_heads.txt
seed_1000_heads.txt
```

---

# Run the simple demonstration

Once a seed has been generated:

```bash
python3 demo_heads.py 100
```

or:

```bash
python3 demo_heads.py 1000
```

The important point is that `demo_heads.py` contains none of the inversion machinery.

It simply loads the integer seed and uses ordinary Python random-number generation.

That separation is deliberate: the demo is intended to make clear that nothing unusual happens while the apparent "coin tossing" takes place.

The unusual step occurred earlier, when the seed was selected.

---

# Reproducible construction

By default, TimeLord fills the unconstrained parts of the MT19937 state using operating-system entropy.

This means repeated runs will normally produce different seeds, all satisfying the requested future.

To make the *construction itself* reproducible, supply `--free-seed`:

```bash
python3 find_heads_seed.py 1000 --free-seed 42
```

This fixes the otherwise unconstrained bits and therefore reproduces the same generated seed.

---

# Why are the seed files hexadecimal?

The constructed seeds are very large integers.

Python 3.11 and later impose a default limit on decimal integer/string conversions of 4,300 digits. Hexadecimal representation avoids this limitation conveniently and is also a natural representation for the underlying 32-bit seed words.

---

# Tests

The test suite uses only the Python standard library:

```bash
python3 -m unittest discover -s tests -v
```

---

# What this demonstration does — and does not — show

TimeLord does **not** show that fair random processes naturally produce 1,000 heads with appreciable probability.

They do not.

Nor does it show that Python's `random` module is statistically defective for its intended simulation uses.

It demonstrates something different:

> **An apparently improbable pseudorandom outcome tells us very little unless we also know how the initial conditions were selected.**

A result may be:

* deterministic;
* reproducible;
* statistically extraordinary under a prespecified seed;

and yet completely unsurprising once we learn that the seed was chosen conditional on obtaining that result.

This distinction matters well beyond toy coin tosses. It is the same general issue encountered whenever researchers search many possibilities and subsequently report the one producing an interesting outcome.

---

# Why “TimeLord”?

A Time Lord does not need to wait passively to discover which future happens.

They select the future they want.

TimeLord does much the same thing to MT19937:

```text
choose future
    ↓
solve backwards
    ↓
construct initial conditions
    ↓
watch the chosen future unfold
```

No time travel required.

---

## Implementation notes

TimeLord is tied to the MT19937 implementation and integer-seeding behaviour used by **CPython**.

It relies on details corresponding to CPython's:

```text
Modules/_randommodule.c
```

Consequently, generated seeds should not be assumed to produce the same behaviour in unrelated Python implementations or generators with different seeding algorithms.

The repository includes verified seed fixtures for both 100 and 1,000 consecutive heads.
