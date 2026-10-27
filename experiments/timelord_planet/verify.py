"""Rebuild, prove CPython transport, and run only recovered documents offline."""
import lzma,hashlib,json,random,re,subprocess,sys,tempfile
from pathlib import Path
from address import child
assert [child(1,'G',2),child(2870994987,'S',3),child(2462232634,'P',4)]==[2870994987,2462232634,2638447889]
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[1]
out=ROOT/'artifacts'
before={name:(out/name).read_bytes() for name in ['planet.html','seed.hex','frame.bin']}
subprocess.run([sys.executable,str(ROOT/'build.py')],check=True,stdout=subprocess.DEVNULL)
assert all((out/name).read_bytes()==data for name,data in before.items())
# Terrain source is byte-identical to the previous ground generator.
source=(ROOT/'src/planet.js').read_text()
for name,digest in json.loads((ROOT/'baseline.json').read_text())['terrain_functions_sha256'].items():
 start=re.search(r'float '+name+r'\(',source).start()
 begin=source.index('{',start);depth=1;end=begin+1
 while depth:
  depth+=(source[end]=='{')-(source[end]=='}');end+=1
 assert hashlib.sha256(source[start:end].encode()).hexdigest()==digest
seed=int((out/'seed.hex').read_text(),0)
r=random.Random(seed)
compressed=(out/'planet.html.lzma').read_bytes()
n=len(compressed)
assert bytes(r.getrandbits(8) for _ in range(n))==compressed
assert (out/'frame.bin').read_bytes()==compressed
filters=[dict(id=lzma.FILTER_LZMA1,dict_size=8192,lc=2,lp=0,pb=0)]
decoder=lzma.LZMADecompressor(format=lzma.FORMAT_RAW,filters=filters)
recovered=decoder.decompress(compressed)
assert decoder.eof and not decoder.unused_data
assert recovered==(out/'planet.html').read_bytes()
assert recovered==b'<body><script>'+(out/'planet.min.js').read_bytes()+b'</script>'
sizes=json.loads((out/'sizes.json').read_text())
assert n==sizes['total_framed_bytes']<=2492
assert (seed.bit_length()+7)//8==sizes['seed_binary_bytes']
with tempfile.TemporaryDirectory(prefix='magrathea-clean-') as directory:
 clean=Path(directory)
 (clean/'load_seed.py').write_bytes((ROOT/'load_seed.py').read_bytes())
 (clean/'seed.hex').write_bytes((out/'seed.hex').read_bytes())
 subprocess.run([sys.executable,'-I','-S','load_seed.py','seed.hex','planet.html'],cwd=clean,check=True)
 assert (clean/'planet.html').read_bytes()==recovered
 # Actual two-file normal/stripped recipients, not imports from development.
 for kind,launcher in [('normal',REPO/'timelord_planet.py'),('stripped',ROOT/'stripped/timelord_planet.py')]:
  dest=clean/kind;dest.mkdir()
  (dest/'timelord_planet.py').write_bytes(launcher.read_bytes())
  (dest/'seed_planet.txt').write_bytes((out/'seed.hex').read_bytes())
  if kind=='normal':
   command=[sys.executable,'-I','-S','timelord_planet.py','--no-open','--output','planet.html']
  else:
   command=[sys.executable,'-I','-S','-c',"import runpy,webbrowser;webbrowser.open=lambda url:True;runpy.run_path('timelord_planet.py',run_name='__main__')"]
  subprocess.run(command,cwd=dest,check=True,stdout=subprocess.DEVNULL)
  assert (dest/'planet.html').read_bytes()==recovered
 # Recreate the unoptimized reference from the unchanged readable source.
 reference=re.sub(r'//[^\n]*','',source)
 reference=re.sub(r'\s+',' ',reference).strip()
 reference=re.sub(r'\s*([{}();,=+*<>?:])\s*',r'\1',reference)
 reference=('<body><script>'+reference+'</script>').encode()
 from compact import CONFIG
 assert hashlib.sha256(reference).hexdigest()==CONFIG['reference_html_sha256']
 (clean/'reference.html').write_bytes(reference)
 if '--browser' in sys.argv:
  args=[sys.argv[sys.argv.index('--browser')+1],str(ROOT/'render.cjs'),str(clean/'normal/planet.html'),str(clean/'stripped/planet.html'),str(clean/'reference.html')]
  args.extend(a for a in ['--video','--webkit'] if a in sys.argv)
  subprocess.run(args,check=True)
report=dict(exact_cpython_getrandbits_reconstruction=True,reproducible_build=True,address_vectors_pass=True,unchanged_terrain_generator=True,total_framed_bytes=n,limit_pass=True,clean_isolated_loaders=['minimal','normal','stripped'],html_sha256=hashlib.sha256(recovered).hexdigest(),packed_sha256=hashlib.sha256(compressed).hexdigest(),seed_bits=seed.bit_length())
(out/'transport-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
