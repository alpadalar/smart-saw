"""
Smart Band Saw Control System - Application Launcher

This script properly launches the application by running it as a module.
"""

import sys
import asyncio
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run the application
from src.main import main

if __name__ == "__main__":
    print("=" * 60)
    print("Smart Band Saw Control System")
    print("=" * 60)
    print()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nApplication stopped by user (Ctrl+C)")
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
