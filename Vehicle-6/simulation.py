from statistics import median
import random
import pygame

from config import *
from helper import *
from genome import Genome
from landmark import Landmark
from vehicle import Vehicle
from source import Source

class Simulation:
    def __init__(self,screen_size: tuple[int, int]) -> None:
        width, height = screen_size

        table_width = int(
            width * TABLE_RATIO
        )

        self.table_section = pygame.Rect(
            0,
            0,
            table_width,
            height,
        )

        self.dashboard_rect = pygame.Rect(
            table_width,
            0,
            width - table_width,
            height,
        )

        self.table_rect = self.table_section.inflate(
            -2 * TABLE_MARGIN,
            -2 * TABLE_MARGIN,
        )

        self.sources: list[Source] = []
        self.vehicles: list[Vehicle] = []
        self.landmarks: list[Landmark] = []

        self.dragged_source: Source | None = None

        self.next_source_index = 4
        self.total_deaths = 0
        self.total_mutations = 0
        self.total_recombinations = 0

        self.paused = False
        self.time_scale_index = 0

        self.reset()

    def reset(self) -> None:
        self.sources = [
            Source(
                Vector2(
                    self.table_rect.centerx,
                    self.table_rect.centery - 210,
                ),
                random.randint(
                    SOURCE_RADIUS_MIN,
                    SOURCE_RADIUS_MAX
                ),
                make_source_color(0),
            ),
            Source(
                Vector2(
                    self.table_rect.centerx + 220,
                    self.table_rect.centery,
                ),
                random.randint(
                    SOURCE_RADIUS_MIN,
                    SOURCE_RADIUS_MAX
                ),
                make_source_color(1),
            ),
            Source(
                Vector2(
                    self.table_rect.centerx,
                    self.table_rect.centery + 210,
                ),
                SOURCE_RADIUS,
                make_source_color(2),
            ),
            Source(
                Vector2(
                    self.table_rect.centerx - 220,
                    self.table_rect.centery,
                ),
                SOURCE_RADIUS,
                make_source_color(3),
            ),
        ]

        starting_genome = Genome.starting()

        self.vehicles = [
            self.create_vehicle(
                starting_genome,
                0,
            )
            for _ in range(
                POPULATION_SIZE
            )
        ]

        self.landmarks = []
        self.dragged_source = None
        self.next_source_index = 4
        self.total_deaths = 0
        self.total_mutations = 0
        self.total_recombinations = 0

        self.paused = False
        self.time_scale_index = 0

    def spawn_position(self) -> Vector2:
        return Vector2(
            self.table_rect.centerx
            + random.uniform(
                -SPAWN_RADIUS,
                SPAWN_RADIUS,
            ),
            self.table_rect.centery
            + random.uniform(
                -SPAWN_RADIUS,
                SPAWN_RADIUS,
            ),
        )
    
    def spawn_landmark_position(self) -> Vector2:
        margin = 30
        return Vector2(
            random.uniform(
                self.table_rect.left + margin,
                self.table_rect.right - margin,
            ),
            random.uniform(
                self.table_rect.top + margin,
                self.table_rect.bottom - margin,
            ),
        )

    def create_vehicle(self,genome: Genome | None = None,generation: int = 0) -> Vehicle:
        if genome is None:
            genome = Genome.random()
        else:
            genome = genome.copy()

        return Vehicle(
            position=self.spawn_position(),
            direction=random.uniform(
                0.0,
                360.0,
            ),
            genome=genome,
            generation=generation,
        )

    def choose_parent(self,exclude: Vehicle | None = None) -> Vehicle | None:
        alive = [
            vehicle
            for vehicle in self.vehicles
            if vehicle.active
            and vehicle is not exclude
        ]

        if not alive:
            return None

        return random.choice(alive)

    def replace_dead(self) -> int:
        dead_vehicles = [
            vehicle
            for vehicle in self.vehicles
            if not vehicle.active
        ]

        replacements = 0

        for dead_vehicle in dead_vehicles:
            if dead_vehicle not in self.vehicles:
                continue

            self.vehicles.remove(dead_vehicle)

            parent = self.choose_parent()

            if parent is None:
                self.vehicles.append(
                    self.create_vehicle()
                )
                replacements += 1
                continue

            parent_genome = parent.genome.copy()
            parent_generation = parent.generation

            second_parent = None

            if (
                len(self.vehicles) > 1
                and random.random()
                < RECOMBINATION_CHANCE
            ):
                second_parent = self.choose_parent(
                    exclude=parent
                )

            self.vehicles.remove(parent)

            if second_parent is not None:
                base_child_genome = Genome.recombine(
                    parent.genome,
                    second_parent.genome,
                )
                self.total_recombinations += 1
            else:
                base_child_genome = parent.genome.copy()

            child_genome = base_child_genome.mutate()

            self.total_mutations += (
                base_child_genome.difference_count(
                    child_genome
                )
            )

            refreshed_parent = self.create_vehicle(
                parent_genome,
                parent_generation,
            )

            child = self.create_vehicle(
                child_genome,
                parent_generation + 1,
            )

            self.vehicles.append(
                refreshed_parent
            )

            self.vehicles.append(
                child
            )

            replacements += 1

        return replacements

    def update_population(self) -> int:
        for vehicle in self.vehicles:
            vehicle.move(
                self.sources,
                self.landmarks,
                self.table_rect
            )

        return self.replace_dead()

    def update(self) -> None:
        if self.paused:
            return

        iterations = TIME_SCALE_OPTIONS[
            self.time_scale_index
        ]

        for _ in range(iterations):
            self.total_deaths += (
                self.update_population()
            )

    def median_genome(self) -> Genome:
        return Genome(
            source_detection_threshold=median(
                vehicle.genome.source_detection_threshold
                for vehicle in self.vehicles
            ),
            speed_scaling=median(
                vehicle.genome.speed_scaling
                for vehicle in self.vehicles
            ),
            rotation_scaling=median(
                vehicle.genome.rotation_scaling
                for vehicle in self.vehicles
            ),
            sensor_spacing=median(
                vehicle.genome.sensor_spacing
                for vehicle in self.vehicles
            ),
        )

    def get_source_at(self,position: Vector2) -> Source | None:
        for source in reversed(self.sources):
            if source.contains_point(position):
                return source
        return None
    
    def get_landmark_at(self,position: Vector2) -> Landmark | None:
        for landmark in reversed(self.landmarks):
            if landmark.contains_point(position):
                return landmark
        return None

    def clamp_source(self,source: Source) -> None:
        source.position.x = clamp(
            source.position.x,
            self.table_rect.left
            + source.radius,
            self.table_rect.right
            - source.radius,
        )

        source.position.y = clamp(
            source.position.y,
            self.table_rect.top
            + source.radius,
            self.table_rect.bottom
            - source.radius,
        )

    def mouse_down(self,position: Vector2,button: int) -> None:
        if not self.table_rect.collidepoint(
            position.x,
            position.y,
        ):
            return

        if button == 1:
            source = self.get_source_at(position)

            if source is not None:
                self.dragged_source = source
                return

            new_source = Source(
                position.copy(),
                random.randint(
                    SOURCE_RADIUS_MIN,
                    SOURCE_RADIUS_MAX
                ),
                make_source_color(
                    self.next_source_index
                ),
            )

            self.next_source_index += 1
            self.sources.append(new_source)
            self.dragged_source = new_source

        elif button == 3:
            source = self.get_source_at(position)

            if source is None:
                return

            if self.dragged_source is source:
                self.dragged_source = None

            self.sources.remove(source)

    def mouse_move(self,position: Vector2) -> None:
        if self.dragged_source is None:
            return

        self.dragged_source.position.update(position)

        self.clamp_source(self.dragged_source)

    def mouse_up(self,button: int) -> None:
        if button == 1:
            self.dragged_source = None

    def key_down(self,event: pygame.event.Event) -> None:
        global MINIMUM_MOVEMENT_ENABLED

        if event.key == pygame.K_SPACE:
            self.paused = not self.paused

        elif event.key in (
            pygame.K_PLUS,
            pygame.K_EQUALS,
            pygame.K_KP_PLUS,
        ):
            self.time_scale_index = min(
                self.time_scale_index + 1,
                len(TIME_SCALE_OPTIONS) - 1,
            )

        elif event.key in (
            pygame.K_MINUS,
            pygame.K_KP_MINUS,
        ):
            self.time_scale_index = max(
                self.time_scale_index - 1,
                0,
            )

        elif event.key == pygame.K_m:
            MINIMUM_MOVEMENT_ENABLED = (
                not MINIMUM_MOVEMENT_ENABLED
            )

        elif event.key == pygame.K_r:
            self.reset()

        elif event.key == pygame.K_a:
            position : Vector2
            while True:

                new_position = self.spawn_landmark_position()
                source = self.get_source_at(new_position)
                landmark = self.get_landmark_at(new_position)

                if source is None and landmark is None:
                    position = new_position
                    break

            new_landmark = Landmark(
                position.copy(),
                LANDMARK_RADIUS,
                (0,0,0),
            )
            self.landmarks.append(new_landmark)
        
        elif event.key == pygame.K_d:
            if self.landmarks:
                self.landmarks.pop()


    def draw(self,surface: pygame.Surface,title_font: pygame.font.Font,section_font: pygame.font.Font,font: pygame.font.Font) -> None:
        pygame.draw.rect(
            surface,
            TABLE_AREA,
            self.table_section,
        )

        pygame.draw.rect(
            surface,
            DASHBOARD_COLOR,
            self.dashboard_rect,
        )

        pygame.draw.line(
            surface,
            DASHBOARD_BORDER,
            self.dashboard_rect.topleft,
            self.dashboard_rect.bottomleft,
            3,
        )

        pygame.draw.rect(
            surface,
            TABLE_COLOR,
            self.table_rect,
        )

        pygame.draw.rect(
            surface,
            TABLE_BORDER,
            self.table_rect,
            5,
        )

        for source in self.sources:
            source.draw(
                surface,
                selected=(
                    source is self.dragged_source
                ),
            )
        
        for landmark in self.landmarks:
            landmark.draw(surface)

        for vehicle in self.vehicles:
            vehicle.draw(
                surface
            )

        best = max(
            self.vehicles,
            key=lambda vehicle: vehicle.fitness,
        )

        average_age = (
            sum(
                vehicle.age
                for vehicle in self.vehicles
            ) / len(self.vehicles)
        )

        median_genome = self.median_genome()

        time_scale = TIME_SCALE_OPTIONS[self.time_scale_index]

        x = self.dashboard_rect.left + 28
        y = 30

        surface.blit(
            title_font.render(
                "Vehicle 6",
                True,
                TEXT,
            ),
            (x, y),
        )

        y += 58

        summary = (
            (
                "Best score",
                f"{best.fitness:.0f}",
            ),
            (
                "Average age",
                f"{average_age:.1f}s",
            ),
            (
                "Best generation",
                str(best.generation),
            ),
        )

        for label, value in summary:
            surface.blit(
                font.render(
                    label,
                    True,
                    TEXT_MUTED,
                ),
                (x, y),
            )

            surface.blit(
                section_font.render(
                    value,
                    True,
                    TEXT,
                ),
                (x, y + 20),
            )

            y += 58

        def draw_genome(heading: str,genome: Genome,start_y: int) -> int:
            surface.blit(
                section_font.render(
                    heading,
                    True,
                    TEXT,
                ),
                (x, start_y),
            )

            start_y += 34

            lines = (
                (
                    "Threshold: "
                    f"{genome.source_detection_threshold:.2f}"
                ),
                (
                    "Speed: "
                    f"{genome.speed_scaling:.0f}"
                ),
                (
                    "Rotation: "
                    f"{genome.rotation_scaling:.2f}"
                ),
                (
                    "Spacing: "
                    f"{genome.sensor_spacing:.0f}"
                ),
            )

            for line in lines:
                surface.blit(
                    font.render(
                        line,
                        True,
                        TEXT,
                    ),
                    (x, start_y),
                )

                start_y += 24

            return start_y

        y = draw_genome(
            "Best genome",
            best.genome,
            y + 4,
        )

        y = draw_genome(
            "Median genome",
            median_genome,
            y + 24,
        )

        details = (
            (
                "Population: "
                f"{len(self.vehicles)}"
            ),
            (
                "Deaths: "
                f"{self.total_deaths}"
            ),
            (
                "Best source finds: "
                f"{best.source_pulses_seen}"
            ),
            # (
            #     "Movement rule: "
            #     f"{'ON' if MINIMUM_MOVEMENT_ENABLED else 'off'}"
            # ),
            (
                "Mutated genes: "
                f"{self.total_mutations}"
            ),
            (
                "Recombinations: "
                f"{self.total_recombinations}"
            ),
            (
                "Sources: "
                f"{len(self.sources)}"
            ),
            (
                "State: "
                f"{'PAUSED' if self.paused else 'running'}"
            ),
            (
                "Time scale: "
                f"{time_scale}x"
            ),
        )

        y += 26

        for line in details:
            surface.blit(
                font.render(
                    line,
                    True,
                    TEXT_MUTED,
                ),
                (x, y),
            )

            y += 23

        controls = (
            "Left-click: add/drag source   "
            "Right-click: remove source   "
            "Space: pause   +/-: speed   "
            # "M: movement rule   R: reset   Esc: quit"
        )

        control_surface = font.render(
            controls,
            True,
            TEXT,
        )

        control_rect = control_surface.get_rect(
            midbottom=(
                self.table_section.centerx,
                self.table_section.bottom - 8,
            )
        )

        pygame.draw.rect(
            surface,
            (20, 22, 25),
            control_rect.inflate(
                22,
                10,
            ),
            border_radius=6,
        )

        surface.blit(
            control_surface,
            control_rect,
        )
