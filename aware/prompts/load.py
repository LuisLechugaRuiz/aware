from jinja2 import Environment, FileSystemLoader, Template, meta
from pathlib import Path
from typing import Dict, Optional

from aware.data.database.client_handlers import ClientHandlers
from aware.utils.logger.file_logger import FileLogger


def get_path(template_name: str, module_name: Optional[str] = None) -> Path:
    prompts_path = Path(__file__).parent / "template"
    if module_name is not None:
        prompts_path = prompts_path / module_name
    return prompts_path / f"{template_name}.j2"


def get_template(template_name: str, module_name: Optional[str] = None) -> Template:
    log = FileLogger("migration_tests")
    template_path = get_path(template_name, module_name)
    log.info(f"Loading template from {template_path.parent}")
    log.info(f"Template name: {template_name}")
    prompts_env = Environment(loader=FileSystemLoader(template_path.parent))
    return prompts_env.get_template(template_path.name)


def get_variables(template_name: str, module_name: Optional[str] = None) -> list[str]:
    """
    Get the variables from a template string.

    Args:
        template_str (str): The template string to parse.

    Returns:
        list[str]: The variables in the template.
    """
    template_path = get_path(template_name, module_name)
    environment = Environment(loader=FileSystemLoader(template_path.parent))
    template_source = environment.loader.get_source(environment, template_path.name)[0]
    parsed_content = environment.parse(template_source)
    variables = meta.find_undeclared_variables(parsed_content)
    return list(variables)


def load_prompt_from_args(template_name: str, args: Dict[str, str]) -> str:
    """
    Load and populate the specified template.

    Args:
        template (str): The name of the template to load.
        args: The arguments to populate the template with.

    Returns:
        str: The populated template.
    """
    try:
        template = get_template(template_name)
        return template.render(**args)
    except Exception as e:
        raise Exception(f"Error loading or rendering template: {e}")


def load_prompt_from_database(
    template_name: str,
    user_id: str,
    module_name: str,
    extra_kwargs: Optional[Dict[str, str]],
) -> str:
    """
    Load and populate the specified template.

    Args:
        template (str): The name of the template to load.

    Returns:
        str: The populated template.
    """
    try:
        log = FileLogger("migration_tests")
        template = get_template(template_name, module_name)
        variables = get_variables(template_name, module_name)
        log.info(f"DEBUG - Variables: {variables}")
        log.info(f"DEBUG - extra_kwargs: {extra_kwargs}")
        content: Dict[str, str] = {}

        remaining_variables = variables.copy()

        if extra_kwargs:
            for variable_name in variables:
                extra_value = extra_kwargs.get(variable_name, None)
                if extra_value is not None:
                    content[variable_name] = extra_value
                    remaining_variables.remove(variable_name)

        log.info(f"DEBUG - content pre: {content}")
        supabase_handler = ClientHandlers().get_supabase_handler()
        for variable_name in remaining_variables:
            content[variable_name] = supabase_handler.get_topic_content(
                user_id=user_id, name=variable_name
            )
        log.info(f"DEBUG - content post: {content}")
        return template.render(**content)
    except Exception as e:
        raise Exception(f"Error loading or rendering template: {e}")
