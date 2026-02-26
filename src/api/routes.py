import json

#api
from fastapi import APIRouter, Response, Depends
from typing import Any, List, Optional, Dict
from . import router, app

# db
from src.alchemy.models import *

from src.alchemy.db import get_db
from sqlalchemy.orm import Session
from sqlalchemy import select, insert, update, delete, func, and_, or_, literal_column
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from geoalchemy2 import WKTElement
from fastapi import HTTPException

# validators / pydantic models
from src.api.validators import normalize_address
from src.api.inputModels import (
    top5RentalsInput,
    detailsFilmInput,
    top5ActorsInput,
    topNRentalsWithActorInput,
    queryFilmsInput,
    rentInput,
    customerFilterEnum,
    queryCustomerInput,
    customerCreateInput,
    customerEditInput,
    customerDeleteInput,
    detailsCustomerInput,
    returnInput,
)

import src.api.outputModels as output_models
from src.api.mappers import _get_or_create_country, _get_or_create_city, _create_address


@router.get("/api/health")
def health_check() -> Any:
    return {"status": "ok"}

#ENDPOINTS

@router.post("/api/top_5_rentals", response_model=output_models.top5RentalsOutput)
def t5_rentals(payload: top5RentalsInput, db: Session = Depends(get_db)) -> output_models.top5RentalsOutput:
    """Selects top 5 rentals across current store"""
    
    rental_count = func.count(Rental.rental_id).label("rental_count") #func is a class with aggregative methods (ie count)
    
    statement = (
        #.label is required to map attrs k,v from ORM s.t. we can load directly into pydantic
        select(Film, Category.name.label("category"), Language.name.label("language"), rental_count)
        .join(Inventory, Inventory.film_id == Film.film_id)
        .join(Rental, Rental.inventory_id == Inventory.inventory_id)
        .join(FilmCategory, FilmCategory.film_id == Film.film_id)
        .join(Category, Category.category_id == FilmCategory.category_id)
        .join(Language, Film.language_id == Language.language_id)
        .where(Inventory.store_id == payload.store_id)
        .group_by(Film.film_id, Category.name, Language.name)
        .order_by(rental_count.desc())
        .limit(5)
    )

    results = db.execute(statement).mappings().all() #.scalars drops non-objs, mappings get all select params k:v

    # build FilmFull objects from Row mappings (omit actors for now)
    pyd_films_with_actors: List[output_models.FilmFull] = []

    for res in results:
        film_obj = res.get("Film") #res does {column_names:values} U {ORM_Object_Name:OBJ}
        film_pyd = output_models.Film.model_validate(film_obj)

        actor_rows = db.execute(
            select(Actor)
            .join(FilmActor, FilmActor.actor_id == Actor.actor_id)
            .where(FilmActor.film_id == film_obj.film_id) # type: ignore
        ).scalars().all()

        actors_pyd_dump = [output_models.Actor.model_validate(a).model_dump() for a in actor_rows]

        film_full_data: Dict[str, Any] = {
            "film": film_pyd.model_dump(), #turn into a dict to retry validation under filmfull
            "actors": actors_pyd_dump,
            "category": res.get("category"),
            "language": res.get("language"),
            "rental_count": int(res.get("rental_count") or 0),
        }

        pyd_films_with_actors.append(output_models.FilmFull.model_validate(film_full_data))

    return output_models.top5RentalsOutput(rentals=pyd_films_with_actors, status=200)


@router.post("/api/details/film", response_model=output_models.detailsFilmOutput)
def film_details(payload: detailsFilmInput, db: Session = Depends(get_db)) -> output_models.detailsFilmOutput:
    """Return full film details including actors and category."""
    pass

@router.post("/api/query/films", response_model=output_models.queryFilmsOutput)
def query_films(payload: queryFilmsInput, db: Session = Depends(get_db)) -> output_models.queryFilmsOutput:
    """Search films by name, genre, or actor. Returns `Film` objects."""
    pass

@router.post("/api/query/customer", response_model=output_models.queryCustomerOutput)
def query_customer(payload: queryCustomerInput, db: Session = Depends(get_db)) -> output_models.queryCustomerOutput:
    """Query customers by first_name, last_name, or customer_id"""
    stmt = select(Customer)

    #case insensitive partial searchjes
    if payload.filter_var == customerFilterEnum.FIRST_NAME and payload.filter_value:
        stmt = stmt.where(Customer.first_name.ilike(f"%{payload.filter_value}%"))
    
    elif payload.filter_var == customerFilterEnum.LAST_NAME and payload.filter_value:
        stmt = stmt.where(Customer.last_name.ilike(f"%{payload.filter_value}%"))
    
    elif payload.filter_var == customerFilterEnum.CUSTOMER_ID and payload.filter_value:
        stmt = stmt.where(Customer.customer_id == payload.filter_value)

    stmt = stmt.offset(payload.offset).limit(payload.top_n)

    rows = db.execute(stmt).scalars().all()  

    out_customers: List[output_models.Customer] = []

    for cust in rows:
        out_customers.append(output_models.Customer.model_validate(cust))

    return output_models.queryCustomerOutput(status=200, customers=out_customers)

