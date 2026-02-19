#api
from fastapi import APIRouter, Response, Depends
from typing import Any
from . import router, app

# db
from src.alchemy.models import *

from src.alchemy.db import get_db
from sqlalchemy.orm import Session
from sqlalchemy import select, insert, update, delete, func, and_, or_, literal_column
from datetime import datetime
from geoalchemy2 import WKTElement
from fastapi import HTTPException

# validators / pydantic models
from src.api.validators import validate_address_dep
from src.api.inputModels import *
import src.api.outputModels as schemas  # use `schemas.Film`, `schemas.Actor`, etc.

# data validation (removed - validation handled elsewhere)


@router.get("/api/health")
def health_check() -> Any:
    """Basic health-check endpoint."""
    return {"status": "ok"}


@router.get("/api")
def root() -> Any:
    return {"message": "Sakila backend API"}

"""
Begin project route dependencies
"""

# ---- helpers: map ORM -> Pydantic -------------------------------------------------

def _actor_row_to_pyd(actor):
    return schemas.Actor(
        actor_id=int(actor.actor_id),
        first_name=actor.first_name,
        last_name=actor.last_name,
        last_update=getattr(actor.last_update, "isoformat", lambda: str(actor.last_update))(),
    )


def _film_to_pyd(db: Session, film_obj):
    # load actors for this film
    actor_rows = (
        db.execute(
            select(Actor).join(FilmActor, FilmActor.actor_id == Actor.actor_id).where(FilmActor.film_id == film_obj.film_id)
        )
        .scalars()
        .all()
    )
    actors = [_actor_row_to_pyd(a) for a in actor_rows]

    # load first category for film
    cat_row = (
        db.execute(
            select(Category.name)
            .join(FilmCategory, FilmCategory.category_id == Category.category_id)
            .where(FilmCategory.film_id == film_obj.film_id)
            .limit(1)
        )
        .scalar()
    )

    return schemas.Film(
        film_id=int(film_obj.film_id),
        title=film_obj.title,
        description=film_obj.description,
        release_year=film_obj.release_year,
        language=int(film_obj.language_id),
        original_language=getattr(film_obj, "original_language_id", None),
        actors=actors,
        category=cat_row or "",
        rental_duration=int(film_obj.rental_duration),
        rental_rate=float(film_obj.rental_rate),
        length=film_obj.length,
        replacement_cost=float(film_obj.replacement_cost),
        rating=film_obj.rating,
        special_features=str(film_obj.special_features) if film_obj.special_features else None,
        last_update=getattr(film_obj.last_update, "isoformat", lambda: str(film_obj.last_update))(),
    )


def _rental_row_to_pyd(row):
    # row can be an ORM Rental instance or mapping
    r = row
    return schemas.Rental(
        rental_id=int(r.rental_id),
        rental_date=str(r.rental_date),
        inventory_id=int(r.inventory_id),
        customer_id=int(r.customer_id),
        return_date=str(r.return_date) if r.return_date is not None else None,
        staff_id=int(r.staff_id),
        last_update=str(r.last_update),
    )

# -----------------------------------------------------------------------------------

@router.post("/api/top_5_rentals", response_model=schemas.top5RentalsOutput)
def t5_rentals(payload: top5RentalsInput, db: Session = Depends(get_db)) -> schemas.top5RentalsOutput:
    """Selects top 5 rentals across current store. Returns full `Film` objects (per output model)."""

    rented_count = func.count(Rental.rental_id).label("rented")

    # get top film ids by rental count for the store
    subq = (
        select(Film.film_id)
        .join(Inventory, Inventory.film_id == Film.film_id)
        .join(Rental, Rental.inventory_id == Inventory.inventory_id)
        .where(Inventory.store_id == payload.store_id)
        .group_by(Film.film_id)
        .order_by(rented_count.desc())
        .limit(5)
    )

    film_ids = [r[0] for r in db.execute(subq).all()]

    if not film_ids:
        return schemas.top5RentalsOutput(status=200, rentals=[])

    films = db.execute(select(Film).where(Film.film_id.in_(film_ids))).scalars().all()

    # preserve ordering from film_ids
    films_by_id = {f.film_id: f for f in films}
    out_films = [_film_to_pyd(db, films_by_id[fid]) for fid in film_ids if fid in films_by_id]

    return schemas.top5RentalsOutput(status=200, rentals=out_films)


@router.post("/api/details/film", response_model=schemas.detailsFilmOutput)
def film_details(payload: detailsFilmInput, db: Session = Depends(get_db)) -> schemas.detailsFilmOutput:
    """Return full film details including actors and category."""
    film_obj = db.get(Film, payload.film_id)
    if not film_obj:
        return schemas.detailsFilmOutput(status=404, film=None)

    film_pyd = _film_to_pyd(db, film_obj)
    return schemas.detailsFilmOutput(status=200, film=film_pyd)

