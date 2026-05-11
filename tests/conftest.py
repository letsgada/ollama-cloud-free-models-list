import sys
from pathlib import Path

# Make the repo root importable so `from utils import ...` works
# regardless of where pytest is invoked from.
sys.path.insert(0, str(Path(__file__).parent.parent))
