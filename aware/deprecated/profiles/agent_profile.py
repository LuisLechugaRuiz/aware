import json
import os

from aware.permanent_storage.permanent_storage import get_permanent_storage_path
from aware.data.database.client_handlers import ClientHandlers


# TODO: MODIFY BY GENERAL PROFILE CLASS FOR EACH AGENT - BASED ON TOOLS.
class AgentProfile:
    def __init__(self, template_name: str, agent_id: str, profile=None):
        # TODO: ADAPT ME!
        # self.template_path = os.path.join(
        #     get_permanent_storage_path(), "user_data", "user_profile_template.json"
        # )

        if profile is not None:
            self.profile = profile
        else:
            self.profile = self.load(user_id)

    def get_profile(self):
        return self.profile

    @classmethod
    def get(self, template_name: str):
        # TODO: From tool path (tool path / module / agent / profile.json)
        with open(self.template_path, "r") as file:
            json_template = json.load(file)

        return json_template

    def load(self, user_id: str):
        with open(self.template_path, "r") as file:
            json_template = json.load(file)

        supabase_handler = ClientHandlers().get_supabase_handler()
        supabase_user_profile = supabase_handler.get_user_profile(user_id)
        if supabase_user_profile is None:
            raise Exception("User profile not found in Supabase.")

        for key, value in supabase_user_profile.items():
            if key in json_template:
                json_template[key]["data"] = value

        return json_template

    def to_json(self):
        return json.dumps(self.profile)

    def to_string(self):
        profile_str = ""
        for category, info in self.profile.items():
            profile_str += (
                f"Field: {category}\n"
                + f"Description: {info['description']}\n"
                + f"Data: {info['data'] if info['data'] else ''}\n\n"
            )
        return profile_str.strip()

    @classmethod
    def from_json(cls, user_id: str, json_str: str):
        data = json.loads(json_str)
        return cls(user_id, profile=data)
