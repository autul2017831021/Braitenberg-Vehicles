from __future__ import annotations
from dataclasses import dataclass
import random
import pygame

from config import *

@dataclass
class Source:
    position: Vector2
    radius: int = random.randint(SOURCE_RADIUS_MIN, SOURCE_RADIUS_MAX)
    color: tuple[int, int, int] = RED

    def __post_init__(self) -> None:
        self.position = Vector2(self.position)

    def contains_point(self, point: Vector2) -> bool:
        return (self.position.distance_to(point) <= self.radius)

    def draw(self,surface: pygame.Surface,selected: bool = False) -> None:
        center = (round(self.position.x),round(self.position.y))

        pygame.draw.circle(
            surface,
            self.color,
            center,
            self.radius,
        )

        pygame.draw.circle(
            surface,
            TEXT_DARK,
            center,
            self.radius,
            2,
        )

        if selected:
            pygame.draw.circle(
                surface,
                WHITE,
                center,
                self.radius + 6,
                3,
            )
