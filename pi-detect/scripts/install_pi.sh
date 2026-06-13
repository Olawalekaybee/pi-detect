#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────
# scripts/install_pi.sh
# One-shot setup for Raspberry Pi Zero 2W
# Run once after flashing Pi OS Lite (64-bit recommended)
# Usage: bash scripts/install_pi.sh
# ─────────────────────────────────────────────────────────────────
set -euo pipefail

echo "════════════════════════════════════════"
echo "  Pi-Detect — Raspberry Pi Setup"
echo "════════════════════════════════════════"

# ── System update ──────────────────────────────────────────────
echo "[1/5] Updating system packages…"
sudo apt-get update -qq
sudo apt-get upgrade -y -qq

# ── System dependencies ────────────────────────────────────────
echo "[2/5] Installing system dependencies…"
sudo apt-get install -y -qq \
  python3-pip \
  python3-picamera2 \
  libcamera-apps \
  libopencv-dev \
  python3-opencv \
  git \
  curl \
  libatlas-base-dev    # required for numpy on ARM

# ── Enable camera interface ────────────────────────────────────
echo "[3/5] Enabling camera interface…"
sudo raspi-config nonint do_camera 0
echo "Camera interface enabled."

# ── Python packages ────────────────────────────────────────────
echo "[4/5] Installing Python packages…"
pip install -r requirements-pi.txt --break-system-packages

# ── Create models + logs directories ──────────────────────────
echo "[5/5] Creating project directories…"
mkdir -p models logs

# ── Copy env template ──────────────────────────────────────────
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from template — please edit it now:"
  echo "  nano .env"
fi

echo ""
echo "✓ Installation complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env:          nano .env"
echo "  2. Set USE_PICAMERA=true in .env"
echo "  3. Add your NGROK_AUTHTOKEN to .env"
echo "  4. Start the stream:   bash scripts/start_stream.sh"
