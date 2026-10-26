# TimeLord planet

Give the recipient `timelord_planet.py` and `seed_planet.txt`. Run:

```sh
python3 timelord_planet.py
```

Requires CPython 3.9+ and a browser with WebGL, high-precision fragment floats,
standard derivatives and `DecompressionStream('gzip')`. No Python packages or
runtime network access are needed. The script reconstructs the complete HTML
from the integer seed, writes it into a temporary directory and opens it.

**Wait five seconds without touching the trackpad or mouse.** The opening image
is deliberately still, then zooms out into a globe. The whole loop takes 40
seconds and returns to the identical landscape. Dragging or scrolling pauses
it; click the image and press **Space** to restart. Safari 26.6.2 was confirmed
working by the recipient; automated checks use Chromium 151 and WebKit 26.5.

To recover the document without opening a browser:

```sh
python3 timelord_planet.py --no-open --output planet.html
```

An alternative transport seed may be passed as a positional path. The bundled
seed reconstructs 2,461 HTML bytes; with its two-byte length frame this is
**2,463 bytes**, within the **2,492-byte** information limit. Its physical integer
is 19,966 bits / 2,496 binary bytes (4,995 bytes as hexadecimal text).

There are two different seeds: `seed_planet.txt` is the large **TimeLord transport
seed**, reconstructing the program, while the generated planet's **world identity
is uint32 1**, already encoded in that program. `world.json` describes that
identity and initial view for future integration; the launcher does not read it.
The two-file delivery is sufficient. In a browser console, the transported
`planet(seed, longitude, latitude, z)` entry point installs another unsigned
32-bit world identity or restores a view. Any key resumes the automatic loop.

All terrain, rendering, shaders, camera choreography, identity/view hooks and
bespoke unpacking code are in the recovered HTML. The Python script is generic
seed-to-file infrastructure with browser launching, not an external renderer.
The browser supplies gzip decompression, WebGL and standard Web APIs. Terrain
is bump-shaded on a sphere; it has finite detail and no cross-GPU pixel-identity
guarantee. The automatic reveal covers 48x magnification, or 200x with exploration.

The repository's `experiments/timelord_planet/README.md` contains the readable
source, reproducible build instructions, exact accounting, automated verification
reports, representative views and a complete-loop video. The archive includes
this note and `world.json` as optional delivery metadata.
