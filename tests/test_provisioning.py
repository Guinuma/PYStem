import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src.download_models import cli, fetch
from src.offline_worker import cpu_config


class ProvisioningTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_dry_run_never_opens_network(self):
        with patch("sys.argv", ["download_models", "--directory", str(self.root)]), \
             patch("src.download_models.urllib.request.urlopen") as request:
            self.assertEqual(cli(), 0)
            request.assert_not_called()

    def test_insufficient_space_blocks_even_explicit_download(self):
        with patch("sys.argv", ["download_models", "--allow-download", "--directory", str(self.root)]), \
             patch("src.download_models.shutil.disk_usage") as usage, \
             patch("src.download_models.urllib.request.urlopen") as request:
            usage.return_value.free = 1
            with self.assertRaises(SystemExit):
                cli()
            request.assert_not_called()

    def test_truncated_download_removes_partial_and_does_not_publish(self):
        response = io.BytesIO(b"short")
        response.headers = {}
        target = self.root / "model.ckpt"
        with patch("src.download_models.urllib.request.urlopen", return_value=response):
            with self.assertRaises(ValueError):
                fetch("https://example.invalid/model", target, expected=100)
        self.assertFalse(target.exists())
        self.assertFalse(target.with_suffix(".ckpt.part").exists())

    def test_cpu_profile_preserves_architecture_and_original(self):
        source = self.root / "original.yaml"
        text = "model:\n  bands: !!python/tuple [2, 4]\ntraining: {}\ninference:\n  batch_size: 4\n  num_overlap: 2\n"
        source.write_text(text)
        inputs = self.root / "input"
        inputs.mkdir()
        args = cpu_config(["--model_type", "bs_roformer", "--config_path", str(source),
                           "--input_folder", str(inputs)])
        derived = Path(args[args.index("--config_path") + 1])
        self.assertEqual(source.read_text(), text)
        self.assertIn("python/tuple", derived.read_text())
        self.assertIn("batch_size: 1", derived.read_text())
        self.assertIn("num_overlap: 2", derived.read_text())
        self.assertIn("use_amp: false", derived.read_text())

    def test_cpu_profile_rejects_mismatched_architecture(self):
        source = self.root / "wrong.yaml"
        source.write_text("training:\n  model_type: htdemucs\n")
        with self.assertRaisesRegex(ValueError, "does not match"):
            cpu_config(["--model_type", "mdx23c", "--config_path", str(source)])


if __name__ == "__main__":
    unittest.main()
