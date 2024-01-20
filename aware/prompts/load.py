from jinja2 import Environment, FileSystemLoader, meta
from pathlib import Path
from typing import Dict

from aware.data.database.client_handlers import ClientHandlers


def get_template(template_name: str) -> Path:
    prompts_path = Path(__file__).parent / "templates"
    prompts_env = Environment(loader=FileSystemLoader(prompts_path))
    return prompts_env.get_template(f"{template_name}.j2")


def get_variables(template_str: str) -> list[str]:
    """
    Get the variables from a template string.

    Args:
        template_str (str): The template string to parse.

    Returns:
        list[str]: The variables in the template.
    """
    env = Environment()
    parsed_content = env.parse(template_str)
    variables = meta.find_undeclared_variables(parsed_content)
    return variables


def load_prompt_from_args(template: str, args: Dict[str, str]) -> str:
    """
    Load and populate the specified template.

    Args:
        template (str): The name of the template to load.
        args: The arguments to populate the template with.

    Returns:
        str: The populated template.
    """
    try:
        template = get_template(template)
        return template.render(**args)
    except Exception as e:
        raise Exception(f"Error loading or rendering template: {e}")


def load_prompt_from_database(template: str, user_id: str) -> str:
    """
    Load and populate the specified template.

    Args:
        template (str): The name of the template to load.

    Returns:
        str: The populated template.
    """
    try:
        template = get_template(template)
        variables = get_variables(template)
        content: Dict[str, str] = {}
        supabase_handler = ClientHandlers().get_supabase_handler()
        for variable_name in variables:
            content[variable_name] = supabase_handler.get_topic_content(
                user_id=user_id, name=variable_name
            )

        return template.render(**content)
    except Exception as e:
        raise Exception(f"Error loading or rendering template: {e}")
