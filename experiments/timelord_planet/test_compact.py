"""Check the new end-marked standard LZMA transport and its recipient error path."""
import importlib.util
import lzma
import tempfile
import unittest
from pathlib import Path
from binary_transport import construct_binary_seed

ROOT=Path(__file__).resolve().parent


class CompactTransportTests(unittest.TestCase):
    def test_end_marker_needs_the_complete_seeded_stream(self):
        filters=[dict(id=lzma.FILTER_LZMA1,dict_size=8192,lc=2,lp=0,pb=0)]
        data=(ROOT/'artifacts/planet.html.lzma').read_bytes()
        decoder=lzma.LZMADecompressor(format=lzma.FORMAT_RAW,filters=filters)
        first=decoder.decompress(data[:-1])
        self.assertFalse(decoder.eof)
        last=decoder.decompress(data[-1:])
        self.assertTrue(decoder.eof)
        self.assertEqual(decoder.unused_data,b'')
        self.assertEqual(first+last,(ROOT/'artifacts/planet.html').read_bytes())

    def test_invalid_seeded_compression_is_rejected(self):
        spec=importlib.util.spec_from_file_location('recipient',ROOT.parents[1]/'timelord_planet.py')
        recipient=importlib.util.module_from_spec(spec);spec.loader.exec_module(recipient)
        # A raw LZMA1 stream must start with zero; FF cannot be a valid stream.
        seed,_,_=construct_binary_seed(b'\xff')
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'bad.seed';path.write_text(hex(seed))
            with self.assertRaises(lzma.LZMAError):recipient.reconstruct(path)


if __name__=='__main__':unittest.main()