@router.post("/api/top_5_actors", response_model=schemas.top5ActorsOutput)
def t5_actors(payload: top5ActorsInput, db: Session = Depends(get_db)) -> schemas.top5ActorsOutput:
    """Top 5 actors by rental count. If payload.store_id is omitted, aggregate across all stores."""
    rented_count = func.count(Rental.rental_id).label("rented")

    stmt = (
        select(Actor.actor_id, Actor.first_name, Actor.last_name, Actor.last_update, rented_count)
        .where(Inventory.store_id == payload.store_id)
        .join(FilmActor, FilmActor.actor_id == Actor.actor_id)
        .join(Film, Film.film_id == FilmActor.film_id)
        .join(Inventory, Inventory.film_id == Film.film_id)
        .join(Rental, Rental.inventory_id == Inventory.inventory_id)
    )

    if payload.store_id is not None:
        stmt = stmt.where(Inventory.store_id == payload.store_id)

    stmt = stmt.group_by(Actor.actor_id).order_by(rented_count.desc()).limit(5)

    rows = db.execute(stmt).all()
    actors = [schemas.Actor(actor_id=int(r.actor_id), first_name=r.first_name, last_name=r.last_name, last_update=str(r.last_update)) for r in rows]

    return schemas.top5ActorsOutput(status=200, actors=actors)

@router.post("/api/top_n_rentals_with_actor", response_model=schemas.topNRentalsWithActorOutput)
def tn_rentals_actor(payload: topNRentalsWithActorInput, db: Session = Depends(get_db)) -> schemas.topNRentalsWithActorOutput:
    """Return rentals that involve films where the given actor appears.
    Pagination via offset/top_n."""
    stmt = (
        select(Rental)
        .join(Inventory, Inventory.inventory_id == Rental.inventory_id)
        .join(Film, Film.film_id == Inventory.film_id)
        .join(FilmActor, FilmActor.film_id == Film.film_id)
        .where(FilmActor.actor_id == payload.actor_id)
        .order_by(Rental.rental_date.desc())
        .offset(payload.offset)
        .limit(payload.top_n)
    )

    rows = db.execute(stmt).scalars().all()
    rentals = [_rental_row_to_pyd(r) for r in rows]
    return schemas.topNRentalsWithActorOutput(status=200, rentals=rentals)

@router.post("/api/query/films", response_model=schemas.queryFilmsOutput)
def query_films(payload: queryFilmsInput, db: Session = Depends(get_db)) -> schemas.queryFilmsOutput:
    """Search films by name, genre, or actor. Returns `Film` objects."""
    stmt = select(Film).distinct().offset(payload.offset).limit(payload.top_n)

    if payload.filter_var == filmsFilterEnum.NAME:
        stmt = select(Film).where(Film.title.ilike(f"%{payload.filter_content}%")).offset(payload.offset).limit(payload.top_n)

    elif payload.filter_var == filmsFilterEnum.GENRE:
        stmt = (
            select(Film)
            .join(FilmCategory, FilmCategory.film_id == Film.film_id)
            .join(Category, Category.category_id == FilmCategory.category_id)
            .where(Category.name.ilike(f"%{payload.filter_content}%"))
            .offset(payload.offset)
            .limit(payload.top_n)
        )

    elif payload.filter_var == filmsFilterEnum.ACTOR:
        stmt = (
            select(Film)
            .join(FilmActor, FilmActor.film_id == Film.film_id)
            .join(Actor, Actor.actor_id == FilmActor.actor_id)
            .where(or_(Actor.first_name.ilike(f"%{payload.filter_content}%"), Actor.last_name.ilike(f"%{payload.filter_content}%")))
            .offset(payload.offset)
            .limit(payload.top_n)
        )

    film_objs = db.execute(stmt).scalars().all()
    films = [_film_to_pyd(db, f) for f in film_objs]
    return schemas.queryFilmsOutput(status=200, films=films)

@router.post("/api/rent", response_model=schemas.rentOutput)
def rent(payload: rentInput, db: Session = Depends(get_db)) -> schemas.rentOutput:
    """Create a Rental for an available inventory item for the given store + film.

    - picks the first inventory item that is not currently rented (no open rental)
    - returns created Rental, or status=400 if none available
    """
    # find available inventory_id for film in store
    sub = (
        select(Inventory.inventory_id)
        .where(and_(Inventory.film_id == payload.film_id, Inventory.store_id == payload.store_id))
        .limit(1)
    )

    # prefer inventory items that have no open rental
    inv_rows = db.execute(select(Inventory).where(and_(Inventory.film_id == payload.film_id, Inventory.store_id == payload.store_id))).scalars().all()
    chosen_inv = None
    for inv in inv_rows:
        open_r = db.execute(select(Rental).where(and_(Rental.inventory_id == inv.inventory_id, Rental.return_date == None))).first()
        if not open_r:
            chosen_inv = inv
            break

    if not chosen_inv:
        return schemas.rentOutput(status=400, rental=None)

    new_rental = Rental(
        rental_date=datetime.utcnow(),
        inventory_id=chosen_inv.inventory_id,
        customer_id=payload.customer_id,
        staff_id=payload.staff_id,
    )
    db.add(new_rental)
    db.commit()
    db.refresh(new_rental)

    return schemas.rentOutput(status=200, rental=_rental_row_to_pyd(new_rental))

