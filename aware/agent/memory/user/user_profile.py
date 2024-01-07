import json
import threading


class UserProfile:
    def __init__(self, file_path):
        self.file_path = file_path
        self.profile = self.load_from_json()
        self.user_profile_lock = threading.Lock()

    def get_name(self):
        with self.user_profile_lock:
            return self.profile["name"]["data"]

    def load_from_json(self):
        with open(self.file_path, "r") as file:
            return json.load(file)

    def edit_user_profile(self, field: str, old_data: str, new_data: str):
        """Find and replace old data with new data in a specified field."""
        with self.user_profile_lock:
            if field in self.profile:
                self.profile[field]["data"] = self.profile[field]["data"].replace(
                    old_data, new_data
                )
                self.save_to_json()
                return f"Data has been edited in {field}."
            else:
                return f"Field {field} does not exist."

    def insert_user_profile(self, field: str, data: str):
        """Insert new data into a specified field."""
        with self.user_profile_lock:
            if field in self.profile:
                # Append the new data if the field already has some data; otherwise, add it directly
                if self.profile[field]["data"]:
                    self.profile[field]["data"] += ", " + data
                else:
                    self.profile[field]["data"] = data
                self.save_to_json()
                return f"Data has been inserted into {field}."
            else:
                return f"Field {field} does not exist."

    def save_to_json(self):
        with open(self.file_path, "w") as file:
            json.dump(self.profile, file, indent=4)

    def to_string(self):
        with self.user_profile_lock:
            profile_str = ""
            for category, info in self.profile.items():
                profile_str += (
                    f"Field: {category}\n"
                    + f"Description: {info['description']}\n"
                    + f"Data: {info['data'] if info['data'] else 'Not specified'}\n\n"
                )
            return profile_str.strip()
