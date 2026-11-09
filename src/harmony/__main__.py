"""
Executable module entrypoint.
Allows running `python -m src.harmony.cli` or `python -m src.harmony`.
"""

import sys
from src.harmony.cli import main

if __name__ == "__main__":
    sys.exit(main())
