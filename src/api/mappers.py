from sqlalchemy.orm import Session
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from geoalchemy2 import WKTElement
from typing import Dict, Any

from src.alchemy.models import Country, City, Address


def _get_or_create_country(db: Session, country_name: str) -> Country:
    """Return existing Country or insert + return a new one (race-safe).

    Uses a flush + IntegrityError retry to handle simple concurrent inserts.
    """
    country_name = country_name.lower()

    country = db.execute(select(Country).where(
        func.lower(Country.country.ilike(country_name)) #don't wanna do data migration, just ignore non-uniform case in db
    )).scalar_one_or_none() #limit 1

    if country:
        return country
    country = Country(country=country_name)
    db.add(country)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        country = db.execute(select(Country).where(Country.country.ilike(country_name))).scalar_one()
    else:
        db.refresh(country)
    return country


def _get_or_create_city(db: Session, city_name: str, country_id: int) -> City:
    """Return existing City or insert + return a new one (race-safe).

    City uniqueness is considered for (city, country_id).
    """
    city = db.execute(select(City).where(City.city.ilike(city_name), City.country_id == country_id)).scalar_one_or_none()
    if city:
        return city
    city = City(city=city_name, country_id=country_id)
    db.add(city)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        city = db.execute(select(City).where(City.city.ilike(city_name), City.country_id == country_id)).scalar_one()
    else:
        db.refresh(city)
    return city


def _create_address(db: Session, addr_payload: Dict[str, Any], city_id: int, lat: float, lon: float) -> Address:
    """Create an Address row with a spatial `location` from lat/lon and return it."""
    loc = WKTElement(f"POINT({lon} {lat})") #each customer (as pertaining to DB schema) has not NULL GEOMETRY datatype in addr
    addr = Address(
        address=addr_payload.get("address_line1") or addr_payload.get("address") or "",
        address2=addr_payload.get("address_line2") or addr_payload.get("address2"),
        district=addr_payload.get("district") or "",
        city_id=city_id,
        postal_code=addr_payload.get("postal_code"),
        phone=addr_payload.get("phone") or "",
        location=loc,
    )
    db.add(addr)
    db.flush()
    db.refresh(addr)
    return addr
