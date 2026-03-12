"""
=============================================================
  Manim Demo  –  Dynamic AI Traffic Flow Optimizer
                 & Emergency Green Corridor
=============================================================
Render command (1080p, high quality):
    manim -pqh manim_demo.py TrafficOptimizerDemo

Quick preview (480p):
    manim -pql manim_demo.py TrafficOptimizerDemo
=============================================================
"""

from manim import *
import numpy as np
import random
import math

# ── colour palette ──────────────────────────────────────────
ROAD_COLOR        = "#2c3e50"
ROAD_LINE_COLOR   = "#f1c40f"
SIDEWALK_COLOR    = "#7f8c8d"
GRASS_COLOR       = "#27ae60"
BG_COLOR          = "#1a1a2e"
BUILDING_COLORS   = ["#34495e", "#2c3e50", "#4a6274", "#5d7b93"]

SIG_RED           = "#e74c3c"
SIG_GREEN         = "#2ecc71"
SIG_YELLOW        = "#f39c12"

CAR_COLORS        = ["#3498db", "#9b59b6", "#1abc9c", "#e67e22", "#ecf0f1",
                     "#e84393", "#00cec9", "#fd79a8", "#6c5ce7", "#ffeaa7"]
AMBULANCE_COLOR   = "#ffffff"
FIRETRUCK_COLOR   = "#e74c3c"

CORRIDOR_GLOW     = "#00ff88"
DASH_COLOR        = "#ffffff"

PANEL_BG          = "#16213e"
PANEL_BORDER      = "#0f3460"
ACCENT            = "#e94560"


# ╔═══════════════════════════════════════════════════════════╗
# ║                   HELPER BUILDERS                        ║
# ╚═══════════════════════════════════════════════════════════╝

class TrafficLight(VGroup):
    """Three-circle traffic signal with housing box."""

    def __init__(self, direction="NS", scale_factor=0.22, **kwargs):
        super().__init__(**kwargs)
        self.direction = direction
        box = RoundedRectangle(
            width=0.35, height=0.9, corner_radius=0.08,
            fill_color="#1a1a1a", fill_opacity=1,
            stroke_color="#555555", stroke_width=1.5,
        ).scale(scale_factor)
        r = 0.10 * scale_factor
        self.red_light = Circle(radius=r, fill_color=SIG_RED, fill_opacity=0.25,
                                stroke_width=0.5, stroke_color="#333")
        self.yellow_light = Circle(radius=r, fill_color=SIG_YELLOW, fill_opacity=0.25,
                                   stroke_width=0.5, stroke_color="#333")
        self.green_light = Circle(radius=r, fill_color=SIG_GREEN, fill_opacity=0.25,
                                  stroke_width=0.5, stroke_color="#333")
        spacing = 0.25 * scale_factor
        self.red_light.move_to(box.get_center() + UP * spacing)
        self.yellow_light.move_to(box.get_center())
        self.green_light.move_to(box.get_center() + DOWN * spacing)
        self.add(box, self.red_light, self.yellow_light, self.green_light)

    def set_state(self, state):
        r_op = y_op = g_op = 0.18
        if state == "red":
            r_op = 1.0
        elif state == "yellow":
            y_op = 1.0
        elif state == "green":
            g_op = 1.0
        self.red_light.set_fill(opacity=r_op)
        self.yellow_light.set_fill(opacity=y_op)
        self.green_light.set_fill(opacity=g_op)
        return self


def make_car(color=None, length=0.32, width=0.18):
    """Tiny rectangle car with windshield."""
    c = color or random.choice(CAR_COLORS)
    body = RoundedRectangle(
        width=length, height=width, corner_radius=0.04,
        fill_color=c, fill_opacity=1, stroke_width=0.5, stroke_color="#222"
    )
    windshield = RoundedRectangle(
        width=length * 0.3, height=width * 0.6, corner_radius=0.02,
        fill_color="#aee1f9", fill_opacity=0.85, stroke_width=0
    ).move_to(body.get_center() + RIGHT * length * 0.2)
    return VGroup(body, windshield)


