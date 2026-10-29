"""Run trusted local engines without Python network connections/downloads."""
import os
from pathlib import Path
import runpy
import sys


def cpu_config(arguments):
    # Parse data and the tuple tag used by official Roformer configs only.
    # Original config/checkpoint files remain untouched.
    import yaml

    class Loader(yaml.SafeLoader):
        pass

    class Dumper(yaml.SafeDumper):
        pass

    Loader.add_constructor("tag:yaml.org,2002:python/tuple",
                           lambda loader, node: tuple(loader.construct_sequence(node)))
    Dumper.add_representer(tuple, lambda dumper, value: dumper.represent_sequence(
        "tag:yaml.org,2002:python/tuple", value))
    index = arguments.index("--config_path") + 1
    config = yaml.load(Path(arguments[index]).read_text(encoding="utf-8"), Loader=Loader)
    if not isinstance(config, dict):
        raise ValueError("Model config must be a YAML mapping")
    model = arguments[arguments.index("--model_type") + 1]
    training = config.setdefault("training", {})
    if training.get("model_type", model) != model:
        raise ValueError("Config model_type does not match the selected architecture")
    training["use_amp"] = False
    config.setdefault("inference", {})["batch_size"] = 1
    folder = Path(arguments[arguments.index("--input_folder") + 1]).parent
    derived = folder / "cpu-config.yaml"
    derived.write_text(yaml.dump(config, Dumper=Dumper), encoding="utf-8")
    arguments[index] = str(derived)
    print("CPU profile: batch_size=1, use_amp=False; original config unchanged", flush=True)
    return arguments


def deny_network(event, args):
    if event in {"socket.connect", "socket.getaddrinfo", "socket.sendto"}:
        raise RuntimeError("PYStem is offline. Provision model files separately before inference.")


def main():
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    sys.addaudithook(deny_network)
    mode, target, *arguments = sys.argv[1:]
    if mode == "--msst":
        arguments = cpu_config(arguments)
    sys.argv = [target, *arguments]
    if mode == "--module":
        runpy.run_module(target, run_name="__main__")
    elif mode in {"--script", "--msst"}:
        sys.path.insert(0, str(Path(target).resolve().parent))
        runpy.run_path(target, run_name="__main__")
    else:
        raise ValueError("Expected --module, --script or --msst")


if __name__ == "__main__":
    main()
