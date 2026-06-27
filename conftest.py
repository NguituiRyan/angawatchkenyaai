import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# archived/ holds the deprecated credit-scoring cluster (kept on disk for reference,
# out of the live app). Don't collect its tests.
collect_ignore_glob = ["archived/*"]
