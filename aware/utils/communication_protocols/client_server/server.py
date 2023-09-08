import zmq
import threading


class Server:
    def __init__(self, address, topics, callback):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.DEALER)
        self.socket.connect(address)  # Connect to broker's backend
        self.callback = callback

        # Register the server for the given topics
        for topic in topics:
            self.socket.send_string(f"register {topic}")

        self.listener_thread = threading.Thread(target=self.listen, daemon=True)
        self.listener_thread.start()

    def listen(self):
        while True:
            multipart_message = self.socket.recv_multipart()
            # Unpack the multipart message
            client_id, actual_message = multipart_message
            message = multipart_message[-1].decode("utf-8")  # Decode the last part
            response = self.callback(message)
            self.socket.send_multipart([client_id, response.encode("utf-8")])

    def close(self):
        self.socket.close()
        self.context.term()

    def __del__(self):
        self.close()
