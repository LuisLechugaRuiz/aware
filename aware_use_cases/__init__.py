from pathlib import Path


def get_config_path():
    return Path(__file__).parent / 'config'


def get_template_config_path(template_name: str):
    # Construct the path to the config file
    config_path = get_config_path()
    return config_path / 'templates' / template_name


def get_user_config_path(user_id: str):
    # Construct the path to the config file
    config_path = get_config_path()
    # Check if the user folder exists
    user_folder = config_path / 'users' / user_id
    if not user_folder.exists():
        user_folder.mkdir(parents=True)
    return user_folder
