import pygame

# Example Command
# commands = [
#     { 'text': 'Run Crypto Bela Strategy', 'action': CryptoBelaStrategyV2 },
#     { 'text': 'Cancel All Open Orders', 'action': lambda: client.cancel_open_orders('BTCUSDT') },
# ]

def InputLoop(commands, loop = True):
    commands.append({'text': 'Exit', 'action': ''})
    while loop:
        for i in range(len(commands)):
            print(f'{i}: {commands[i]["text"]}')
        choice = int(input('Enter Choice: '))

        if choice >= len(commands) - 1:
            print('Goodbye')
            break

        commands[choice]['action']()
        print('Action Completed: ' + commands[choice]['text'])


class Game:
    def __init__(self):
        pygame.init()
        self.SCREEN_WIDTH = 1600
        self.SCREEN_HEIGHT = 700
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.fontSize = 20
        self.myFont = pygame.font.SysFont("freesansbold", self.fontSize)
        self.start()
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

COLORS = {
    "GREY": (150, 150, 150),
    "BLACK": (0, 0, 0),
    "RED": (255, 0, 0),
    "GREEN": (0, 255, 0),
    "BLUE": (0, 0, 255),
    "YELLOW": (255, 255, 0),
    "CYAN": (0, 255, 255),
    "PINK": (220, 20, 60),
    "PURPLE": (138, 43, 226),
    "ORANGE": (255, 165, 0),
    "WHITE": (255, 255, 255)
}