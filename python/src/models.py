"""SQLAlchemy table-models that allow python to peer into the database schema using
OOP-defined DDL."""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, Float
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """The Base class has a class-state variable 'metadata'. Tables will attatch to the metadata instance in-memory"""
    pass

"""
class xxxxx(Base):
    __tablename__ = <table_name_in_db>
    <table_column_in_db> = Column(Type: enum(Integer, String(<int length>), Text, ForeignKey('<table_name>.<table_pk>'), Float, ...), nullable = True : bool, primary_key = False : bool)
"""

class Film(Base):
    __tablename__ = "film"
    
    film_id = Column(Integer, primary_key=True)
    name = Column("....")
    Column("....")
