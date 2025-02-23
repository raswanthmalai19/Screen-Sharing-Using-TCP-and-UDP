import socket
import struct
import pickle
import zlib
import time
import mss
import numpy as np
import cv2

class UDPServer:
    def __init__(self, port, compression_level=1):
        self.clients = set()
        self.compression_level = compression_level
        self.running = True

        # Set up screen capture
        self.sct = mss.mss()
        self.monitor = self.sct.monitors[1]

        # Define UDP parameters
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('', port))

        self.MAX_PACKET_SIZE = 65507
        self.PAYLOAD_SIZE = self.MAX_PACKET_SIZE - 4
        self.frame_interval = 1 / 30  # 30 FPS

        print(f"Server started on port {port}")

    def capture_screen(self):
        screenshot = self.sct.grab(self.monitor)
        frame = np.array(screenshot)
        return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

    def process_frame(self, frame):
        serialized = pickle.dumps(frame)
        compressed = zlib.compress(serialized, self.compression_level)
        return compressed

    def split_frame_data(self, frame_data):
        packets = []
        total_packets = (len(frame_data) + self.PAYLOAD_SIZE - 1) // self.PAYLOAD_SIZE

        for i in range(total_packets):
            start_pos = i * self.PAYLOAD_SIZE
            end_pos = start_pos + self.PAYLOAD_SIZE
            chunk = frame_data[start_pos:end_pos]
            packet = struct.pack('!I', i) + chunk
            packets.append(packet)

        return packets, total_packets

    def send_frame_to_client(self, frame_data, client_address):
        try:
            packets, total_packets = self.split_frame_data(frame_data)
            metadata = struct.pack('!II', total_packets, len(frame_data))
            self.server_socket.sendto(metadata, client_address)

            for packet in packets:
                self.server_socket.sendto(packet, client_address)
                time.sleep(0.0001)  # Slight delay between packets for smoother transmission
            return True
        except socket.timeout:
            print(f"Timeout while sending to {client_address}. Retrying connection...")
            return False
        except Exception as e:
            print(f"Error sending frame to {client_address}: {e}")
            return False

    def handle_clients(self):
        last_frame_time = 0
        while self.running:
            current_time = time.time()
            if current_time - last_frame_time < self.frame_interval:
                time.sleep(0.001)
                continue

            frame = self.capture_screen()
            frame_data = self.process_frame(frame)

            for client in list(self.clients):
                if not self.send_frame_to_client(frame_data, client):
                    self.clients.remove(client)
                    print(f"Client disconnected: {client}")

            last_frame_time = current_time

            # Check for new clients
            try:
                self.server_socket.settimeout(0.1)  # Increased timeout for new clients
                data, client_address = self.server_socket.recvfrom(1024)
                if data == b'READY':
                    if client_address not in self.clients:
                        self.clients.add(client_address)
                        print(f"New client connected: {client_address}")
            except socket.timeout:
                continue

    def run(self):
        print("Waiting for clients to connect...")
        try:
            self.handle_clients()
        except KeyboardInterrupt:
            print("Server shutting down...")
        finally:
            self.cleanup()

    def cleanup(self):
        self.running = False
        self.sct.close()
        self.server_socket.close()

# Server Initialization
if __name__ == '__main__':
    port = 12345  # Use your desired port
    server = UDPServer(port)
    server.run()
