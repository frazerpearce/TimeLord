# Magrathea

*Custom-made luxury planet building.*

Magrathea is the procedural planet-building strand of TimeLord. Its complete
transported frame remains 2,463 bytes.

**The demo works, fits, and was actually run from its reconstructed TimeLord
integer seed.** The complete binary frame is **2,463 bytes**, 29 below the
2,492-byte payload-information limit. It recovers a self-contained **2,461-byte
HTML document**. The physical integer is **19,966 bits / 2,496 binary bytes**;
its hexadecimal text file occupies **4,995 bytes**. These are different measures.
This is procedural packing and rendering, with no compiler bootstrapping.
The original heads/text demos are unchanged. Development also preserved the
separate Bootstrap workspace's compiler experiments.

## Recipient delivery

The existing `timelord_planet.py`, `seed_planet.txt` and `timelord-planet.zip`
filenames remain supported for compatibility with previously shared links. The
primary delivery archive is now `magrathea.zip`. TimeLord names the seed transport;
Magrathea names the planet-building project.

From the repository root, run `python3 timelord_planet.py`. The default transport
seed is `seed_planet.txt`, beside that script. Give recipients just these two
files, or [download the standalone ZIP](artifacts/magrathea.zip).
The archive includes a short [delivery guide](DELIVERY.md) and optional
[world identity metadata](world.json). The initial world identity is uint32 `1`;
this is separate from the large integer that reconstructs the program.

The launcher prints the opening-hold and pause/resume instructions. Safari
26.6.2 was confirmed working by the recipient. An additional WebKit 26.5 check
verified automatic zoom and Space-to-resume behavior without shader or script
errors. The full automated rendering suite below remains a Chromium check.

Repackage and test the recipient bundle with:

```sh
python3 experiments/timelord_planet/package.py
python3 experiments/timelord_planet/test_delivery.py -v
```

Open [the executable document](artifacts/planet.html) in a browser, or watch
[the complete 40-second loop](artifacts/loop.mp4). Representative views:
[A](artifacts/A.png), [globe](artifacts/globe.png), [B](artifacts/B.png),
[returned A](artifacts/A-return.png).

## Run from the integer

```sh
cd /path/to/TimeLord/experiments/timelord_planet
mkdir -p /tmp/planet-clean
cp load_seed.py artifacts/seed.hex /tmp/planet-clean/
cd /tmp/planet-clean
python3 -I -S load_seed.py seed.hex planet.html
open planet.html
```

The fixed **344-byte** loader uses actual CPython `random.Random(integer)` and
successive `getrandbits(8)` calls. The first two output bytes encode the following
HTML length, little endian. No `setstate`, custom PRNG, decompression or scene
logic is in the loader. The integer file is a hexadecimal integer, not an
instruction stream or precomputed terrain. Once reconstructed, only the HTML
is needed to run; neither Python nor the loader participates in rendering.

**Declared execution host:** a browser with WebGL 1, fragment `highp` floats,
`OES_standard_derivatives`, standard DOM/JavaScript/typed arrays, Blob/Response
streams, and `DecompressionStream('gzip')`, plus its graphics implementation.
The HTML contains the base64 conversion and streaming decompression invocation.
The standard browser gzip implementation itself is declared host infrastructure.
This is not a CPU/OS-only self-contained implementation. No external viewer,
library, shader, downloaded asset or server supplies any planet algorithm.
No network access is required. A local static HTTP server is optional when a
browser restricts local files; it serves exactly the same document.

Tested on macOS ARM64, Chromium **151.0.7922.34**, ANGLE Vulkan SwiftShader.
The test browser was downloaded as a development tool; it is not a runtime asset.
No browser dependency installation or asset download occurs when opening the demo.
Other browsers meeting the feature contract have not been verified here; the recipient separately confirmed Safari 26.6.2.

Drag with a mouse button to rotate; wheel/trackpad scroll changes magnification.
Any key resumes the loop from A, retaining the selected world seed. There are no
on-screen controls, text, touch-pinch handler, or loading assets. Each five-second
hold is intentionally still. Resizing changes the pixel sampling resolution.

## World and camera

`src/planet.js` is the readable development source, with separate sections for
host setup, local noise/terrain, shading, camera choreography and integration.
`build.py` strips comments/whitespace conservatively, gzips the complete program,
and writes its self-unpacking HTML. No external minifier is needed.

Terrain is a continuous, Cartesian 3D value-noise field evaluated on the unit
sphere, with a low-frequency three-component domain warp and **13 hierarchical
octaves**. Large structures remain in every evaluation as smaller amplitudes are
added. The octave frequency ratio is 2.03; amplitude ratio is .55. Coarse height
selects oceans, continental land, uplands and snow-colored peaks. Fine variations
produce connected ridges and valleys; this is an artistic fractal surface, not
a simulation of erosion, tectonics, hydrology or physical geology. The same
Cartesian function works at both poles, with no longitude texture seam.

