"""CPU adapters; optional engines run in their own Python environment."""
from dataclasses import dataclass
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile


@dataclass(frozen=True)
class ModelSpec:
    label: str
    engine: str
    stems: tuple[str, ...]


MODELS = {
    "htdemucs": ModelSpec("HTDemucs", "demucs", ("drums", "bass", "other", "vocals")),
    "htdemucs_ft": ModelSpec("HTDemucs FT", "demucs", ("drums", "bass", "other", "vocals")),
    "htdemucs_6s": ModelSpec("HTDemucs 6 stems", "demucs", ("drums", "bass", "other", "vocals", "guitar", "piano")),
    "mdx23c": ModelSpec("MDX23C vocals (experimental, local weights)", "msst", ("vocals", "instrumental")),
    "bs_roformer": ModelSpec("BS-Roformer vocals (experimental, local weights)", "msst", ("vocals", "instrumental")),
}


@dataclass(frozen=True)
class Options:
    model: str = "htdemucs"
    checkpoint: str | None = None
    config: str | None = None
    msst_dir: str | None = None
    python: str = sys.executable
    threads: int = 4
    timeout: float = 1800


def local_file(value, label):
    if not value or not Path(value).is_file():
        raise ValueError(f"{label}: provide an existing local file (no automatic download).")
    return Path(value).resolve()


class DemucsBackend:
    def command(self, audio, output, options):
        return ["--module", "demucs", "--device", "cpu", "--name", options.model,
                "--out", str(output), str(audio)]

    def result_dir(self, output, audio, options):
        return output / options.model / audio.stem


class MSSTBackend:
    def command(self, audio, output, options):
        checkpoint = local_file(options.checkpoint, "Checkpoint")
        config = local_file(options.config, "YAML config")
        if not options.msst_dir:
            raise ValueError("Provide --msst-dir pointing to a local MSST checkout.")
        script = local_file(Path(options.msst_dir) / "inference.py", "MSST inference.py")
        return ["--msst", str(script), "--model_type", options.model,
                "--config_path", str(config), "--start_check_point", str(checkpoint),
                "--input_folder", str(audio.parent), "--store_dir", str(output),
                "--force_cpu", "--extract_instrumental", "--pcm_type", "FLOAT",
                "--filename_template", "{instr}"]

    def result_dir(self, output, audio, options):
        return output


BACKENDS = {"demucs": DemucsBackend(), "msst": MSSTBackend()}


def run_separation(audio_path, output_dir="output", options=None):
    options = options or Options()
    audio = local_file(audio_path, "Audio")
    if options.model not in MODELS:
        raise ValueError(f"Unknown model: {options.model}. Choose from {', '.join(MODELS)}")
    if options.threads < 1 or options.timeout <= 0:
        raise ValueError("Threads and timeout must be positive.")
    backend = BACKENDS[MODELS[options.model].engine]
    destination = Path(output_dir).resolve() / options.model / audio.stem
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Stage one input so folder-based engines cannot process neighbouring tracks.
    # Fresh output also prevents stale files masking a failed inference.
    with tempfile.TemporaryDirectory(prefix="pystem-", dir=destination.parent) as temporary:
        root = Path(temporary)
        inputs = root / "input"
        inputs.mkdir()
        staged = inputs / audio.name
        shutil.copy2(audio, staged)
        outputs = root / "output"
        args = backend.command(staged, outputs, options)
        command = [options.python, str(Path(__file__).with_name("offline_worker.py")), *args]
        env = os.environ.copy()
        env.update(HF_HUB_OFFLINE="1", CUDA_VISIBLE_DEVICES="",
                   OMP_NUM_THREADS=str(options.threads), MKL_NUM_THREADS=str(options.threads))
        subprocess.run(command, check=True, env=env, timeout=options.timeout)
        result = backend.result_dir(outputs, staged, options)
        files = list(result.glob("*.wav"))
        if not files or any(file.stat().st_size <= 44 for file in files):
            raise RuntimeError("Engine produced no usable WAV stems.")
        expected = MODELS[options.model].stems
        if expected and not all((result / f"{stem}.wav").is_file() for stem in expected):
            raise RuntimeError("Engine did not produce all expected stems.")
        destination.mkdir(parents=True, exist_ok=True)
        for file in files:
            shutil.copy2(file, destination / file.name)
    return destination
