import random,pathlib,webbrowser
r=random.Random(int(pathlib.Path('seed_planet.txt').read_text(),0))
n=r.getrandbits(8)|r.getrandbits(8)<<8
p=pathlib.Path('planet.html').resolve()
p.write_bytes(bytes(r.getrandbits(8) for _ in range(n)))
webbrowser.open(p.as_uri())
