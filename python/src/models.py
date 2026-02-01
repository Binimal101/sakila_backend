"""SQLAlchemy table-models that allow python to peer into the database schema using
OOP-defined DDL."""

#column types
from sqlalchemy import (
    Column,
    Integer,
    Numeric,
    String,
    Text,
    DateTime,
    LargeBinary,
    ForeignKey,
    Index,
    UniqueConstraint,
    text,
)

#mysql specific types
from sqlalchemy.dialects.mysql import (
    TINYINT,
    SMALLINT,
    MEDIUMINT,
    INTEGER,
    YEAR,
    ENUM,
    SET,
    TIMESTAMP,
    GEOMETRY,
)

#Base super for table models
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
    title = Column(String(128), nullable=False)
    description = Column(Text)
    release_year = Column(YEAR)
    language_id = Column(TINYINT(unsigned=True), ForeignKey("language.language_id"), nullable=False)
    original_language_id = Column(TINYINT(unsigned=True), ForeignKey("language.language_id"))
    rental_duration = Column(Integer, nullable=False) #default = 3
    rental_rate = Column(Numeric(4,2), nullable=False) #default = 4.99, numeric > float to specify precision for modifications
    length = Column(Integer)
    replacement_cost = Column(Numeric(5,2), nullable=False) #default = 19.99
    rating = Column(ENUM('G','PG','PG-13','R','NC-17'), name="film_rating_enum")
    special_features = Column(SET('Trailers','Commentaries','Deleted Scenes','Behind the Scenes'), name="film_features_enum") #name= is used for SET and ENUM differently than normal
    
    last_update = Column(
        TIMESTAMP, 
        server_default=text("CURRENT_TIMESTAMP"),  #text(...) here is different from Text(...)
        server_onupdate=text("CURRENT_TIMESTAMP"), #text embeds SQL statements to RHS of db-type attrs
        nullable=False
    )
    
class Actor(Base):
    __tablename__ = "actor"

    actor_id = Column(SMALLINT(unsigned=True), primary_key=True, autoincrement=True)
    first_name = Column(String(45), nullable=False)
    last_name = Column(String(45), nullable=False)

    last_update = Column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_actor_last_name", "last_name"),
    )


class FilmActor(Base):
    __tablename__ = "film_actor"

    actor_id = Column(SMALLINT(unsigned=True), ForeignKey("actor.actor_id"), primary_key=True, nullable=False)
    film_id = Column(SMALLINT(unsigned=True), ForeignKey("film.film_id"), primary_key=True, nullable=False)

    last_update = Column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_fk_film_id", "film_id"),
    )


class Category(Base):
    __tablename__ = "category"

    category_id = Column(TINYINT(unsigned=True), primary_key=True, autoincrement=True)
    name = Column(String(25), nullable=False)

    last_update = Column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )


class FilmCategory(Base):
    __tablename__ = "film_category"

    film_id = Column(SMALLINT(unsigned=True), ForeignKey("film.film_id"), primary_key=True, nullable=False)
    category_id = Column(TINYINT(unsigned=True), ForeignKey("category.category_id"), primary_key=True, nullable=False)

    last_update = Column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    __table_args__ = (
        Index("fk_film_category_category", "category_id"),
    )


class Language(Base):
    __tablename__ = "language"

    language_id = Column(TINYINT(unsigned=True), primary_key=True, autoincrement=True)
    name = Column(String(20), nullable=False)  # DDL says CHAR(20); String(20) is fine for mapping

    last_update = Column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )


class FilmText(Base):
    __tablename__ = "film_text"

    film_id = Column(SMALLINT(unsigned=True), primary_key=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)

    __table_args__ = (
        Index("idx_title_description", "title", "description", mysql_prefix="FULLTEXT"),
    )


class Inventory(Base):
    __tablename__ = "inventory"

    inventory_id = Column(MEDIUMINT(unsigned=True), primary_key=True, autoincrement=True)
    film_id = Column(SMALLINT(unsigned=True), ForeignKey("film.film_id"), nullable=False)
    store_id = Column(TINYINT(unsigned=True), ForeignKey("store.store_id"), nullable=False)

    last_update = Column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_fk_film_id", "film_id"),
        Index("idx_store_id_film_id", "store_id", "film_id"),
    )


class Rental(Base):
    __tablename__ = "rental"

    rental_id = Column(Integer, primary_key=True, autoincrement=True)  # DDL: int NOT NULL AUTO_INCREMENT
    rental_date = Column(DateTime, nullable=False)
    inventory_id = Column(MEDIUMINT(unsigned=True), ForeignKey("inventory.inventory_id"), nullable=False)
    customer_id = Column(SMALLINT(unsigned=True), ForeignKey("customer.customer_id"), nullable=False)
    return_date = Column(DateTime)
    staff_id = Column(TINYINT(unsigned=True), ForeignKey("staff.staff_id"), nullable=False)

    last_update = Column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("rental_date", "inventory_id", "customer_id", name="rental_date"),
        Index("idx_fk_inventory_id", "inventory_id"),
        Index("idx_fk_customer_id", "customer_id"),
        Index("idx_fk_staff_id", "staff_id"),
    )


