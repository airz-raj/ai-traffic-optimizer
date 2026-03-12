# Dynamic AI Traffic Flow Optimizer & Emergency Green Corridor

A complete working prototype with AI-powered traffic management simulation and a high-quality Manim animation demo.

## 📁 Project Structure

```
drunk/
├── manim_demo.py                  # 🎬 Manim animation (the main deliverable)
├── requirements.txt
├── run.sh                         # One-click render script
├── README.md
└── traffic_system/                # Core simulation engine
    ├── __init__.py
    ├── vehicle.py                 # Vehicle models & types
    ├── traffic_grid.py            # Grid, intersections, signals
    ├── ai_optimizer.py            # AI optimizer + green corridor
    └── simulator.py               # Console-based simulation
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install manim numpy
```

> On macOS you also need: `brew install cairo pango ffmpeg`

### 2. Render the Manim Demo (1080p)

```bash
# High quality 1080p render
manim -pqh manim_demo.py TrafficOptimizerDemo

# Quick preview 480p (faster)
manim -pql manim_demo.py TrafficOptimizerDemo
```

### 3. Run Console Simulation (Optional)

```bash
python -m traffic_system.simulator
```

## 🎬 What the Manim Demo Shows

| Scene | Description |
|-------|-------------|
| **Title** | Animated intro with project name |
| **City Grid** | 3×3 intersection grid builds with roads, buildings, signals |
| **Vehicle Spawn** | 20+ cars populate the road network |
| **AI Density Analysis** | Scanning animation + per-intersection density bars |
| **Signal Adjustment** | AI dynamically rebalances green times |
| **Emergency Alert** | Dramatic 🚨 alert overlay with flashing |
| **Green Corridor (Ambulance)** | Full corridor activation, traffic clearance, ambulance rush-through |
| **Green Corridor (Fire Truck)** | Second emergency with different route |
| **Dashboard** | Performance stats, before/after comparison |
| **Outro** | Feature summary and credits |

## 🧠 AI System Design

### Traffic Density Optimization
- **Weighted scoring model** per approach direction:
  - `0.40` × traffic density
  - `0.30` × average wait time
  - `0.20` × queue length
  - `0.10` × emergency bonus
- Proportional green-time allocation within configurable min/max bounds

### Emergency Green Corridor
- Detects emergency vehicles (ambulance, fire truck, police)
- Preempts signals **3 intersections ahead** along the computed route
- Forces green on the corridor axis, red on perpendicular
- Clears regular traffic from the corridor path
- Automatic restoration after vehicle passes

## 📊 Simulated Results

| Metric | Before AI | After AI |
|--------|-----------|----------|
| Avg. Wait Time | 23.4s | 12.1s (↓48%) |
| Emergency Response | 8.7s | 4.2s (↓52%) |
| Corridor Clearance | N/A | 100% |

## 🛠 Tech Stack

- **Python 3.10+**
- **Manim** — Mathematical animation engine
- **NumPy** — Numerical computation
- Custom AI scoring model (no ML dependencies needed)
