import zmq
import threading


class Proxy:
    def __init__(self, ip, xsub_port, xpub_port):
        self.context = zmq.Context()

        # XSUB socket for publishers to connect
        self.xsub_socket = self.context.socket(zmq.XSUB)
        self.xsub_socket.bind(f"tcp://{ip}:{xsub_port}")

        # XPUB socket for subscribers to connect
        self.xpub_socket = self.context.socket(zmq.XPUB)
        self.xpub_socket.bind(f"tcp://{ip}:{xpub_port}")

        self.xsub_port = xsub_port
        self.xpub_port = xpub_port

        self.listener_thread = threading.Thread(target=self.start, daemon=True)
        self.listener_thread.start()

    def start(self):
        print(
            f"Starting ZeroMQ proxy with XSUB port {self.xsub_port} and XPUB port {self.xpub_port}"
        )
        zmq.proxy(self.xsub_socket, self.xpub_socket)

    def close(self):
        self.xsub_socket.close()
        self.xpub_socket.close()
        self.context.term()

    def __del__(self):
        self.close()
