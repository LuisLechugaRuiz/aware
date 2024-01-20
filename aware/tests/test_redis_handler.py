import unittest
import json
from unittest.mock import Mock
from redis import Redis
from aware.data.database.redis_handler.redis_handler import RedisHandler
from aware.chat.new_conversation_schemas import (
    ChatMessage,
    UserMessage,
    AssistantMessage,
    SystemMessage,
    ToolResponseMessage,
    ToolCall,
    ToolCalls,
    Function,
)


class TestRedisHandler(unittest.TestCase):
    def setUp(self):
        # Mock Redis client
        self.mock_redis_client = Mock(spec=Redis)

        # Create instance of RedisHandler with the mocked client
        self.redis_handler = RedisHandler(self.mock_redis_client)

    def test_add_message(self):
        # Setup
        chat_id = "conv1"
        message_id = "msg1"
        timestamp = "1234567890"
        message = UserMessage(name="Alice", content="Hello")

        # Prepare the expected data format
        inner_data = message.to_json()  # This is already a JSON string
        outer_data = json.dumps({"type": "UserMessage", "data": inner_data})
        expected_message_data = {
            "data": outer_data
        }  # The outer dictionary to be passed to hmset

        # Execute
        chat_message = ChatMessage(message_id, timestamp, message)
        self.redis_handler.add_message(chat_id, chat_message)

        # Assert
        message_key = f"conversation:{chat_id}:message:{message_id}"
        self.mock_redis_client.hmset.assert_called_with(
            message_key, expected_message_data
        )
        self.mock_redis_client.zadd.assert_called_with(
            f"conversation:{chat_id}", {message_key: float(timestamp)}
        )

    def test_get_conversation(self):
        # Setup
        chat_id = "conv1"
        message_keys = [f"conversation:{chat_id}:message:{i}" for i in range(1, 6)]
        self.mock_redis_client.zrange.return_value = message_keys

        # Mocking Redis hget responses for each message
        test_function = Function(arguments='{"arg1":"value1"}', name="test_function")

        tool_call = ToolCall(
            id="this_is_test_function_id",
            type="function",
            function=test_function,
        )
        tool_calls = ToolCalls(name="Bot", tool_calls=[tool_call])

        self.mock_redis_client.hget.side_effect = [
            json.dumps(
                {
                    "type": "SystemMessage",
                    "data": json.dumps({"content": "A random test"}),
                }
            ).encode(),
            json.dumps(
                {
                    "type": "UserMessage",
                    "data": json.dumps(
                        {"name": "Alice", "content": "Hello, call test function"}
                    ),
                }
            ).encode(),
            json.dumps(
                {
                    "type": "AssistantMessage",
                    "data": json.dumps({"name": "Bot", "content": "Hi there"}),
                }
            ).encode(),
            json.dumps(
                {
                    "type": "ToolCalls",
                    "data": json.dumps(tool_calls.to_dict()),
                }
            ).encode(),
            json.dumps(
                {
                    "type": "ToolResponseMessage",
                    "data": json.dumps(
                        {
                            "content": "Test function called properly",
                            "tool_call_id": "this_is_test_function_id",
                        }
                    ),
                }
            ).encode(),
        ]

        # Execute
        conversation = self.redis_handler.get_conversation(chat_id)
        print(conversation)

        # Assert
        self.assertEqual(len(conversation), 5)
        self.assertIsInstance(conversation[0], SystemMessage)
        self.assertIsInstance(conversation[1], UserMessage)
        self.assertIsInstance(conversation[2], AssistantMessage)
        self.assertIsInstance(conversation[3], ToolCalls)
        self.assertIsInstance(conversation[4], ToolResponseMessage)
        self.assertEqual(conversation[0].content, "A random test")
        self.assertEqual(conversation[1].content, "Hello, call test function")
        self.assertEqual(conversation[2].content, "Hi there")
        self.assertEqual(
            conversation[3].to_dict()["tool_calls"][0]["id"],
            "this_is_test_function_id",
        )
        self.assertEqual(
            conversation[3].to_dict()["tool_calls"][0]["function"]["name"],
            "test_function",
        )
        self.assertEqual(conversation[4].tool_call_id, "this_is_test_function_id")

        # Print the full conversation as string
        for message in conversation:
            print(message.to_string())

    def tearDown(self):
        self.mock_redis_client.reset_mock()


if __name__ == "__main__":
    unittest.main()
