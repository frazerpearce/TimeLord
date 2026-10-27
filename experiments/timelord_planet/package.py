"""Build the small standalone recipient bundle, with deterministic ZIP metadata."""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
output = ROOT / 'artifacts/magrathea.zip'
files = {
    'timelord_planet.py': REPO / 'timelord_planet.py',
    'seed_planet.txt': REPO / 'seed_planet.txt',
    'README.md': ROOT / 'DELIVERY.md',
    'world.json': ROOT / 'world.json',
}
assert files['seed_planet.txt'].read_bytes() == (ROOT / 'artifacts/seed.hex').read_bytes()
def pack(destination, members):
    with zipfile.ZipFile(destination, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, source in members.items():
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 26, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, source.read_bytes())

pack(output, files)
stripped = ROOT / 'artifacts/magrathea-stripped.zip'
stripped_files = {
    'timelord_planet.py': ROOT / 'stripped/timelord_planet.py',
    'seed_planet.txt': REPO / 'seed_planet.txt',
}
pack(stripped, stripped_files)
# Keep the original public download URL working.
(ROOT / 'artifacts/timelord-planet.zip').write_bytes(output.read_bytes())
manifest = {
    'archive': output.name,
    'compatibility_archive': 'timelord-planet.zip',
    'archive_bytes': output.stat().st_size,
    'archive_sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
    'stripped': {
        'archive': stripped.name,
        'archive_bytes': stripped.stat().st_size,
        'launcher_bytes': stripped_files['timelord_planet.py'].stat().st_size,
        'archive_sha256': hashlib.sha256(stripped.read_bytes()).hexdigest(),
        'files': {name: hashlib.sha256(source.read_bytes()).hexdigest() for name, source in stripped_files.items()},
    },
    'files': {name: hashlib.sha256(source.read_bytes()).hexdigest() for name, source in files.items()},
}
(ROOT / 'artifacts/delivery.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps(manifest, indent=2))
