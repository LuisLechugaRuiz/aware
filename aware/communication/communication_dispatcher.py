# TODO: This class will receive certain "events" from communication handler and manage the reaction at system level. i.e: Activating other processes or adding info to their conversations.


class CommunicationDispatcher:
    def __init__(self):
        pass

    def create_request(self, request: Request) -> Request:
        pass

    def create_event(self, event: Event) -> Event:
        pass

    def update_topic(
        self,
        topic_publisher: TopicPublisher,
        message: Dict[str, Any],
        function_call_id: str,
    ) -> str:
        pass

    def set_request_completed(self, function_args: Dict[str, Any]):
        pass

    # TODO: Implement this to manage events state.
    # def set_event_completed(self, event: Event):
    #     pass

    def update_request_feedback(self, request: Request, feedback: str):
        pass
