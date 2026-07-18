from statistics import median
import sys
import pygame

from config import *
from simulation import Simulation


def main() -> None:
    pygame.init()

    screen = pygame.display.set_mode((0, 0),pygame.FULLSCREEN)

    pygame.display.set_caption("Braitenberg Vehicle 6")
    clock = pygame.time.Clock()
    title_font = pygame.font.SysFont("arial",28,bold=True)
    section_font = pygame.font.SysFont("arial",20,bold=True)
    font = pygame.font.SysFont("arial",16)
    simulation = Simulation(screen.get_size())

    running = True

    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                else:
                    simulation.key_down(event)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                simulation.mouse_down(Vector2(event.pos),event.button)

            elif event.type == pygame.MOUSEMOTION:
                simulation.mouse_move(Vector2(event.pos))

            elif event.type == pygame.MOUSEBUTTONUP:
                simulation.mouse_up(event.button)

        simulation.update()

        screen.fill(BACKGROUND)
        simulation.draw(screen,title_font,section_font,font)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
