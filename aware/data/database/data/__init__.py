import json
from pathlib import Path


def get_data_path() -> Path:
    return Path(__file__).parent


def get_topics():
    try:
        topics_path = get_data_path() / "topics.json"
        with open(topics_path, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return None
