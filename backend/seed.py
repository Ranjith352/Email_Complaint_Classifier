import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import seed_enterprise_data

if __name__ == "__main__":
    print("Starting enterprise database seeding...")
    seed_enterprise_data()
    print("Enterprise database seeding completed successfully.")
