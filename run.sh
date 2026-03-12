#!/bin/bash
# ─────────────────────────────────────────────
#  Dynamic AI Traffic Flow Optimizer
#  One-click render script
# ─────────────────────────────────────────────
set -e

cd "$(dirname "$0")"

echo "╔════════════════════════════════════════════╗"
echo "║  AI Traffic Flow Optimizer — Manim Render  ║"
echo "╚════════════════════════════════════════════╝"
echo ""

# Check dependencies
if ! command -v manim &> /dev/null; then
    echo "⚠  Manim not found. Installing..."
    pip install manim numpy
fi

QUALITY="${1:-h}"   # default high quality; pass 'l' for low

echo "🎬  Rendering demo (quality: ${QUALITY})..."
echo ""

manim -pq${QUALITY} manim_demo.py TrafficOptimizerDemo

echo ""
echo "✅  Done!  Video saved in media/videos/"
