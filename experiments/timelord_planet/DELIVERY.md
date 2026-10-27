# Magrathea

*Custom-made luxury planet building.*

Give the recipient `timelord_planet.py` and `seed_planet.txt`. Run:

```sh
python3 timelord_planet.py
```

Requires CPython 3.9+ with its standard `random` and `gzip` modules, and a browser
with WebGL 1, high-precision fragment floats and standard derivatives. No Python
packages or runtime network access are needed. Python reconstructs compressed
binary bytes from the integer, decompresses the complete HTML and opens it.
The browser no longer needs DecompressionStream or a base64 unpacking wrapper.

Leave the mouse and trackpad untouched to watch the film. The camera holds A
for five seconds, reveals the globe, visits B and returns to exactly the same
ground view at 40 seconds. Clouds are active throughout, with visible formation/dissipation and latitude-dependent
trade-wind, westerly and polar flow bands. These are a visual approximation.
A fixed sun lights the ground and clouds; the orbit reveals a genuine night side.
After a three-second returned-A hold, the camera zooms out and smoothly enters
an ongoing steady orbit. It does not restart the film automatically.

Drag to rotate or scroll to zoom: these pause only the automatic camera, while
weather keeps moving. Click the image and press **Space** to reset both the film
and weather to time zero. Other keys do not reset them.

```sh
python3 timelord_planet.py --no-open --output planet.html
```

The stripped ZIP contains only the same seed and a six-line launcher, with no
comments, checks, argument parsing or status output. Extract it, change into
its directory and run `python3 timelord_planet.py`; it writes `planet.html` there.
Both variants use the installed Python interpreter; neither bundles Python.

The complete transported frame is **2,275 bytes**: a 2,273-byte gzip stream plus
two-byte length. It recovers **4,784 bytes of executable HTML**. The physical
integer is **19,966 bits / 2,496 binary bytes**, or **4,995 bytes** as hexadecimal
text. Distribution ZIP sizes are separate measurements in `delivery.json`.

`seed_planet.txt` is the large **TimeLord transport seed**, reconstructing the
program. The planet's **world identity is uint32 1**, already encoded inside it.
`world.json` is optional integration metadata, not a runtime dependency.
The normal ZIP's README and world metadata can be omitted for a two-file delivery.

All bespoke terrain, clouds, shaders, camera choreography and integration hooks
are inside the compressed HTML. Python's generic reconstruction/decompression
launcher and standard gzip implementation are declared loading infrastructure,
measured separately. The browser supplies standard WebGL/DOM APIs. This is not
CPU/OS-only self-containment. The ground is bump-shaded on a sphere, clouds use
a thin shell, and detail is finite. Cross-GPU field/pixel identity is not claimed.

This version changes the transport format from uncompressed HTML to binary gzip:
use a matching seed and launcher from the same archive. Existing download URLs
are retained. The old version remains in TimeLord commit `31914fa`.

The repository's `experiments/timelord_planet/README.md` has the source, build
commands, exact measurements, tests, captures and a film-to-orbit video.
