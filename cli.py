"""
CLI Entry Point for Discord Member Monitoring Bot
Run this file to access the command-line interface
"""

import asyncio
import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.cli_manager import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCLI stopped by user")
    except Exception as e:
        print(f"CLI error: {e}")
        sys.exit(1)