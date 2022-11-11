import os.path
import socket
import socketserver
import pickle
from typing import Optional


HOST, PORT = "localhost", 9999
CACHE_DATA = dict()


def cache_reading(attrs: set[str], indexes: list[int], ax1_beg: Optional[int], ax1_end: Optional[int]) -> dict:
    action_type = "r".encode(encoding="ascii")
    sending_data = (tuple(attrs), tuple(indexes), ax1_beg, ax1_end)
    sending_data = pickle.dumps(sending_data)
    length = len(sending_data).to_bytes(4, byteorder="big")
    sending_data = b"".join((action_type, length, sending_data))
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((HOST, PORT))
            sock.sendall(sending_data)
            total_size = int.from_bytes(sock.recv(4), byteorder="big")
            received_data, received_size = [], 0
            while True:
                rcv = sock.recv(4096)
                received_data.append(rcv)
                received_size += len(rcv)
                if received_size >= total_size:
                    break
        return pickle.loads(received_data[0] if len(received_data) == 1 else b"".join(received_data))
    except ConnectionRefusedError:
        return {}


def cache_writing(data: dict, indexes: list[int], ax1_beg: Optional[int], ax1_end: Optional[int]):
    action_type = "w".encode(encoding="ascii")
    sending_data = (data, tuple(indexes), ax1_beg, ax1_end)
    sending_data = pickle.dumps(sending_data)
    length = len(sending_data).to_bytes(4, byteorder="big")
    sending_data = b"".join((action_type, length, sending_data))
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((HOST, PORT))
            sock.sendall(sending_data)
    except ConnectionRefusedError:
        pass


class CacheHandler(socketserver.BaseRequestHandler):

    def handle(self):
        action_type = self.request.recv(1).decode(encoding="ascii")
        total_size = int.from_bytes(self.request.recv(4), byteorder="big")
        received_data, received_size = [], 0
        while True:
            rcv = self.request.recv(4096)
            received_data.append(rcv)
            received_size += len(rcv)
            if received_size >= total_size:
                break
        data = pickle.loads(received_data[0] if len(received_data) == 1 else b"".join(received_data))
        if action_type == "r":
            sending_data = dict()
            for attr in data[0]:
                try:
                    sending_data[attr] = CACHE_DATA[(attr, data[1], data[2], data[3])]
                except KeyError:
                    pass
            sending_data = pickle.dumps(sending_data)
            length = len(sending_data).to_bytes(4, byteorder="big")
            sending_data = b"".join((length, sending_data))
            self.request.sendall(sending_data)
        else:
            for key, val in data[0].items():
                CACHE_DATA[(key, data[1], data[2], data[3])] = val


def cache_start():
    with socketserver.TCPServer((HOST, PORT), CacheHandler) as server:
        print(f"Сервер кеша запущен на ({HOST}, {PORT})")
        server.serve_forever()


if __name__ == "__main__":
    with socketserver.TCPServer((HOST, PORT), CacheHandler) as srv:
        print(f"Сервер кеша запущен на ({HOST}, {PORT})")
        srv.serve_forever()
