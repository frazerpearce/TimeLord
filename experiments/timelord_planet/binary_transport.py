"""Binary adapter; the vendored TimeLord implementation stays unchanged.

The original inverter chooses key[0]=0. At full rank there are no free state
bits to retry if its most significant seed limb vanishes. Choosing key[0]=1
is sufficient in that exceptional case: the final mixing expression is a
permutation of key[0], so at most one choice can give a zero top limb.
"""
import random

from vendor import timelord_mt as mt


def _key(target, first):
    state, key = mt.init_genrand(), [0] * mt.N
    key[0] = first
    state[1] = ((state[1] ^ ((state[0] ^ (state[0] >> 30)) * 1664525)) + first) & mt.MASK
    for i in range(2, mt.N):
        mix = (state[i] ^ ((state[i-1] ^ (state[i-1] >> 30)) * 1664525)) & mt.MASK
        key[i-1] = (target[i] - mix - (i-1)) & mt.MASK
        state[i] = target[i]
    mix = (state[1] ^ ((state[623] ^ (state[623] >> 30)) * 1664525)) & mt.MASK
    key[623] = (target[1] - mix - 623) & mt.MASK
    return key


def construct_binary_seed(data, free_seed=42):
    data = bytes(data)
    try:
        return mt.construct_output_seed(data, 8, free_seed)
    except RuntimeError as exc:
        if 'top seed limb vanished' not in str(exc):
            raise
    # Exceptional development-time fallback; no encoder is needed at replay.
    rhs = []
    for desired, offset in zip(data, mt.fixed_word_outputs(len(data))):
        adjusted = desired ^ (offset >> 24)
        rhs.extend((adjusted >> bit) & 1 for bit in range(7, -1, -1))
    free_bits = random.Random(free_seed).getrandbits(mt.VARIABLE_COUNT)
    solution, rank = mt.solve_gf2(mt.symbolic_output_rows(len(data), 8), rhs, free_bits)
    state = [mt.UPPER] + [(solution >> (32*i)) & mt.MASK for i in range(mt.N-1)]
    key = _key(mt.reverse_second_seed_loop(state), 1)
    assert key[-1] != 0
    seed = sum(limb << (32*i) for i, limb in enumerate(key))
    return seed, rank, mt.VARIABLE_COUNT-rank
