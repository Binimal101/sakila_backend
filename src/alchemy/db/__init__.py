"""SQLAlchemy abstractions"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

DATABASE_URL = "mysql+pymysql://user:password@localhost/sakila"

engine = create_engine( #synchronous engine, lets not take into acct. race conditions :p
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    pool_pre_ping=True,  # Verify connections before using them
    echo=False,  # Set to True for SQL logging during development
)

SessionLocal = sessionmaker( #session factory
    autocommit=False,
    autoflush=False,
    bind=engine,
)

def get_db():
    """
    Dependency function for FastAPI or similar frameworks.
    
    Usage in FastAPI:
        @app.get("/items/")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    
    Yields:
        Session: SQLAlchemy session instance
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()