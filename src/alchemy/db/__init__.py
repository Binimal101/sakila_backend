"""SQLAlchemy abstractions"""

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv

from src import DATABASE_URL

engine = create_engine( #synchronous engine, lets not take into acct. race conditions :p
    DATABASE_URL, # type: ignore
    poolclass=QueuePool,
    pool_size=5,
    pool_pre_ping=True,  # Verify connections before using them
)

SessionLocal = sessionmaker( #session factory
    autocommit=False,
    autoflush=False,
    bind=engine,
)

def get_db():
    """
    Dependency func for fAPI.
        @app.get("/items/")
        def read_items(db: Session = fastapi.Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()