class Payment(Base):
    __tablename__ = "payment"

    payment_id = Column(SMALLINT(unsigned=True), primary_key=True, autoincrement=True)
    customer_id = Column(SMALLINT(unsigned=True), ForeignKey("customer.customer_id"), nullable=False)
    staff_id = Column(TINYINT(unsigned=True), ForeignKey("staff.staff_id"), nullable=False)
    rental_id = Column(Integer, ForeignKey("rental.rental_id"))
    amount = Column(Numeric(5, 2), nullable=False)
    payment_date = Column(DateTime, nullable=False)

    last_update = Column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
        nullable=True,  # DDL: timestamp NULL DEFAULT ...
    )

    __table_args__ = (
        Index("idx_fk_staff_id", "staff_id"),
        Index("idx_fk_customer_id", "customer_id"),
        Index("fk_payment_rental", "rental_id"),
    )


class Customer(Base):
    __tablename__ = "customer"

    customer_id = Column(SMALLINT(unsigned=True), primary_key=True, autoincrement=True)
    store_id = Column(TINYINT(unsigned=True), ForeignKey("store.store_id"), nullable=False)
    first_name = Column(String(45), nullable=False)
    last_name = Column(String(45), nullable=False)
    email = Column(String(50))
    address_id = Column(SMALLINT(unsigned=True), ForeignKey("address.address_id"), nullable=False)
    active = Column(TINYINT(1), nullable=False, server_default=text("1"))
    create_date = Column(DateTime, nullable=False)

    last_update = Column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
        nullable=True,  # DDL: timestamp NULL DEFAULT ...
    )

    __table_args__ = (
        Index("idx_fk_store_id", "store_id"),
        Index("idx_fk_address_id", "address_id"),
        Index("idx_last_name", "last_name"),
    )


class Store(Base):
    __tablename__ = "store"

    store_id = Column(TINYINT(unsigned=True), primary_key=True, autoincrement=True)
    manager_staff_id = Column(TINYINT(unsigned=True), ForeignKey("staff.staff_id"), nullable=False)
    address_id = Column(SMALLINT(unsigned=True), ForeignKey("address.address_id"), nullable=False)

    last_update = Column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_fk_address_id", "address_id"),
        UniqueConstraint("manager_staff_id", name="idx_unique_manager"),
    )


class Staff(Base):
    __tablename__ = "staff"

    staff_id = Column(TINYINT(unsigned=True), primary_key=True, autoincrement=True)
    first_name = Column(String(45), nullable=False)
    last_name = Column(String(45), nullable=False)
    address_id = Column(SMALLINT(unsigned=True), ForeignKey("address.address_id"), nullable=False)
    picture = Column(LargeBinary)  # DDL: blob
    email = Column(String(50))
    store_id = Column(TINYINT(unsigned=True), ForeignKey("store.store_id"), nullable=False)
    active = Column(TINYINT(1), nullable=False, server_default=text("1"))
    username = Column(String(16), nullable=False)
    password = Column(String(40))  # bin collation in DDL is DB-side detail

    last_update = Column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_fk_store_id", "store_id"),
        Index("idx_fk_address_id", "address_id"),
    )


class Address(Base):
    __tablename__ = "address"

    address_id = Column(SMALLINT(unsigned=True), primary_key=True, autoincrement=True)
    address = Column(String(50), nullable=False)
    address2 = Column(String(50))
    district = Column(String(20), nullable=False)
    city_id = Column(SMALLINT(unsigned=True), ForeignKey("city.city_id"), nullable=False)
    postal_code = Column(String(10))
    phone = Column(String(20), nullable=False)
    location = Column(GEOMETRY, nullable=False)  # MySQL spatial type

    last_update = Column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_fk_city_id", "city_id"),
        Index("idx_location", "location", mysql_prefix="SPATIAL"),
    )


class City(Base):
    __tablename__ = "city"

    city_id = Column(SMALLINT(unsigned=True), primary_key=True, autoincrement=True)
    city = Column(String(50), nullable=False)
    country_id = Column(SMALLINT(unsigned=True), ForeignKey("country.country_id"), nullable=False)

    last_update = Column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_fk_country_id", "country_id"),
    )


class Country(Base):
    __tablename__ = "country"

    country_id = Column(SMALLINT(unsigned=True), primary_key=True, autoincrement=True)
    country = Column(String(50), nullable=False)

    last_update = Column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
