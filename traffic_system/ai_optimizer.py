"""
AI-Powered Traffic Optimizer.
Uses real-time traffic density analysis to dynamically adjust signal timings.
Implements green corridor logic for emergency vehicles.
"""
import math
from typing import Dict, List, Tuple, Optional
from .vehicle import Direction, VehicleType, TrafficSnapshot
from .traffic_grid import TrafficGrid, Intersection, SignalState, TrafficSignal


class AITrafficOptimizer:
    """
    Core AI engine that:
    1. Analyzes traffic density per approach at every intersection
    2. Computes optimal green-time splits using a weighted scoring model
    3. Detects emergency vehicles and activates green corridors
    4. Performs corridor-wide signal preemption
    """

    # --- Tunable weights for the scoring model ---
    WEIGHT_DENSITY = 0.40
    WEIGHT_WAIT = 0.30
    WEIGHT_QUEUE = 0.20
    WEIGHT_EMERGENCY = 0.10       # bonus weight when emergency present

    EMERGENCY_PREEMPT_RANGE = 3   # how many intersections ahead to preempt

    def __init__(self, grid: TrafficGrid):
        self.grid = grid
        self.cycle_time = 60.0     # total cycle length in seconds
        self.min_green = 10.0
        self.max_green = 50.0
        self.yellow = 4.0
        self.decision_log: List[dict] = []

    # ------------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------------

    def optimize_all(self):
        """Run one optimization pass over every intersection."""
        emergency_corridors = self._detect_emergency_corridors()

        for pos, intersection in self.grid.intersections.items():
            if pos in emergency_corridors:
                direction = emergency_corridors[pos]
                self._apply_emergency_preemption(intersection, direction)
            else:
                self._optimize_intersection(intersection)

    # ------------------------------------------------------------------
    # DENSITY-BASED SIGNAL OPTIMIZATION
    # ------------------------------------------------------------------

    def _optimize_intersection(self, ix: Intersection):
        """Compute scores for NS vs EW and allocate green time proportionally."""
        ns_score = self._approach_score(ix, Direction.NORTH) + self._approach_score(ix, Direction.SOUTH)
        ew_score = self._approach_score(ix, Direction.EAST) + self._approach_score(ix, Direction.WEST)

        total = ns_score + ew_score
        if total == 0:
            ns_ratio = 0.5
        else:
            ns_ratio = ns_score / total

        usable = self.cycle_time - 2 * self.yellow
        ns_green = max(self.min_green, min(self.max_green, usable * ns_ratio))
        ew_green = max(self.min_green, min(self.max_green, usable * (1 - ns_ratio)))

        # Apply
        for d in (Direction.NORTH, Direction.SOUTH):
            ix.signals[d].green_duration = ns_green
        for d in (Direction.EAST, Direction.WEST):
            ix.signals[d].green_duration = ew_green

        self.decision_log.append({
            "intersection": ix.grid_pos,
            "ns_score": round(ns_score, 2),
            "ew_score": round(ew_score, 2),
            "ns_green": round(ns_green, 1),
            "ew_green": round(ew_green, 1),
            "type": "density_optimization",
        })

    def _approach_score(self, ix: Intersection, direction: Direction) -> float:
        snap = ix.get_snapshot(direction)
        score = (
            self.WEIGHT_DENSITY * snap.density
            + self.WEIGHT_WAIT * min(snap.avg_wait_time / 60.0, 1.0)
            + self.WEIGHT_QUEUE * min(snap.vehicle_count / 10.0, 1.0)
        )
        if snap.has_emergency:
            score += self.WEIGHT_EMERGENCY * 5.0  # big bonus
        return score

    # ------------------------------------------------------------------
    # EMERGENCY GREEN CORRIDOR
    # ------------------------------------------------------------------

    def _detect_emergency_corridors(self) -> Dict[Tuple[int, int], Direction]:
        """
        For every active emergency vehicle, compute the corridor of intersections
        that need to be preempted ahead of it.
        Returns {intersection_pos: direction_to_make_green}
        """
        corridors: Dict[Tuple[int, int], Direction] = {}

        for ev in self.grid.emergency_vehicles:
            route = ev.route
            idx = ev.current_route_idx
            ahead = route[idx: idx + self.EMERGENCY_PREEMPT_RANGE + 1]
            for i, pos in enumerate(ahead):
                if i + 1 < len(ahead):
                    next_pos = ahead[i + 1]
                    direction = self.grid._infer_direction(pos, next_pos)
                    # The emergency vehicle *arrives* from the opposite direction
                    corridors[pos] = direction
            self.grid.green_corridor = list(corridors.keys())
            self.grid.stats["green_corridor_activations"] += 1

        return corridors

    def _apply_emergency_preemption(self, ix: Intersection, corridor_direction: Direction):
        """Force green for the emergency vehicle's travel axis."""
        ix.emergency_override = True
        ix.emergency_direction = corridor_direction

        perpendicular = self._perpendicular_directions(corridor_direction)
        opposite = corridor_direction.opposite

        # Green for corridor axis
        for d in (corridor_direction, opposite):
            ix.signals[d].state = SignalState.GREEN
            ix.signals[d].green_duration = self.max_green  # extend
        # Red for perpendicular
        for d in perpendicular:
            ix.signals[d].state = SignalState.RED

        self.decision_log.append({
            "intersection": ix.grid_pos,
            "corridor_dir": corridor_direction.value,
            "type": "emergency_preemption",
        })

    @staticmethod
    def _perpendicular_directions(d: Direction) -> List[Direction]:
        if d in (Direction.NORTH, Direction.SOUTH):
            return [Direction.EAST, Direction.WEST]
        return [Direction.NORTH, Direction.SOUTH]

    # ------------------------------------------------------------------
    # ANALYTICS
    # ------------------------------------------------------------------

    def get_intersection_report(self, pos: Tuple[int, int]) -> dict:
        ix = self.grid.get_intersection(pos)
        if not ix:
            return {}
        return {
            "position": pos,
            "total_vehicles": ix.total_vehicles(),
            "signals": {d.value: ix.signals[d].state.value for d in Direction},
            "green_durations": {d.value: round(ix.signals[d].green_duration, 1) for d in Direction},
            "emergency_override": ix.emergency_override,
            "queues": {d.value: ix.vehicle_count(d) for d in Direction},
        }

    def get_grid_summary(self) -> dict:
        total_v = len(self.grid.vehicles)
        total_e = len(self.grid.emergency_vehicles)
        avg_wait = (
            sum(v.waiting_time for v in self.grid.vehicles) / max(total_v, 1)
        )
        return {
            "time_step": self.grid.time_step,
            "total_vehicles": total_v,
            "emergency_vehicles": total_e,
            "avg_wait_time": round(avg_wait, 2),
            "green_corridor_active": len(self.grid.green_corridor) > 0,
            "corridor_intersections": self.grid.green_corridor,
            "total_corridor_activations": self.grid.stats["green_corridor_activations"],
        }
