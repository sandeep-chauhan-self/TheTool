# backend/migrations.py
from db import init_db_if_needed
if __name__ == "__main__":
    print("Initializing DB and schema...")
    init_db_if_needed()
    print("Done.")
