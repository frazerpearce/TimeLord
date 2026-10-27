# Magrathea

*Custom-made luxury planet building.*

**Works, fits, and was actually run offline from its reconstructed TimeLord
integer seed.** The new complete frame is **2,275 bytes**, 217 below the
2,492-byte information limit. The ground is unchanged. Clouds move and evolve
through the original 40-second film, then the camera enters a sustained orbit.

## Run or deliver

From the repository root:

```sh
python3 timelord_planet.py
# Or reconstruct without opening a browser:
python3 timelord_planet.py --no-open --output planet.html
```

Download [Magrathea](artifacts/magrathea.zip) or the
[stripped two-file distribution](artifacts/magrathea-stripped.zip).
The normal archive includes [instructions](DELIVERY.md) and optional
[identity/view metadata](world.json). The stripped archive contains exactly the
same seed and a 287-byte, six-line Python launcher: no comments, checks,
argument parsing or status messages. Extract it, enter the extracted directory,
and run `python3 timelord_planet.py`; it writes `planet.html` and opens it.

The normal script finds `seed_planet.txt` beside itself. The stripped script
reads it in the current directory. Both require CPython 3.9+ and a compatible
browser, with no installed Python packages or runtime network access.
The Python interpreter itself has not been bundled or stripped.

Existing `timelord_planet.py`, `seed_planet.txt` and `timelord-planet.zip` public
paths remain supported. Download the seed and launcher together: this version
uses binary gzip transport, whereas the earlier loader expected direct HTML.
The original version is preserved in TimeLord commit `31914fa`, and a development
snapshot was saved separately before editing. The heads/text demos and the
Bootstrap compiler experiments have not been changed.

Open the [recovered executable document](artifacts/planet.html), inspect
[A](artifacts/A.png), [globe](artifacts/globe.png), [B](artifacts/B.png),
[returned A with later weather](artifacts/A-return.png),
[steady orbit](artifacts/orbit.png), or watch the
[130-second film-to-orbit capture](artifacts/loop.mp4).

## Camera and weather timeline

| Seconds | Automatic camera |
|---|---|
| 0–5 | Hold A |
| 5–10 | Zoom out |
| 10–15 | Rotate to B |
| 15–20 | Zoom in |
| 20–25 | Hold B |
| 25–30 | Zoom out |
| 30–35 | Rotate back to A |
| 35–40 | Zoom in to precisely the original A camera |
| 40–43 | Hold the returned landscape |
| 43–48 | Zoom out to the globe |
| 48–52 | Smoothly accelerate the orbital camera |
| 52 onward | Steady orbit at .08 radians/s, about 78.54 s/revolution |

A stays at `(longitude=.4, latitude=.3)` and B at `(2.2,-.45)` radians, roughly
109 degrees apart. Both local views have orthographic half-height `z=.025` in
planet radii. Globe half-height is 1.2. The coordinates and world seed were never
searched or moved for visual attractiveness.

The camera is evaluated from absolute elapsed time, not integrated or wrapped
back to zero after the film. Motion uses quintic smootherstep. Orbital position
uses its analytic integral over a four-second speed ramp, so velocity enters
and leaves the ramp continuously. Latitude and apparent globe size stay fixed
in steady orbit. The unit sphere and its geography never rotate in local space;
only the viewpoint changes.

Drag or wheel zoom pauses the **camera**, while cloud time keeps advancing.
**Space** resets the film and weather clock to zero, retaining the selected
world identity. Other keys have no effect. Resizing changes pixel sampling.
There is no separate touch-pinch handler or on-screen interface.

## Terrain and clouds

`src/planet.js` separates setup, noise/terrain, cloud field, shading, timeline
and integration. The terrain's three functions (`H`, `N`, `terrain`) are
byte-for-byte identical to the previous generator. `baseline.json` records
hashes checked by `verify.py`. Large-scale domain-warped 3D value noise plus
13 octaves gives persistent continents, oceans, uplands, ridges and valleys.
This is an artistic fractal field, not an erosion, hydrology or tectonics model.

Ground geometry remains a unit sphere with differential bump shading from that
same filtered terrain field. It is not displaced geometry or a flight simulator.
No field depends on camera traversal, and terrain has no time argument.

