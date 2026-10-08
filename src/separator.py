import subprocess
import sys
from pathlib import Path


def separate_audio(audio_path, output_dir="output"):
    audio_file = Path(audio_path)

    # Verify that the audio file exists
    if not audio_file.is_file():
        print(f"Error: File not found: {audio_file}")
        return False

    # Build the Demucs command
    command = [
        sys.executable,
        "-m",
        "demucs",
        "--device",
        "cpu",
        "--out",
        str(output_dir),
        str(audio_file),
    ]

    print(f"\nSeparating: {audio_file.name}")
    print("This may take a few minutes...\n")

    try:
        subprocess.run(command, check=True)

    except subprocess.CalledProcessError:
        print("\nError: Audio separation failed.")
        return False

    # Show where the separated stems were saved
    output_path = Path(output_dir) / "htdemucs" / audio_file.stem

    print("\nSeparation completed!")
    print(f"Files saved to: {output_path.resolve()}")

    return True