
from typing import Any, Dict
from aware.utils.parser.new_pydantic_parser import NewPydanticParser

# TODO:!!! THIS SHOULD BE THE AWARE DEFAULT CREATION OF REQUESTS. AGENTS CAN CONNECT WITH ANY OTHER AGENT IN THE GROUP.
# WE CREATE THE REQUESTS ON AGENT DECISION INSTEAD OF OUTSIDE.

# AGENT HAVE ACCESS TO SINGLE FUNCTION:

# # The only one that needs to answer with a specific template is always the server, the client can send free format, enabling much bigger space of possiblilities for each agent!!
# CREATE_REQUEST(AGENT_NAME, DESCRIPTION, EXPECTED_RESPONSE)

# SO EXPECTED RESPONSE IS WHERE THIS GET_SCHEMA HAPPENS. AGENT NEEDS TO CREATE A DICT[STR, STR] where the value is a PYDANTIC FORMAT:

# I.E: content = List[Content], Content = Dict[str, str] how we do this? Which kind of info we ask to the LLM to produce this?
# Task: Ask to GPT-4 how to solve this, which would be the best format. but first save the ideas.

# TODO: Add agents -> AGENT ID TO AGENT ID!!
class RequestCreation:
    def __init__(self):
        pass

    # TODO: Add create_action option also
    def create_request_communication(self, client_name: str, service_name: str, query: str, response_format: Dict[str, Any]):
        self.create_request(query, response_format)
        # 1. Create client.
        self.create_request_client(client_name)
        # 2. Create service.
        self.create_request_service(service_name)
        pass

    def create_action_communication(self, client_name: str, service_name: str, query: str, feedback_format: Dict[str, Any], response_format: Dict[str, Any]):
        self.create_action(query, feedback_format, response_format)
        # 1. Create client.
        self.create_action_client(client_name)
        # 2. Create service.
        self.create_action_service(service_name)
        pass

    def create_request(self, query: str, response_format: Dict[str, Any]):
        # TODO: Get schema and save it into Supabase and Redis to obtain it directly when fetching the request.
        pass

    def create_request_client(self, client_name: str):
        # 1. Create client.
        pass

    def create_request_service(self, service_name: str):
        # 1.
        pass

    def get_schema(self, name: str, args: Dict[str, Any], description: str):
        return NewPydanticParser.get_openai_schema(name=name, args=args, description=description)


def create_format() -> Dict[str, str]:
    args = {}
    while input("Add argument? (y/n): ") == "y":
        name = input("Name: ")
        type = input("Type: ")
        args[name] = type
    return args


def main():
    request_creation = RequestCreation()
    client_name = input("Client name: ")
    service_name = input("Service name: ")
    query = input("Query: ")

    # TODO: Here we should differentiate between request_message and response_message, we can also ask if is sync or async
    is_async = input("Is async? (y/n): ")
    if is_async == "y":
        print("--- Creating feedback ---")
        feedback_format = create_format()
        schema = request_creation.get_schema(name="update_feedback", args=feedback_format, description="Update feedback")
        print(f"Schema: {schema}")
        print("--- Creating response ---")
        response_format = create_format()
        request_creation.create_action_communication(client_name, service_name, query, feedback_format, response_format)
    else:
        print("--- Creating response ---")
        response_format = create_format()
        schema = request_creation.get_schema(name="set_request_completed", args=response_format, description="validation info")
        print(f"Schema: {schema}")
        request_creation.create_request_communication(client_name, service_name, query, response_format)


if __name__ == "__main__":
    main()