def make_emergency_vehicle(vtype="ambulance"):
    color = AMBULANCE_COLOR if vtype == "ambulance" else FIRETRUCK_COLOR
    length, width = 0.42, 0.22
    body = RoundedRectangle(
        width=length, height=width, corner_radius=0.04,
        fill_color=color, fill_opacity=1, stroke_width=1, stroke_color="#e74c3c"
    )
    cross_h = Rectangle(width=0.12, height=0.04, fill_color="#e74c3c",
                         fill_opacity=1, stroke_width=0)
    cross_v = Rectangle(width=0.04, height=0.12, fill_color="#e74c3c",
                         fill_opacity=1, stroke_width=0)
    cross = VGroup(cross_h, cross_v).move_to(body.get_center() + LEFT * 0.06)
    # siren
    siren = Circle(radius=0.035, fill_color="#ff0000", fill_opacity=1,
                   stroke_width=0).move_to(body.get_top() + RIGHT * 0.08)
    return VGroup(body, cross, siren)


def make_building(w=0.5, h=0.7, color=None):
    c = color or random.choice(BUILDING_COLORS)
    bld = Rectangle(width=w, height=h, fill_color=c, fill_opacity=1,
                    stroke_color="#1a1a2e", stroke_width=0.6)
    # windows
    wins = VGroup()
    rows = int(h / 0.18)
    cols = int(w / 0.15)
    for rr in range(rows):
        for cc in range(cols):
            wr = Rectangle(width=0.06, height=0.06,
                           fill_color="#f7dc6f" if random.random() > 0.35 else "#2c3e50",
                           fill_opacity=0.9, stroke_width=0)
            wr.move_to(bld.get_corner(UL) + RIGHT * (0.1 + cc * 0.14)
                       + DOWN * (0.1 + rr * 0.17))
            wins.add(wr)
    return VGroup(bld, wins)


# ╔═══════════════════════════════════════════════════════════╗
# ║               MAIN SCENE — Full Demo                     ║
# ╚═══════════════════════════════════════════════════════════╝

