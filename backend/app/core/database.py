from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Database configuration
# We use SQLite for now. For production, change this URL to PostgreSQL.
SQLALCHEMY_DATABASE_URL = "sqlite:///bot_database.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class from which all models will inherit
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()