# Magrathea compact

*Custom-made luxury planet building.*

Branch: `Magrathea_compact`. All features from main commit `d7aa3cd` are retained.
The complete transported program is **2,207 bytes**, down from **2,471**:
**264 bytes saved (10.68%)**, with **285 bytes free** under the 2,492-byte limit.
This is the best measured candidate, not a claim of a global minimum.

## Run or deliver

```sh
python3 timelord_planet.py
```

Give someone [the compact ZIP](artifacts/magrathea-compact.zip), or the
[stripped compact ZIP](artifacts/magrathea-compact-stripped.zip). The stripped
ZIP contains exactly `timelord_planet.py` and `seed_planet.txt`. Extract it,
enter the directory, and run the command above. It writes and opens `planet.html`.
The normal launcher finds the seed beside itself; the stripped launcher reads
it from the current directory.

Only standard CPython 3.9+ with its `random` and `lzma` modules is required.
No Python packages, custom codec, downloaded data, or runtime network access.
A WebGL browser supplies the same graphics and DOM facilities as before.
The interpreter is not bundled. Use the launcher and seed from the same ZIP:
this branch uses LZMA transport; main uses gzip.

```sh
python3 timelord_planet.py --no-open --output planet.html
```

Leave the mouse/trackpad untouched for the 40-second A/B/A film, returned-view
hold, globe reveal and continuing orbit. Drag or scroll to explore; the camera
pauses while weather and sunlight continue. Space resets the whole timeline.
Terrain, cloud evolution, latitude winds, ocean glint, twilight, moving sunlight
and independently timed night-side lightning are unchanged. Geography and the
returned camera are fixed; illumination advances with time. World identity is
still uint32 `1`, distinct from the large transport seed.

## What saves space

- Shorter internal GLSL and JavaScript identifiers, without renaming object
  properties or strings. Public `planet`, `camera`, `draw`, controls and parent
  integration remain available.
- Standard WebGL numeric enum values replace their longer symbolic names.
- Equivalent boolean expressions and shorter global assignments.
- Tuned **standard LZMA1** replaces gzip. Its end marker replaces the external
  two-byte length. Every rendered formula, constant and order of operations is
  retained in the unchanged readable [source](src/planet.js).

The readable source has not been golfed. [compact.py](compact.py) applies the
checked-in [configuration](compact-config.json) at build time. [optimize.py](optimize.py)
searches alternative identifier allocations and standard compression settings;
a normal rebuild does not repeat the search. The final search measured 20,782
candidates; earlier trials also compared gzip strategies, LZMA2, delta and BCJ
filters. See [measured comparisons](artifacts/compact-comparison.json).

The raw decoder uses `lzma.FORMAT_RAW` with `FILTER_LZMA1`, dictionary 8,192,
`lc=2`, `lp=0`, `pb=0`. Encoding uses normal mode, HC3, nice length 32 and search
depth 64. These are generic compression parameters, with no scene dictionary or
Magrathea algorithms hidden in the wrapper. Python supplies its standard decoder;
all bespoke graphics, terrain, clouds, controls and camera code remain in the seed.

The raw format has an end marker but no container checksum. The normal launcher
rejects malformed/oversized streams, caps consumption at 2,492 draws and prints
the recovered SHA-256. The stripped launcher intentionally omits checks/comments.
This is an offline demonstration, not a cryptographic transport.

## Actual byte accounting

| Measurement | Bytes |
|---|---:|
| Readable JavaScript, comments included | 6,855 |
| Minified JavaScript and shaders | 4,677 |
| Complete recovered HTML | 4,700 |
| Raw LZMA1 stream including its end marker | 2,207 |
| Additional framing | 0 |
| **Complete transported payload** | **2,207** |
| **Free capacity under 2,492** | **285** |
| Generic checked reconstruction script | 472 |
| Normal launcher | 2,444 |
| Stripped launcher | 377 |
| Physical transport seed binary storage | 2,496 |
| Transport seed as hexadecimal text | 4,994 |

The integer is **19,962 bits**. Payload savings make room for more encoded
program/data; they do not shrink the MT19937 transport integer to 2,207 bytes.
ZIP sizes are separate and recorded in [delivery.json](artifacts/delivery.json).
[frame.bin](artifacts/frame.bin) and [planet.html.lzma](artifacts/planet.html.lzma)
are identical: the complete raw stream, not an external asset reference.
[sizes.json](artifacts/sizes.json) contains the authoritative hashes and counts.

CPython's unmodified `random.Random(integer_seed)` and successive `getrandbits(8)`
recover the stream. The standard incremental LZMA decoder stops at its end marker;
there is no hard-coded application length, `setstate`, modified RNG, or payload
lookup. This is standard-library/browser self-containment, not CPU/OS-only.

## Reproduce and verify

```sh
python3 experiments/timelord_planet/build.py
python3 experiments/timelord_planet/package.py
python3 experiments/timelord_planet/verify.py
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s experiments/timelord_planet -p 'test_*.py' -v
```

`verify.py` rebuilds the same seed and bytes, checks the original terrain function
hashes, reconstructs using actual CPython outputs, and runs isolated minimal,
normal and stripped recipients with `-I -S` (no site packages).

With an existing Node/Playwright installation and local browsers:

```sh
python3 experiments/timelord_planet/verify.py --browser /path/to/node
python3 experiments/timelord_planet/verify.py --browser /path/to/node --webkit
```

The harness opens **only recovered recipient HTML**. Its existing checks cover
shaders, evolving clouds, local storm clocks, wind bands, sunlight, glint,
terrain continuity, camera choreography and controls. Diagnostic shaders restore
readable identifier names solely for observation; the production app remains
minified. It also recreates the original published HTML from unchanged source
and checks its SHA-256 before **32 exact comparisons per browser**: 12 film times,
18 renders across six world seeds, manual controls and reset. Production pixel
hashes and returned views must match exactly. No arithmetic simplifications or
lower precision are used. Cross-GPU pixel identity is not promised.

Chromium uses its network-offline mode; WebKit blocks HTTP(S) routes because
its offline switch rejects local files here. Both require only local HTML.
The original heads/text tests remain unchanged. Browser and transport reports
are in [artifacts](artifacts/verification-summary.json).

The [existing movie](artifacts/loop.mp4) and [weather clip](artifacts/weather.mp4)
were captured from the equivalent main program. Their original document hashes
remain recorded in [media.json](artifacts/media.json), alongside the compact
comparison references. The [historical report](IMPLEMENTATION.md) documents the
unchanged terrain/weather model, coordinate/address integration and numerical
limits; its old transport and size claims apply only to main at `d7aa3cd`.

Optional development search, using standard Python only:

```sh
python3 experiments/timelord_planet/optimize.py --output /tmp/compact-candidate.json
```

Search output is a candidate configuration, not a replacement delivery. Rebuild,
recheck exact image equivalence and regenerate the packages before publishing it.