class TrafficOptimizerDemo(MovingCameraScene):
    """
    Complete animated demo of the AI Traffic Flow Optimizer
    with Emergency Green Corridor.
    
    Scene breakdown
    ───────────────
    0. Title & intro text
    1. Build 3×3 city grid with roads, buildings, signals
    2. Spawn cars, show normal traffic flow
    3. Show AI density analysis overlay (bar charts per intersection)
    4. Demonstrate dynamic signal timing adjustment
    5. Emergency vehicle appears — siren animation
    6. Green corridor activates across multiple intersections
    7. Ambulance rushes through, corridor clears
    8. Stats dashboard & outro
    """

    def setup(self):
        self.camera.background_color = BG_COLOR
        self.GRID = 3
        self.SPACING = 2.2
        self.intersections = {}   # (r,c) -> center point
        self.signals = {}          # (r,c) -> {dir: TrafficLight}
        self.road_segments = {}
        self.car_mobs = []
        self.buildings = VGroup()

    # ─────────────── 0. TITLE ────────────────────────────────

    def _play_title(self):
        title = Text("Dynamic AI Traffic Flow Optimizer",
                     font_size=36, color=WHITE, weight=BOLD)
        subtitle = Text("& Emergency Green Corridor System",
                        font_size=24, color=ACCENT)
        subtitle.next_to(title, DOWN, buff=0.3)
        badge = VGroup(title, subtitle).move_to(ORIGIN)

        # decorative line
        line_l = Line(LEFT * 5, LEFT * 0.5, color=ACCENT, stroke_width=2)
        line_r = Line(RIGHT * 0.5, RIGHT * 5, color=ACCENT, stroke_width=2)
        lines = VGroup(line_l, line_r).next_to(subtitle, DOWN, buff=0.25)

        self.play(
            Write(title, run_time=1.5),
            GrowFromCenter(subtitle, run_time=1.5),
        )
        self.play(Create(line_l), Create(line_r), run_time=0.8)
        self.wait(1.5)
        self.play(FadeOut(badge), FadeOut(lines), run_time=0.8)

    # ─────────────── 1. BUILD CITY GRID ──────────────────────

    def _build_grid(self):
        grid_group = VGroup()
        offset = np.array([
            -(self.GRID - 1) * self.SPACING / 2,
            (self.GRID - 1) * self.SPACING / 2,
            0
        ])

        road_width = 0.45

        # --- horizontal roads ---
        for r in range(self.GRID):
            y = offset[1] - r * self.SPACING
            left_x = offset[0] - self.SPACING * 0.6
            right_x = -offset[0] + self.SPACING * 0.6
            road = Rectangle(
                width=right_x - left_x, height=road_width,
                fill_color=ROAD_COLOR, fill_opacity=1, stroke_width=0
            ).move_to([0, y, 0])
            # dashed centre line
            dashes = DashedLine(
                [left_x, y, 0], [right_x, y, 0],
                dash_length=0.10, dashed_ratio=0.5,
                color=ROAD_LINE_COLOR, stroke_width=1
            )
            grid_group.add(road, dashes)

        # --- vertical roads ---
        for c in range(self.GRID):
            x = offset[0] + c * self.SPACING
            top_y = offset[1] + self.SPACING * 0.6
            bot_y = -offset[1] - self.SPACING * 0.6
            road = Rectangle(
                width=road_width, height=top_y - bot_y,
                fill_color=ROAD_COLOR, fill_opacity=1, stroke_width=0
            ).move_to([x, 0, 0])
            dashes = DashedLine(
                [x, bot_y, 0], [x, top_y, 0],
                dash_length=0.10, dashed_ratio=0.5,
                color=ROAD_LINE_COLOR, stroke_width=1
            )
            grid_group.add(road, dashes)

        # --- intersection squares (overlap fill) ---
        for r in range(self.GRID):
            for c in range(self.GRID):
                cx = offset[0] + c * self.SPACING
                cy = offset[1] - r * self.SPACING
                self.intersections[(r, c)] = np.array([cx, cy, 0])
                sq = Square(
                    side_length=road_width + 0.08,
                    fill_color=ROAD_COLOR, fill_opacity=1, stroke_width=0
                ).move_to([cx, cy, 0])
                grid_group.add(sq)

        # --- buildings between intersections ---
        for r in range(self.GRID - 1):
            for c in range(self.GRID - 1):
                cx = (self.intersections[(r, c)][0] + self.intersections[(r, c + 1)][0]) / 2
                cy = (self.intersections[(r, c)][1] + self.intersections[(r + 1, c)][1]) / 2
                bw = self.SPACING * 0.55
                bh = self.SPACING * 0.55
                bld = make_building(bw, bh, random.choice(BUILDING_COLORS))
                bld.move_to([cx, cy, 0])
                self.buildings.add(bld)

        # --- traffic signals at every intersection ---
        for (r, c), center in self.intersections.items():
            sig_ns = TrafficLight("NS").move_to(center + LEFT * 0.35 + UP * 0.35)
            sig_ew = TrafficLight("EW").move_to(center + RIGHT * 0.35 + DOWN * 0.35)
            sig_ns.set_state("green")
            sig_ew.set_state("red")
            self.signals[(r, c)] = {"NS": sig_ns, "EW": sig_ew}
            grid_group.add(sig_ns, sig_ew)

        # --- Animate build ---
        header = Text("Building Smart City Grid...", font_size=24, color="#aaa")
        header.to_edge(UP, buff=0.4)
        self.play(FadeIn(header, shift=DOWN * 0.3), run_time=0.5)
        self.play(FadeIn(grid_group, lag_ratio=0.02), run_time=2.0)
        self.play(FadeIn(self.buildings, lag_ratio=0.05), run_time=1.5)
        self.play(FadeOut(header), run_time=0.4)
        self.grid_group = grid_group

    # ─────────────── 2. SPAWN & MOVE CARS ────────────────────

    def _spawn_cars(self, count=18):
        """Create car mobjects and place them on roads."""
        cars = VGroup()
        positions_used = []

        for i in range(count):
            car = make_car()
            # pick a random road segment
            r = random.randint(0, self.GRID - 1)
            c = random.randint(0, self.GRID - 1)
            center = self.intersections[(r, c)]
            horizontal = random.random() > 0.5
            offset_val = random.uniform(-0.8, 0.8)
            lane_off = random.choice([-0.1, 0.1])

            if horizontal:
                pos = center + RIGHT * offset_val + UP * lane_off
            else:
                car.rotate(PI / 2)
                pos = center + UP * offset_val + RIGHT * lane_off

            car.move_to(pos)
            cars.add(car)
            self.car_mobs.append({"mob": car, "horizontal": horizontal,
                                  "row": r, "col": c})

        label = Text("Vehicles entering the grid", font_size=20, color="#ccc")
        label.to_edge(UP, buff=0.4)
        self.play(FadeIn(label, shift=DOWN * 0.2), run_time=0.3)
        self.play(LaggedStart(*[GrowFromCenter(c) for c in cars],
                              lag_ratio=0.04, run_time=2.0))
        self.wait(0.5)

        # brief driving animation
        anims = []
        for info in self.car_mobs:
            d = random.uniform(0.3, 0.7) * random.choice([-1, 1])
            direction = RIGHT * d if info["horizontal"] else UP * d
            anims.append(info["mob"].animate.shift(direction))
        self.play(AnimationGroup(*anims, lag_ratio=0.02, run_time=2.5))
        self.play(FadeOut(label), run_time=0.3)
        self.cars_group = cars

    # ─────────────── 3. AI DENSITY ANALYSIS ──────────────────

    def _show_density_analysis(self):
        header = Text("AI Density Analysis — Real-Time Computer Vision",
                      font_size=22, color=ACCENT, weight=BOLD)
        header.to_edge(UP, buff=0.3)
        self.play(Write(header), run_time=0.8)

        # scanning animation: a sweeping line
        scan_line = Line(UP * 4, DOWN * 4, color=ACCENT, stroke_width=2, stroke_opacity=0.6)
        scan_line.move_to(LEFT * 5)
        self.play(scan_line.animate.move_to(RIGHT * 5), run_time=2.0, rate_func=linear)
        self.remove(scan_line)

        # draw density bars at each intersection
        bars = VGroup()
        bar_labels = VGroup()
        for (r, c), center in self.intersections.items():
            density = random.randint(2, 10)
            bar_h = density * 0.06
            bar = Rectangle(
                width=0.18, height=bar_h,
                fill_color=interpolate_color(
                    ManimColor(SIG_GREEN), ManimColor(SIG_RED), density / 10
                ),
                fill_opacity=0.85, stroke_width=0.5, stroke_color=WHITE
            )
            bar.move_to(center + UP * (bar_h / 2 + 0.3))
            num = Text(str(density), font_size=11, color=WHITE)
            num.next_to(bar, UP, buff=0.04)
            bars.add(bar)
            bar_labels.add(num)

        self.play(
            LaggedStart(*[GrowFromEdge(b, DOWN) for b in bars],
                        lag_ratio=0.06, run_time=1.8),
        )
        self.play(FadeIn(bar_labels, lag_ratio=0.04), run_time=0.8)
        self.wait(1.2)

        # AI decision text
        decision = Text("AI computing optimal signal splits...",
                        font_size=18, color="#aaa")
        decision.next_to(header, DOWN, buff=0.2)
        self.play(FadeIn(decision), run_time=0.4)
        self.wait(1.0)

        self.play(FadeOut(bars), FadeOut(bar_labels),
                  FadeOut(decision), FadeOut(header), run_time=0.7)

    # ─────────────── 4. DYNAMIC SIGNAL ADJUSTMENT ────────────

    def _show_signal_adjustment(self):
        header = Text("Dynamic Signal Timing Adjustment",
                      font_size=22, color=SIG_GREEN, weight=BOLD)
        header.to_edge(UP, buff=0.3)
        self.play(Write(header), run_time=0.8)

        # Animate signals switching at different intersections
        # Phase 1: Heavy NS traffic → extend NS green
        note1 = Text("Heavy N-S traffic detected → extending green",
                      font_size=16, color="#ccc")
        note1.to_edge(DOWN, buff=0.5)
        self.play(FadeIn(note1), run_time=0.4)

        switch_anims = []
        for r in range(self.GRID):
            for c in range(self.GRID):
                # flash NS signals to show they stay green longer
                ns_sig = self.signals[(r, c)]["NS"]
                glow = ns_sig.copy().set_opacity(0.5).scale(1.3)
                glow.set_color(SIG_GREEN)
                switch_anims.append(Indicate(ns_sig, color=SIG_GREEN, scale_factor=1.15))
        self.play(AnimationGroup(*switch_anims, lag_ratio=0.05, run_time=2.0))
        self.wait(0.6)

        # Phase 2: Switch some to EW
        note2 = Text("Balancing E-W corridors...",
                      font_size=16, color="#ccc")
        note2.to_edge(DOWN, buff=0.5)
        self.play(ReplacementTransform(note1, note2), run_time=0.4)

        switch2 = []
        chosen = [(0, 1), (1, 2), (2, 0)]
        for (r, c) in chosen:
            ns_sig = self.signals[(r, c)]["NS"]
            ew_sig = self.signals[(r, c)]["EW"]
            switch2.append(ApplyMethod(ns_sig.set_state, "red"))
            switch2.append(ApplyMethod(ew_sig.set_state, "green"))
        self.play(AnimationGroup(*switch2, lag_ratio=0.1, run_time=1.5))
        self.wait(0.8)
        self.play(FadeOut(note2), FadeOut(header), run_time=0.5)

    # ─────────────── 5. EMERGENCY VEHICLE ────────────────────

    def _emergency_dispatch(self):
        # Dramatic announcement
        overlay = Rectangle(
            width=14, height=8, fill_color=BLACK, fill_opacity=0.6, stroke_width=0
        )
        alert_text = Text("🚨 EMERGENCY VEHICLE DETECTED 🚨",
                          font_size=30, color="#ff0000", weight=BOLD)
        sub_text = Text("Ambulance dispatched — AI activating Green Corridor",
                        font_size=18, color=WHITE)
        sub_text.next_to(alert_text, DOWN, buff=0.35)
        alert_grp = VGroup(alert_text, sub_text)

        self.play(FadeIn(overlay, run_time=0.3))
        self.play(Write(alert_text, run_time=0.8))
        self.play(FadeIn(sub_text, shift=UP * 0.2), run_time=0.5)

        # Flash effect
        for _ in range(3):
            self.play(
                alert_text.animate.set_color("#ff4444"), run_time=0.15
            )
            self.play(
                alert_text.animate.set_color("#ff0000"), run_time=0.15
            )

        self.wait(0.5)
        self.play(FadeOut(alert_grp), FadeOut(overlay), run_time=0.5)

    # ─────────────── 6. GREEN CORRIDOR ───────────────────────

    def _green_corridor(self):
        header = Text("AI Green Corridor — Priority Route Clearance",
                      font_size=22, color=CORRIDOR_GLOW, weight=BOLD)
        header.to_edge(UP, buff=0.3)
        self.play(Write(header), run_time=0.8)

        # Define the corridor path: (0,0) → (0,1) → (0,2) → (1,2) → (2,2)
        corridor_path = [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2)]
        corridor_centers = [self.intersections[p] for p in corridor_path]

        # 1) Highlight corridor intersections with glowing squares
        glow_squares = VGroup()
        for pos in corridor_path:
            center = self.intersections[pos]
            sq = Square(
                side_length=0.55, fill_color=CORRIDOR_GLOW,
                fill_opacity=0.25, stroke_color=CORRIDOR_GLOW, stroke_width=2
            ).move_to(center)
            glow_squares.add(sq)

        self.play(LaggedStart(*[GrowFromCenter(s) for s in glow_squares],
                              lag_ratio=0.15, run_time=1.5))

        # 2) Turn all corridor signals green, perpendicular to red
        sig_anims = []
        for i, pos in enumerate(corridor_path):
            if i < len(corridor_path) - 1:
                nxt = corridor_path[i + 1]
                dr = nxt[0] - pos[0]
                dc = nxt[1] - pos[1]
                if dc != 0:  # horizontal movement → EW green
                    sig_anims.append(
                        ApplyMethod(self.signals[pos]["EW"].set_state, "green"))
                    sig_anims.append(
                        ApplyMethod(self.signals[pos]["NS"].set_state, "red"))
                else:  # vertical movement → NS green
                    sig_anims.append(
                        ApplyMethod(self.signals[pos]["NS"].set_state, "green"))
                    sig_anims.append(
                        ApplyMethod(self.signals[pos]["EW"].set_state, "red"))

        self.play(AnimationGroup(*sig_anims, lag_ratio=0.08, run_time=1.5))

        # 3) Move regular cars out of the corridor
        note = Text("Clearing traffic from corridor...", font_size=16, color="#ccc")
        note.to_edge(DOWN, buff=0.5)
        self.play(FadeIn(note), run_time=0.3)

        clear_anims = []
        for info in self.car_mobs:
            mob = info["mob"]
            # If car is near corridor, push it aside
            for cc in corridor_centers:
                if np.linalg.norm(mob.get_center() - cc) < 1.0:
                    push_dir = UP * 0.6 if random.random() > 0.5 else DOWN * 0.6
                    clear_anims.append(mob.animate.shift(push_dir).set_opacity(0.4))
                    break
        if clear_anims:
            self.play(AnimationGroup(*clear_anims, lag_ratio=0.03, run_time=1.5))

        self.play(FadeOut(note), run_time=0.3)

        # 4) Draw path line
        path_points = [c.copy() for c in corridor_centers]
        corridor_line = VMobject(color=CORRIDOR_GLOW, stroke_width=4, stroke_opacity=0.8)
        corridor_line.set_points_smoothly(path_points)
        self.play(Create(corridor_line), run_time=1.2)

        # 5) Ambulance drives through
        ambulance = make_emergency_vehicle("ambulance")
        ambulance.move_to(corridor_centers[0] + LEFT * 1.5)

        # Siren glow ring
        siren_ring = Circle(
            radius=0.3, stroke_color="#ff0000", stroke_width=3,
            fill_opacity=0
        ).move_to(ambulance.get_center())

        self.play(FadeIn(ambulance, scale=0.5), run_time=0.5)
        self.add(siren_ring)

        # Animate ambulance along the corridor
        for i, target in enumerate(corridor_centers):
            # determine rotation
            if i > 0:
                prev = corridor_centers[i - 1]
                diff = target - prev
                angle = np.arctan2(diff[1], diff[0])
                ambulance.rotate(angle - getattr(self, '_last_angle', 0), about_point=ambulance.get_center())
                self._last_angle = angle

            # Siren pulse
            siren_pulse = Circle(
                radius=0.15, stroke_color="#ff0000",
                stroke_width=2, fill_opacity=0
            ).move_to(ambulance.get_center())

            self.play(
                ambulance.animate.move_to(target),
                siren_ring.animate.move_to(target),
                siren_pulse.animate.scale(3).set_opacity(0),
                run_time=0.7,
                rate_func=smooth,
            )
            self.remove(siren_pulse)

            # Flash the intersection green
            sq = glow_squares[i]
            self.play(
                Flash(sq.get_center(), color=CORRIDOR_GLOW,
                      flash_radius=0.4, num_lines=8, line_length=0.15,
                      run_time=0.3),
            )

        # Ambulance exits
        exit_point = corridor_centers[-1] + DOWN * 2
        self.play(
            ambulance.animate.move_to(exit_point).set_opacity(0),
            siren_ring.animate.move_to(exit_point).set_opacity(0),
            run_time=1.0,
        )
        self.remove(ambulance, siren_ring)

        # Success message
        success = Text("✅ Emergency vehicle passed — corridor cleared in 4.2s",
                       font_size=18, color=CORRIDOR_GLOW)
        success.to_edge(DOWN, buff=0.5)
        self.play(FadeIn(success, shift=UP * 0.2), run_time=0.5)
        self.wait(1.0)

        # Cleanup corridor visuals
        self.play(
            FadeOut(glow_squares), FadeOut(corridor_line),
            FadeOut(success), FadeOut(header),
            run_time=0.8,
        )

        # Restore car opacity
        restore = [info["mob"].animate.set_opacity(1.0) for info in self.car_mobs]
        self.play(AnimationGroup(*restore, lag_ratio=0.02, run_time=0.8))

    # ─────────────── 7. SECOND EMERGENCY (FIRE TRUCK) ─────────

    def _fire_truck_corridor(self):
        header = Text("🚒 Fire Truck — Cross-Grid Corridor",
                      font_size=22, color=FIRETRUCK_COLOR, weight=BOLD)
        header.to_edge(UP, buff=0.3)
        self.play(Write(header), run_time=0.7)

        # Different corridor: (2,0) → (1,0) → (0,0) → (0,1) → (0,2)
        corridor2 = [(2, 0), (1, 0), (0, 0), (0, 1), (0, 2)]
        centers2 = [self.intersections[p] for p in corridor2]

        # Glow
        glows2 = VGroup()
        for pos in corridor2:
            sq = Square(
                side_length=0.55, fill_color=FIRETRUCK_COLOR,
                fill_opacity=0.2, stroke_color=FIRETRUCK_COLOR, stroke_width=2
            ).move_to(self.intersections[pos])
            glows2.add(sq)
        self.play(LaggedStart(*[GrowFromCenter(s) for s in glows2],
                              lag_ratio=0.12, run_time=1.2))

        # Signals
        sig_anims = []
        for i, pos in enumerate(corridor2):
            if i < len(corridor2) - 1:
                nxt = corridor2[i + 1]
                dc = nxt[1] - pos[1]
                if dc != 0:
                    sig_anims.append(
                        ApplyMethod(self.signals[pos]["EW"].set_state, "green"))
                    sig_anims.append(
                        ApplyMethod(self.signals[pos]["NS"].set_state, "red"))
                else:
                    sig_anims.append(
                        ApplyMethod(self.signals[pos]["NS"].set_state, "green"))
                    sig_anims.append(
                        ApplyMethod(self.signals[pos]["EW"].set_state, "red"))
        self.play(AnimationGroup(*sig_anims, lag_ratio=0.08, run_time=1.0))

        # Path line
        path_points = [c.copy() for c in centers2]
        cline = VMobject(color=FIRETRUCK_COLOR, stroke_width=4, stroke_opacity=0.7)
        cline.set_points_smoothly(path_points)
        self.play(Create(cline), run_time=0.8)

        # Fire truck
        ftruck = make_emergency_vehicle("firetruck")
        ftruck.move_to(centers2[0] + DOWN * 1.2)
        self.play(FadeIn(ftruck, scale=0.5), run_time=0.4)

        self._last_angle = 0
        for i, target in enumerate(centers2):
            if i > 0:
                prev = centers2[i - 1]
                diff = target - prev
                angle = np.arctan2(diff[1], diff[0])
                ftruck.rotate(angle - self._last_angle, about_point=ftruck.get_center())
                self._last_angle = angle
            pulse = Circle(radius=0.12, stroke_color=FIRETRUCK_COLOR,
                           stroke_width=2, fill_opacity=0).move_to(ftruck.get_center())
            self.play(
                ftruck.animate.move_to(target),
                pulse.animate.scale(3).set_opacity(0),
                run_time=0.6, rate_func=smooth,
            )
            self.remove(pulse)

        exit_pt = centers2[-1] + RIGHT * 2
        self.play(ftruck.animate.move_to(exit_pt).set_opacity(0), run_time=0.6)
        self.remove(ftruck)

        done = Text("✅ Fire truck cleared — signals restoring",
                     font_size=18, color=FIRETRUCK_COLOR)
        done.to_edge(DOWN, buff=0.5)
        self.play(FadeIn(done, shift=UP * 0.2), run_time=0.4)
        self.wait(0.8)
        self.play(FadeOut(glows2), FadeOut(cline), FadeOut(done),
                  FadeOut(header), run_time=0.7)

    # ─────────────── 8. STATS DASHBOARD ──────────────────────

    def _show_dashboard(self):
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.0)

        title = Text("System Performance Dashboard",
                     font_size=30, color=WHITE, weight=BOLD)
        title.to_edge(UP, buff=0.5)

        # Stats panel
        panel = RoundedRectangle(
            width=10, height=5, corner_radius=0.2,
            fill_color=PANEL_BG, fill_opacity=0.95,
            stroke_color=PANEL_BORDER, stroke_width=2,
        ).move_to(DOWN * 0.3)

        stats = [
            ("Total Vehicles Processed", "147"),
            ("Avg. Wait Time (Normal)", "23.4s"),
            ("Avg. Wait Time (AI Optimized)", "12.1s  ↓48%"),
            ("Emergency Response Time", "4.2s"),
            ("Green Corridor Activations", "2"),
            ("Corridor Clearance Rate", "100%"),
            ("Signal Adjustments Made", "38"),
        ]

        stat_entries = VGroup()
        for i, (label, value) in enumerate(stats):
            lbl = Text(label, font_size=16, color="#aaa")
            val = Text(value, font_size=16, color=CORRIDOR_GLOW, weight=BOLD)
            row = VGroup(lbl, val).arrange(RIGHT, buff=1.0)
            stat_entries.add(row)

        stat_entries.arrange(DOWN, buff=0.25, aligned_edge=LEFT)
        stat_entries.move_to(panel.get_center())

        self.play(Write(title), FadeIn(panel), run_time=1.0)
        self.play(LaggedStart(*[FadeIn(s, shift=RIGHT * 0.3) for s in stat_entries],
                              lag_ratio=0.12, run_time=2.5))
        self.wait(1.5)

        # Efficiency chart
        subtitle = Text("Wait Time Reduction", font_size=18, color=WHITE)
        subtitle.next_to(panel, DOWN, buff=0.5)

        # Before/After bars
        before_bar = Rectangle(width=3.5, height=0.4, fill_color=SIG_RED,
                               fill_opacity=0.8, stroke_width=0)
        after_bar = Rectangle(width=1.8, height=0.4, fill_color=SIG_GREEN,
                              fill_opacity=0.8, stroke_width=0)
        before_lbl = Text("Before AI: 23.4s", font_size=14, color=WHITE)
        after_lbl = Text("After AI: 12.1s", font_size=14, color=WHITE)

        before_bar.next_to(subtitle, DOWN, buff=0.3).align_to(subtitle, LEFT)
        after_bar.next_to(before_bar, DOWN, buff=0.15).align_to(before_bar, LEFT)
        before_lbl.next_to(before_bar, RIGHT, buff=0.2)
        after_lbl.next_to(after_bar, RIGHT, buff=0.2)

        self.play(FadeIn(subtitle), run_time=0.4)
        self.play(
            GrowFromEdge(before_bar, LEFT), FadeIn(before_lbl),
            run_time=0.8,
        )
        self.play(
            GrowFromEdge(after_bar, LEFT), FadeIn(after_lbl),
            run_time=0.8,
        )
        self.wait(2.0)

    # ─────────────── 9. OUTRO ────────────────────────────────

    def _outro(self):
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.8)

        lines = VGroup(
            Text("Dynamic AI Traffic Flow Optimizer", font_size=28,
                 color=WHITE, weight=BOLD),
            Text("✦  Real-time computer vision density analysis", font_size=16, color="#ccc"),
            Text("✦  Adaptive signal timing via AI scoring model", font_size=16, color="#ccc"),
            Text("✦  Emergency green corridor with preemption", font_size=16, color="#ccc"),
            Text("✦  Multi-vehicle priority support", font_size=16, color="#ccc"),
            Text("", font_size=10),
            Text("Prototype Demo — Built with Manim", font_size=14, color="#777"),
        ).arrange(DOWN, buff=0.25)

        self.play(LaggedStart(*[FadeIn(l, shift=UP * 0.2) for l in lines],
                              lag_ratio=0.15, run_time=2.5))
        self.wait(2.0)
        self.play(FadeOut(lines), run_time=1.5)

    # ══════════════════════════════════════════════════════════
    #                     CONSTRUCT
    # ══════════════════════════════════════════════════════════

    def construct(self):
        self._play_title()
        self._build_grid()
        self._spawn_cars(count=20)
        self._show_density_analysis()
        self._show_signal_adjustment()
        self._emergency_dispatch()
        self._green_corridor()
        self._fire_truck_corridor()
        self._show_dashboard()
        self._outro()
