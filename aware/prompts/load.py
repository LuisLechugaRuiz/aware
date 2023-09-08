from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from typing import Optional


def load_prompt(template: str, path: Optional[str] = None, **kwargs) -> str:
    """
    Load and populate the specified template.

    Args:
        template (str): The name of the template to load.
        **kwargs: The arguments to populate the template with.

    Returns:
        str: The populated template.
    """
    try:
        prompts_path = Path(__file__).parent
        if path is not None:
            prompts_path = prompts_path / path
        prompts_env = Environment(loader=FileSystemLoader(prompts_path))
        template = prompts_env.get_template(f"{template}.j2")
        return template.render(**kwargs)
    except Exception as e:
        raise Exception(f"Error loading or rendering template: {e}")
