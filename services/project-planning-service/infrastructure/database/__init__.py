"""
Database Infrastructure Package
================================

Provides database connectivity, session management, and initialization.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator
import os

from .models import Base


# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

def get_database_url() -> str:
    """Get database URL from environment or use default SQLite."""
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return db_url
    
    # Default to SQLite in data directory
    db_path = os.getenv("DATABASE_PATH", "data/project_planning.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return f"sqlite:///{db_path}"


# ============================================================================
# DATABASE ENGINE AND SESSION
# ============================================================================

# Create engine
DATABASE_URL = get_database_url()

# Engine configuration
engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    # SQLite-specific configuration
    engine_kwargs.update({
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool
    })

engine = create_engine(DATABASE_URL, **engine_kwargs)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def init_database():
    """Initialize database schema."""
    Base.metadata.create_all(bind=engine)
    print(f"✅ Database initialized at: {DATABASE_URL}")


def drop_database():
    """Drop all database tables (use with caution)."""
    Base.metadata.drop_all(bind=engine)
    print(f"⚠️  Database tables dropped at: {DATABASE_URL}")


# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Provide a transactional database session.
    
    Usage:
        with get_db_session() as session:
            # Perform database operations
            session.add(model_instance)
            session.commit()
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI routes to get database session.
    
    Usage:
        @app.get("/...")
        def route(db: Session = Depends(get_db)):
            # Use db session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

