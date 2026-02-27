import sys
from pathlib import Path

# Make src/ importable so tests can do `from server.xxx import ...`
# without needing the package to be installed.
sys.path.insert(0, str(Path(__file__).parent / "src"))