@router.post("/api/customer/create", response_model=output_models.customerCreateOutput)
def create_customer(payload: customerCreateInput, db: Session = Depends(get_db)) -> output_models.customerCreateOutput:
    """Create customer + address.

    Reuses `normalize_address` helper from `validators` and get-or-create helpers.
    """

    normalized = normalize_address(payload)
    components = normalized.get("components", {})
    country_name = components.get("country") or payload.address.country
    city_name = components.get("city") or payload.address.city
    lat = normalized.get("latitude") or 0.0 #rn its already 0, but implement in case we wanna change it later
    lon = normalized.get("longitude") or 0.0

    try:
        with db.begin():
            country = _get_or_create_country(db, country_name)
            city = _get_or_create_city(db, city_name, country.country_id) # type: ignore

            addr = _create_address(db, payload.address.model_dump(), city.city_id, lat, lon) # type: ignore

            cust_kwargs = {k: v for (k, v) in payload.model_dump().items() if hasattr(Customer, k)}
            cust_kwargs.update(address_id=addr.address_id, create_date=datetime.utcnow(), active=1)

            cust = Customer(**cust_kwargs)
            db.add(cust)
            db.flush()
            db.refresh(cust)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    cust_pyd = output_models.Customer.model_validate(cust)
    addr_pyd = output_models.Address.model_validate(addr)
    addr_dict = addr_pyd.model_dump()
    addr_dict.update({"city": city.city, "country": country.country})

    cust_full_dict = {
        "customer": cust_pyd.model_dump(),
        "address": addr_dict,
        "location": {"latitude": lat, "longitude": lon},
        "rental_history": [],
        "outgoing_rentals": [],
    }

    out_cust_full = output_models.CustomerFull.model_validate(cust_full_dict)
    return output_models.customerCreateOutput(status=200, customer=out_cust_full)

@router.post("/api/details/customer", response_model=output_models.detailsCustomerOutput)
def customer_details(payload: detailsCustomerInput, db: Session = Depends(get_db)) -> output_models.detailsCustomerOutput:
    """Return customer info, rental history and outgoing rentals"""
    
    stmt = (
        #labels for city and country to map over to nomenclature of pyd
        select(Customer, Address, City.city.label("city_name"), Country.country.label("country_name"))
        .join(Address, Address.address_id == Customer.address_id)
        .join(City, City.city_id == Address.city_id)
        .join(Country, Country.country_id == City.country_id)
        .where(Customer.customer_id == payload.customer_id)
    )
    
    row = db.execute(stmt).mappings().first()
    if not row:
        return output_models.detailsCustomerOutput(status=404, customer=None)

    cust = row["Customer"]
    addr = row["Address"]

    addr_pyd = output_models.Address.model_validate(addr)
    cust_pyd = output_models.Customer.model_validate(cust)

    addr_dict = addr_pyd.model_dump()
    addr_dict.update({
        "city": row["city_name"],
        "country": row["country_name"]
    })

    rentals_stmt = select(Rental).where(Rental.customer_id == cust.customer_id).order_by(Rental.rental_date.desc())
    rental_rows = db.execute(rentals_stmt).scalars().all()
    
    rentals_pyd = [output_models.Rental.model_validate(r) for r in rental_rows]
    
    #in-memory stratification for ease of use on cli-side
    rental_history = [r.model_dump() for r in rentals_pyd if r.return_date is not None]
    outgoing_rentals = [r.model_dump() for r in rentals_pyd if r.return_date is None]

    cust_full_dict = {
        "customer": cust_pyd.model_dump(),
        "address": addr_dict,
        "location": None,
        "rental_history": rental_history,
        "outgoing_rentals": outgoing_rentals
    }

    out_cust_full = output_models.CustomerFull.model_validate(cust_full_dict)

    return output_models.detailsCustomerOutput(status=200, customer=out_cust_full)

@router.post("/api/rent", response_model=output_models.rentOutput)
def rent_film(payload: rentInput, db: Session = Depends(get_db)) -> output_models.rentOutput:
    """Create a Rental record for a matching inventory item.
        throws err if rental is already taken out

    """

    # validate inventory row with pydantic
    inv = output_models.Inventory.model_validate(
        db.get(Inventory, payload.inventory_id)
    )

    outgoing_record = db.execute(
        select(Rental)
        .where(
            Rental.inventory_id == inv.inventory_id,
            Rental.return_date == None,
        )
        .limit(1)
    ).scalar_one_or_none()

    if outgoing_record:
        return output_models.rentOutput(status=409, rental=None, payment=None)

    film = output_models.Film.model_validate(db.get(Film, inv.film_id))

    today = datetime.now()

    # create rental record
    db.add(rent := Rental(
        rental_date=today,
        inventory_id=inv.inventory_id,
        customer_id=payload.customer_id,
        staff_id=payload.staff_id,
    ))
    db.commit()
    db.refresh(rent) #puts in the ID param
    rent = output_models.Rental.model_validate(rent)

    #creates the ORM object, puts it in the database (after commit), refreshes obj to have id param for validation
    db.add(pmt := Payment(
        customer_id=payload.customer_id,
        staff_id=payload.staff_id,
        rental_id=rent.rental_id,
        amount=film.rental_rate * film.rental_duration,
        payment_date=today
    ))
    db.add(pmt)
    db.commit()
    db.refresh(pmt)
    pmt = output_models.Payment.model_validate(pmt)

    return output_models.rentOutput(
        status=200,
        rental=rent,
        payment=pmt,
    )

@router.post("/api/return", response_model=output_models.returnOutput)
def return_film(payload: returnInput, db: Session = Depends(get_db)) -> output_models.returnOutput:
    """Mark rental as returned (set return_date to now)."""
    pass

app.include_router(router)