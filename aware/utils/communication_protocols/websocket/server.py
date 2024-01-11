import asyncio
import websockets
import json


class WebSocketServer:
    clients = set()

    def __init__(self, host, port, callback):
        self.host = host
        self.port = port
        self.callback = callback

    async def handler(self, websocket, path):
        self.clients.add(websocket)
        print("NEW CLIENT")
        try:
            async for message in websocket:
                data = json.loads(message)
                actual_message = data["message"]
                await self.callback(actual_message)
        finally:
            self.clients.remove(websocket)

    async def send_message(self, message):
        if self.clients:  # Check if there are any clients connected
            tasks = [
                asyncio.create_task(client.send(message)) for client in self.clients
            ]
            await asyncio.wait(tasks)

    async def run(self):
        async with websockets.serve(self.handler, self.host, self.port):
            await asyncio.Future()  # Run the server forever
