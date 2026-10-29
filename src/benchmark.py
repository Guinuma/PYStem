"""Reproducible CPU end-to-end benchmark; no checkpoint downloads."""
import argparse
import array
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import wave


def sha256(path):
    with open(path, "rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()


def synthetic(path, seconds=8, rate=44100):
    """Deterministic stereo tones: functional input, NOT a music quality test."""
    samples = array.array("h")
    for index in range(seconds * rate):
        t = index / rate
        value = sum(0.08 * math.sin(2 * math.pi * f * t) for f in (110, 440, 1760))
        samples.extend((int(value * 32767), int(value * 32767)))
    if sys.byteorder != "little":
        samples.byteswap()
    with wave.open(str(path), "wb") as file:
        file.setparams((2, 2, rate, 0, "NONE", "not compressed"))
        file.writeframes(samples.tobytes())


def audio_info(path):
    # ffmpeg handles PCM and IEEE float WAV from the different engines.
    metadata = subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries",
        "stream=sample_rate,channels,duration", "-of", "json", str(path)], text=True)
    stream = json.loads(metadata)["streams"][0]
    return {"sample_rate": int(stream["sample_rate"]), "channels": int(stream["channels"]),
            "duration_seconds": float(stream["duration"])}


def verify_stems(folder, source_info):
    results = []
    for path in sorted(folder.rglob("*.wav")):
        info = audio_info(path)
        raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", str(path),
                                       "-f", "f32le", "-acodec", "pcm_f32le", "-"])
        values = array.array("f")
        values.frombytes(raw)
        if sys.byteorder != "little":
            values.byteswap()
        finite = bool(values) and all(math.isfinite(v) for v in values)
        aligned = abs(info["duration_seconds"] - source_info["duration_seconds"]) <= 0.05
        compatible = (info["sample_rate"] == source_info["sample_rate"] and
                      info["channels"] == source_info["channels"])
        results.append({"file": str(path.relative_to(folder)), **info,
                        "finite": finite, "duration_matches": aligned,
                        "format_matches_input": compatible,
                        "sha256": sha256(path)})
    return results


def stop_tree(process, psutil):
    try:
        parent = psutil.Process(process.pid)
        children = parent.children(recursive=True)
        for child in children:
            try:
                child.kill()
            except psutil.NoSuchProcess:
                pass
        parent.kill()
    except psutil.NoSuchProcess:
        pass
    process.wait()


def cli():
    try:
        import psutil
    except ImportError:
        raise SystemExit("Install requirements-benchmark.txt in the benchmark environment.")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", nargs="?", help="Omit to generate an 8-second stereo tone WAV")
    parser.add_argument("--model", default="htdemucs")
    parser.add_argument("--runs", type=int, default=2)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=300)
    parser.add_argument("--report-dir", required=True, help="New directory, never overwrites a report")
    parser.add_argument("--checkpoint")
    parser.add_argument("--config")
    parser.add_argument("--msst-dir")
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--artifact", action="append", default=[], help="Actual model/config file to hash (repeatable)")
    args = parser.parse_args()
    if args.runs < 1 or args.threads < 1 or args.timeout <= 0:
        parser.error("Runs, threads and timeout must be positive")
    artifacts = args.artifact + [p for p in (args.checkpoint, args.config) if p]
    for path in artifacts + ([args.audio] if args.audio else []):
        if not Path(path).is_file():
            parser.error(f"Local file not found: {path}")
    report_dir = Path(args.report_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=False)
    audio = Path(args.audio).resolve() if args.audio else report_dir / "synthetic.wav"
    if not args.audio:
        synthetic(audio)
    info = audio_info(audio)
    if info["duration_seconds"] <= 0:
        parser.error("Input audio must have positive duration")
    report = {"schema_version": 1, "created_utc": datetime.now(timezone.utc).isoformat(),
              "model": args.model, "device": "cpu",
              "threads": args.threads, "platform": platform.platform(),
              "processor": platform.processor(), "logical_cpus": os.cpu_count(),
              "ram_bytes": psutil.virtual_memory().total,
              "audio": {"name": audio.name, "sha256": sha256(audio), **info},
              "synthetic": not bool(args.audio), "artifacts": [
                  {"name": Path(p).name, "bytes": Path(p).stat().st_size, "sha256": sha256(p)}
                  for p in artifacts], "versions": {}, "runs": [],
              "memory_method": "sampled sum RSS of CLI and descendants every 100ms; shared pages may be counted twice",
              "timing_method": "end-to-end fresh process, includes imports, loading, staging and export; not inference-only",
              "quality_metrics": None}
    report["msst_cpu_overrides"] = {"inference.batch_size": 1, "training.use_amp": False}
    for package in ("demucs", "torch", "numpy", "psutil"):
        try:
            report["versions"][package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            report["versions"][package] = None
    report["versions_scope"] = "benchmark interpreter; optional MSST environment must be recorded separately"
    version_code = ("import importlib.metadata as m,json; "
                    "print(json.dumps({d.metadata['Name']:d.version for d in m.distributions()}))")
    report["engine_environment"] = json.loads(subprocess.check_output(
        [args.python, "-c", version_code], text=True))
    if args.msst_dir:
        revision = subprocess.run(["git", "-C", args.msst_dir, "rev-parse", "HEAD"],
                                  capture_output=True, text=True)
        report["msst_commit"] = revision.stdout.strip() if revision.returncode == 0 else None
    for index in range(args.runs):
        output = report_dir / f"run-{index + 1}"
        command = [sys.executable, str(Path(__file__).with_name("main.py")), str(audio),
                   "--model", args.model, "--output", str(output), "--threads", str(args.threads),
                   "--timeout", str(args.timeout), "--python", args.python]
        for key in ("checkpoint", "config", "msst_dir"):
            value = getattr(args, key)
            if value:
                command.extend(["--" + key.replace("_", "-"), value])
        started = time.perf_counter()
        peak = 0
        timed_out = False
        with (report_dir / f"run-{index + 1}.log").open("w", encoding="utf-8") as log:
            process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
            while process.poll() is None:
                try:
                    parent = psutil.Process(process.pid)
                    rss = 0
                    for item in [parent, *parent.children(recursive=True)]:
                        try:
                            rss += item.memory_info().rss
                        except psutil.NoSuchProcess:
                            pass
                    peak = max(peak, rss)
                except psutil.NoSuchProcess:
                    pass
                if time.perf_counter() - started > args.timeout + 10:
                    timed_out = True
                    stop_tree(process, psutil)
                    break
                time.sleep(0.1)
        elapsed = time.perf_counter() - started
        validation_error = None
        try:
            stems = verify_stems(output, info) if process.returncode == 0 else []
        except (OSError, ValueError, KeyError, IndexError, subprocess.SubprocessError) as error:
            stems = []
            validation_error = str(error)
        valid = bool(stems) and all(s["finite"] and s["duration_matches"] and
                                    s["format_matches_input"] for s in stems)
        run = {"run": index + 1, "exit_code": process.returncode, "timed_out": timed_out,
               "elapsed_seconds": elapsed, "real_time_factor": elapsed / info["duration_seconds"],
               "sampled_peak_tree_rss_bytes": peak, "outputs_valid": valid,
               "validation_error": validation_error, "stems": stems}
        report["runs"].append(run)
        (report_dir / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps({k: v for k, v in run.items() if k != "stems"}))
    return 0 if all(r["exit_code"] == 0 and r["outputs_valid"] for r in report["runs"]) else 1


if __name__ == "__main__":
    raise SystemExit(cli())
