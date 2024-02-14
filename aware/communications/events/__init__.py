import json
from pathlib import Path


def get_events():
    try:
        topics_path = Path(__file__).parent / "events.json"
        with open(topics_path, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return None
