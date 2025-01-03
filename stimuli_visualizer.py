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

def main(fixation_movie_path, movie_path, zmq_port):
    pygame.init()
    frames, width, height = extract_frames(movie_path)
    fixation_frames, fixation_width, fixation_height = extract_frames(fixation_movie_path)
    
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
    frames_list_fixation = []
    # add frames of fixation movie to the beginning of the frames list
    for frame in fixation_frames:
        frame = cv2.resize(frame, (screen_width, screen_height))
        frame = cv2.transpose(frame)
        frames_list_fixation.append(frame)

    # Rewrite the frame into frames
    frames_list = []
    for frame in frames:
        frame = cv2.resize(frame, (screen_width, screen_height))  # Resize the frame to match the screen dimensions
        frame = cv2.transpose(frame)  # Transpose the frame
        frames_list.append(frame)

    frame_index = 0
    frame_rate = 0  # default frame rate in frames per second
    if frame_rate > 0:
        wait_time = int(1000 / frame_rate)  # Calculate wait time in milliseconds
        pygame.time.set_timer(pygame.USEREVENT, wait_time)

    # create a black frame to present before the first frame of the movie
    # the frame variable a black frame
    
    # copy frame into black_frame
    #black_frame = np.zeros((screen_height, screen_width, 3), dtype=np.uint8)
    #black_frame = cv2.transpose(black_frame)  # Transpose the frame
    #black_frame = black_frame.fill(0)

    # present the first frame as a black frame
    black_frame = np.copy(frame)
    black_frame.fill(0)
    pygame.surfarray.blit_array(screen, black_frame)
    pygame.display.update()
    
    #frame = frames_list[frame_index]
    #pygame.surfarray.blit_array(screen, frame)
    #pygame.display.update()
    frame_index = (frame_index + 1) % len(frames_list)
    
    current_state = "dark_screen"
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.USEREVENT:
                if current_state == b"fixation_movie":
                    frame = frames_list_fixation[(frame_index + 1) % len(frames_list_fixation)]
                elif current_state == b"mobile_movie":
                    frame = frames_list[(frame_index + 1) % len(frames_list)]
                else:
                    frame = black_frame
                
                pygame.surfarray.blit_array(screen, frame)
                pygame.display.update()
                frame_index += 1
            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                screen_width, screen_height = event.w, event.h

        try:
            new_state, new_frame_rate = socket.recv_multipart(flags=zmq.NOBLOCK)
            #new_frame_rate, new_state = message.split(',')
            new_frame_rate = int(new_frame_rate)
            if new_frame_rate != frame_rate:
                frame_rate = new_frame_rate
                if frame_rate > 0:
                    wait_time = int(1000 / frame_rate)  # Recalculate wait time in milliseconds
                    pygame.time.set_timer(pygame.USEREVENT, wait_time)
                else:
                    pygame.time.set_timer(pygame.USEREVENT, 0)  # Disable the timer
                    
            if new_state != current_state:
                current_state = new_state
                frame_index = 0  # Reset frame index when state changes
                if current_state == b"fixation_movie":
                    frame = frames_list_fixation[frame_index % len(frames_list_fixation)]
                elif current_state == b"mobile_movie":
                    frame = frames_list[frame_index % len(frames_list)]
                else:
                    frame = black_frame

                # draw the first frame of the new state
                pygame.surfarray.blit_array(screen, frame)
                pygame.display.update()


        except zmq.Again:
            pass

    pygame.quit()

if __name__ == "__main__":
    main(r".\media\Fixation_resized.avi", r".\media\Mobile_movie_trim2.avi", 5555)