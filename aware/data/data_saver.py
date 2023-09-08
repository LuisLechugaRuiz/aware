import json
from pathlib import Path
import os


DEF_FILE_NAME_PREFIX = "conversation"


class DataSaver:
    """Store all the traces from the agents"""

    def __init__(self, module_name: str):
        self.module_name = module_name
        self.traces_path = Path(__file__).parent / "traces" / module_name
        self.current_file = self.get_current_file()
        self.max_lines = 50000

    def get_current_file(self):
        if not self.traces_path.exists():
            self.traces_path.mkdir(parents=True, exist_ok=True)

        files = list(self.traces_path.glob(f"{DEF_FILE_NAME_PREFIX}_*.json"))
        if files:
            return sorted(files)[-1]
        else:
            new_file = self.traces_path / f"{DEF_FILE_NAME_PREFIX}_0.json"
            new_file.touch()
            return new_file

    def start_new_conversation(self, system_message):
        with open(self.current_file, "r") as file:
            lines = file.readlines()
            number_of_lines = len(lines)
        if number_of_lines > self.max_lines:
            current_file_index = int(
                self.current_file.name.split(f"{DEF_FILE_NAME_PREFIX}_")[-1].split(
                    ".json"
                )[0]
            )
            new_file_index = current_file_index + 1
            self.current_file = (
                self.traces_path / f"{DEF_FILE_NAME_PREFIX}_{new_file_index}.json"
            )
        new_convo = {"messages": [system_message]}
        with open(self.current_file, "a") as file:
            file.write(json.dumps(new_convo) + "\n")

    def add_message(self, message):
        try:
            with open(self.current_file, "rb+") as file:
                try:
                    file.seek(-2, os.SEEK_END)
                    while file.read(1) != b"\n":
                        file.seek(-2, os.SEEK_CUR)
                except OSError:
                    file.seek(0)
                last_line_start = file.tell() if file.tell() > 0 else 0
                file.seek(last_line_start)
                last_line = file.readline().decode()
                last_convo = json.loads(last_line)

                # Update and write back
                last_convo["messages"].append(message)
                file.seek(last_line_start)
                file.write(json.dumps(last_convo).encode() + b"\n")
                file.truncate()
        except FileNotFoundError:
            print("No existing conversation file found. Creating a new one.")
            self.start_new_conversation(message)
        except Exception as e:
            print(f"Error updating conversation: {e}")
