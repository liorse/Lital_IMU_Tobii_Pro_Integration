import pygame
import ffmpeg
import zmq
import numpy as np
import cv2

def extract_frames(movie_path):
    probe = ffmpeg.probe(movie_path)
    video_info = next(stream for stream in probe['streams'] if stream['codec_type'] == 'video')
    width = int(video_info['width'])
    height = int(video_info['height'])
    out, _ = (
        ffmpeg
        .input(movie_path)
        .output('pipe:', format='rawvideo', pix_fmt='rgb24')
        .global_args('-threads', '10')  # Adjust the number of threads as needed
        .run(capture_stdout=True)
    )
    video = np.frombuffer(out, np.uint8).reshape([-1, height, width, 3])
    return video, width, height

def main(movie_path, zmq_port):
    pygame.init()
    frames, width, height = extract_frames(movie_path)
    
    # Get the screen dimensions
    screen_info = pygame.display.Info()
    screen_width = screen_info.current_w
    screen_height = screen_info.current_h
    
    screen = pygame.display.set_mode((screen_width, screen_height))
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(f"tcp://localhost:{zmq_port}")
    socket.setsockopt_string(zmq.SUBSCRIBE, '')

    running = True
    # rewrite the frame into frames

    frames_list = []
    for frame in frames:
        frame = cv2.resize(frame, (screen_width, screen_height))  # Resize the frame to match the screen dimensions
        frame = cv2.transpose(frame)  # Transpose the frame
        frames_list.append(frame)

    clock = pygame.time.Clock()
    clock.tick(120)  # Set the frame rate to 60 fps
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        try:
            frame_rate = int(socket.recv_string(flags=zmq.NOBLOCK))
        except zmq.Again:
            frame_rate = 1000  # default frame rate

        for frame in frames_list:
            start_time = pygame.time.get_ticks()
            '''
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break
            if not running:
                break
            '''
            pygame.surfarray.blit_array(screen, frame)
            pygame.display.update()
            
            pygame.time.delay(int(1000 / frame_rate))
            #clock.tick(frame_rate)
            end_time = pygame.time.get_ticks()
            elapsed_time = end_time - start_time
            print(f"Frame render time: {elapsed_time} ms")

    pygame.quit()

if __name__ == "__main__":
    main(r"C:\Users\Liors\Documents\GitHub\Lital_IMU_Tobii_Pro_Integration\Mobile_movie_trim2.avi", 5555)