**Geometry is a sphere, not displaced terrain.** An orthographic ray intersects
that sphere; terrain changes its color and differential bump normal. The normal
comes from screen derivatives of the same filtered height field, with exaggerated
relief, and camera-relative illumination. The spherical silhouette remains fixed.
Local views are overhead terrain images, not a horizon-level flight simulator.
No images, maps, terrain meshes or cached traversal-dependent samples are stored.

Camera state is `[longitude, latitude, z]`, with angles in radians, no roll, and
orthographic half-height `z` in planet radii. View-space rays map to planet-local
coordinates by the shader's explicit rotation matrix. The center point is
`[sin(longitude)*cos(latitude), sin(latitude), cos(longitude)*cos(latitude)]`.
The horizontal span is the vertical span times the viewport aspect ratio.

A is fixed at `(0.4, 0.3)` and B at `(2.2, -0.45)` radians, both at `z=.025`.
They were selected as ordinary coordinates before the first render, without
searching terrain or seeds. Their great-circle separation is approximately
109 degrees. Seed 1 is the default. The field and shading were improved at these
fixed coordinates; the locations were never moved to find prettier outputs.

| Seconds | Action |
|---|---|
| 0–5 | Hold A |
| 5–10 | Zoom out from .025 to 1.2 |
| 10–15 | Rotate A to B |
| 15–20 | Zoom in to .025 |
| 20–25 | Hold B |
| 25–30 | Zoom out |
| 30–35 | Rotate B to A |
| 35–40 | Zoom in to the original state |

Motion uses quintic smootherstep, with zero first and second derivatives at
endpoints. Time is reduced modulo 40; the camera never integrates velocity or
accumulates rotations. Both `camera(0)` and `camera(40)` explicitly return
`[.4,.3,.025]`. The loop is continuous at its wrap, followed by the A hold.

## Scale range and limits

The automatic reveal covers **48× linear magnification** (`1.2 / .025`).
Exploration is clamped to `.006 <= z <= 1.5`; the tested local-to-globe range
`.006 .. 1.2` is **200×**. At 960×640, the local vertical field of view is .05
planet radii at the automatic locations, or .012 at maximum magnification.
One vertical pixel spans `2*z/640` radii: **7.8125e-5** at .025 and
**1.875e-5** at .006. These are dimensionless measurements; no physical radius
or metres-per-pixel claim is encoded.

The finest nominal lattice frequency is `2.7 * 2.03^12`, approximately
13,223 cycles per radius before domain-warp stretch. This is finite detail,
not an infinite terrain. Each octave is smoothly attenuated by its projected
frequency: `1-smoothstep(.3,1,frequency*z/height*10.8)`.
The conservative cutoff fades fine octaves before approximately two screen pixels
per lattice interval, retaining every coarser octave. At the globe limb,
orthographic foreshortening is greater than this center-based estimate; residual
limb aliasing is possible. The small frame does not implement anisotropic filtering,
a full Jacobian-based footprint, multisample terrain shading or high-quality
self-shadowing. Fine relief can show derivative-quad artifacts at extreme zoom.

Large-scale fields remain stable while fine detail appears: eight predetermined
GPU field probes differ by at most **0.011277 height units** between globe and
ordinary local filtering. Going from `.025` to `.006` exposes additional field
variation, up to **0.0003052** at these probes. Tests measure field values, rather
than equating rescaled screenshot pixels. Tiny coastlines and bump shading can
change as filtered high frequencies appear; geography is not perfectly invariant
under filtering. Finer zoom than .006 is outside the supported exploration range.

Float noise hashing uses GLSL `sin`; cross-GPU arithmetic and transcendental
implementations can perturb the field as well as lighting. World evaluation is
pure and repeatable for a given seed, coordinate, filter and backend, independently
of traversal. Cross-GPU field bit identity or pixel identity is **not** promised.
Identity/address derivation below is fixed-width integer arithmetic, independent
of these rendering differences.

## Integration with future universe and galaxy payloads

The transported callable entry point is:

```js
planet(worldSeed, longitude = .4, latitude = .3, z = .025)
```

`worldSeed` follows JavaScript `>>>0`: an unsigned 32-bit integer, modulo 2^32.
Pass integer values in `0..4294967295` for language-independent interchange.
The shader receives low/high 16-bit halves, so high identity bits participate
without first losing them to a single 32-bit float conversion. The noise mapping
is not a collision-free or cryptographic mapping of all possible planet seeds.
The **world seed** selects terrain; the much larger **TimeLord transport seed**
recovers the entire program. They have different purposes and representations.

Calling `planet` installs that world and camera and pauses automation. Preserve
`{worldSeed, longitude, latitude, z}` to leave and restore the same view. At an
identical viewport/backend, this reproduces identical pixels. `draw(t)` returns
the installed view and renders it. Any key resets the automatic choreography;
`camera(t)` exposes its explicit state for inspection. These globals are the
small integration boundary, not a framework.

A parent may install `window.parentPlanet = (seed, longitude, latitude, z) => ...`.
A wheel zoom reaching the exploration limit `z=1.5` invokes that callback. The
parent decides whether to hide/dispose the child canvas and restore its own
scene. No parent renderer, world-position system or message bus is transported.
The entry point does not allocate additional renderers when changing worlds.

