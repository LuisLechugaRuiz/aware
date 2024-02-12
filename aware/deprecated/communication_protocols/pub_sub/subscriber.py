import zmq
import threading


class Subscriber:
    def __init__(self, address, topic, callback):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect(address)
        self.socket.subscribe(topic)
        self.callback = callback
        self.listener_thread = threading.Thread(target=self.listen, daemon=True)
        self.listener_thread.start()

    def listen(self):
        while True:
            message = self.socket.recv_string()
            topic, message = self.parse_message(message)
            self.callback(message)

    def parse_message(self, message):
        parts = message.split(" ", 1)
        if len(parts) > 1:
            topic = parts[0]
            actual_message = parts[1].lstrip()  # Remove leading spaces
            return topic, actual_message
        else:
            return None, message

    def close(self):
        self.socket.close()
        self.context.term()

    def __del__(self):
        self.close()
