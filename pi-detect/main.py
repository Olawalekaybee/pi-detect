#!/usr/bin/env python3
"""
Pi-Detect: Real-time Object Detection with Live Streaming
Entry point for the Flask application.
"""

import argparse
from app import create_app
from app.config import Config
from app.utils.logger import get_logger

logger = get_logger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Pi-Detect — Real-time object detection livestream"
    )
    parser.add_argument(
        "--host", default=Config.HOST, help="Host address (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=Config.PORT, help="Port (default: 5000)"
    )
    parser.add_argument(
        "--debug", action="store_true", default=False, help="Enable debug mode"
    )
    parser.add_argument(
        "--no-detection", action="store_true", default=False,
        help="Stream raw camera feed without detection (useful for testing)"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    logger.info("=" * 50)
    logger.info("  Pi-Detect — Object Detection Livestream")
    logger.info("=" * 50)
    logger.info(f"  Host     : {args.host}")
    logger.info(f"  Port     : {args.port}")
    logger.info(f"  Debug    : {args.debug}")
    logger.info(f"  Detection: {not args.no_detection}")
    logger.info("=" * 50)

    app = create_app(detection_enabled=not args.no_detection)

    app.run(
        host=args.host,
        port=args.port,
        debug=args.debug,
        threaded=True,
        use_reloader=False,  # Prevent double-init of camera
    )


if __name__ == "__main__":
    main()
