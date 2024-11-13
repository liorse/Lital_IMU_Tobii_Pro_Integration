import zmq
import time

context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:5555")

# Example: Send speed and volume updates
while True:
    new_speed = input("Enter new playback speed (e.g., 1.5 for 1.5x): ")
    new_volume = input("Enter new volume level (e.g., 0.8 for 80%): ")
    
    message = f"{new_speed},{new_volume}"
    socket.send_string(message)
    time.sleep(0.1)  # Small delay to avoid flooding messages
