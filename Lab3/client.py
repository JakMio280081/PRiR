import socket
import sys

import numpy as np

from send import send_all
from receive import receive_all

PORT = 2040


def edge_filter(task):
    start, end, top, fragment = task
    gray = fragment.astype(np.float32)
    padded = np.pad(gray, 1, mode="edge")

    a = padded[:-2, :-2]
    b = padded[:-2, 1:-1]
    c = padded[:-2, 2:]
    d = padded[1:-1, :-2]
    f = padded[1:-1, 2:]
    g = padded[2:, :-2]
    h = padded[2:, 1:-1]
    i = padded[2:, 2:]

    gx = -a + c - 2 * d + 2 * f - g + i
    gy = -a - 2 * b - c + g + 2 * h + i
    result = np.clip(np.sqrt(gx * gx + gy * gy), 0, 255).astype(np.uint8)
    return start, result[start - top:end - top]


def client_main(server_ip):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((server_ip, PORT))
        print("Polaczono z serwerem")
        fragment = receive_all(client_socket)
        print("Odebrano fragment obrazu")
        processed_fragment = edge_filter(fragment)
        send_all(client_socket, processed_fragment)
        print("Fragment przetworzony i wyslany do serwera")


if __name__ == "__main__":
    server_ip = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    client_main(server_ip)
