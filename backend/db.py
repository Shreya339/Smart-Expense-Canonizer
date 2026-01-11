
from sqlmodel import SQLModel, create_engine, Session
from .config import DB_URL

engine = create_engine(DB_URL, echo=False)

# Initialize the database schema (create tables if missing)
def init_db():
    SQLModel.metadata.create_all(engine)

# Dependency / helper to open a DB session safely
def get_session():
    # Dependency / helper to open a DB session safely
    return Session(engine)



"""
That allows me to store every classification decision along with confidence, source, risk flags, and audit metadata — which is critical for trust, debugging, and compliance in a financial product.

The DB also supports learning behavior, such as merchant-level embedding memory and override tracking. Over time the system becomes cheaper and more accurate while still being fully auditable.

Why SQLite?

SQLite is perfect here because:

✔ zero setup
✔ file-based
✔ persistent between runs
✔ easy to ship
✔ production-adjacent (many apps use SQLite at edge)

And we still abstract the DB behind:

DB_URL


So later this app could run on:

PostgreSQL

MySQL

Cloud SQL

Without rewriting logic.  -> GOOD ARCHITECTURE
"""