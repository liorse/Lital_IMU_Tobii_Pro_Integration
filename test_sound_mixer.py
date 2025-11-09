import pygame

pygame.init()
pygame.mixer.init()

sound1 = pygame.mixer.Sound('./media/8_months_babies_toys_compressed.mp3')
sound1.play(loops=-1, fade_ms=500)

while pygame.mixer.get_busy():
    pygame.time.wait(2000)
   
    # lower the volume over 500 ms
    for i in range(100, -1, -1):
        sound1.set_volume(i / 100)
        pygame.time.wait(10)

    pygame.time.wait(2000)
    # increase the volume over 500 ms
    for i in range(1, 101):
        sound1.set_volume(i / 100)
        pygame.time.wait(10)

pygame.mixer.quit()
pygame.quit()

