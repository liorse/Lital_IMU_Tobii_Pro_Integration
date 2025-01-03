import mido
import pygame.midi
import time
import zmq
import threading

# Global variables for current playback speed and volume
current_speed = 1.0
current_volume = 1.0  # Full volume

def zmq_listener():
    global current_speed, current_volume
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect("tcp://localhost:5555")  # Adjust as needed
    socket.setsockopt_string(zmq.SUBSCRIBE, "")

    while True:
        # Receive a message in the format "speed,volume" (e.g., "1.5,0.8")
        message = socket.recv_string()
        speed, volume = map(float, message.split(","))
        print(f"Received new speed: {speed}, new volume: {volume}")

        # Update speed and volume
        current_speed = speed
        current_volume = volume

def play_midi_in_real_time(file_path):
    global current_speed, current_volume

    # Initialize Pygame MIDI
    pygame.midi.init()
    output_id = pygame.midi.get_default_output_id()
    midi_out = pygame.midi.Output(output_id)
    # Set an instrument suitable for mobile melodies for babies
    instrument = 8 # music box
    midi_out.set_instrument(instrument)

    # Load the MIDI file
    midi_file = mido.MidiFile(file_path)

    try:
        # Loop through the MIDI messages
        for message in midi_file.play():
            if message.type == 'note_on' or message.type == 'note_off':
                # Adjust volume by scaling the velocity
                if message.velocity > 0:  # Only adjust if there's a note_on event
                    original_velocity = message.velocity
                    message.velocity = int(original_velocity * current_volume)
                    message.velocity = max(0, min(message.velocity, 127))  # Clamp to MIDI range

                # Send the MIDI message to the output
                midi_out.write_short(message.bytes()[0], message.bytes()[1], message.bytes()[2])

            # Adjust the delay based on the current speed
            #time.sleep(message.time / current_speed)
            #time.sleep(0.1)
    except KeyboardInterrupt:
        print("Playback stopped")
    finally:
        midi_out.close()
        pygame.midi.quit()

# Start the ZeroMQ listener in a separate thread
threading.Thread(target=zmq_listener, daemon=True).start()

# Start MIDI playback with real-time speed and volume control
file_path = "./media/brahms-lullaby-wiegenlied-piano.mid"  # Replace with your MIDI file path
play_midi_in_real_time(file_path)
