from __future__ import annotations
from dataclasses import dataclass
from statistics import median
import math
import pygame

from config import *
from source import Source
from genome import Genome
from landmark import Landmark


class Vehicle:
    def __init__(self,position: Vector2,direction: float,genome: Genome,generation: int = 0) -> None:
        self.position = Vector2(position)
        self.direction = direction
        self.genome = genome
        self.generation = generation

        self.age = 0.0
        self.distance_traveled = 0.0

        self.source_pulses_seen = 0
        self.last_source_pulse_age = 0.0

        self.active = True

        self.radius = math.floor(8 + genome.ratio("speed_scaling") * 12)

        self.color = genome.color()

        self.source_detection_threshold = (genome.source_detection_threshold)
        self.speed_scaling = genome.speed_scaling
        self.rotation_scaling = genome.rotation_scaling
        self.sensor_spacing = genome.sensor_spacing

        self.sensor_radius = 5
        self.sensor_offset = (self.radius + self.sensor_radius)

        self.left_sensor_position = self.position.copy()
        self.right_sensor_position = self.position.copy()

        self.sensor_color = (0,0,0)
        self.was_above_source_threshold = False

        self.update_sensors()

    @property
    def fitness(self) -> float:
        return (self.source_pulses_seen * 0.5 + self.distance_traveled * 0.02 + self.age)

    def update_sensors(self) -> None:
        forward = Vector2(0.0,-1.0).rotate(self.direction)
        right = forward.rotate(-90.0)
        front = (self.position + forward * self.sensor_offset)

        self.left_sensor_position = (front - right * (self.sensor_spacing / 2.0))
        self.right_sensor_position = (front + right * (self.sensor_spacing / 2.0))

    def draw(self, surface: pygame.Surface) -> None:
        ring_width = math.floor(
            1
            + self.genome.ratio(
                "rotation_scaling"
            ) * 6
        )

        pointer_length = (
            18
            + self.genome.ratio(
                "rotation_scaling"
            ) * 20
        )

        forward = Vector2(
            0.0,
            -1.0,
        ).rotate(
            self.direction
        )

        pointer_end = (
            self.position
            + forward * pointer_length
        )

        center = (
            round(self.position.x),
            round(self.position.y),
        )

        pygame.draw.circle(
            surface,
            self.color,
            center,
            self.radius,
        )

        pygame.draw.circle(
            surface,
            WHITE,
            center,
            self.radius,
            ring_width,
        )

        pygame.draw.line(
            surface,
            WHITE,
            center,
            (
                round(pointer_end.x),
                round(pointer_end.y),
            ),
            ring_width,
        )

        pygame.draw.circle(
            surface,
            self.sensor_color,
            (
                round(
                    self.left_sensor_position.x
                ),
                round(
                    self.left_sensor_position.y
                ),
            ),
            self.sensor_radius,
        )

        pygame.draw.circle(
            surface,
            self.sensor_color,
            (
                round(
                    self.right_sensor_position.x
                ),
                round(
                    self.right_sensor_position.y
                ),
            ),
            self.sensor_radius,
        )

    @staticmethod
    def calculate_one_source(position: Vector2,source: Source) -> float:
        distance = position.distance_to(source.position)
        return 1.0 / max(distance * distance,1.0)

    def calculate_total_source(self,position: Vector2,sources: list[Source]) -> float:
        return sum(
            self.calculate_one_source(position,source)
            for source in sources
        )
    
    @staticmethod
    def calculate_one_landmark(position: Vector2,landmark: Landmark) -> float:
        distance = position.distance_to(landmark.position)
        return 1.0 / max(distance * distance,1.0)

    def calculate_total_landmark(self,position: Vector2,landmarks: list[Landmark]) -> float:
        return sum(
            self.calculate_one_landmark(position,landmark)
            for landmark in landmarks
        )

    def detect_threshold_pulse(self,output: float, pulse_from_landmark: bool = False) -> bool:
        above = (output > self.source_detection_threshold)

        pulse = (above and not self.was_above_source_threshold)

        self.was_above_source_threshold = above

        if not pulse:
            return False

        if not pulse_from_landmark:
            self.source_pulses_seen += 1

        self.last_source_pulse_age = self.age

        return True

    def is_outside_world(self,table_rect: pygame.Rect) -> bool:
        return (
            self.position.x - self.radius <= table_rect.left
            or self.position.x + self.radius >= table_rect.right
            or self.position.y - self.radius <= table_rect.top
            or self.position.y + self.radius >= table_rect.bottom
        )

    def has_failed_minimum_movement(self) -> bool:
        if not MINIMUM_MOVEMENT_ENABLED:
            return False

        if self.age < MINIMUM_MOVEMENT_AGE_SECONDS:
            return False

        return (self.distance_traveled / self.age < MINIMUM_AVERAGE_SPEED)
    
    def has_failed_source_starvation(self) -> bool:
        if not SOURCE_STARVATION_ENABLED:
            return False

        if self.age < SOURCE_STARVATION_GRACE_SECONDS:
            return False

        return (self.age - self.last_source_pulse_age > SOURCE_STARVATION_LIMIT_SECONDS)

    def get_movement_for_source(self,sources: list[Source]) -> tuple[float,float] :
        left_energy = self.calculate_total_source(self.left_sensor_position,sources)
        right_energy = self.calculate_total_source(self.right_sensor_position,sources)

        left_output = (self.speed_scaling* left_energy)
        right_output = (self.speed_scaling * right_energy)

        total_sensor_output = ( left_output + right_output ) / 2.0

        speed = max( 0.05, 1.0 - total_sensor_output )
        rotation = ( right_output - left_output) * self.rotation_scaling * -1.0
        self.detect_threshold_pulse(total_sensor_output)

        return (speed,rotation)
        
    def get_movement_for_landmark(self,landmarks: list[Landmark]) -> tuple[float,float] :
        left_energy = self.calculate_total_landmark(self.left_sensor_position,landmarks)
        right_energy = self.calculate_total_landmark(self.right_sensor_position,landmarks)

        left_output = (self.speed_scaling* left_energy)
        right_output = (self.speed_scaling * right_energy)

        total_sensor_output = ( left_output + right_output ) / 2.0

        speed = max( 0.01, 1.0 - total_sensor_output )
        rotation = ( right_output - left_output) * self.rotation_scaling * 1.0
        self.detect_threshold_pulse(total_sensor_output, True)

        return (speed,rotation)
        
    def move(self,sources: list[Source],landmarks: list[Landmark],table_rect: pygame.Rect) -> None:
        if not sources and not landmarks:
            self.update_sensors()
            return

        (speed_for_source, rotation_for_source) = self.get_movement_for_source(sources)
        (speed_for_landmark, rotation_for_landmark) = self.get_movement_for_landmark(landmarks)

        total_rotation = (rotation_for_source + rotation_for_landmark)
        self.direction += total_rotation
        direction_vector = Vector2(0.0, -1.0).rotate(self.direction)

        speed = (speed_for_source + speed_for_landmark) / 2.0
        
        movement = ( direction_vector * speed )

        self.position += movement
        self.distance_traveled += movement.length()
        self.age += SIM_STEP_SECONDS

        if (
            self.is_outside_world(
                table_rect
            )
            or self.has_failed_minimum_movement()
            or self.has_failed_source_starvation()
        ):
            self.active = False

        self.update_sensors()

