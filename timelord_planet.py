#!/usr/bin/env python3
"""Magrathea: recover a complete offline planet from a TimeLord integer.

This generic loader supplies gzip decompression, but no graphics, terrain or camera code.
Deliver this script with seed_planet.txt; all application logic is in the seed.
"""
import argparse
import hashlib
import gzip
from pathlib import Path
import random
import tempfile
import webbrowser


def reconstruct(seed_path):
    """Decode the binary frame and decompress its complete HTML document."""
    seed = int(Path(seed_path).read_text(encoding="ascii").strip(), 0)
    if seed < 0:
        raise ValueError("expected a nonnegative integer seed")
    rng = random.Random(seed)
    length = rng.getrandbits(8) | (rng.getrandbits(8) << 8)
    if not 0 < length <= 2490:
        raise ValueError("invalid TimeLord binary frame length")
    return gzip.decompress(bytes(rng.getrandbits(8) for _ in range(length)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("seed", nargs="?", type=Path,
                        default=Path(__file__).resolve().with_name("seed_planet.txt"),
                        help="hexadecimal transport seed (default: beside this script)")
    parser.add_argument("--output", type=Path, help="path for the recovered HTML")
    parser.add_argument("--no-open", action="store_true", help="write without opening a browser")
    args = parser.parse_args()
    try:
        document = reconstruct(args.seed)
    except (OSError, ValueError, EOFError) as error:
        parser.error(str(error))
    output = args.output or Path(tempfile.mkdtemp(prefix="timelord-planet-")) / "planet.html"
    output = output.expanduser().resolve()
    output.write_bytes(document)
    print("Recovered: {} ({} HTML bytes)".format(output, len(document)))
    print("SHA-256: " + hashlib.sha256(document).hexdigest())
    print("The opening view holds for 5 seconds. Leave the trackpad/mouse untouched.")
    print("After the film, the camera orbits. Drag/scroll pauses the camera; Space resets film and weather.")
    if not args.no_open and not webbrowser.open(output.as_uri()):
        print("Open this file in a WebGL browser: " + output.as_uri())
    return output


if __name__ == "__main__":
    main()
