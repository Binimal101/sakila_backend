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

#pydantic models
from src.api.inputModels import (
    top5RentalsInput,
    detailsFilmInput,
    top5ActorsInput,
    topNRentalsWithActorInput,
    queryFilmsInput,
    rentInput,
    customerFilterEnum,
    filmFilterEnum,
    queryCustomerInput,
    customerCreateInput,
    customerEditInput,
    customerDeleteInput,
    detailsCustomerInput,
    returnInput,
)

import src.api.outputModels as output_models
from src.api.mappers import upsert_full_address, AddressFullResult


@router.get("/api/health")
def health_check() -> Any:
    return {"status": "ok"}

#ENDPOINTS

@router.post("/api/top_5_actors", response_model=output_models.top5ActorsOutput)
def t5_actors(payload: top5ActorsInput, db: Session = Depends(get_db)) -> output_models.top5ActorsOutput:
    actor_count = func.count

    films = db.execute(
        select(Inventory).where(Inventory.store_id == payload.store_id)
    ).scalars().all()

    t5actors = db.execute(
        select(Actor.actor_id, actor_count().label("actor_count"))
        .join(FilmActor, FilmActor.actor_id == Actor.actor_id)
        .where(
            FilmActor.film_id.in_([x.film_id for x in films])
        )
        .group_by(Actor.actor_id)
        .order_by(actor_count().desc())
        .limit(5)
    ).all()

    actor_list = [output_models.Actor.model_validate(db.get(Actor, row.actor_id))
                  for row in t5actors]

    return output_models.top5ActorsOutput(status=200, actors=actor_list)
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

    filmcat = db.execute( #technically could be 1-n, films-categories, but in practice (currently in db) its 1-1
        select(Film, Category).where(Film.film_id == payload.film_id)
        .join(FilmCategory, Film.film_id == FilmCategory.film_id)
        .join(Category, Category.category_id == FilmCategory.category_id)
    ).mappings().first() 

    if filmcat is None:
        return output_models.detailsFilmOutput(status=500, message="improper assumptions when processing film and it's categories")    
    
    film = output_models.Film.model_validate(filmcat["Film"])
    cat = filmcat["Category"].name
    language = db.get(Language, film.language_id).name # type: ignore

    actors_orm = db.execute(
        select(Actor)
        .join(FilmActor, FilmActor.actor_id == Actor.actor_id)
        .where(FilmActor.film_id == film.film_id)
    ).scalars().all()

    actors = [output_models.Actor.model_validate(a) for a in actors_orm]

    return output_models.detailsFilmOutput(film=output_models.FilmFull(
        film=film,
        actors=actors,
        category=cat,
        language=language, # type: ignore
    ), status=200)

@router.post("/api/query/films", response_model=output_models.queryFilmsOutput)
def query_films(payload: queryFilmsInput, db: Session = Depends(get_db)) -> output_models.queryFilmsOutput:
    """Search films by name, genre, or actor. Returns `FilmFull` objects."""
    stmt = select(Film)

    #case insensitive partial searchjes
    if payload.filter_var == filmFilterEnum.NAME and payload.filter_value:
        stmt = stmt.where(Film.title.ilike(f"%{payload.filter_value}%"))
    
    elif payload.filter_var == filmFilterEnum.GENRE and payload.filter_value:
        stmt = stmt.where(Category.name.ilike(f"%{payload.filter_value}%"))
    
    elif payload.filter_var == filmFilterEnum.ACTOR and payload.filter_value:
        stmt = stmt.where(or_(
            Actor.first_name.ilike(payload.filter_value), 
            Actor.last_name.ilike(payload.filter_value)
        ))
    
    stmt = (stmt
        .join(FilmCategory, FilmCategory.film_id == Film.film_id)
        .join(Category, Category.category_id == FilmCategory.category_id)
        .join(FilmActor, FilmActor.film_id == Film.film_id)
        .join(Actor, Actor.actor_id == FilmActor.actor_id)
    )

    stmt = stmt.offset(payload.offset).limit(payload.top_n)

    orm_films = db.execute(stmt).scalars().all()

    #take filtered results and make them fit output model
    if orm_films is None:
        return output_models.queryFilmsOutput(status=404, films=[], message="No films found with following filter params")

    out_films: List[output_models.FilmFull] = []

    for film in orm_films:
        ret = film_details(payload=detailsFilmInput(film_id=film.film_id), db=db)
        if ret.status != 200:
            return output_models.queryFilmsOutput(
                status=ret.status,
                message=f"error calling film/details from film/query with fid={film.film_id}: {ret.message}"
            )
        out_films.append(output_models.FilmFull.model_validate(ret.film))

    return output_models.queryFilmsOutput(status=200, films=out_films)

