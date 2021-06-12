import pygame
import neat
import time
import os
import random

pygame.font.init()

# Set up constants and images
WINDOW_WIDTH = 500
WINDOW_HEIGHT = 800

# Double image size for each bird image
BIRD_IMAGES = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird1.png"))),
               pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird2.png"))),
               pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird3.png")))]

PIPE_IMAGE = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png")))
BASE_IMAGE = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png")))
BACKGROUND = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bg.png")))

SCORE_FONT = pygame.font.SysFont("comicsans", 50)


# Draw the bird
class Bird:
    IMAGES = BIRD_IMAGES
    MAX_ROTATION = 25
    ROT_VELOCITY = 20
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.velocity = 0
        self.height = self.y
        self.image_count = 0  # there are three images
        self.image = self.IMAGES[0]

    def jump(self):
        self.velocity = -10.5
        self.tick_count = 0
        self.height = self.y

    def move(self):
        self.tick_count += 1

        # Physics movement (vertical displacement)
        # Negative Displacement = Up
        # Positive Displacement = Down

        displacement = self.velocity * self.tick_count + 1.5 * self.tick_count ** 2

        if displacement >= 16:
            displacement = 16

        if displacement < 0:
            displacement -= 2

        self.y = self.y + displacement

        # Tilt Upwards
        if displacement < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VELOCITY

    def draw(self, window):
        self.image_count += 1

        # Move the wings
        if self.image_count < self.ANIMATION_TIME:
            self.image = self.IMAGES[0]
        elif self.image_count < self.ANIMATION_TIME * 2:
            self.image = self.IMAGES[1]
        elif self.image_count < self.ANIMATION_TIME * 3:
            self.image = self.IMAGES[2]
        elif self.image_count < self.ANIMATION_TIME * 4:
            self.image = self.IMAGES[1]
        elif self.image_count == self.ANIMATION_TIME * 4 + 1:
            self.image = self.IMAGES[0]
            self.image_count = 0

        if self.tilt <= -80:
            self.image = self.IMAGES[1]
            self.image_count = self.ANIMATION_TIME * 2

        # Rotated Image Around the Center
        rotated_image = pygame.transform.rotate(self.image, self.tilt)
        new_rectangle = rotated_image.get_rect(center=self.image.get_rect(topleft= (self.x, self.y)).center)
        window.blit(rotated_image, new_rectangle.topleft)
        
    def get_mask(self):
        return pygame.mask.from_surface(self.image)


class Pipe:
    GAP = 200
    VELOCITY = 5

    def __init__(self, x):
        self.x = x
        self.height = 0

        # Pipe Locations
        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMAGE, False, True)
        self.PIPE_BOTTOM = PIPE_IMAGE

        self.passed = False
        self.set_height()

    def set_height(self):
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        self.x -= self.VELOCITY

    def draw(self, window):
        window.blit(self.PIPE_TOP, (self.x, self.top))
        window.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird):
        # Use masking to figure out point-perfect collision
        bird_mask = bird.get_mask()
        top_bar_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_bar_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        # Offset -> How far the masks are away from each other
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        # Calculate overlapping pixels -> point of collision
        collide_bottom = bird_mask.overlap(bottom_bar_mask, bottom_offset)
        collide_top = bird_mask.overlap(top_bar_mask, top_offset)

        if collide_bottom or collide_top:
            return True

        return False


class Base:
    VELOCITY = 5
    WIDTH = BASE_IMAGE.get_width()
    IMAGE = BASE_IMAGE

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        self.x1 -= self.VELOCITY
        self.x2 -= self.VELOCITY

        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, window):
        window.blit(self.IMAGE, (self.x1, self.y))
        window.blit(self.IMAGE, (self.x2, self.y))


def draw_window(window, bird, pipes, base, score):
    window.blit(BACKGROUND, (0, 0))

    base.draw(window)
    for pipe in pipes:
        pipe.draw(window)

    bird.draw(window)

    test = SCORE_FONT.render("Score: " + str(score), 1, (255, 255, 255))
    window.blit(test, (WINDOW_WIDTH - 10 - test.get_width(), 10))

    pygame.display.update()


# Main Game Loop
def main():
    score = 0
    bird = Bird(230, 350)

    base = Base(730)
    pipes = [Pipe(700)]

    window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()

    run = True
    while run:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        removed = []
        add_pipe = False
        for pipe in pipes:
            if pipe.collide(bird):
                # bird.move()
                score = 0

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                removed.append(pipe)

            if not pipe.passed and pipe.x < bird.x:
                pipe.passed = True
                add_pipe = True

            pipe.move()

        if add_pipe:
            score += 1
            pipes.append(Pipe(700))

        for r in removed:
            pipes.remove(r)

        # Bird hits the ground
        if bird.y + bird.image.get_height() >= 730:
            pass

        base.move()
        draw_window(window, bird, pipes, base, score)

    pygame.quit()
    quit()


main()
