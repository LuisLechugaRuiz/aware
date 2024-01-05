import threading

from aware.agent.memory.memory_manager import MemoryManager
from aware.architecture.helpers.topics import DEF_SEARCH_DATABASE
from aware.chat.chat import Chat
from aware.config.config import Config
from aware.utils.communication_protocols import Client
from aware.utils.logger.file_logger import FileLogger


DEF_DEFAULT_EMPTY_CONTEXT = "No context yet, please update it."


class SystemMemoryManager(MemoryManager):
    def __init__(self):
        # What do we want?
        # - Search for user data -> A client to search user data.
        # - Search for system data -> Based on specific tool.
        # - Store data at System.
        # - Context to maintain a narrative of the task.
        # - Thought to optimize the execution based on the discover data.

        # In this case the memory should explore existing info to provide the most relevant knowledge to the executor.

        # TODO: This are not UserMessages but execution of the different tools...
        self.messages_queue: Queue[UserMessage] = Queue()

        # it should also save information releated to the task REFLECTING on the execution and saving LEARNINGS!
        self.run_thread = threading.Thread(target=self.run_memory_agent)
        self.run_thread.start()
        self.conversation_timer = None
        self.thought = ""
        self.context = DEF_DEFAULT_EMPTY_CONTEXT

        # TODO: ADAPT FUNCTIONS - THIS AGENT WILL RUN TWO DIFFERENT EXECUTIONS:
        # 1 - SAVE INFO FROM A CONVERSATION - MEANS UPDATING USER PROFILE IF NEEDED.
        # 2 - SEARCH FOR INFO - MEANS RUNNING THE AGENT AND WAITING FOR THE RESPONSE - WILL BE CALLED BY THE ASSISTANT.
        self.conversation_functions = [
            self.append_context,
            self.edit_context,
            self.transmit_insight,
            self.wait_for_user,
        ]

        # TODO: use user_id.
        user_name = self.get_name()

        # TODO: ADAPTT
        super().__init__(
            user_name=user_name,
            chat=Chat(
                module_name="user_memory_manager",
                logger=FileLogger("user_memory_manager", should_print=False),
                system_prompt_kwargs={
                    "user_name": user_name,
                    "assistant_name": Config().assistant_name,
                    "user_profile": self.user_profile.to_string(),
                    "context": "No context yet, please update me.",
                    "conversation_warning_threshold": False,
                    "conversation_remaining_tokens": Config().max_conversation_tokens,
                },
                assistant_name=f"{Config().assistant_name}_memory_manager",
                api_key=Config().openai_memory_api_key,
            ),
            functions=self.conversation_functions,
            logger=FileLogger("user_memory_manager", should_print=False),
        )
        if register:
            self.create_user(name=user_name)

        # TODO: Handle this properly, should we search for info at any category or run the agent?? !!
        # ON NEW MESSAGE JUST ADD IT AS USER FOR OUR AGENT AND WAIT FOR THE RESPONSE!!!!
        self.search_user_info_client = Client(
            address=f"tcp://{Config().assistant_ip}:{Config().client_port}",
            topics=[f"{self.user_name}_{DEF_SEARCH_DATABASE}"],
        )

    def update_system(self):
        """Override the default update system to add the user profile and context."""

        remaining_tokens, should_trigger_warning = self.chat.get_remaining_tokens()
        system_prompt_kwargs = {
            "user_name": self.user_name,
            "assistant_name": Config().assistant_name,
            "context": self.get_context(),
            "conversation_warning_threshold": should_trigger_warning,
            "conversation_remaining_tokens": remaining_tokens,
        }
        self.chat.edit_system_message(system_prompt_kwargs=system_prompt_kwargs)

    def run_memory_agent(self):
        while True:
            # Wait for a message to arrive.
            while self.messages_queue.empty():
                pass

            # Fill with all the messages.
            while not self.messages_queue.empty():
                message = self.messages_queue.get()

                self.chat.conversation.add_user_message(
                    message.message, user_name=message.user_name
                )

                self.messages_queue.task_done()

            # Transmit the insight to the agent.
            message = self.run_agent()
            if message:
                self.transmit_insight(message)
                self.logger.info(f"Agent finished with message: {message}")

    def get_context(self):
        # TODO: Make this thread safe.

        if self.context is None:
            conversation_summary = self.weaviate_db.get_last_conversation_summary()
            if conversation_summary.error is None:
                self.context = conversation_summary.data
            else:
                self.context = ""

        return self.context

    # TODO: THIS CONVERSATION SHOULD BE CALLED ON CONVERSATION FINISHES OR AFTER X AMOUNT OF TOKENS TO STORE A PERMANENT SUMMARY (THE CONTEXT)
    def on_conversation_finished(self):
        """
        Store the summary of the conversation in the database.
        """
        # print(
        #     "CONVERSATION FINISHED, NOW I SHOULD ASK THE LLM TO PROVIDE A POTENTIAL QUERY BEFORE SAVING!"
        # )
        # potential_query = input(
        #     "DEBUGGING, ADD A POTENTIAL QUERY: "
        # )  # TODO: ASK THE AGENT.
        # result = self.weaviate_db.store_conversation(
        #     user_name=self.user_name,
        #     summary=self.get_context(),
        #     potential_query=potential_query,
        # )
        # return result
        pass

    def wait_for_user(self):
        """
        Pauses operations, awaiting the next user input before proceeding.
        """
        self.stop_agent()
        return "Waiting for user's input..."

    def search_conversation(self, query: str):
        """
        Search for a specific query in the conversation.

        Args:
            query (str): Query to search for.
        """
        return self.weaviate_db.search_conversation(query)

    def edit_context(self, old_data: str, new_data: str):
        """
        Edit the assistant's context overwriting the old context with the new context.

        Args:
            old_data (str): Old data that should be replaced.
            new_data (str): New data to replace the old data.
        """
        # TODO: Make this thread safe.
        try:
            self.context.replace(old_data, new_data)
            return "Context edited."
        except Exception as e:
            return f"Error while editing context: {e}"

    def append_context(self, data: str):
        """
        Append data at the end of the assistant's context.

        Args:
            data (str): Data to be appended.
        """
        if self.context == DEF_DEFAULT_EMPTY_CONTEXT:
            self.context = ""
        # TODO: Make this thread safe.
        self.context += data
        return "Context appended."

    def search_user_info(self, query: str):
        user_info = self.search_user_info_client.send(
            topic=f"{self.user_name}_{DEF_SEARCH_DATABASE}", message=query
        )

    def transmit_insight(self, insight: str):
        """
        Crafts a strategic insight in the first person, as if it's the agent's own thought.
        This insight is intended to optimize the agent's performance to achieve the task using the tools at its disposal.

        Args:
            insight (str): A strategic insight or piece of advice, phrased as if it's the agent's own thought.
        """
        print(f"Thought: {insight}")
        self.thought = insight
        self.stop_agent()  # TODO: Define if we should stop after thinking.
        return "Insight transmitted."