Weather is a separate, domain-separated 3D field selected by the world seed,
using eight smoothly filtered octaves. Clouds now visibly form and dissipate:
two overlapping generations are smoothly blended, with a new generation every
12 seconds and a spatially varying phase to avoid synchronized global pulsing.
Each generation samples a distinct deterministic noise domain. Continuous
sampling-slice drift adds deformation within a generation. The old field exactly
matches the next generation's previous field at handoff; zero blend derivatives
prevent popping. Cloud ages are bounded to 24 seconds, avoiding indefinitely
stretched streaks under differential winds.

Wind depends on `y=sin(latitude)` through
`wind(y)=.018*(-1+6*y*y-6*y*y*y*y)` radians/s. Backward advection uses the opposite
angle for lookup, so actual flow is westward near the equator, eastward at middle
latitudes and westward near the poles. Sign changes occur at approximately 27.4
and 62.6 degrees in both hemispheres. Tangential motion naturally vanishes at
the poles. These are qualitative trades/westerlies/polar-easterlies bands, not
a numerical integration of Coriolis forces or a physical atmosphere model.
The [24-second fixed-view weather clip](artifacts/weather.mp4) makes formation
and dissipation visible separately from camera motion.

All weather is a pure function of local position, seed, filter footprint and
absolute time; no stateful random draws occur while running.

Clouds are sampled at orthographic intersections with a shell of radius 1.012,
creating parallax relative to the ground. Opacity is capped at .5, allowing the
ground to remain visible even under cloud banks. Filtered cloud height also
provides differential cloud-top lighting. A displaced sample of the same field
provides a compact approximate ground shadow. The cloud surface is thin and
bump-shaded: there is no volume, multiple scattering or volumetric ray marching.
Clear local views can occur naturally. The cloud renderer is active from the
first image and never switches off at camera transitions.


Lighting uses one fixed planet-local sun direction, `normalize([1,-.1,.3])`.
Ground and cloud bump normals are rotated into planet coordinates before lighting;
the cloud-shadow lookup uses this same direction. A terminator mask prevents
back-facing bumps or clouds from glowing on the night side. Ambient illumination
is 1.8%, and the atmospheric rim fades with sunlight. The camera can orbit into
night without dragging the light along. The planet itself is not spinning, so a
fixed ground location has constant solar illumination apart from cloud shadows.

Both fields use Cartesian sphere coordinates, with no longitude texture seam
or pole singularity. All derivative calculations run outside divergent masks.
Ground and cloud masks are applied after derivative evaluation.

`draw(t)` supplies the same absolute `t` to the camera and weather. Returning to
A reproduces the **ground and camera**, not the complete weather composite.
The cloud clock remains continuous at 40, 43, 48 and 52 seconds. On the tested
Chromium backend the initial/returned ground-only RGBA hash is identical. It
differs from the previous release because illumination has changed:

```text
52410181989a097e10c9ecaf14c492c1b0d500d2f92f04dc48fc6fedc78a4d1e
```

## Scale and numerical limits

The film retains a 48x magnification reveal (`1.2/.025`). Exploration retains
`.006 <= z <= 1.5`, with a tested local-to-globe range of 200x (`1.2/.006`).
At 960×640 the vertical span is `2*z` radii, or .05 at the film's local view.
A vertical pixel spans 7.8125e-5 radii there, and 1.875e-5 at maximum zoom.
No physical radius/metres-per-pixel is specified.

Terrain has frequency ratio 2.03, amplitude ratio .55, and a finest nominal
lattice frequency `2.7*2.03^12`, about 13,223 per radius before warp stretch.
Its filter is `1-smoothstep(.3,1,f*z/height*10.8)`. Clouds have frequency ratio
2.03, amplitude ratio .5 and filter `1-smoothstep(.3,1,f*z/height*32)` for their
base frequency 8. These are smooth center-footprint estimates; they do not
provide a complete anisotropic/Jacobian filter at the limb. Residual limb and
derivative-quad artifacts are possible. There is finite detail, not infinite
zoom. Very long runtimes eventually lose GPU float clock/angle precision.

