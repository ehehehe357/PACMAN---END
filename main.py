import sys
import pygame

from ui.pixel_assets import WIDTH, HEIGHT
from ui.menu import Menu
from ui.game_screen import GameScreen

FPS = 60

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pacman Arcade")
clock = pygame.time.Clock()

menu = Menu(screen, WIDTH, HEIGHT)
game = GameScreen()
state = "MENU"

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif state == "MENU":
            result = menu.handle_input(event)
            if result == "EXIT":
                running = False
            elif isinstance(result, dict) and result["action"] == "START_GAME":
                screen = game.start(result["mode"], result["map"], result.get("algo"), result.get("goal_type", "single"))
                state = "PLAYING"
        elif state == "PLAYING":
            if game.handle_event(event) == "BACK":
                screen = pygame.display.set_mode((WIDTH, HEIGHT))
                menu.screen = screen
                menu.reset()
                state = "MENU"

    if state == "PLAYING":
        game.update()

    if state == "MENU":
        menu.draw()
    else:
        game.draw(screen)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()