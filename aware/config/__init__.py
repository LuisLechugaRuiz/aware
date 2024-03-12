from pathlib import Path
import yaml


def get_modules():
    modules_path = Path(__file__).parent / "modules.yaml"
    with open(modules_path, "r", encoding="UTF-8") as file:
        return yaml.safe_load(file)


def get_internal_processes_path():
    return Path(__file__).parent / "internal_processes"
