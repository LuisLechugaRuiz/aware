import inspect
from pydantic import BaseModel
from typing import Any, Dict, Type, List

from aware.utils.parser.json_pydantic_parser import JsonPydanticParser

# This file has been moved and implemented properly on communication/setup.
#  We need to consider where it makes more sense, for now I leave it there as we might use it also directly from core.

# Extract the schema and save it into a file at REQUEST! TODO: Move this function to communication setup which will help us to make it cleaner.
def save_request()

# Future - UI
# Lets create a small ui here that ask the user to add name of the function and then in parallel the type of the argument.
# We can just show it on the prompt down.


if __name__ == "__main__":
    __main__()