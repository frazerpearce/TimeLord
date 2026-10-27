# Magrathea compact

*Custom-made luxury planet building.*

This is the `Magrathea_compact` branch: the same planet and features in a smaller
standard-Python transport. Extract the ZIP, enter its directory and run:

```sh
python3 timelord_planet.py
```

Requires standard CPython 3.9+ with `random` and `lzma`, and a WebGL browser.
No Python packages, runtime downloads or network access are needed. The
interpreter is not bundled. Deliver `timelord_planet.py` with `seed_planet.txt`;
they must come from the same ZIP. This branch uses LZMA; main uses gzip.

The film holds A, reveals the globe, visits B and returns to the same geography
and camera at 40 seconds. Clouds evolve under latitude-dependent winds. Ocean
glint, twilight, slowly moving sunlight and independent local storm flashes on
the night side are included. After a three-second hold, the camera zooms out and
enters a continuing steady orbit. Drag/scroll pauses the camera; Space restarts
the film, weather and sunlight. Leave the controls untouched to watch.

The normal launcher can also write without opening the browser:

```sh
python3 timelord_planet.py --no-open --output planet.html
```

The stripped ZIP contains exactly the same seed and an eight-line, 377-byte
launcher, with no checks, comments or status output. It reads the seed from the
current directory and writes `planet.html` there.

The entire transported program is **2,207 bytes**, including the standard LZMA1
end marker and with no external framing: **264 bytes less** than main, leaving
**285 bytes free** under the 2,492-byte limit. It expands to **4,700 HTML bytes**.
The physical seed remains **19,962 bits / 2,496 binary bytes**, or **4,994 bytes**
as hexadecimal text. World identity remains uint32 `1`.

The standard incremental LZMA decoder uses raw LZMA1 with an 8,192-byte dictionary,
`lc=2`, `lp=0`, `pb=0`. No application code or scene data is in the wrapper; all
terrain, clouds, lighting and controls are transported. Raw LZMA has no container
checksum; the normal launcher reports the recovered document's SHA-256.
The original and compact programs pass 32 exact pixel/view comparisons in each
of Chromium and WebKit. Fields remain deterministic on a given backend; identical
pixels across different GPUs are not promised. The ground is bump-shaded on a
sphere, clouds use a thin shell, and detail is finite.

The repository's `experiments/timelord_planet/README.md` documents measurements,
reproduction, compression search, decoder assumptions and validation reports.
