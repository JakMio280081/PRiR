import socket
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from PIL import Image

from send import send_all
from receive import receive_all

PORT = 2040


def split_image(image, n_clients):
    width, height = image.size
    fragments = []
    for i in range(n_clients):
        start = i * height // n_clients
        end = (i + 1) * height // n_clients
        top = max(0, start - 1)
        bottom = min(height, end + 1)
        fragment = np.array(image.crop((0, top, width, bottom)))
        fragments.append((start, end, top, fragment))
    return fragments


def merge_image(processed_fragments, width, height):
    result = np.zeros((height, width), dtype=np.uint8)
    for start, fragment in processed_fragments:
        result[start:start + fragment.shape[0], :] = fragment
    return Image.fromarray(result)


def handle_client(client_socket, fragment, client_number):
    with client_socket:
        send_all(client_socket, fragment)
        print(f"Wyslano fragment do klienta {client_number}", flush=True)
        processed_fragment = receive_all(client_socket)
        print(f"Odebrano wynik od klienta {client_number}", flush=True)
        return processed_fragment


def server_main(image_path, n_clients):
    image = Image.open(image_path).convert("L")
    if not 1 <= n_clients <= image.height:
        raise ValueError("Liczba klientow musi wynosic od 1 do wysokosci obrazu")
    fragments = split_image(image, n_clients)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(("0.0.0.0", PORT))
        server_socket.listen(n_clients)
        print(f"Serwer nasluchuje na porcie {PORT}. Czeka na {n_clients} klientow...", flush=True)

        connections = []
        for i in range(n_clients):
            client_socket, address = server_socket.accept()
            print(f"Polaczono z klientem {i + 1}: {address}", flush=True)
            connections.append(client_socket)

        with ThreadPoolExecutor(max_workers=n_clients) as pool:
            tasks = [
                pool.submit(handle_client, connections[i], fragments[i], i + 1)
                for i in range(n_clients)
            ]
            processed_fragments = [task.result() for task in tasks]

    result_image = merge_image(processed_fragments, image.width, image.height)
    result_image.save("processed_image.png")
    print("Gotowe! Wynik zapisano w processed_image.png", flush=True)


if __name__ == "__main__":
    image_path = sys.argv[1] if len(sys.argv) > 1 else "obraz.png"
    n_clients = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    server_main(image_path, n_clients)