Across eight predetermined probes, terrain differs by at most .011277 height
units between globe and ordinary local filtering. Additional detail exposed
from `.025` to `.006` changes these probes by up to .0003052. Tiny coastlines,
cloud density and lighting can vary as filtered detail appears. Stored textures,
terrain maps, frame sequences and traversal-dependent caches are absent.

GLSL floating-point noise hashing uses `sin`; different graphics implementations
can change the fields as well as rendered pixels. Pure world/weather evaluation
is repeatable at the same seed, coordinate, time, filter and backend. Neither
field nor pixel bit identity across GPUs is promised. Fixed-width identity
and address derivation are independent of these floating-point variations.

## Binary transport and host contract

The complete minified HTML is gzip-compressed directly. The seed reproduces:

```text
two-byte little-endian compressed length | gzip bytes
```

The generic Python loader instantiates actual `random.Random(integer_seed)`,
then calls `getrandbits(8)` successively for the entire frame. Python's standard
`gzip.decompress` recovers HTML, which is written and opened. There is no
`setstate`, substituted PRNG, application algorithm in the launcher, base64
encoding, or browser unpacking program.

**Explicit new loading contract:** CPython, its `random` implementation and
standard-library gzip/DEFLATE decoder are declared loading infrastructure.
Generic reconstruction/decompression/writing/launching code is measured
separately, outside the application-information frame. All bespoke terrain,
weather, rendering, controls, camera constants and integration code are inside
the compressed HTML. This differs from the old direct-HTML loader contract;
it is not a claim of CPU/OS-only self-containment.

The running HTML needs a browser with WebGL 1, fragment `highp`,
`OES_standard_derivatives` and standard DOM/JavaScript APIs. It no longer requires
DecompressionStream, Blob/Response streams or base64 decoding. Browser, driver,
OS and hardware are host infrastructure, not transported implementations.
No graphics assets, libraries or network calls are needed.

## Exact accounting

| Measurement | Bytes |
|---|---:|
| Readable JavaScript, comments included | 6,037 |
| Raw HTML with readable JavaScript | 6,060 |
| Minified JavaScript/shaders | 4,761 |
| Complete executable minified HTML | 4,784 |
| Binary gzip stream, including header/trailer | 2,273 |
| Length framing | 2 |
| **Complete transported frame** | **2,275** |
| **Room remaining under 2,492** | **217** |
| Minimal generic reconstruction loader | 373 |
| Normal launcher | 2,257 |
| Stripped launcher | 287 |
| Physical integer binary storage | 2,496 |
| Physical integer hexadecimal text file | 4,995 |

The seed has **19,966 bits**. `artifacts/sizes.json` contains authoritative
machine-readable values and hashes. Distribution ZIP sizes/hashes are recorded
separately in `artifacts/delivery.json`; they are not claimed to fit in the seed.
`frame.bin` and `planet.html.gz` are the actual transported frame and gzip body.

The old package used 1,722 gzip bytes expanded into 2,296 base64 bytes, plus a
165-byte HTML browser unpacker and two-byte frame: **2,463 bytes**. Repacking
that unchanged old scene as binary-compressed complete HTML measured **1,740**
framed bytes, freeing 723 bytes. The current weather, latitude winds, fixed-sun lighting, orbital
transition and Space-only restart add 535 compressed bytes, yielding **2,275**.
This is 188 bytes smaller than the original delivery, and 225 bytes larger than
the preceding 2,050-byte cloud/orbit version (commit `90dc33b`). No minimum-size
claim is made.

## Identity and integration

`planet(worldSeed, longitude=.4, latitude=.3, z=.025)` installs a world/view and
pauses the automatic camera. Identity uses JavaScript `>>>0`, unsigned uint32;
interchange integer values in `0..4294967295`. Low/high 16-bit halves reach the
shader separately. The default world identity is 1. This is distinct from the
large TimeLord transport seed reconstructing the application. Neither the noise
mapping nor the address hash is claimed collision-free or cryptographic.

