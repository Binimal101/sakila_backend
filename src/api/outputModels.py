import src

from datetime import datetime
from pydantic import BaseModel, model_validator, field_validator, computed_field, constr, ConfigDict
from typing import Optional
from typing import List, Optional

class BaseOutputModel(BaseModel):
    """Shared base for output models that need date validation for last_update"""
    model_config = ConfigDict(from_attributes=True)

    @field_validator('last_update', mode='before', check_fields=False)
    def _last_update_to_str(cls, v):
        if isinstance(v, datetime):
            return v.isoformat()
        return v

class Rental(BaseOutputModel):
    rental_id: int
    rental_date: str
    inventory_id: int
    customer_id: int
    return_date: Optional[str] = None
    staff_id: int
    last_update: str

    @field_validator('rental_date', 'return_date', mode='before', check_fields=False)
    def _date_to_str(cls, v):
        if isinstance(v, datetime):
            return v.isoformat()
        return v

    #this adds a new attr, computed AFTER model validation
    @computed_field 
    def is_active(self) -> bool:
        return self.return_date is None

class Actor(BaseOutputModel):
    actor_id: int
    first_name: str
    last_name: str
    last_update: str

class Film(BaseOutputModel):
    film_id: int
    title: str
    description: Optional[str] = None
    release_year: Optional[int] = None
    original_language: Optional[int] = None
    rental_duration: int
    rental_rate: float
    length: Optional[int] = None
    replacement_cost: float
    rating: Optional[str] = None
    special_features: Optional[str] = None
    last_update: str

    @field_validator("special_features", mode="before") # will inject retval into special_features field be4 validation
    def special_features_str(cls, v):
        if isinstance(v, (set, list, tuple)):
            return ",".join(sorted(map(str, v)))
        return v

class FilmFull(BaseModel):
    film: Film
    actors: List[Actor]
    category: str
    language: str
    
    #begin query specific metadata, too lazy to stratify
    rental_count: Optional[int]

class top5RentalsOutput(BaseModel):
    status: int
    rentals: Optional[List[FilmFull]]

class detailsFilmOutput(BaseModel):
    status: int
    film: Optional[FilmFull]

class top5ActorsOutput(BaseModel):
    status: int
    actors: Optional[List[Actor]] #note this is accross ALL stores
 
class topNRentalsWithActorOutput(BaseModel):
    status: int
    rentals: Optional[List[Rental]]

class queryFilmsOutput(BaseModel):
    status: int
    films: Optional[List[FilmFull]]

class Inventory(BaseOutputModel):
    inventory_id: int
    film_id: int
    store_id: int
    last_update: str

class Payment(BaseOutputModel):
    payment_id: int
    customer_id: int
    staff_id: int
    rental_id: int
    amount: float
    payment_date: str

    @field_validator("payment_date", mode="before")
    def pmt_date(cls, v):
        if isinstance(v, datetime):
            return v.isoformat()
        return v


class rentOutput(BaseModel):
    status: int
    rental: Optional[Rental] = None 
    payment: Optional[Payment] = None

class Address(BaseOutputModel):
    address_id: Optional[int] = None #used in case from converting directly from ORM, will be None elsewhere BAD PRACTICE
    address: str
    address2: Optional[str]
    district: str # ~= state
    city_id: int
    postal_code: str
    phone: str
    last_update: datetime

class City(BaseOutputModel):
    city: str
    country_id: int
    last_update: datetime

class Country(BaseOutputModel):
    country: str
    last_update: datetime

class Customer(BaseOutputModel):
    customer_id: int
    store_id: int
    first_name: str
    last_name: str
    email: Optional[str] = None
    active: Optional[bool] = True
    create_date: str
    last_update: str

    @field_validator('create_date', mode='before', check_fields=False)
    def create_date_str(cls, v):
        if isinstance(v, datetime):
            return v.isoformat()
        return v

class CustomerFull(BaseModel):
    customer: Customer
    address: Address
    city: City
    country: Country
    location: Optional[dict] = None
    rental_history: Optional[List[Rental]] = None
    outgoing_rentals: Optional[List[Rental]] = None

class queryCustomerOutput(BaseModel):
    status: int
    customers: Optional[List[Customer]]
    message: Optional[str] = None  # human-readable info or error details

class customerCreateOutput(BaseModel):
    status: int
    customer: Optional[CustomerFull]
    message: Optional[str] = None  # informative text for front-end display

class customerEditOutput(BaseModel):
    status: int
    customer: Optional[Customer]
    message: Optional[str] = None

class customerDeleteOutput(BaseModel):
    status: int
    message: Optional[str] = None

class detailsCustomerOutput(BaseModel):
    status: int
    customer: Optional[CustomerFull]
    message: Optional[str] = None

class returnOutput(BaseModel):
    status: int