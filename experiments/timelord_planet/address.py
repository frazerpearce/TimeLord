"""Reference for FUTURE parent modules, not needed or loaded by the planet.

FNV-1a-32 over a fixed-width hierarchy edge. IDs and seeds are unsigned uint32.
This is address selection, never TimeLord transport decoding or random seeding.
"""
def child(parent, kind, identifier):
    """kind is exactly 'G' (galaxy), 'S' (star), or 'P' (planet)."""
    if kind not in ('G','S','P') or not 0 <= parent < 2**32 or not 0 <= identifier < 2**32:
        raise ValueError('invalid hierarchy edge')
    value=2166136261
    for byte in parent.to_bytes(4,'little')+kind.encode('ascii')+identifier.to_bytes(4,'little'):
        value=((value^byte)*16777619)&0xffffffff
    return value

if __name__=='__main__':
    galaxy=child(1,'G',2)
    star=child(galaxy,'S',3)
    planet=child(star,'P',4)
    print(galaxy,star,planet)
