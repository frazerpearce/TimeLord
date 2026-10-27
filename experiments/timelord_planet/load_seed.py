"""Generic standard-library LZMA TimeLord loader; no application logic."""
from pathlib import Path
import lzma,random,sys
r=random.Random(int(Path(sys.argv[1]).read_text(),0))
d=lzma.LZMADecompressor(format=lzma.FORMAT_RAW,filters=[{'id':lzma.FILTER_LZMA1,'dict_size':8192,'lc':2,'lp':0,'pb':0}])
b=b''
for _ in range(2492):
 b+=d.decompress(bytes([r.getrandbits(8)]))
 if d.eof:break
else:raise ValueError('invalid or oversized stream')
Path(sys.argv[2]).write_bytes(b)
