"""
Initialize both databases with seed data:
- readonly.db: Read-only data (for MCP db server)
- crud.db: CRUD database (for API server)
"""
import sqlite3
import os

DB_DIR = os.path.join(os.path.dirname(__file__))

USERS = [
    (1, "Alice Johnson", "alice@example.com", "IT"),
    (2, "Bob Smith", "bob@example.com", "IT"),
    (3, "Carol White", "carol@example.com", "HR"),
    (4, "David Brown", "david@example.com", "Finance"),
    (5, "Eve Davis", "eve@example.com", "IT"),
]

INCIDENTS = [
    (1, "INC001", "Cannot login to system", "open"),
    (2, "INC002", "Email not working", "open"),
    (3, "INC003", "Printer issue on floor 3", "in_progress"),
    (4, "INC004", "Software installation request", "resolved"),
    (5, "INC005", "Network slow in meeting room", "open"),
]


def init_db(db_path: str):
    """Initialize a database with tables and seed data."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT,
            email TEXT,
            department TEXT
        )
    """)

    # Create incidents table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY,
            number TEXT,
            description TEXT,
            status TEXT
        )
    """)

    # Check if data already exists
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        # Seed users
        cursor.executemany("INSERT INTO users VALUES (?, ?, ?, ?)", USERS)
        # Seed incidents
        cursor.executemany("INSERT INTO incidents VALUES (?, ?, ?, ?)", INCIDENTS)
        print(f"  Seeded 5 users and 5 incidents")
    else:
        print("  Data already exists")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    readonly_path = os.path.join(DB_DIR, "readonly.db")
    crud_path = os.path.join(DB_DIR, "crud.db")

    print(f"Initializing READ-ONLY database: {readonly_path}")
    init_db(readonly_path)

    print(f"Initializing CRUD database: {crud_path}")
    init_db(crud_path)

    print("\nDone! Both databases are ready.")
