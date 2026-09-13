#!/usr/bin/env python3
"""Construct an integer seed making CPython's first N coin tosses heads.

This targets CPython's MT19937 and init_by_array implementation. Twist and
temper are linear over GF(2), so two equations per toss force getrandbits(2)
to return 1. The seeding loops are reversed to obtain an ordinary integer.
Unconstrained state bits are randomized rather than set to zero.
"""

import argparse
import random
import secrets
import sys
import time

if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(0)

N, M = 624, 397
UPPER, LOWER = 0x80000000, 0x7fffffff
MATRIX_A, MASK = 0x9908b0df, 0xffffffff
VARIABLE_COUNT = (N - 1) * 32


def twist_words(mt):
    """Exact in-place twist used by CPython's bundled MT19937."""
    mt = mt[:]
    for i in range(N - M):
        y = (mt[i] & UPPER) | (mt[i + 1] & LOWER)
        mt[i] = mt[i + M] ^ (y >> 1) ^ (MATRIX_A if y & 1 else 0)
    for i in range(N - M, N - 1):
        y = (mt[i] & UPPER) | (mt[i + 1] & LOWER)
        mt[i] = mt[i + M - N] ^ (y >> 1) ^ (MATRIX_A if y & 1 else 0)
    y = (mt[N - 1] & UPPER) | (mt[0] & LOWER)
    mt[N - 1] = mt[M - 1] ^ (y >> 1) ^ (MATRIX_A if y & 1 else 0)
    return [x & MASK for x in mt]


def temper(x):
    x ^= x >> 11
    x ^= (x << 7) & 0x9d2c5680
    x ^= (x << 15) & 0xefc60000
    x ^= x >> 18
    return x & MASK


def twist_symbolic(state):
    """Twist words whose individual bits are GF(2) coefficient masks."""
    state = [word[:] for word in state]

    def one(i, j):
        y = state[i + 1][:]
        y[31] = state[i][31]
        lsb = y[0]
        out = []
        for bit in range(32):
            value = state[j][bit] ^ (y[bit + 1] if bit < 31 else 0)
            if (MATRIX_A >> bit) & 1:
                value ^= lsb
            out.append(value)
        return out

    for i in range(N - M):
        state[i] = one(i, i + M)
    for i in range(N - M, N - 1):
        state[i] = one(i, i + M - N)
    y = state[0][:]
    y[31] = state[N - 1][31]
    lsb = y[0]
    out = []
    for bit in range(32):
        value = state[M - 1][bit] ^ (y[bit + 1] if bit < 31 else 0)
        if (MATRIX_A >> bit) & 1:
            value ^= lsb
        out.append(value)
    state[N - 1] = out
    return state


def temper_symbolic(bits):
    def right(value, shift):
        return [value[b] ^ (value[b + shift] if b + shift < 32 else 0)
                for b in range(32)]

    def left_mask(value, shift, mask):
        return [value[b] ^ (value[b - shift] if b >= shift and
                            ((mask >> b) & 1) else 0) for b in range(32)]

    bits = right(bits, 11)
    bits = left_mask(bits, 7, 0x9d2c5680)
    bits = left_mask(bits, 15, 0xefc60000)
    return right(bits, 18)


def symbolic_output_rows(count):
    """Coefficient masks for output bits 31 and 30 of the first count words."""
    mt = [[0] * 32]
    for word in range(1, N):
        mt.append([1 << ((word - 1) * 32 + bit) for bit in range(32)])
    rows = []
    remaining = count
    while remaining:
        mt = twist_symbolic(mt)
        block = min(remaining, N)
        for word in mt[:block]:
            bits = temper_symbolic(word)
            rows.extend((bits[31], bits[30]))
        remaining -= block
    return rows


def fixed_word_outputs(count):
    """Affine offset caused by init_by_array's fixed state word zero."""
    mt = [0] * N
    mt[0] = UPPER
    outputs = []
    while len(outputs) < count:
        mt = twist_words(mt)
        block = min(count - len(outputs), N)
        outputs.extend(temper(x) for x in mt[:block])
    return outputs


def solve_gf2(rows, rhs, free_bits):
    """Solve constraints while preserving random non-pivot variables."""
    pivots = {}
    for row, value in zip(rows, rhs):
        while row:
            pivot = row.bit_length() - 1
            if pivot not in pivots:
                pivots[pivot] = (row, value)
                break
            old_row, old_value = pivots[pivot]
            row ^= old_row
            value ^= old_value
        else:
            if value:
                raise RuntimeError("inconsistent MT constraints")
    if len(pivots) != len(rows):
        raise RuntimeError("output constraints are not independent")

    pivot_mask = 0
    for pivot in pivots:
        pivot_mask |= 1 << pivot
    solution = free_bits & ~pivot_mask
    # Pivot is each row's highest bit, so solve in ascending order.
    for pivot in sorted(pivots):
        row, value = pivots[pivot]
        parity = bin(row & solution).count("1") & 1
        if parity != value:
            solution |= 1 << pivot
    return solution, len(pivots)


def init_genrand(seed=19650218):
    mt = [0] * N
    mt[0] = seed & MASK
    for i in range(1, N):
        mt[i] = (1812433253 * (mt[i - 1] ^ (mt[i - 1] >> 30)) + i) & MASK
    return mt


def reverse_second_seed_loop(final_state):
    """Recover the state preceding init_by_array's second mixing loop."""
    state = final_state[:]
    state[1] = ((state[1] + 1) ^
                ((state[623] ^ (state[623] >> 30)) * 1566083941)) & MASK
    for i in range(623, 1, -1):
        state[i] = ((state[i] + i) ^
                    ((state[i - 1] ^ (state[i - 1] >> 30)) *
                     1566083941)) & MASK
    return state


def key_for_first_seed_loop(target):
    """Choose 624 little-endian 32-bit limbs consumed from a Python integer."""
    mt = init_genrand()
    key = [0] * N
    # key[0]=0; temporary mt[1] drives the subsequent forward construction.
    mt[1] = (mt[1] ^ ((mt[0] ^ (mt[0] >> 30)) * 1664525)) & MASK
    for i in range(2, N):
        mix = (mt[i] ^ ((mt[i - 1] ^ (mt[i - 1] >> 30)) * 1664525)) & MASK
        key[i - 1] = (target[i] - mix - (i - 1)) & MASK
        mt[i] = target[i]
    mt[0] = mt[623]
    mix = (mt[1] ^ ((mt[0] ^ (mt[0] >> 30)) * 1664525)) & MASK
    key[623] = (target[1] - mix - 623) & MASK
    if key[623] == 0:
        raise RuntimeError("top seed limb vanished; rerun with different free bits")
    return key


def construct_seed(toss_count, free_seed=None):
    rows = symbolic_output_rows(toss_count)
    rhs = []
    # getrandbits(2)==1 means tempered top bits 01, with no rejection.
    for value in fixed_word_outputs(toss_count):
        rhs.extend((((value >> 31) & 1), ((value >> 30) & 1) ^ 1))
    if free_seed is None:
        free_bits = secrets.randbits(VARIABLE_COUNT)
    else:
        free_bits = random.Random(free_seed).getrandbits(VARIABLE_COUNT)
    solution, rank = solve_gf2(rows, rhs, free_bits)

    state = [UPPER]
    state.extend((solution >> (32 * word)) & MASK for word in range(N - 1))
    key = key_for_first_seed_loop(reverse_second_seed_loop(state))
    seed = sum(limb << (32 * i) for i, limb in enumerate(key))
    return seed, rank, VARIABLE_COUNT - rank


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
