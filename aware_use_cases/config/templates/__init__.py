from pathlib import Path


def read_user_config(config_name):
    # Construct the path to the config file
    current_dir = Path(__file__).parent  # Gets the directory of the current file
    config_path = current_dir / 'users' / f'{config_name}.json'

    # Read the JSON config file
    with open(config_path, 'r') as file:
        import json
        config = json.load(file)

    return config