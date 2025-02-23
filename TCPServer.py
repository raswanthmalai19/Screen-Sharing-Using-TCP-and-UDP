from socket import *
import threading
import sys
import numpy
import cv2
import pickle
import zlib
import mss
import tkinter as tk


LIST = 0
THREAD = 1


class TCPServer():
    def __init__(self, port, process_type, compression_level=1, full_screen=1):
        self.clients = []
        self.type = process_type
        self.compression_level = compression_level
        self.full_screen = (full_screen == 1)
        
        # Set screen resolution explicitly
        self.screen_width = 1920  # Set desired screen width
        self.screen_height = 1080  # Set desired screen height
        
        # Set monitor to capture full screen with desired resolution
        self.monitor = {
            "top": 0,
            "left": 0,
            "width": self.screen_width,
            "height": self.screen_height
        }

        # establish the server socket
        self.server_socket = socket(AF_INET, SOCK_STREAM)
        self.server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.server_socket.bind(('', port))
        self.server_socket.listen()


    def send_frames_list(self):
        with mss.mss() as sct:  # Use context manager for mss
            try:
                while True:
                    screenshot = sct.grab(self.monitor)
                    pixel_array = numpy.array(screenshot)
                    serialized_parray = pickle.dumps(pixel_array)
                    compressed_sparray = zlib.compress(serialized_parray, self.compression_level)
                    size = len(compressed_sparray)
                    
                    # Send to all clients
                    for client in self.clients[:]:  # Create a copy of the list to iterate
                        try:
                            client.sendall((str(size) + "\n").encode())
                            client.sendall(compressed_sparray)
                        except:
                            self.clients.remove(client)
                            print("Removed a client from list of clients")
            finally:
                for client in self.clients:
                    client.close()

    def send_frames_threading(self, connection_socket):
        with mss.mss() as sct:  # Use context manager for mss
            try:
                while True:
                    screenshot = sct.grab(self.monitor)
                    pixel_array = numpy.array(screenshot)
                    serialized_parray = pickle.dumps(pixel_array)
                    compressed_sparray = zlib.compress(serialized_parray, self.compression_level)
                    size = len(compressed_sparray)
                    
                    connection_socket.sendall((str(size) + "\n").encode())
                    connection_socket.sendall(compressed_sparray)
            except Exception as e:
                print(f"Error sending frames: {e}")
            finally:
                connection_socket.close()
                print("Thread: a client has disconnected")

    def run(self):
        print(f"Server started... Capturing screen at {self.screen_width}x{self.screen_height}")

        if self.type == LIST:
            threading.Thread(target=self.send_frames_list, daemon=True).start()
            try:
                while True:
                    connection_socket, addr = self.server_socket.accept()
                    self.clients.append(connection_socket)
                    print(f"List: adding client {addr} to list of clients")
            finally:
                self.server_socket.close()
        else:
            try:
                while True:
                    connection_socket, addr = self.server_socket.accept()
                    threading.Thread(target=self.send_frames_threading, 
                                  args=(connection_socket,), 
                                  daemon=True).start()
                    print(f"Thread: client {addr} has connected")
            finally:
                self.server_socket.close()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        tcp_server = TCPServer(12345, THREAD)
    elif len(sys.argv) == 2:
        tcp_server = TCPServer(int(sys.argv[1]), THREAD)
    elif len(sys.argv) == 3 and sys.argv[1] == "TEST":
        tcp_server = TCPServer(12345, LIST, int(sys.argv[2]))
    elif len(sys.argv) == 3:
        process_type = LIST if (sys.argv[2] == "LIST") else THREAD
        tcp_server = TCPServer(int(sys.argv[1]), process_type)
    elif len(sys.argv) == 4:
        process_type = LIST if (sys.argv[2] == "LIST") else THREAD
        tcp_server = TCPServer(int(sys.argv[1]), process_type, int(sys.argv[3]))
    elif len(sys.argv) == 5:
        process_type = LIST if (sys.argv[2] == "LIST") else THREAD
        tcp_server = TCPServer(int(sys.argv[1]), process_type, int(sys.argv[3]), int(sys.argv[4]))
    else:
        print("Invalid Arguments")
        sys.exit(1)
    tcp_server.run()
