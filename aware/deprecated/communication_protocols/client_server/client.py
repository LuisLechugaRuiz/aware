import zmq


class Client:
    def __init__(self, address):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.DEALER)
        self.socket.connect(address)

    def send(self, topic, message):
        formatted_message = f"{topic} {message}"
        self.socket.send_string(formatted_message)

        multipart_response = self.socket.recv_multipart()
        response = multipart_response[-1].decode("utf-8")
        return response

    def close(self):
        self.socket.close()
        self.context.term()

    def __del__(self):
        self.close()
