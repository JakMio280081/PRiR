import pickle


def receive_exact(sock, size):
    data = bytearray()
    while len(data) < size:
        part = sock.recv(min(4096, size - len(data)))
        if not part:
            raise ConnectionError("Polaczenie zostalo przerwane")
        data.extend(part)
    return bytes(data)


def receive_all(sock):
    length = int.from_bytes(receive_exact(sock, 4), byteorder="big")
    if length > 100_000_000:
        raise ValueError("Zbyt duza wiadomosc")
    return pickle.loads(receive_exact(sock, length))
