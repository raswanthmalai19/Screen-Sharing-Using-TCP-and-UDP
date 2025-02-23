import socket
import sys
import cv2
import numpy as np
import struct
import tkinter as tk
import pickle
import zlib

class UDPClient:
    def __init__(self, hostname, port, full_screen):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
        self.server_address = (socket.gethostbyname(hostname), port)

        # Get screen dimensions
        root = tk.Tk()
        self.screen_width = root.winfo_screenwidth()
        self.screen_height = root.winfo_screenheight()
        root.destroy()

        # Set display dimensions
        self.display_width = self.screen_width if full_screen == 1 else 1280
        self.display_height = self.screen_height if full_screen == 1 else 720
        self.full_screen = (full_screen == 1)

        self.MAX_PACKET_SIZE = 65507
        self.PAYLOAD_SIZE = self.MAX_PACKET_SIZE - 4

        print(f"Connected to server at {self.server_address}")

    def receive_frame(self):
        try:
            self.client_socket.sendto(b'READY', self.server_address)

            metadata, _ = self.client_socket.recvfrom(8)
            total_packets, frame_size = struct.unpack('!II', metadata)

            chunks = [None] * total_packets
            received_packets = 0
            self.client_socket.settimeout(1)

            while received_packets < total_packets:
                try:
                    packet, _ = self.client_socket.recvfrom(self.MAX_PACKET_SIZE)
                    packet_index = struct.unpack('!I', packet[:4])[0]
                    packet_data = packet[4:]

                    if packet_index < total_packets and chunks[packet_index] is None:
                        chunks[packet_index] = packet_data
                        received_packets += 1

                except socket.timeout:
                    print(f"Timeout: Received {received_packets}/{total_packets} packets")
                    return None

            if all(chunk is not None for chunk in chunks):
                frame_data = b''.join(chunks)
                decompressed_data = zlib.decompress(frame_data)
                frame = pickle.loads(decompressed_data)
                return frame

        except Exception as e:
            print(f"Error receiving frame: {e}")

        return None

    def run(self):
        cv2.namedWindow("Screen Share", cv2.WINDOW_NORMAL)

        if self.full_screen:
            cv2.setWindowProperty("Screen Share", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        else:
            cv2.resizeWindow("Screen Share", self.display_width, self.display_height)

        self.client_socket.settimeout(None)

        try:
            while True:
                frame = self.receive_frame()
                if frame is not None:
                    if len(frame.shape) == 3:
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    frame = cv2.resize(frame, (self.display_width, self.display_height))
                    cv2.imshow("Screen Share", frame)

                if cv2.waitKey(1) & 0xFF == 27:  # ESC key to exit
                    break

        except KeyboardInterrupt:
            print("Client shutting down...")
        finally:
            cv2.destroyAllWindows()
            self.client_socket.close()

# Client Initialization
if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: python client.py <server_ip> <port> <full_screen>")
        sys.exit(1)

    hostname = sys.argv[1]
    port = int(sys.argv[2])
    full_screen = int(sys.argv[3])

    client = UDPClient(hostname, port, full_screen)
    client.run()