"""Generic two-byte-length binary TimeLord loader; no application logic."""
from pathlib import Path
import random
import sys
r=random.Random(int(Path(sys.argv[1]).read_text(),0))
n=r.getrandbits(8)|r.getrandbits(8)<<8
if not 0<n<=2490: raise ValueError('invalid frame')
Path(sys.argv[2]).write_bytes(bytes(r.getrandbits(8) for _ in range(n)))
