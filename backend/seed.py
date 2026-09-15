import sys
from pathlib import Path

# Add backend directory and root to sys.path
backend_dir = Path(__file__).resolve().parent
root_dir = backend_dir.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from seed import run_seed

if __name__ == "__main__":
    print("Starting enterprise database seeding...")
    run_seed()
    print("Enterprise database seeding completed successfully.")
