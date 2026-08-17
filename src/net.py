import pickle
import socket
import threading
import time


class Network:
    """Class managing TCP socket communication between players."""

    def __init__(self, port: int = 8080):
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn = None
        self.opponent_ready = False

    @staticmethod
    def get_local_ip() -> str:
        """Detect local IPv4 address."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        except Exception:
            ip = "127.0.0.1"
        finally:
            s.close()
        return ip

    def start_server(self):
        """Start TCP server and wait for incoming connection."""
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(("0.0.0.0", self.port))
        self.socket.listen(1)
        self.conn, addr = self.socket.accept()
        return addr

    def connect(self, ip: str, port: int):
        """Connect to host server."""
        self.socket.connect((ip, port))
        self.conn = self.socket

    def reset_ready(self):
        """Reset ready state for rematch rounds."""
        self.opponent_ready = False

    def _listen_for_ready(self):
        """Thread worker listening for ready signal."""
        while not self.opponent_ready:
            try:
                data = self.conn.recv(1024).decode().strip()
                if "READY" in data:
                    self.opponent_ready = True
                    break
            except Exception:
                break

    def wait_for_opponent(self) -> bool:
        """Synchronize start/rematch with opponent."""
        listen_thread = threading.Thread(
            target=self._listen_for_ready, daemon=True
        )
        listen_thread.start()

        try:
            self.conn.sendall("READY\n".encode())
        except Exception as e:
            print(f"❌ Network Error: Failed to send READY signal: {e}")
            return False

        print("⏳ Waiting for opponent to finish setup...")
        while not self.opponent_ready:
            time.sleep(0.2)

        print("⚡ Opponent is ready! Starting game...\n")
        return True

    def send_data(self, data):
        """Serialize and send Python object."""
        try:
            serialized = pickle.dumps(data)
            self.conn.sendall(len(serialized).to_bytes(4, "big") + serialized)
        except Exception as e:
            print(f"❌ Error sending data: {e}")

    def recv_data(self):
        """Receive and deserialize Python object."""
        try:
            raw_size = self.conn.recv(4)
            if not raw_size:
                return None
            size = int.from_bytes(raw_size, "big")
            data = bytearray()
            while len(data) < size:
                packet = self.conn.recv(size - len(data))
                if not packet:
                    return None
                data.extend(packet)
            return pickle.loads(data)
        except Exception:
            return None
