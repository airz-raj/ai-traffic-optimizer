"""
Vehicle models for the traffic simulation.
"""
import random
import enum
from dataclasses import dataclass, field
from typing import List, Tuple, Optional


class VehicleType(enum.Enum):
    CAR = "car"
    BUS = "bus"
    TRUCK = "truck"
    AMBULANCE = "ambulance"
    FIRE_TRUCK = "fire_truck"
    POLICE = "police"

    @property
    def is_emergency(self) -> bool:
        return self in (VehicleType.AMBULANCE, VehicleType.FIRE_TRUCK, VehicleType.POLICE)


class Direction(enum.Enum):
    NORTH = "N"
    SOUTH = "S"
    EAST = "E"
    WEST = "W"

    @property
    def opposite(self):
        mapping = {
            Direction.NORTH: Direction.SOUTH,
            Direction.SOUTH: Direction.NORTH,
            Direction.EAST: Direction.WEST,
            Direction.WEST: Direction.EAST,
        }
        return mapping[self]


@dataclass
class Vehicle:
    vehicle_id: int
    vehicle_type: VehicleType
    position: Tuple[float, float]          # (x, y) on the grid
    direction: Direction
    speed: float = 0.0                      # current speed
    max_speed: float = 60.0                 # km/h
    route: List[Tuple[int, int]] = field(default_factory=list)
    current_route_idx: int = 0
    waiting_time: float = 0.0
    is_stopped: bool = False

    @property
    def is_emergency(self) -> bool:
        return self.vehicle_type.is_emergency

    def next_intersection(self) -> Optional[Tuple[int, int]]:
        if self.current_route_idx < len(self.route):
            return self.route[self.current_route_idx]
        return None

    def advance_route(self):
        self.current_route_idx += 1

    def stop(self):
        self.speed = 0.0
        self.is_stopped = True

    def go(self):
        self.speed = self.max_speed
        self.is_stopped = False


@dataclass
class TrafficSnapshot:
    """Snapshot of traffic conditions at an intersection approach."""
    intersection_id: Tuple[int, int]
    direction: Direction
    vehicle_count: int
    avg_wait_time: float
    has_emergency: bool
    emergency_distance: Optional[float] = None
    density: float = 0.0  # vehicles per unit length


class VehicleFactory:
    _next_id = 0

    @classmethod
    def create_random_vehicle(cls, position, direction, route=None) -> Vehicle:
        cls._next_id += 1
        vtype = random.choices(
            [VehicleType.CAR, VehicleType.BUS, VehicleType.TRUCK],
            weights=[0.75, 0.15, 0.10]
        )[0]
        return Vehicle(
            vehicle_id=cls._next_id,
            vehicle_type=vtype,
            position=position,
            direction=direction,
            max_speed=random.uniform(40, 70),
            route=route or [],
        )

    @classmethod
    def create_emergency_vehicle(cls, vtype: VehicleType, position, direction, route=None) -> Vehicle:
        cls._next_id += 1
        return Vehicle(
            vehicle_id=cls._next_id,
            vehicle_type=vtype,
            position=position,
            direction=direction,
            max_speed=80.0,
            route=route or [],
        )
