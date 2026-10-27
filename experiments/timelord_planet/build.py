"""No downloaded build tools: identifier minification + standard raw LZMA1."""
import lzma,hashlib,json,random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
from binary_transport import construct_binary_seed
from compact import CONFIG,minify
source=(ROOT/'src/planet.js').read_text()
mini=minify(source)
document=('<body><script>'+mini+'</script>').encode()
compressed=lzma.compress(document,format=lzma.FORMAT_RAW,filters=CONFIG['lzma_filters'])
frame=compressed  # LZMA's end marker replaces the length header.
out=ROOT/'artifacts';out.mkdir(exist_ok=True)
(out/'planet.min.js').write_text(mini)
(out/'planet.html').write_bytes(document)
(out/'frame.bin').write_bytes(frame)
(out/'planet.html.lzma').write_bytes(compressed)
info=dict(raw_source_bytes=len(source.encode()),raw_html_bytes=len(('<body><script>'+source+'</script>').encode()),minified_bytes=len(mini.encode()),executable_html_bytes=len(document),packed_payload_bytes=len(compressed),framing_bytes=0,total_framed_bytes=len(frame),limit_bytes=2492,html_sha256=hashlib.sha256(document).hexdigest(),packed_sha256=hashlib.sha256(compressed).hexdigest(),baseline=dict(framed_bytes=2471,commit='d7aa3cd'),compression='raw LZMA1 with end marker',compression_filters=CONFIG['lzma_filters'])
if '--no-seed' not in sys.argv:
 assert len(frame)<=2492,info
 seed,rank,free=construct_binary_seed(frame)
 rng=random.Random(seed)
 assert bytes(rng.getrandbits(8) for _ in frame)==frame
 (out/'seed.hex').write_text(hex(seed)+'\n')
 (ROOT.parents[1]/'seed_planet.txt').write_text(hex(seed)+'\n')
 info.update(seed_bits=seed.bit_length(),seed_binary_bytes=(seed.bit_length()+7)//8,seed_hex_file_bytes=(out/'seed.hex').stat().st_size,constraint_rank=rank,free_state_bits=free)
info['host']='CPython random + standard lzma loading infrastructure; browser WebGL1, highp fragment floats, OES_standard_derivatives and standard DOM; not CPU/OS-only'
info['python_version']=sys.version.split()[0]
info['normal_launcher_bytes']=(ROOT.parents[1]/'timelord_planet.py').stat().st_size
info['stripped_launcher_bytes']=(ROOT/'stripped/timelord_planet.py').stat().st_size
info['loader_bytes']=(ROOT/'load_seed.py').stat().st_size
(out/'sizes.json').write_text(json.dumps(info,indent=2)+'\n')
print(json.dumps(info,indent=2))