@router.post("/api/query/customer", response_model=schemas.queryCustomerOutput)
def query_customer(payload: queryCustomerInput, db: Session = Depends(get_db)) -> schemas.queryCustomerOutput:
    """Query customers by first/last name or id with pagination."""
    stmt = (
        select(Customer, Address, City.city.label("city_name"), Country.country.label("country_name"))
        .join(Address, Address.address_id == Customer.address_id)
        .join(City, City.city_id == Address.city_id)
        .join(Country, Country.country_id == City.country_id)
    )

    if payload.filter_var == customerFilterEnum.FIRST_NAME and payload.filter_text:
        stmt = stmt.where(Customer.first_name.ilike(f"%{payload.filter_text}%"))
    elif payload.filter_var == customerFilterEnum.LAST_NAME and payload.filter_text:
        stmt = stmt.where(Customer.last_name.ilike(f"%{payload.filter_text}%"))
    elif payload.filter_var == customerFilterEnum.CUSTOMER_ID and payload.filter_text:
        try:
            cid = int(payload.filter_text)
            stmt = stmt.where(Customer.customer_id == cid)
        except ValueError:
            return schemas.queryCustomerOutput(status=400, customers=[])

    stmt = stmt.offset(payload.offset).limit(payload.top_n)

    rows = db.execute(stmt).all()
    out_customers = []
    for cust, addr, city_name, country_name in rows:
        out_customers.append(
            Customer(
                customer_id=int(cust.customer_id),
                store_id=int(cust.store_id),
                first_name=cust.first_name,
                last_name=cust.last_name,
                email=cust.email,
                address=schemas.Address(
                    address_line1=addr.address,
                    address_line2=addr.address2,
                    district=addr.district,
                    city=city_name,
                    country=country_name,
                    postal_code=addr.postal_code,
                ),
                location=None,
                active=bool(cust.active),
                create_date=str(cust.create_date),
                last_update=str(cust.last_update),
            )
        )

    return schemas.queryCustomerOutput(status=200, customers=out_customers)

@router.post("/api/customer/create", response_model=schemas.customerCreateOutput)
def create_customer(payload: customerCreateInput, normalized: dict = Depends(validate_address_dep), db: Session = Depends(get_db)) -> schemas.customerCreateOutput:
    """Create customer + address. Uses normalized address from `validate_address_dep` dependency."""
    # ensure country exists
    country_name = normalized.get("components", {}).get("country") or payload.address.country
    country = db.execute(select(Country).where(Country.country.ilike(country_name))).scalar_one_or_none()
    if not country:
        country = Country(country=country_name)
        db.add(country)
        db.commit()
        db.refresh(country)

    # ensure city exists
    city_name = normalized.get("components", {}).get("city") or payload.address.city
    city = db.execute(select(City).where(City.city.ilike(city_name), City.country_id == country.country_id)).scalar_one_or_none()
    if not city:
        city = City(city=city_name, country_id=country.country_id)
        db.add(city)
        db.commit()
        db.refresh(city)

    # insert address (use WKTElement for location)
    lat = normalized.get("latitude")
    lon = normalized.get("longitude")
    if lat is None or lon is None:
        # fallback to 0/0 — validators should prevent this in most cases
        lat = 0.0
        lon = 0.0

    location = WKTElement(f"POINT({lon} {lat})")

    addr = Address(
        address=payload.address.address_line1,
        address2=payload.address.address_line2,
        district=payload.address.district,
        city_id=city.city_id,
        postal_code=payload.address.postal_code,
        phone="",
        location=location,
    )
    db.add(addr)
    db.commit()
    db.refresh(addr)

    # create customer
    cust = Customer(
        store_id=payload.store_id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email,
        address_id=addr.address_id,
        active=1,
        create_date=datetime.utcnow(),
    )
    db.add(cust)
    db.commit()
    db.refresh(cust)

    # build output customer
    out_addr = schemas.Address(
        address_line1=addr.address,
        address_line2=addr.address2,
        district=addr.district,
        city=city.city,
        country=country.country,
        postal_code=addr.postal_code,
    )

    out_cust = schemas.Customer(
        customer_id=int(cust.customer_id),
        store_id=int(cust.store_id),
        first_name=cust.first_name,
        last_name=cust.last_name,
        email=cust.email,
        address=out_addr,
        location={"latitude": lat, "longitude": lon},
        active=bool(cust.active),
        create_date=str(cust.create_date),
        last_update=str(cust.last_update),
    )

    return schemas.customerCreateOutput(status=200, customer=out_cust)

