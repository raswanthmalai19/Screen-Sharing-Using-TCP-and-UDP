# Screen Sharing Using TCP and UDP

This repository provides a Python-based implementation of a real-time screen-sharing application that utilizes both TCP and UDP protocols for data transmission. The project is designed to enable efficient sharing of screen content between devices over a network.

## Features
- **Real-Time Screen Sharing**: Captures and streams screen content to a remote client.
- **Dual Protocol Support**:
  - **TCP**: Ensures reliable transmission of essential control data and metadata.
  - **UDP**: Provides fast, low-latency streaming of screen frames.
- **Efficient Compression**: Compresses screen data to reduce bandwidth usage.
- **Cross-Platform**: Works on Windows, macOS, and Linux.
  
## How It Works
1. The **server** captures the screen content and compresses the data.
2. Using **TCP**, the server sends control signals (e.g., connection setup, resolution info).
3. The screen frames are transmitted to the client via **UDP** for low-latency streaming.
4. The **client** receives the data, decompresses it, and displays it in real-time.

   
