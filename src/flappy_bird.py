import pygame
import neat
import time
import os
import random
import time

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
    GAP = 225
    VELOCITY = 10

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
    VELOCITY = 10
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


def draw_window(window, birds, pipes, base, score):
    window.blit(BACKGROUND, (0, 0))

    base.draw(window)
    for pipe in pipes:
        pipe.draw(window)

    for bird in birds:
        bird.draw(window)

    score_text = SCORE_FONT.render("Score: " + str(score), 1, (255, 255, 255))
    window.blit(score_text, (WINDOW_WIDTH - 10 - score_text.get_width(), 10))
    high_score_text = SCORE_FONT.render("High Score: " + str(score), 1, (255, 255, 255))
    window.blit(high_score_text, (WINDOW_WIDTH - 10 - high_score_text.get_width(), 45))

    pygame.display.update()


# Main Game Loop
def main(genomes, config):
    score = 0
    high_score = 0

    networks = []
    genomes_main = []
    birds = []

    for _, genome in genomes:
        # Set neural network and bird object for each genome
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        networks.append(net)
        birds.append(Bird(230, 350))

        # Initial Fitness is 0
        genome.fitness = 0
        genomes_main.append(genome)

    base = Base(730)
    pipes = [Pipe(700)]

    window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()

    run = True
    restart = False
    mid_restart = False

    while run:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()

        pipe_index = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].PIPE_TOP.get_width():
                pipe_index = 1
        else:
            # No birds left, quit generation
            run = False
            break

        for x, bird in enumerate(birds):
            bird.move()
            genomes_main[x].fitness += 0.2

            output = networks[x].activate((bird.y, abs(bird.y - pipes[pipe_index].height), abs(bird.y - pipes[pipe_index].bottom)))

            if output[0] > 0.7:
                bird.jump()

        removed = []
        add_pipe = False
        for pipe in pipes:
            for x, bird in enumerate(birds):
                if pipe.collide(bird):
                    # bird.move()
                    # restart = True
                    # mid_restart = True
                    genomes_main[x].fitness -= 1  # Remove fitness from bird that hits pipe
                    birds.pop(x)  # Remove from neural network
                    networks.pop(x)
                    genomes_main.pop(x)

                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                removed.append(pipe)

            pipe.move()

        if add_pipe:
            score += 1
            for genome in genomes_main:
                genome.fitness += 5  # encourage birds to go through pipes
            pipes.append(Pipe(700))

        for r in removed:
            pipes.remove(r)

        for x, bird in enumerate(birds):
            # Bird hits the ground
            if bird.y + bird.image.get_height() >= 730 or bird.y < 0:
                # score = 0
                # bird.move()
                # restart = True
                # mid_restart = True
                birds.pop(x)
                networks.pop(x)
                genomes_main.pop(x)

        base.move()
        draw_window(window, birds, pipes, base, score)

        if restart and mid_restart is False:
            time.sleep(2)
            restart = False


def run(config_path):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_path)

    population = neat.Population(config)

    population.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    population.add_reporter(stats)

    winner = population.run(main, 50)


if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config.txt")
    run(config_path)
