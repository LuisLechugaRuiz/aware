import zmq
import threading


class ActionBroker:
    def __init__(self, ip, client_port, server_port):
        self.context = zmq.Context()
        self.client_socket = self.context.socket(zmq.ROUTER)
        self.client_socket.bind(f"tcp://{ip}:{client_port}")

        self.server_socket = self.context.socket(zmq.ROUTER)
        self.server_socket.bind(f"tcp://{ip}:{server_port}")

        # Mapping of topics to server identities
        self.topic_to_server = {}

        self.thread = threading.Thread(target=self.start)
        self.thread.start()

    def start(self):
        poller = zmq.Poller()
        poller.register(self.client_socket, zmq.POLLIN)
        poller.register(self.server_socket, zmq.POLLIN)

        while True:
            socks = dict(poller.poll())

            if self.client_socket in socks:
                client_id, message = self.client_socket.recv_multipart()
                topic, actual_message = self.parse_message(message)

                server_id = self.topic_to_server.get(topic)
                if server_id:
                    self.server_socket.send_multipart(
                        [server_id, client_id, actual_message]
                    )
                else:
                    self.client_socket.send_multipart(
                        [client_id, b"Error: No server available for topic"]
                    )

            if self.server_socket in socks:
                multipart_message = self.server_socket.recv_multipart()
                if len(multipart_message) == 3:
                    server_id, client_id, response = multipart_message
                    self.client_socket.send_multipart([client_id, response])
                elif len(multipart_message) == 2:
                    server_id, message = multipart_message
                    if message.startswith(b"register "):
                        topic = message.split(b" ", 1)[1].decode()
                        self.topic_to_server[topic] = server_id

    def parse_message(self, message):
        parts = message.decode().split(" ", 1)
        return (parts[0], parts[1].encode()) if len(parts) > 1 else (None, message)

    def close(self):
        self.client_socket.close()
        self.server_socket.close()
        self.context.term()

    def __del__(self):
        self.close()
