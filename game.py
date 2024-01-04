import pygame

class Game:
    def __init__(self):
        pygame.init()
        self.SCREEN_WIDTH = 1600
        self.SCREEN_HEIGHT = 700
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.fontSize = 20
        self.myFont = pygame.font.SysFont("freesansbold", self.fontSize)
        self.start
        while True:
            self.update()
            self.draw()
            self.clock.tick(60)
    
    def start(self):
        pass

    def update(self):
        pass

    def draw(self):
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        self.screen.fill(self.colors.GREY)
        pygame.display.update()
        pass