from socket import *
import sys
import cv2
import pickle
import zlib
import tkinter as tk

class TCPClient:
    def __init__(self, hostname, port, full_screen):
        self.client_socket = socket(AF_INET, SOCK_STREAM)
        self.client_socket.connect((gethostbyname(hostname), port))
        
        # Get screen dimensions
        root = tk.Tk()
        self.screen_width = root.winfo_screenwidth()
        self.screen_height = root.winfo_screenheight()
        root.destroy()
        
        # Initialize display dimensions
        self.display_width = self.screen_width if full_screen == 1 else 1280
        self.display_height = self.screen_height if full_screen == 1 else 720
        self.full_screen = (full_screen == 1)

    def calculate_display_size(self, frame_width, frame_height):
        """Calculate the optimal display size maintaining aspect ratio"""
        screen_ratio = self.display_width / self.display_height
        frame_ratio = frame_width / frame_height
        
        if frame_ratio > screen_ratio:
            new_width = self.display_width
            new_height = int(self.display_width / frame_ratio)
        else:
            new_height = self.display_height
            new_width = int(self.display_height * frame_ratio)
            
        return new_width, new_height
    
    def resize_window(self, width, height):
        cv2.namedWindow("Screen Share", cv2.WINDOW_NORMAL)
        
        if self.full_screen:
            cv2.setWindowProperty("Screen Share", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        else:
            cv2.moveWindow("Screen Share", 
                         (self.screen_width - width) // 2,
                         (self.screen_height - height) // 2)
            cv2.resizeWindow("Screen Share", width, height)
    
    def receive_frame_data(self):
        """Receive the complete frame data from server"""
        # First receive the total size of the frame data
        size_data = b''
        while b'\n' not in size_data:
            size_data += self.client_socket.recv(1)
        
        frame_size = int(size_data.decode().strip())
        
        # Now receive the complete frame data
        frame_data = b''
        remaining = frame_size
        
        while remaining > 0:
            # Receive in chunks of 8192 bytes
            chunk_size = min(remaining, 8192)
            chunk = self.client_socket.recv(chunk_size)
            if not chunk:
                raise ConnectionError("Connection lost while receiving frame data")
            frame_data += chunk
            remaining -= len(chunk)
            
        return frame_data
    
    def run(self):
        first_frame = True
        
        try:
            while True:
                try:
                    # Receive the complete frame data
                    frame_data = self.receive_frame_data()
                    
                    # Decompress and unpickle the frame
                    frame = pickle.loads(zlib.decompress(frame_data))
                    
                    # Get frame dimensions
                    frame_height, frame_width = frame.shape[:2]
                    
                    # Calculate proper display dimensions on first frame
                    if first_frame:
                        display_width, display_height = self.calculate_display_size(frame_width, frame_height)
                        self.resize_window(display_width, display_height)
                        first_frame = False
                    
                    # Resize frame while maintaining aspect ratio
                    frame_resized = cv2.resize(frame, 
                                            (display_width, display_height),
                                            interpolation=cv2.INTER_AREA)
                    
                    # Display frame
                    cv2.imshow("Screen Share", frame_resized)
                    
                    if cv2.waitKey(1) == 27:
                        break
                        
                except Exception as e:
                    print("Error:", e)
                    continue
                    
        finally:
            print("Disconnected from server")
            self.client_socket.close()
            cv2.destroyAllWindows()

# Parse command line arguments
if len(sys.argv) == 4:
    hostname = sys.argv[1]
    port = int(sys.argv[2])
    full_screen = int(sys.argv[3])
    tcp_client = TCPClient(hostname, port, full_screen)
    tcp_client.run()
else:
    print("Invalid arguments. Usage: python client.py <hostname> <port> <full_screen>")
    sys.exit(1)