@router.post("/api/query/customer", response_model=output_models.queryCustomerOutput)
def query_customer(payload: queryCustomerInput, db: Session = Depends(get_db)) -> output_models.queryCustomerOutput:
    """Perform a paged search of customers.

    The body must specify a filter type (first name, last name, or ID) and a
    corresponding value.  Results are returned in `customers` along with a
    200 status.  If no rows match the criteria you still get 200 but the
    `message` field will note "no customers found"; invalid filters won't be
    accepted by the input model.

    This endpoint is intended for UI list views and autosuggest widgets. It
    never throws HTTP errors except for malformed requests; front ends can
    display `message` to inform users when a lookup yields nothing.
    """
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
    """Create a new customer along with its address details.

    The payload must include full address information and a valid phone number
    (used for de‑duplication).  On success the newly created customer (plus
    address/city/country) is returned in `customer`.  If the customer already
    exists or the database rejects the insert the response will still be 200
    but `message` will contain the error text, making it easy for a front end to
    pop up a human‑readable warning.  This endpoint is designed to be called
    from a registration or admin form; it does not itself perform any
    authentication or authorization.
    """

    lat, lon = 0, 0

    try:
        with db.begin():
            result = upsert_full_address(db, payload.address, payload.phone_number)
            city = result.city
            country = result.country
            address = result.address

            cust = Customer(
                store_id=payload.store_id,
                first_name=payload.first_name,
                last_name=payload.last_name,
                email=payload.email,
                address_id=address.address_id,
            )
            db.add(cust)
            db.flush()
            db.refresh(cust)
    except Exception as e:
        # return error in message field so front end can display it
        return output_models.customerCreateOutput(status=500, customer=None, message=str(e))

    cust_pyd = output_models.Customer.model_validate(cust)
    addr_pyd = output_models.Address.model_validate(address)

    # build pydantic objects for city/country as well so CustomerFull is happy
    city_pyd = output_models.City.model_validate(city)
    country_pyd = output_models.Country.model_validate(country)

    cust_full = output_models.CustomerFull(
        customer=cust_pyd,
        address=addr_pyd,
        city=city_pyd,
        country=country_pyd,
        location={"latitude": lat, "longitude": lon},
        rental_history=[],
        outgoing_rentals=[],
    )

    return output_models.customerCreateOutput(status=200, customer=cust_full)

@router.post("/api/customer/edit", response_model=output_models.customerEditOutput)
def customer_edit(payload: customerEditInput, db: Session = Depends(get_db)) -> output_models.customerEditOutput:
    """Modify an existing customer's fields.

    Only the fields present in the payload will be updated; omitted fields
    remain unchanged.  If the caller supplies a new address + phone number (both need to be provided) the
    address table is upserted automatically.  The response provides the
    updated customer object on success.  If the requested `customer_id` does
    not exist a 404 status with a descriptive `message` is returned.
    """

    customer_record = db.get(Customer, payload.customer_id)

    if customer_record is None:
        return output_models.customerEditOutput(status=404, customer=None,
            message=f"no customer found with id {payload.customer_id}")

    address = None
    if None not in (payload.address, payload.phone_number):
        result = upsert_full_address(db, payload.address, payload.phone_number) # type: ignore
        city = result.city
        country = result.country
        address = result.address
    
    db.execute(
        update(Customer).where(Customer.customer_id == customer_record.customer_id)
        .values( #overwrite if provided, otherwise default
                store_id=payload.store_id or customer_record.store_id,
                first_name=payload.first_name or customer_record.first_name,
                last_name=payload.last_name or customer_record.last_name,
                email=payload.email or customer_record.email,
                address_id=(address.address_id if address else None) or customer_record.address_id, # type: ignore
        )
    )

    db.commit()
    db.flush()
    db.refresh(customer_record)
    return output_models.customerEditOutput(status=200, customer=customer_record) # type: ignore
    
