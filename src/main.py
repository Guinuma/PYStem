import argparse
import sys
try:
    from .separator import separate_audio
    from .backends import MODELS
except ImportError:
    from separator import separate_audio
    from backends import MODELS


def show_menu():
    print("\n========== PYStem ==========")
    print("1. Separate audio")
    print("2. Exit")
    print("============================")


def main():
    print("Welcome to PYStem!")
    print("AI-powered music source separation")

    while True:
        show_menu()

        option = input("Choose an option: ").strip()

        if option == "1":
            audio_path = input("Enter audio file path: ").strip().strip('"')
            model = input(f"Model ({', '.join(MODELS)}) [htdemucs]: ").strip() or "htdemucs"
            settings = {}
            if model in MODELS and MODELS[model].engine == "msst":
                for key, label in (("msst_dir", "MSST checkout"), ("python", "MSST Python executable"),
                                   ("config", "YAML config"), ("checkpoint", "Checkpoint")):
                    settings[key] = input(f"{label} path: ").strip().strip('"')
            separate_audio(audio_path, model=model, **settings)

        elif option == "2":
            print("Goodbye!")
            break

        else:
            print("Invalid option. Please try again.")


def cli():
    parser = argparse.ArgumentParser(description="PYStem: offline CPU source separation")
    parser.add_argument("audio", nargs="?")
    parser.add_argument("--model", choices=MODELS, default="htdemucs")
    parser.add_argument("--output", default="output")
    parser.add_argument("--checkpoint")
    parser.add_argument("--config")
    parser.add_argument("--msst-dir")
    parser.add_argument("--python", default=sys.executable, help="Python in the selected engine environment")
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=1800)
    args = parser.parse_args()
    if args.audio is None:
        main()
        return 0
    return 0 if separate_audio(args.audio, args.output, model=args.model,
                              checkpoint=args.checkpoint, config=args.config,
                              msst_dir=args.msst_dir, python=args.python,
                              threads=args.threads, timeout=args.timeout) else 1


if __name__ == "__main__":
    raise SystemExit(cli())
