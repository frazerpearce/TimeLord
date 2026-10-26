"""Transport/build checks, plus a clean directory for the browser verification."""
import base64,gzip,hashlib,json,random,subprocess,sys,tempfile
from pathlib import Path
from address import child
assert child(1,'G',2)==2870994987
assert child(2870994987,'S',3)==2462232634
assert child(2462232634,'P',4)==2638447889
ROOT=Path(__file__).resolve().parent
out=ROOT/'artifacts'
before={name:(out/name).read_bytes() for name in ['planet.html','seed.hex']}
subprocess.run([sys.executable,str(ROOT/'build.py')],check=True,stdout=subprocess.DEVNULL)
assert all((out/name).read_bytes()==data for name,data in before.items())
seed=int((out/'seed.hex').read_text(),0)
r=random.Random(seed)
n=r.getrandbits(8)|(r.getrandbits(8)<<8)
recovered=bytes(r.getrandbits(8) for _ in range(n))
assert recovered==(out/'planet.html').read_bytes()
assert (out/'frame.bin').read_bytes()==n.to_bytes(2,'little')+recovered
sizes=json.loads((out/'sizes.json').read_text())
assert n+2==sizes['total_framed_bytes']<=2492
assert (seed.bit_length()+7)//8==sizes['seed_binary_bytes']
encoded=recovered.split(b"atob('")[1].split(b"')")[0]
assert gzip.decompress(base64.b64decode(encoded))==(out/'planet.min.js').read_bytes()
with tempfile.TemporaryDirectory(prefix='timelord-planet-clean-') as clean:
 clean=Path(clean)
 (clean/'load_seed.py').write_bytes((ROOT/'load_seed.py').read_bytes())
 (clean/'seed.hex').write_bytes((out/'seed.hex').read_bytes())
 subprocess.run([sys.executable,'-I','-S','load_seed.py','seed.hex','planet.html'],cwd=clean,check=True)
 assert (clean/'planet.html').read_bytes()==recovered
 # Browser receives only the recovered HTML, without source files or helpers.
 if '--browser' in sys.argv:
  subprocess.run([sys.argv[sys.argv.index('--browser')+1],str(ROOT/'render.cjs'),str(clean/'planet.html'),'--verify']+(['--video'] if '--video' in sys.argv else []),check=True)
report=dict(exact_cpython_getrandbits_reconstruction=True,reproducible_build=True,address_vectors_pass=True,total_framed_bytes=n+2,limit_pass=True,clean_isolated_loader=True,packed_sha256=hashlib.sha256(recovered).hexdigest(),seed_bits=seed.bit_length())
(out/'transport-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