@router.post("/api/customer/delete", response_model=output_models.customerDeleteOutput)
def customer_delete(payload: customerDeleteInput, db: Session = Depends(get_db)) -> output_models.customerDeleteOutput:
    """Remove a customer by ID.

    Returns 200 and a confirmation message when deletion succeeds. If the
    provided `customer_id` does not exist the response will have a 404 status
    and `message` explaining that no such row was found.  Consumers can use
    this endpoint for clean‑up tasks or admin UIs.
    """
    customer = db.get(Customer, payload.customer_id)
    if customer is None:
        return output_models.customerDeleteOutput(status=404,
            message=f"cannot delete; customer {payload.customer_id} not found")

    db.delete(customer)
    db.flush()
    db.commit()

    return output_models.customerDeleteOutput(status=200)

@router.post("/api/details/customer", response_model=output_models.detailsCustomerOutput)
def customer_details(payload: detailsCustomerInput, db: Session = Depends(get_db)) -> output_models.detailsCustomerOutput:
    """Fetch one customer's full profile.

    The response includes the base customer row, their address/city/country
    hierarchy and lists of past and currently active rentals.  Useful for
    displaying a detailed view or for building reports. If the supplied ID is
    missing from the database a 404 response with an explanatory message is
    returned instead of a bare `null`.
    """
    
    stmt = (
        select(Customer, Address, City, Country)
        .join(Address, Address.address_id == Customer.address_id)
        .join(City, City.city_id == Address.city_id)
        .join(Country, Country.country_id == City.country_id)
        .where(Customer.customer_id == payload.customer_id)
    )
    
    row = db.execute(stmt).mappings().first()
    if not row:
        return output_models.detailsCustomerOutput(status=404, customer=None,
            message=f"customer {payload.customer_id} does not exist")

    addr = row["Address"]
    city = row["City"]
    country = row["Country"]
    cust = row["Customer"]

    addr_pyd = output_models.Address.model_validate(addr)
    city_pyd = output_models.City.model_validate(city)
    countyr_pyd = output_models.Country.model_validate(country)
    cust_pyd = output_models.Customer.model_validate(cust)

    rentals_stmt = select(Rental).where(Rental.customer_id == cust.customer_id).order_by(Rental.rental_date.desc())
    rental_rows = db.execute(rentals_stmt).scalars().all()
    
    rentals_pyd = [output_models.Rental.model_validate(r) for r in rental_rows]
    
    rental_full_pyds = [
        output_models.RentalFull(
            rental=r,
            film=(
                db.get(Film, db.get(Inventory, r.inventory_id).film_id) # type: ignore
            )
        ) for r in rentals_pyd
    ]

    #in-memory stratification for ease of use on cli-side
    rental_history = [r for r in rental_full_pyds if r.rental.return_date is not None]
    outgoing_rentals = [r for r in rental_full_pyds if r.rental.return_date is None]

    return output_models.detailsCustomerOutput(
        customer=output_models.CustomerFull(
            customer=cust_pyd,
            address=addr_pyd,
            city=city_pyd,
            country=countyr_pyd,
            rental_history=rental_history,
            outgoing_rentals=outgoing_rentals
        ),
        status=200
    )
    
@router.post("/api/rent", response_model=output_models.rentOutput)
def rent_film(payload: rentInput, db: Session = Depends(get_db)) -> output_models.rentOutput:
    """Create a Rental record for a matching inventory item.
        throws err if rental is already taken out"""

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
        return output_models.rentOutput(status=404, rental=None, payment=None, message="someone currently has this rented out, please try another item!")

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
    
    if (rental := db.get(Rental, payload.rental_id)) is None:
        return output_models.returnOutput(status=404, message="rental instance doesn't exist")
    
    rental.return_date = datetime.now()  # type: ignore
    db.commit()

    return output_models.returnOutput(status=200)


app.include_router(router)