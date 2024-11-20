import mido
import pygame.midi
import time
import zmq
import threading
from datetime import datetime

# Global variables for current playback speed and volume
old_current_speed = 0.1
current_speed = 0.1
current_volume = 0.1  # Full volume

class CustomTimer(threading.Timer):
    def __init__(self, interval, function, args=None, kwargs=None):
        super().__init__(interval, function, args, kwargs)
        self.start_time = None

    def start(self):
        self.start_time = datetime.now()
        super().start()

    def get_elapsed_time(self):
        if self.start_time:
            return (datetime.now() - self.start_time).total_seconds()
        return None
    
def zmq_listener():
    global current_speed, current_volume
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect("tcp://localhost:5556")  # Adjust as needed
    socket.setsockopt_string(zmq.SUBSCRIBE, "")

    while True:
        # Receive a message in the format "speed,volume" (e.g., "1.5,0.8")
        message = socket.recv_string()
        speed, volume = map(float, message.split(","))
        #print(f"Received new speed: {speed}, new volume: {volume}")

        # Update speed and volume
        old_current_speed = current_speed
        current_speed = speed
        current_volume = volume

def play_midi_in_real_time(file_path):
    global current_speed, current_volume

    # Initialize Pygame MIDI
    pygame.midi.init()
    output_id = pygame.midi.get_default_output_id()
    midi_out = pygame.midi.Output(output_id)
    # Set an instrument suitable for mobile melodies for babies
    instrument = 8  # music box
    midi_out.set_instrument(instrument)

    # Load the MIDI file
    midi_file = mido.MidiFile(file_path)

    def play_message(message):
        if message.type == 'note_on' or message.type == 'note_off':
            # Adjust volume by scaling the velocity
            if message.velocity > 0:  # Only adjust if there's a note_on event
                original_velocity = message.velocity
                message.velocity = int(original_velocity * current_volume)
                message.velocity = max(0, min(message.velocity, 127))  # Clamp to MIDI range

            # Send the MIDI message to the output
            midi_out.write_short(message.bytes()[0], message.bytes()[1], message.bytes()[2])

    def schedule_messages():
        global old_current_speed, current_speed
        while True:
            current_time = 0
            for message in midi_file:
                if message.time > 0:
                    if current_speed == 0:
                        # pause the playback until current_speed is different than 0
                        while current_speed == 0:
                            time.sleep(0.01)                            
                    else:
                        current_time = message.time / current_speed
                else:
                    current_time = 0
                
                thread_sound = CustomTimer(current_time, play_message, args=[message])
                thread_sound.start()
                
                while thread_sound.is_alive():
                    time.sleep(0.01)
                    
                '''
                    if current_speed != old_current_speed:
                        thread_sound.cancel()
                        if message.time > 0:
                            current_time = message.time / current_speed
                            elapsed_time = thread_sound.get_elapsed_time()
                            print("elapsed time", elapsed_time)
                            print("total time", current_time)
                        else:
                            current_time = 0
                        if current_time < elapsed_time:
                            current_time = 0
                        else:
                            current_time = current_time - elapsed_time                                        
                        thread_sound = CustomTimer(current_time, play_message, args=[message])
                        thread_sound.start()
                        old_current_speed = current_speed
                '''
    try:
        old_current_speed = current_speed
        schedule_messages()
    except KeyboardInterrupt:
        print("Playback stopped")
    finally:
        midi_out.close()
        pygame.midi.quit()

# Start the ZeroMQ listener in a separate thread
threading.Thread(target=zmq_listener, daemon=True).start()

if __name__ == "__main__":
    # Start MIDI playback with real-time speed and volume control
    # source for the file is here https://bitmidi.com/brahms-lullaby-wiegenlied-piano-mid
    file_path = "./media/brahms-lullaby-wiegenlied-piano.mid"  # Replace with your MIDI file path
    play_midi_in_real_time(file_path)