from pathlib import Path
import os


def get_private_data(filename: str):
    private_data_path = get_private_data_path()
    return os.path.join(private_data_path, filename)


def get_private_data_path():
    return Path(__file__).parent / "private_data"
