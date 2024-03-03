import json
from pathlib import Path
from typing import Dict


class AgentProfile:
    def __init__(self, profile: Dict[str, str]):
        self.profile = profile

    @classmethod
    def load_from_template(self, module_name: str, agent_name: str):
        path = Path(__file__).parent / module_name / agent_name / "profile.json"
        with open(path, "r") as file:
            return json.load(file)

    def append_profile(self, field: str, data: str):
        """Append new data into a specified field."""
        if field in self.profile:
            # Append the new data if the field already has some data; otherwise, add it directly
            if self.profile[field]["data"]:
                self.profile[field]["data"] += ", " + data
            else:
                self.profile[field]["data"] = data
            return f"Data has been appended into {field}."
        else:
            return f"Field {field} does not exist."

    def edit_profile(self, field: str, old_data: str, new_data: str):
        """Find and replace old data with new data in a specified field."""
        if field in self.profile:
            self.profile[field]["data"] = self.profile[field]["data"].replace(
                old_data, new_data
            )
            return f"Data has been edited in {field}."
        else:
            return f"Field {field} does not exist."

    def to_string(self):
        profile_str = ""
        for category, info in self.profile.items():
            profile_str += (
                f"Field: {category}\n"
                + f"Description: {info['description']}\n"
                + f"Data: {info['data'] if info['data'] else 'Not specified'}\n\n"
            )
        return profile_str.strip()

    def to_json(self):
        return json.dumps(self.profile)