Camera state is `[longitude,latitude,z]`, with radians, no roll and orthographic
half-height in planet radii. Center is
`[sin(longitude)*cos(latitude),sin(latitude),cos(longitude)*cos(latitude)]`.
Preserve world identity, view, generator version and elapsed weather time to
restore a full scene; just identity/view suffices to restore the ground.
For explicit testing/parent rendering, `draw(t)` renders at supplied seconds and
returns the view; `camera(t)` exposes the timeline. Calling `planet` does not
reset the application clock. A future parent may install
`parentPlanet(seed,longitude,latitude,z)`; wheel zoom reaching `z=1.5` invokes it.
There is no parent renderer or integration framework hidden outside the payload.

For future hierarchical addressing, `address.py` defines each edge as FNV-1a-32
of `uint32_le(parentSeed) || ASCII(kind) || uint32_le(childID)`, where kind is
`G`, `S` or `P`. Initial value is 2166136261; each byte updates
`h=((h XOR byte)*16777619) mod 2^32`. Universe seed 1, galaxy ID 2, star ID 3,
planet ID 4 gives `2870994987 -> 2462232634 -> 2638447889`. Keep the hierarchy tuple
and generator version as the complete address. This optional parent reference
is not read by the packed planet. Use hierarchical parent coordinates and local
planet coordinates, never universe and surface detail in one float position.

## Rebuild, test and capture

Only the Python standard library and the included MIT-licensed TimeLord inverter
are required to build and package. Tested with CPython 3.13.9.

```sh
python3 experiments/timelord_planet/build.py
python3 experiments/timelord_planet/package.py
python3 experiments/timelord_planet/verify.py
python3 experiments/timelord_planet/test_delivery.py -v
python3 -m unittest discover -s tests -v
```

`verify.py` requires byte-identical rebuilds, checks preserved terrain source,
actual CPython output, framing/size, exact decompression and isolated minimal,
normal and stripped loaders. Browser verification requires Node/Playwright:

```sh
npm install --no-save playwright
npx playwright install chromium webkit
cd experiments/timelord_planet
PLANET_NODE=$(command -v node)
python3 verify.py --browser "$PLANET_NODE"
python3 verify.py --browser "$PLANET_NODE" --webkit
```

Or set `PLAYWRIGHT_MODULE` to an existing module directory and
`PLAYWRIGHT_BROWSERS_PATH` to its browser cache. macOS may require ordinary
Terminal execution where a sandbox blocks browser initialization.

The browser checks load only recovered recipient HTML. They verify exact
camera/ground-only frame endpoints, changing composites, seeded field purity,
cloud evolution beyond rigid advection, spatial/time continuity, seam/poles,
coarse/fine stability, six seeds, eight fixed locations, exact view restoration,
controls, continuous weather time, smooth generation handoffs, latitude wind signs and
hemisphere symmetry, day/night brightness under the fixed sun, smooth orbit
acceleration, sustained angular speed and fixed globe size. Both normal and stripped recovered documents are
opened. Diagnostic ground shaders remove only the transported cloud/shadow
compositing block; diagnostic field shaders reuse actual transported field code.
No missing application algorithms come from the verifier.

Chromium runs with its network offline. WebKit on this host rejects local-file
navigation with its offline switch; its HTTP(S) routes are instead aborted.
Both checks require no requests beyond the recovered local HTML. Reports identify
this distinction, backend, hashes, numerical samples, timing and any errors.
The script's actual requestAnimationFrame callback is also exercised.

To capture the film, a complete day/night orbit and a fixed-view weather clip:

```sh
python3 verify.py --browser "$PLANET_NODE" --video
ffmpeg -y -framerate 12 -i artifacts/frames/%04d.png \
  -c:v libx264 -crf 20 -pix_fmt yuv420p -movflags +faststart artifacts/loop.mp4
ffmpeg -y -framerate 12 -i artifacts/weather-frames/%04d.png \
  -c:v libx264 -crf 20 -pix_fmt yuv420p -movflags +faststart artifacts/weather.mp4
```

The delivered video lasts 130 seconds at 960×640; the interactive version uses
browser animation frames. Capture PNGs can be deleted after encoding. The video
and snapshots are outputs only, never runtime inputs. Browser and video tools
are development dependencies, not application assets.
