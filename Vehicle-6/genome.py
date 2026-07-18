from __future__ import annotations
from dataclasses import dataclass
import colorsys
import random

from config import *
from helper import *


@dataclass(slots=True)
class Genome:
    source_detection_threshold: float
    speed_scaling: float
    rotation_scaling: float
    sensor_spacing: float

    @classmethod
    def random(cls) -> "Genome":
        return cls(
            source_detection_threshold=random_gaussian_gene(
                *GENOME_LIMITS["source_detection_threshold"]
            ),
            speed_scaling=random_gaussian_gene(
                *GENOME_LIMITS["speed_scaling"]
            ),
            rotation_scaling=random_gaussian_gene(
                *GENOME_LIMITS["rotation_scaling"]
            ),
            sensor_spacing=random_gaussian_gene(
                *GENOME_LIMITS["sensor_spacing"]
            ),
        )

    @classmethod
    def starting(cls) -> "Genome":
        return cls(
            source_detection_threshold=sum(
                GENOME_LIMITS["source_detection_threshold"]
            ) / 2.0,
            speed_scaling=sum(
                GENOME_LIMITS["speed_scaling"]
            ) / 2.0,
            rotation_scaling=sum(
                GENOME_LIMITS["rotation_scaling"]
            ) / 2.0,
            sensor_spacing=sum(
                GENOME_LIMITS["sensor_spacing"]
            ) / 2.0,
        )

    def copy(self) -> "Genome":
        return Genome(
            source_detection_threshold=self.source_detection_threshold,
            speed_scaling=self.speed_scaling,
            rotation_scaling=self.rotation_scaling,
            sensor_spacing=self.sensor_spacing,
        )

    def mutate(self) -> "Genome":
        child = self.copy()

        for key, (low, high) in GENOME_LIMITS.items():
            if random.random() >= GENE_MUTATION_CHANCE:
                continue

            if random.random() < LARGE_MUTATION_CHANCE:
                setattr(
                    child,
                    key,
                    random_gaussian_gene(low, high),
                )
                continue

            current_value = getattr(child, key)
            mutation_step = MUTATION_STEPS[key]

            setattr(
                child,
                key,
                clamp(
                    current_value
                    + random.uniform(
                        -mutation_step,
                        mutation_step,
                    ),
                    low,
                    high,
                ),
            )

        return child

    @classmethod
    def recombine(cls,first: "Genome",second: "Genome") -> "Genome":
        values: dict[str, float] = {}

        for key in GENOME_LIMITS:
            source = (
                first
                if random.random() < 0.5
                else second
            )

            values[key] = getattr(
                source,
                key,
            )

        return cls(**values)

    def difference_count(self,other: "Genome") -> int:
        return sum(
            1
            for key in GENOME_LIMITS
            if getattr(self, key)
            != getattr(other, key)
        )

    def ratio(self, key: str) -> float:
        low, high = GENOME_LIMITS[key]
        return (getattr(self, key) - low) / (high - low)

    def color(self) -> tuple[int, int, int]:
        low, high = GENOME_LIMITS["source_detection_threshold"]
        ratio = (self.source_detection_threshold - low) / (high - low)
        hue = 0.58 - 0.45 * ratio
        red, green, blue = colorsys.hsv_to_rgb(
            hue,
            0.85,
            1.0,
        )

        return (
            round(red * 255),
            round(green * 255),
            round(blue * 255),
        )
