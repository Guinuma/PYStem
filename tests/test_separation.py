from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from src.backends import MSSTBackend, Options, run_separation
from src.separator import separate_audio


class SeparationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.audio = self.root / "track with spaces.wav"
        self.audio.write_bytes(b"input")
        self.out = self.root / "out"

    def fake_demucs(self, command, **kwargs):
        self.assertIn("cpu", command)
        self.assertEqual(kwargs["env"]["HF_HUB_OFFLINE"], "1")
        self.assertEqual(kwargs["env"]["CUDA_VISIBLE_DEVICES"], "")
        output = Path(command[command.index("--out") + 1])
        folder = output / "htdemucs" / self.audio.stem
        folder.mkdir(parents=True)
        for stem in ("drums", "bass", "other", "vocals"):
            (folder / f"{stem}.wav").write_bytes(b"x" * 100)

    @patch("src.backends.subprocess.run")
    def test_default_demucs_and_legacy_boolean(self, run):
        run.side_effect = self.fake_demucs
        self.assertTrue(separate_audio(self.audio, self.out))
        self.assertEqual(len(list((self.out / "htdemucs" / self.audio.stem).glob("*.wav"))), 4)
        self.assertFalse(list(self.out.rglob("pystem-*")))

    @patch("src.backends.subprocess.run")
    def test_missing_input_and_unknown_model_do_not_launch(self, run):
        self.assertFalse(separate_audio(self.root / "missing.wav", self.out))
        self.assertFalse(separate_audio(self.audio, self.out, model="unknown"))
        run.assert_not_called()

    @patch("src.backends.subprocess.run")
    def test_missing_local_checkpoint_does_not_launch(self, run):
        for model in ("mdx23c", "bs_roformer"):
            self.assertFalse(separate_audio(self.audio, self.out, model=model))
        run.assert_not_called()

    @patch("src.backends.subprocess.run")
    def test_stale_outputs_cannot_mask_no_outputs(self, run):
        old = self.out / "htdemucs" / self.audio.stem
        old.mkdir(parents=True)
        (old / "vocals.wav").write_bytes(b"old" * 100)
        self.assertFalse(separate_audio(self.audio, self.out))
        self.assertEqual((old / "vocals.wav").read_bytes(), b"old" * 100)

    @patch("src.backends.subprocess.run")
    def test_process_failure_and_timeout_return_false(self, run):
        for error in (subprocess.CalledProcessError(1, "engine"),
                      subprocess.TimeoutExpired("engine", 1), FileNotFoundError("Python")):
            run.side_effect = error
            self.assertFalse(separate_audio(self.audio, self.out))

    def test_msst_both_architectures_use_cpu_and_exact_pair(self):
        for name in ("model.ckpt", "model.yaml", "inference.py"):
            (self.root / name).touch()
        for model in ("mdx23c", "bs_roformer"):
            args = MSSTBackend().command(self.audio, self.out, Options(
                model=model, checkpoint=str(self.root / "model.ckpt"),
                config=str(self.root / "model.yaml"), msst_dir=str(self.root)))
            self.assertIn("--force_cpu", args)
            self.assertEqual(args[args.index("--model_type") + 1], model)
            self.assertEqual(args[args.index("--input_folder") + 1], str(self.root))

    def test_offline_worker_blocks_network_before_connecting(self):
        script = self.root / "network.py"
        script.write_text("import socket\nsocket.create_connection(('example.com', 443))\n")
        worker = Path(__file__).resolve().parents[1] / "src" / "offline_worker.py"
        result = subprocess.run([sys.executable, str(worker), "--script", str(script)],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PYStem is offline", result.stderr)

    def test_msst_subprocess_stages_only_selected_track_and_exports_stems(self):
        # A local protocol stub exercises adapter wiring, NOT neural inference.
        (self.root / "neighbour.wav").write_bytes(b"do not process")
        (self.root / "config.yaml").write_text("training: {}\ninference: {}\n")
        (self.root / "model.ckpt").touch()
        script = self.root / "inference.py"
        script.write_text('''import argparse
from pathlib import Path
import wave
p = argparse.ArgumentParser()
for name in ('model_type', 'config_path', 'start_check_point', 'input_folder', 'store_dir', 'pcm_type', 'filename_template'):
    p.add_argument('--' + name)
p.add_argument('--force_cpu', action='store_true')
p.add_argument('--extract_instrumental', action='store_true')
a = p.parse_args()
assert a.force_cpu and a.extract_instrumental
assert len(list(Path(a.input_folder).iterdir())) == 1
assert a.model_type in ('mdx23c', 'bs_roformer')
Path(a.store_dir).mkdir(parents=True)
for stem in ('vocals', 'instrumental'):
    with wave.open(str(Path(a.store_dir) / (stem + '.wav')), 'wb') as f:
        f.setparams((2, 2, 44100, 0, 'NONE', ''))
        f.writeframes(bytes(400))
''')
        for model in ("mdx23c", "bs_roformer"):
            result = run_separation(self.audio, self.out, Options(
                model=model, msst_dir=str(self.root), config=str(self.root / "config.yaml"),
                checkpoint=str(self.root / "model.ckpt")))
            self.assertEqual({p.name for p in result.iterdir()}, {"vocals.wav", "instrumental.wav"})


if __name__ == "__main__":
    unittest.main()
