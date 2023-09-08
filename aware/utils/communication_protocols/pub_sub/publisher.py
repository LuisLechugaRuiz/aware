import zmq


class Publisher:
    def __init__(self, address, topic):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.connect(address)
        self.topic = topic

    def publish(self, message):
        self.socket.send_string(f"{self.topic} {message}")

    def close(self):
        self.socket.close()
        self.context.term()

    def __del__(self):
        self.close()