@router.post("/api/customer/edit", response_model=schemas.customerEditOutput)
def edit_customer(payload: customerEditInput, db: Session = Depends(get_db)) -> schemas.customerEditOutput:
    """Update customer fields and optionally their address."""
    cust = db.get(Customer, payload.customer_id)
    if not cust:
        return schemas.customerEditOutput(status=404, customer=None)

    # update scalar fields
    for attr in ("store_id", "first_name", "last_name", "email"):
        val = getattr(payload, attr, None)
        if val is not None:
            setattr(cust, attr, val)

    # update phone/address if provided
    if payload.address:
        addr = db.get(Address, cust.address_id)
        if addr:
            addr.address = payload.address.address_line1
            addr.address2 = payload.address.address_line2
            addr.district = payload.address.district
            addr.postal_code = payload.address.postal_code
            db.add(addr)

    db.add(cust)
    db.commit()
    db.refresh(cust)

    # build output
    # note: city/country lookup for customer's address
    addr = db.get(Address, cust.address_id)
    city = db.get(City, addr.city_id) if addr else None
    country = db.get(Country, city.country_id) if city else None

    out_addr = schemas.Address(
        address_line1=addr.address if addr else "",
        address_line2=addr.address2 if addr else None,
        district=addr.district if addr else "",
        city=city.city if city else "",
        country=country.country if country else "",
        postal_code=addr.postal_code if addr else None,
    )

    out_cust = schemas.Customer(
        customer_id=int(cust.customer_id),
        store_id=int(cust.store_id),
        first_name=cust.first_name,
        last_name=cust.last_name,
        email=cust.email,
        address=out_addr,
        location=None,
        active=bool(cust.active),
        create_date=str(cust.create_date),
        last_update=str(cust.last_update),
    )

    return schemas.customerEditOutput(status=200, customer=out_cust)

@router.post("/api/details/customer", response_model=schemas.detailsCustomerOutput)
def customer_details(payload: detailsCustomerInput, db: Session = Depends(get_db)) -> schemas.detailsCustomerOutput:
    """Return customer info, rental history and outgoing (not-yet-returned) rentals."""
    cust = db.get(Customer, payload.customer_id)
    if not cust:
        return schemas.detailsCustomerOutput(status=404, customer=None, rental_history=None, outgoing_rentals=None)

    # address + city/country
    addr = db.get(Address, cust.address_id)
    city = db.get(City, addr.city_id) if addr else None
    country = db.get(Country, city.country_id) if city else None

    out_addr = schemas.Address(
        address_line1=addr.address if addr else "",
        address_line2=addr.address2 if addr else None,
        district=addr.district if addr else "",
        city=city.city if city else "",
        country=country.country if country else "",
        postal_code=addr.postal_code if addr else None,
    )

    out_cust = schemas.Customer(
        customer_id=int(cust.customer_id),
        store_id=int(cust.store_id),
        first_name=cust.first_name,
        last_name=cust.last_name,
        email=cust.email,
        address=out_addr,
        location=None,
        active=bool(cust.active),
        create_date=str(cust.create_date),
        last_update=str(cust.last_update),
    )

    # rental history
    history_rows = db.execute(select(Rental).where(Rental.customer_id == cust.customer_id).order_by(Rental.rental_date.desc())).scalars().all()
    rental_history = [_rental_row_to_pyd(r) for r in history_rows]

    # outgoing rentals (no return_date)
    outgoing_rows = db.execute(select(Rental).where(Rental.customer_id == cust.customer_id, Rental.return_date == None)).scalars().all()
    outgoing = [_rental_row_to_pyd(r) for r in outgoing_rows]

    return schemas.detailsCustomerOutput(status=200, customer=out_cust, rental_history=rental_history, outgoing_rentals=outgoing)

@router.post("/api/return", response_model=schemas.returnOutput)
def return_(payload: returnInput, db: Session = Depends(get_db)) -> schemas.returnOutput:
    """Mark rental as returned (set return_date to now)."""
    r = db.get(Rental, payload.rental_id)
    if not r:
        return schemas.returnOutput(status=404)
    if r.return_date is not None:
        return schemas.returnOutput(status=400)

    r.return_date = datetime.utcnow()
    db.add(r)
    db.commit()
    db.refresh(r)
    return schemas.returnOutput(status=200)

app.include_router(router)