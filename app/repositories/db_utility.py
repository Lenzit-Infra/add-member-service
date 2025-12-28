# app/repositories/db_utility.py
from sqlalchemy.orm import Session
from app.core.database import Base, engine, SessionLocal
from app.models.agent import Agent, AgentSession, AgentGroupMembership
from app.models.group import Group
from app.models.member import Member
from app.models.order import Order, OrderSourceGroup
from app.models.logs import OperationLog, MemberMovement

# List of all models (tables) in reverse order of dependency for clean deletion
# This order is safer for SQLite to handle foreign key constraints
ALL_MODELS = [
    OperationLog, MemberMovement, 
    OrderSourceGroup, Order, 
    AgentGroupMembership, AgentSession, 
    Agent, Member, Group 
]

def clear_table(model_class):
    """Deletes all records from a single specified table."""
    db = SessionLocal()
    try:
        # Use query(model_class).delete() for bulk deletion
        count = db.query(model_class).delete()
        db.commit()
        return count
    except Exception as e:
        db.rollback()
        print(f"Error clearing {model_class.__tablename__}: {e}")
        return 0
    finally:
        db.close()

def clear_all_data():
    """Deletes all data from all defined tables, keeping the table structure."""
    print("--- WARNING: Deleting ALL data ---")
    total_deleted = 0
    
    # We loop through the list of models and delete one by one
    for Model in ALL_MODELS:
        count = clear_table(Model)
        print(f"Deleted {count} records from {Model.__tablename__}.")
        total_deleted += count
    
    print(f"Total records deleted: {total_deleted}")
    print("Database tables are cleared and ready.")

def drop_all_tables():
    """Drops all tables and recreates the schema. Use with caution."""
    print("--- WARNING: DROPPING AND RECREATING ALL TABLES (Hard Reset) ---")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Database schema successfully reset.")