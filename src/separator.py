"""Backwards-compatible public entry point."""
import subprocess
try:
    from .backends import Options, run_separation
except ImportError:
    from backends import Options, run_separation


def separate_audio(audio_path, output_dir="output", *, model="htdemucs", **kwargs):
    """Return success as before; engines use CPU and local model files only."""
    print(f"\nSeparating with {model} on CPU...")
    try:
        result = run_separation(audio_path, output_dir, Options(model=model, **kwargs))
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"Error: Audio separation failed: {error}")
        return False
    print(f"\nSeparation completed!\nFiles saved to: {result}")
    return True
