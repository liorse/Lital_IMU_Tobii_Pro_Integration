import zmq
import sys
import time

def main():
    context = zmq.Context()
    socket = context.socket(zmq.PUSH)
    socket.bind("tcp://*:5555")  # Bind to the port to allow connections

    try:
        while True:
            frame_rate = input("Enter frame rate: ")
            socket.send_string(frame_rate)
            print(f"Sent frame rate: {frame_rate}")
            #time.sleep(0.1)  # Adjust the sleep time as needed
    except KeyboardInterrupt:
        print("Interrupted by user. Exiting...")
    finally:
        socket.close()
        context.term()
        sys.exit(0)

if __name__ == "__main__":
    main()