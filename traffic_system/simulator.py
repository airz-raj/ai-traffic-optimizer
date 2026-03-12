"""
Console-based simulation runner — demonstrates the full pipeline
without needing Manim.  Run with:
    python -m traffic_system.simulator
"""
import random, time, os
from .vehicle import VehicleType, Direction, VehicleFactory
from .traffic_grid import TrafficGrid, SignalState
from .ai_optimizer import AITrafficOptimizer


def _clear():
    os.system("cls" if os.name == "nt" else "clear")


def _sig_char(state: SignalState) -> str:
    return {"green": "🟢", "red": "🔴", "yellow": "🟡"}[state.value]


def run_simulation(steps: int = 30, grid_size: int = 4):
    grid = TrafficGrid(rows=grid_size, cols=grid_size)
    ai = AITrafficOptimizer(grid)

    # Seed traffic
    grid.spawn_random_vehicles(count=30)

    print("=" * 60)
    print("  Dynamic AI Traffic Flow Optimizer — Simulation")
    print("=" * 60)

    for step in range(1, steps + 1):
        grid.step()

        # Every 5 steps, add a few more cars
        if step % 5 == 0:
            grid.spawn_random_vehicles(count=random.randint(3, 8))

        # At step 10, dispatch an ambulance
        if step == 10:
            ev = grid.spawn_emergency(
                VehicleType.AMBULANCE,
                start=(0, 0),
                end=(grid_size - 1, grid_size - 1),
            )
            print(f"\n🚑  AMBULANCE dispatched!  Route: {ev.route}")

        # At step 18, dispatch a fire truck
        if step == 18:
            ev = grid.spawn_emergency(
                VehicleType.FIRE_TRUCK,
                start=(grid_size - 1, 0),
                end=(0, grid_size - 1),
            )
            print(f"\n🚒  FIRE TRUCK dispatched!  Route: {ev.route}")

        # ---- AI optimization pass ----
        ai.optimize_all()

        # Advance emergency vehicles along route
        for ev in list(grid.emergency_vehicles):
            ev.advance_route()
            nxt = ev.next_intersection()
            if nxt is None:
                grid.remove_vehicle(ev)

        # ---- Print status ----
        summary = ai.get_grid_summary()
        print(f"\n--- Step {step:>3} ---")
        print(f"  Vehicles on grid : {summary['total_vehicles']}")
        print(f"  Emergency active : {summary['emergency_vehicles']}")
        print(f"  Avg wait time    : {summary['avg_wait_time']:.1f}s")
        print(f"  Green corridor   : {'YES ✅' if summary['green_corridor_active'] else 'no'}")

        if summary["green_corridor_active"]:
            print(f"  Corridor nodes   : {summary['corridor_intersections']}")

        # Mini grid view
        for r in range(grid.rows):
            row_str = "    "
            for c in range(grid.cols):
                ix = grid.intersections[(r, c)]
                ns = ix.signals[Direction.NORTH].state
                ew = ix.signals[Direction.EAST].state
                is_corridor = (r, c) in grid.green_corridor
                marker = "🟦" if is_corridor else "⬜"
                row_str += f" {marker}{_sig_char(ns)}{_sig_char(ew)}"
            print(row_str)

    print("\n" + "=" * 60)
    print("  Simulation complete.")
    print("=" * 60)
    for entry in ai.decision_log[-6:]:
        print(f"  LOG: {entry}")


if __name__ == "__main__":
    run_simulation()
