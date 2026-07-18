from __future__ import annotations
from dataclasses import dataclass
import pygame

from config import *

@dataclass
class Landmark:
    position: Vector2
    radius: int = 20
    color: tuple[int, int, int] = (0,0,0)

    def __post_init__(self) -> None:
        self.position = Vector2(self.position)

    def contains_point(
        self,
        point: Vector2,
    ) -> bool:
        return (
            self.position.distance_to(point)
            <= self.radius
        )

    def triangle_points(self,) -> list[tuple[int, int]]:
        center_x = self.position.x
        center_y = self.position.y

        top = (
            round(center_x),
            round(center_y - self.radius),
        )

        bottom_left = (
            round(center_x - self.radius),
            round(center_y + self.radius),
        )

        bottom_right = (
            round(center_x + self.radius),
            round(center_y + self.radius),
        )

        return [
            top,
            bottom_left,
            bottom_right,
        ]

    def draw(self,surface: pygame.Surface,) -> None:
        points = self.triangle_points()

        pygame.draw.polygon(
            surface,
            self.color,
            points,
        )

        pygame.draw.polygon(
            surface,
            TEXT_DARK,
            points,
            width=2,
        )