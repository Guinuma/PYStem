"""Explicit, size-checked provisioning, separate from offline inference."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import urllib.request


CATALOG = {
    "mdx23c": {
        "checkpoint": "https://github.com/ZFTurbo/Music-Source-Separation-Training/releases/download/v1.0.0/model_vocals_mdx23c_sdr_10.17.ckpt",
        "bytes": 448101203,
        "config": "https://github.com/ZFTurbo/Music-Source-Separation-Training/releases/download/v1.0.0/config_vocals_mdx23c.yaml",
        "author": "ZFTurbo / MVSep",
    },
    "bs_roformer": {
        "checkpoint": "https://github.com/TRvlvr/model_repo/releases/download/all_public_uvr_models/model_bs_roformer_ep_317_sdr_12.9755.ckpt",
        "bytes": 639331213,
        "config": "https://raw.githubusercontent.com/ZFTurbo/Music-Source-Separation-Training/6fdad13686bb7e84d029ec66f9dbe76e65c93ebf/configs/viperx/model_bs_roformer_ep_317_sdr_12.9755.yaml",
        "author": "viperx; hosted by TRvlvr/UVR",
    },
}


def fetch(url, target, expected=None):
    if target.exists():
        raise FileExistsError(f"Refusing to overwrite {target}")
    partial = target.with_suffix(target.suffix + ".part")
    digest = hashlib.sha256()
    size = 0
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "PYStem-local-research"})
        with urllib.request.urlopen(request, timeout=60) as response, partial.open("wb") as file:
            declared = response.headers.get("Content-Length")
            if expected and declared and int(declared) != expected:
                raise ValueError("Remote checkpoint size changed; review catalog before downloading")
            limit = expected if expected else 1024 * 1024  # configs only
            while chunk := response.read(1024 * 1024):
                size += len(chunk)
                if size > limit:
                    raise ValueError("Download exceeds reviewed size")
                digest.update(chunk)
                file.write(chunk)
        if expected and size != expected:
            raise ValueError("Incomplete checkpoint download")
        partial.replace(target)
    finally:
        partial.unlink(missing_ok=True)
    return {"file": target.name, "url": url, "bytes": size, "sha256": digest.hexdigest()}


def cli():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-download", action="store_true", help="Explicit consent to download reviewed artifacts")
    parser.add_argument("--models", nargs="+", choices=CATALOG, default=list(CATALOG))
    parser.add_argument("--directory", default="models")
    args = parser.parse_args()
    directory = Path(args.directory).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    needed = sum(CATALOG[name]["bytes"] for name in args.models)
    free = shutil.disk_usage(directory).free
    print(f"Checkpoints: {needed / 1e9:.3f} GB; free: {free / 1e9:.1f} GB; reserve: 2 GB", flush=True)
    if free < needed + 2_000_000_000:
        parser.error("Insufficient space with safety reserve")
    if not args.allow_download:
        print("Dry run only. Review terms and sizes, then use --allow-download.")
        return 0
    for name in args.models:
        entry = CATALOG[name]
        folder = directory / name
        folder.mkdir(exist_ok=True)
        print(f"Downloading {name}...", flush=True)
        artifacts = [fetch(entry["checkpoint"], folder / "model.ckpt", entry["bytes"]),
                     fetch(entry["config"], folder / "config.yaml")]
        manifest = {"model": name, "author": entry["author"],
                    "retrieved_utc": datetime.now(timezone.utc).isoformat(),
                    "weights_license": "not confirmed; no redistribution approval inferred",
                    "hash_note": "locally computed, not independently authenticated upstream checksums",
                    "artifacts": artifacts}
        (folder / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print(f"Saved {name} and SHA-256 manifest", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
