
import colorsys
import random

from config import GAUSSIAN_STDDEV_FRACTION

def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def random_gaussian_gene(low: float, high: float) -> float:
    mean = (low + high) / 2.0
    std = (high - low) / GAUSSIAN_STDDEV_FRACTION

    while True:
        value = random.gauss(mean, std)
        if low <= value <= high:
            return value


def make_source_color(index: int) -> tuple[int, int, int]:
    hue = (index * 0.17) % 1.0
    red, green, blue = colorsys.hsv_to_rgb(hue, 0.85, 1.0)

    return (
        round(red * 255),
        round(green * 255),
        round(blue * 255),
    )