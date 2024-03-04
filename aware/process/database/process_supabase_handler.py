from supabase import Client
from typing import Dict, List, Optional

from aware.process.process_data import ProcessData, ProcessFlowType
from aware.process.process_ids import ProcessIds
from aware.process.state_machine.state import ProcessState
from aware.utils.logger.file_logger import FileLogger


class ProcessSupabaseHandler:
    def __init__(self, client: Client):
        self.client = client
        self.logger = FileLogger("agent_supabase_handler")

    def create_current_process_state(
        self, user_id: str, process_id: str, process_state_id: str
    ) -> ProcessState:
        self.logger.info(f"Creating current process state for process: {process_id}")
        response = (
            self.client.table("current_process_states")
            .insert(
                {
                    "user_id": user_id,
                    "process_id": process_id,
                    "current_state_id": process_state_id,
                }
            )
            .execute()
            .data
        )
        self.logger.info(
            f"Current process state created for process: {process_id}. Response: {response}"
        )

    def create_process(
        self,
        user_id: str,
        agent_id: str,
        name: str,
        tools_class: str,
        flow_type: ProcessFlowType,
    ) -> ProcessData:
        self.logger.info(f"Creating process {name}")
        data = (
            self.client.table("processes")
            .insert(
                {
                    "user_id": user_id,
                    "agent_id": agent_id,
                    "name": name,
                    "tools_class": tools_class,
                    "flow_type": flow_type.value,
                }
            )
            .execute()
            .data
        )
        data = data[0]
        self.logger.info(f"Process: {name}, created. Initializing process data")
        return ProcessData(
            id=data["id"],
            name=data["name"],
            tools_class=data["tools_class"],
            flow_type=ProcessFlowType(data["flow_type"]),
        )

    def create_process_state(
        self,
        user_id: str,
        process_id: str,
        name: str,
        task: str,
        instructions: str,
        tools: Dict[str, str],
    ) -> ProcessState:
        self.logger.info(f"Creating process state {name}")
        data = (
            self.client.table("process_states")
            .insert(
                {
                    "user_id": user_id,
                    "process_id": process_id,
                    "name": name,
                    "task": task,
                    "instructions": instructions,
                }
            )
            .execute()
            .data
        )
        data = data[0]
        process_state_id = data["id"]
        self.logger.info(f"Process state: {name}, created.")
        self.logger.info(f"Creating tools for process state: {name}")
        for tool_name, transition_state_name in tools.items():
            data = (
                # TODO: tools is not the right name, should be a transition
                self.client.table("tools")
                .insert(
                    {
                        "user_id": user_id,
                        "process_state_id": process_state_id,
                        "name": tool_name,
                        "transition_state_name": transition_state_name,
                    }
                )
                .execute()
                .data
            )
        return ProcessState(
            id=process_state_id,
            name=name,
            tools=tools,
            task=task,
            instructions=instructions,
        )

    def get_agent_process_id(self, agent_id: str, process_name: str) -> Optional[str]:
        data = (
            self.client.table("processes")
            .select("*")
            .eq("agent_id", agent_id)
            .eq("name", process_name)
            .execute()
            .data
        )
        if not data:
            return None
        return data[0]["id"]

    def get_current_process_state(self, process_id: str) -> ProcessState:
        current_process_state = (
            self.client.rpc("get_current_process_state", {"p_process_id": process_id})
            .execute()
            .data
        )
        tools = (
            self.client.rpc("get_tools", {"p_process_id": process_id}).execute().data
        )
        process_tools = {}
        for tool in tools:
            process_tools[tool["name"]] = tool["transition_state_name"]

        return ProcessState(
            name=current_process_state["name"],
            tools=process_tools,
            task=current_process_state["task"],
            instructions=current_process_state["instructions"],
        )

    def get_process_data(self, process_id: str) -> Optional[ProcessData]:
        data = (
            self.client.table("processes")
            .select("*")
            .eq("id", process_id)
            .execute()
            .data
        )
        if not data:
            return None
        data = data[0]
        return ProcessData(
            id=data["id"],
            name=data["name"],
            tools_class=data["tools_class"],
            flow_type=ProcessFlowType(data["flow_type"]),
        )

    def get_process_ids(self, process_id: str) -> Optional[ProcessIds]:
        data = (
            self.client.table("processes")
            .select("*")
            .eq("id", process_id)
            .execute()
            .data
        )
        if not data:
            return None
        data = data[0]
        return ProcessIds(
            user_id=data["user_id"],
            agent_id=data["agent_id"],
            process_id=process_id,
        )

    def get_process_states(self, process_id: str) -> List[ProcessState]:
        data = (
            self.client.table("process_states")
            .select("*")
            .eq("process_id", process_id)
            .execute()
            .data
        )
        process_states = []
        if not data:
            return process_states
        for row in data:
            process_states.append(
                ProcessState(
                    name=row["name"],
                    tools=row["tools"],
                    task=row["task"],
                    instructions=row["instructions"],
                )
            )
        return process_states

    def update_current_process_state(self, process_id: str, process_state_id: str):
        self.client.table("current_process_states").update(
            {"current_state_id": process_state_id}
        ).eq("process_id", process_id).execute()
