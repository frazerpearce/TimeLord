import random,pathlib,webbrowser,lzma
r=random.Random(int(pathlib.Path('seed_planet.txt').read_text(),0))
d=lzma.LZMADecompressor(format=lzma.FORMAT_RAW,filters=[{'id':lzma.FILTER_LZMA1,'dict_size':8192,'lc':2,'lp':0,'pb':0}])
b=b''
while not d.eof:b+=d.decompress(bytes([r.getrandbits(8)]))
p=pathlib.Path('planet.html').resolve()
p.write_bytes(b)
webbrowser.open(p.as_uri())
