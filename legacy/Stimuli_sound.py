import numpy as np
import sounddevice as sd
import librosa
import zmq
import threading

# Global variables for current playback speed and volume level
current_speed = 1.0
current_volume = 1.0  # Volume as a multiplier (1.0 is 100%)

def zmq_listener():
    global current_speed, current_volume
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect("tcp://localhost:5555")  # Adjust as needed
    socket.setsockopt_string(zmq.SUBSCRIBE, "")

    while True:
        # Receive message in the format "speed,volume" (e.g., "1.5,0.8")
        message = socket.recv_string()
        speed, volume = map(float, message.split(","))
        print(f"Received new speed: {speed}, new volume: {volume}")
        current_speed = speed
        current_volume = volume

def play_audio_in_real_time_loop(file_path):
    global current_speed, current_volume

    # Load the audio file
    y, sr = librosa.load(file_path, sr=None)

    # decrease the buffer size to reduce latency to 3 seconds
    # reduce y to 3 seconds length
    #y = y[:sr*30]
    sd.default.latency = 'low'

    # Define chunk size for real-time streaming
    chunk_size = 2048

    # Start real-time playback using sounddevice
    stream = sd.OutputStream(samplerate=sr, channels=1, dtype='float32')
    stream.start()
    i = 0
    buffer = librosa.effects.time_stretch(y, rate = current_speed)
    try:
        while True:  # Loop indefinitely to play audio in a loop
            # Adjust playback speed without changing pitch
            if i + chunk_size > len(buffer):
                i = 0
            current_pos_ratio = i/len(buffer)
            buffer = librosa.effects.time_stretch(y, rate = current_speed)
            start_buffer = int(current_pos_ratio*len(buffer))
            # Play the audio chunks with volume adjustment
            old_speed = current_speed
            
            for i in range(start_buffer, len(buffer), chunk_size):
                chunk = buffer[i:i + chunk_size]

                # Apply volume control
                chunk = chunk * current_volume

                # Ensure each chunk is the correct shape for streaming
                if len(chunk) < chunk_size:
                    chunk = np.pad(chunk, (0, chunk_size - len(chunk)), 'constant')
                
                # Play the adjusted audio chunk
                stream.write(chunk)
                
                if old_speed != current_speed:
                    break
                    


    except KeyboardInterrupt:
        print("Playback stopped")
    finally:
        stream.stop()
        stream.close()

# Start the ZeroMQ listener in a separate thread
threading.Thread(target=zmq_listener, daemon=True).start()

# Start audio playback in real-time loop
file_path = "./media/Mobile_movie_30_sec.wav"  # Replace with your file path
play_audio_in_real_time_loop(file_path)
