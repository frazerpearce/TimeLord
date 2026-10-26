"""No downloaded build tools: conservative whitespace minification + gzip."""
import base64,gzip,hashlib,json,random,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
from binary_transport import construct_binary_seed
source=(ROOT/'src/planet.js').read_text()
mini=re.sub(r'//[^\n]*','',source)
mini=re.sub(r'\s+',' ',mini).strip()
# Preserve GLSL's preprocessor line boundaries: they are escaped in the JS string.
mini=re.sub(r'\s*([{}();,=+*<>?:])\s*',r'\1',mini)
compressed=gzip.compress(mini.encode(),compresslevel=9,mtime=0)
wrapper="<body><script>new Response(new Blob([Uint8Array.from(atob('"+base64.b64encode(compressed).decode()+"'),c=>c.charCodeAt(0))]).stream().pipeThrough(new DecompressionStream('gzip'))).text().then(eval)</script>"
payload=wrapper.encode();frame=len(payload).to_bytes(2,'little')+payload
out=ROOT/'artifacts';out.mkdir(exist_ok=True)
(out/'planet.min.js').write_text(mini)
(out/'planet.html').write_bytes(payload)
(out/'frame.bin').write_bytes(frame)
(out/'planet.js.gz').write_bytes(compressed)
info=dict(raw_source_bytes=len(source.encode()),minified_bytes=len(mini.encode()),gzip_bytes=len(compressed),base64_bytes=len(base64.b64encode(compressed)),html_wrapper_bytes=len(payload)-len(base64.b64encode(compressed)),packed_payload_bytes=len(payload),framing_bytes=2,total_framed_bytes=len(frame),limit_bytes=2492,payload_sha256=hashlib.sha256(payload).hexdigest())
if '--no-seed' not in sys.argv:
 assert len(frame)<=2492,info
 seed,rank,free=construct_binary_seed(frame)
 rng=random.Random(seed)
 assert bytes(rng.getrandbits(8) for _ in frame)==frame
 (out/'seed.hex').write_text(hex(seed)+'\n')
 info.update(seed_bits=seed.bit_length(),seed_binary_bytes=(seed.bit_length()+7)//8,seed_hex_file_bytes=(out/'seed.hex').stat().st_size,constraint_rank=rank,free_state_bits=free)
info['host']='Browser with WebGL1, OES_standard_derivatives, highp fragment floats, DecompressionStream(gzip), Blob/Response, standard DOM; not CPU/OS-only'
info['python_version']=sys.version.split()[0]
info['loader_bytes']=(ROOT/'load_seed.py').stat().st_size
(out/'sizes.json').write_text(json.dumps(info,indent=2)+'\n')
print(json.dumps(info,indent=2))
