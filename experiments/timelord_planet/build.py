"""No downloaded build tools: conservative whitespace minification + gzip."""
import gzip,hashlib,json,random,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
from binary_transport import construct_binary_seed
source=(ROOT/'src/planet.js').read_text()
mini=re.sub(r'//[^\n]*','',source)
mini=re.sub(r'\s+',' ',mini).strip()
# Preserve GLSL's preprocessor line boundaries: they are escaped in the JS string.
mini=re.sub(r'\s*([{}();,=+*<>?:])\s*',r'\1',mini)
document=('<body><script>'+mini+'</script>').encode()
compressed=gzip.compress(document,compresslevel=9,mtime=0)
frame=len(compressed).to_bytes(2,'little')+compressed
out=ROOT/'artifacts';out.mkdir(exist_ok=True)
(out/'planet.min.js').write_text(mini)
(out/'planet.html').write_bytes(document)
(out/'frame.bin').write_bytes(frame)
(out/'planet.html.gz').write_bytes(compressed)
info=dict(raw_source_bytes=len(source.encode()),raw_html_bytes=len(('<body><script>'+source+'</script>').encode()),minified_bytes=len(mini.encode()),executable_html_bytes=len(document),gzip_bytes=len(compressed),packed_payload_bytes=len(compressed),framing_bytes=2,total_framed_bytes=len(frame),limit_bytes=2492,html_sha256=hashlib.sha256(document).hexdigest(),packed_sha256=hashlib.sha256(compressed).hexdigest(),baseline=dict(framed_bytes=2463,gzip_js_bytes=1722,base64_bytes=2296,html_unpacker_bytes=165,commit='31914fa'))
if '--no-seed' not in sys.argv:
 assert len(frame)<=2492,info
 seed,rank,free=construct_binary_seed(frame)
 rng=random.Random(seed)
 assert bytes(rng.getrandbits(8) for _ in frame)==frame
 (out/'seed.hex').write_text(hex(seed)+'\n')
 (ROOT.parents[1]/'seed_planet.txt').write_text(hex(seed)+'\n')
 info.update(seed_bits=seed.bit_length(),seed_binary_bytes=(seed.bit_length()+7)//8,seed_hex_file_bytes=(out/'seed.hex').stat().st_size,constraint_rank=rank,free_state_bits=free)
info['host']='CPython random + gzip loading infrastructure; browser WebGL1, highp fragment floats, OES_standard_derivatives and standard DOM; not CPU/OS-only'
info['python_version']=sys.version.split()[0]
info['normal_launcher_bytes']=(ROOT.parents[1]/'timelord_planet.py').stat().st_size
info['stripped_launcher_bytes']=(ROOT/'stripped/timelord_planet.py').stat().st_size
info['loader_bytes']=(ROOT/'load_seed.py').stat().st_size
(out/'sizes.json').write_text(json.dumps(info,indent=2)+'\n')
print(json.dumps(info,indent=2))
