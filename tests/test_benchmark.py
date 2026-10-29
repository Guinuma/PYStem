from pathlib import Path
import shutil
import struct
import tempfile
import unittest

from src.benchmark import audio_info, sha256, synthetic, verify_stems


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
class BenchmarkValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_reproducible_input_and_format_checks(self):
        a, b = self.root / "a.wav", self.root / "b.wav"
        synthetic(a, seconds=1)
        synthetic(b, seconds=1)
        self.assertEqual(sha256(a), sha256(b))
        info = audio_info(a)
        self.assertEqual(info, {"sample_rate": 44100, "channels": 2, "duration_seconds": 1.0})
        stems = verify_stems(self.root, info)
        self.assertTrue(all(s["finite"] and s["duration_matches"] and
                            s["format_matches_input"] for s in stems))

    def test_nonfinite_float_wav_is_rejected(self):
        samples = struct.pack("<100f", *([float("nan")] * 100))
        fmt = struct.pack("<HHIIHH", 3, 1, 44100, 44100 * 4, 4, 32)
        data = b"WAVEfmt " + struct.pack("<I", len(fmt)) + fmt + b"data" + struct.pack("<I", len(samples)) + samples
        file = self.root / "nan.wav"
        file.write_bytes(b"RIFF" + struct.pack("<I", len(data)) + data)
        self.assertFalse(verify_stems(self.root, audio_info(file))[0]["finite"])

    def test_wrong_duration_is_reported(self):
        file = self.root / "short.wav"
        synthetic(file, seconds=1)
        info = audio_info(file)
        info["duration_seconds"] = 2.0
        self.assertFalse(verify_stems(self.root, info)[0]["duration_matches"])


if __name__ == "__main__":
    unittest.main()