For future hierarchical addresses, use the reference in `address.py`:

1. Serialize `parentSeed` as four unsigned little-endian bytes.
2. Append one ASCII type byte: `G`, `S` or `P`.
3. Append the child's unsigned 32-bit ID as four little-endian bytes.
4. FNV-1a-32: start at 2166136261; for each byte set
   `h = ((h XOR byte) * 16777619) modulo 2^32`.

Starting at universe seed 1 with galaxy ID 2, star ID 3 and planet ID 4 yields
`2870994987 -> 2462232634 -> 2638447889`. Hash collisions are possible; a full
address remains the hierarchy tuple and generator version, not just its 32-bit
projection. No language-dependent `hash()` is used. `address.py` is an optional
reference for future parent modules; the packed planet never imports or needs it.

Keep parent positions in parent-local coordinates with hierarchical integer
addresses. Pass only a planet identity and dimensionless local camera into this
payload. Future orbital positions belong in the parent transform. This avoids
mixing universe distances and local detail in one floating-point position.
Persist the generator version alongside seed/view if exact restoration must
survive changes to the generator.

## Exact size accounting

| Component | Bytes |
|---|---:|
| Readable source, including comments | 3,905 |
| Whitespace-minified complete JavaScript/shaders | 3,320 |
| Gzip stream | 1,722 |
| Same stream as base64 | 2,296 |
| Complete HTML and decompression invocation around base64 | 165 |
| **Executable HTML payload** | **2,461** |
| TimeLord little-endian length framing | 2 |
| **Complete transported frame** | **2,463** |
| Physical integer binary storage | 2,496 |
| Hex integer file, including prefix/newline | 4,995 |
| External generic loader source | 344 |

The gzip stream includes its headers/trailer. The 165-byte wrapper includes all
bespoke decoding and execution code. The loader is the explicitly excluded,
generic seed-to-file infrastructure; it contributes no planet code. Browser,
CPython loading environment, OS and graphics/decompression implementations are
host infrastructure, not transported implementations. `frame.bin`, the HTML,
gzip stream and `sizes.json` preserve exact byte measurements. Build tools and
test instrumentation are not part of application execution.

The first complete version measured 2,503 framed bytes. Removing a redundant
URL-query interface, preserving callable identity/view hooks, and changing
shading/filtering produced the final 2,463 bytes. No return leg, sphere topology,
identity hook or octave hierarchy was removed to fit. No global minimum is claimed.

## Rebuild and verify

Build and transport checks use only Python's standard library and the included
binary adapter/unmodified vendored TimeLord inverter (with its MIT license). Tested with CPython 3.13.9.

```sh
cd /path/to/TimeLord/experiments/timelord_planet
python3 build.py
python3 verify.py
```

`verify.py` first rebuilds and requires identical HTML and transport seed. It
checks actual CPython integer seeding, the exact frame, gzip round-trip, the size
limit, physical seed size and the isolated `-I -S` loader in a temporary directory.
The temporary directory contains only loader, seed and recovered HTML.

Browser tests require Node and Playwright with its matching Chromium installation.
For a standard Node installation, from the repository root:

```sh
npm install --no-save playwright
npx playwright install chromium
cd experiments/timelord_planet
PLANET_NODE=$(command -v node)
python3 verify.py --browser "$PLANET_NODE"
```

Alternatively set `PLAYWRIGHT_MODULE` to the absolute path of an existing
Playwright module and `PLAYWRIGHT_BROWSERS_PATH` to its installed browsers.
Browser tests may need normal Terminal execution where macOS sandboxing blocks
Chromium's process initialization.

Browser checks run with networking offline and accept only the one recovered HTML
request. They verify shader compilation, explicit camera/frame equality at 0/40,
holds and near-zero endpoint velocity, exact leave/return restoration, controls,
six world seeds, field traversal independence, seam/poles, local continuity,
coarse/fine scale stability and eight predetermined render locations. GPU field
probes extract the transported shader's actual terrain function, replacing only
its output stage for observation. This code is test instrumentation and is never
loaded by the executable document.

`browser-verification.json` records exact initial/final RGBA SHA-256, sample
values, browser/backend identity, states and timings. On this backend a native
application animation callback ran at approximately 60 callbacks/s during a
1.5-second hold check. The report separately measures 60 moving-view draws with
synchronous pixel readback; performance is machine/backend-dependent.

To capture the entire loop again from a fresh reconstruction:

```sh
python3 verify.py --browser "$PLANET_NODE" --video
ffmpeg -y -framerate 12 -i artifacts/frames/%04d.png \
  -c:v libx264 -crf 20 -pix_fmt yuv420p -movflags +faststart artifacts/loop.mp4
```

The video is a 40-second, 960×640 capture sampled at 12fps, world seed 1; the
interactive demo renders on browser animation frames. No frame sequence is used
by the demo. Intermediate capture PNGs may be deleted after encoding. Browser
and video tools are verification dependencies only. The delivered captured views
and video are outputs, not inputs to the planet payload.
