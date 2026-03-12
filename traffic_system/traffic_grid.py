"""
Traffic Grid & Intersection models.
"""
import enum
import random
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Set
from .vehicle import Vehicle, Direction, TrafficSnapshot, VehicleType


class SignalState(enum.Enum):
    RED = "red"
    GREEN = "green"
    YELLOW = "yellow"


@dataclass
class TrafficSignal:
    """A single traffic signal controlling one approach direction."""
    direction: Direction
    state: SignalState = SignalState.RED
    timer: float = 0.0
    green_duration: float = 30.0
    yellow_duration: float = 5.0
    red_duration: float = 35.0
    min_green: float = 10.0
    max_green: float = 90.0


@dataclass
class Intersection:
    """A single intersection with 4-way signals."""
    grid_pos: Tuple[int, int]
    signals: Dict[Direction, TrafficSignal] = field(default_factory=dict)
    queues: Dict[Direction, List[Vehicle]] = field(default_factory=dict)
    emergency_override: bool = False
    emergency_direction: Optional[Direction] = None

    def __post_init__(self):
        if not self.signals:
            # Default: NS green, EW red
            self.signals = {
                Direction.NORTH: TrafficSignal(Direction.NORTH, SignalState.GREEN),
                Direction.SOUTH: TrafficSignal(Direction.SOUTH, SignalState.GREEN),
                Direction.EAST: TrafficSignal(Direction.EAST, SignalState.RED),
                Direction.WEST: TrafficSignal(Direction.WEST, SignalState.RED),
            }
        if not self.queues:
            self.queues = {d: [] for d in Direction}

    def get_signal(self, direction: Direction) -> TrafficSignal:
        return self.signals[direction]

    def vehicle_count(self, direction: Direction) -> int:
        return len(self.queues[direction])

    def total_vehicles(self) -> int:
        return sum(len(q) for q in self.queues.values())

    def has_emergency_vehicle(self, direction: Optional[Direction] = None) -> bool:
        if direction:
            return any(v.is_emergency for v in self.queues[direction])
        return any(v.is_emergency for v in q for q in self.queues.values())

    def get_snapshot(self, direction: Direction) -> TrafficSnapshot:
        queue = self.queues[direction]
        has_emerg = any(v.is_emergency for v in queue)
        avg_wait = sum(v.waiting_time for v in queue) / max(len(queue), 1)
        return TrafficSnapshot(
            intersection_id=self.grid_pos,
            direction=direction,
            vehicle_count=len(queue),
            avg_wait_time=avg_wait,
            has_emergency=has_emerg,
            density=len(queue) / 5.0,  # normalized
        )


class TrafficGrid:
    """
    Grid-based traffic network.
    rows x cols intersections connected by roads.
    """

    def __init__(self, rows: int = 4, cols: int = 4):
        self.rows = rows
        self.cols = cols
        self.intersections: Dict[Tuple[int, int], Intersection] = {}
        self.vehicles: List[Vehicle] = []
        self.emergency_vehicles: List[Vehicle] = []
        self.green_corridor: List[Tuple[int, int]] = []
        self.time_step = 0
        self.stats = {
            "total_throughput": 0,
            "avg_wait_time": 0.0,
            "emergency_response_time": 0.0,
            "green_corridor_activations": 0,
        }
        self._build_grid()

    def _build_grid(self):
        for r in range(self.rows):
            for c in range(self.cols):
                self.intersections[(r, c)] = Intersection(grid_pos=(r, c))

    def get_intersection(self, pos: Tuple[int, int]) -> Optional[Intersection]:
        return self.intersections.get(pos)

    def get_neighbors(self, pos: Tuple[int, int]) -> Dict[Direction, Tuple[int, int]]:
        r, c = pos
        neighbors = {}
        if r > 0:
            neighbors[Direction.NORTH] = (r - 1, c)
        if r < self.rows - 1:
            neighbors[Direction.SOUTH] = (r + 1, c)
        if c > 0:
            neighbors[Direction.WEST] = (r, c - 1)
        if c < self.cols - 1:
            neighbors[Direction.EAST] = (r, c + 1)
        return neighbors

    def add_vehicle(self, vehicle: Vehicle):
        if vehicle.is_emergency:
            self.emergency_vehicles.append(vehicle)
        self.vehicles.append(vehicle)

    def remove_vehicle(self, vehicle: Vehicle):
        if vehicle in self.vehicles:
            self.vehicles.remove(vehicle)
        if vehicle in self.emergency_vehicles:
            self.emergency_vehicles.remove(vehicle)

    def compute_route(self, start: Tuple[int, int], end: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Simple BFS pathfinding on the grid."""
        from collections import deque
        visited: Set[Tuple[int, int]] = {start}
        queue = deque([(start, [start])])
        while queue:
            current, path = queue.popleft()
            if current == end:
                return path
            for d, neighbor in self.get_neighbors(current).items():
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        return [start]

    def spawn_random_vehicles(self, count: int = 5):
        """Spawn vehicles at random edge intersections."""
        edges = []
        for r in range(self.rows):
            for c in range(self.cols):
                if r == 0 or r == self.rows - 1 or c == 0 or c == self.cols - 1:
                    edges.append((r, c))

        from .vehicle import VehicleFactory
        for _ in range(count):
            start = random.choice(edges)
            end = random.choice(edges)
            while end == start:
                end = random.choice(edges)
            route = self.compute_route(start, end)
            direction = self._infer_direction(route[0], route[1] if len(route) > 1 else route[0])
            v = VehicleFactory.create_random_vehicle(
                position=start, direction=direction, route=route
            )
            self.add_vehicle(v)
            self.intersections[start].queues[direction].append(v)

    def spawn_emergency(self, vtype: VehicleType, start: Tuple[int, int], end: Tuple[int, int]):
        from .vehicle import VehicleFactory
        route = self.compute_route(start, end)
        direction = self._infer_direction(route[0], route[1] if len(route) > 1 else route[0])
        v = VehicleFactory.create_emergency_vehicle(vtype, start, direction, route)
        self.add_vehicle(v)
        self.intersections[start].queues[direction].append(v)
        return v

    def _infer_direction(self, from_pos, to_pos):
        dr = to_pos[0] - from_pos[0]
        dc = to_pos[1] - from_pos[1]
        if dr < 0:
            return Direction.NORTH
        if dr > 0:
            return Direction.SOUTH
        if dc > 0:
            return Direction.EAST
        return Direction.WEST

    def step(self, dt: float = 1.0):
        """Advance simulation by dt seconds."""
        self.time_step += 1
        # Update waiting times
        for v in self.vehicles:
            if v.is_stopped:
                v.waiting_time += dt
