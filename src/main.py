"""
Main application entry point.
"""

import asyncio
import signal
import sys
import logging
from pathlib import Path

from .core.lifecycle import ApplicationLifecycle

logger = logging.getLogger(__name__)


def setup_signal_handlers(app: ApplicationLifecycle, loop: asyncio.AbstractEventLoop):
    """
    Setup signal handlers for graceful shutdown.

    Args:
        app: ApplicationLifecycle instance
        loop: asyncio event loop
    """
    def signal_handler(signum, frame):
        """Handle shutdown signals."""
        signame = signal.Signals(signum).name
        logger.info(f"Received signal {signame} - initiating shutdown")

        # Request shutdown
        app.request_shutdown()

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """
    Main application entry point.
    """
    app = None

    try:
        # Create application
        app = ApplicationLifecycle()

        # Setup signal handlers
        loop = asyncio.get_event_loop()
        setup_signal_handlers(app, loop)

        # Start all services
        await app.start()

        # Run until shutdown requested
        await app.run_forever()

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1

    finally:
        # Graceful shutdown
        if app:
            await app.stop()

    return 0


if __name__ == "__main__":
    # Run application
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
