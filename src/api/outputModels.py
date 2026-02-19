import src

from pydantic import BaseModel, model_validator, computed_field, constr
from typing import Optional
from typing import List, Optional, Any

class Rental(BaseModel):
    rental_id: int
    rental_date: str
    inventory_id: int
    customer_id: int
    return_date: Optional[str] = None
    staff_id: int
    last_update: str

    #this adds a new attr, computed AFTER model validation
    @computed_field 
    def is_active(self) -> bool:
        return self.return_date is None

class Actor(BaseModel):
    actor_id: int
    first_name: str
    last_name: str
    last_update: str

class Film(BaseModel):
    film_id: int
    title: str
    description: Optional[str] = None
    release_year: Optional[int] = None
    language: int
    original_language: Optional[int] = None
    category: str
    rental_duration: int
    rental_rate: float
    length: Optional[int] = None
    replacement_cost: float
    rating: Optional[str] = None
    special_features: Optional[str] = None
    last_update: str

class FilmWithActors(BaseModel):
    film: Film
    actors: List[Actor]

class top5RentalsOutput(BaseModel):
    status: int
    rentals: Optional[List[FilmWithActors]]

class detailsFilmOutput(BaseModel):
    status: int
    film: Optional[FilmWithActors]

class top5ActorsOutput(BaseModel):
    status: int
    actors: Optional[List[Actor]] #note this is accross ALL stores
 
class topNRentalsWithActorOutput(BaseModel):
    status: int
    rentals: Optional[List[Rental]]

class queryFilmsOutput(BaseModel):
    status: int
    films: Optional[List[FilmWithActors]]

class rentOutput(BaseModel):
    status: int
    rental: Optional[Rental] #optionally can just return the ID, prolly better

class Address(BaseModel):
    address_line1: str
    address_line2: Optional[str]
    district: str # ~= state
    city: str
    country: str
    postal_code: Optional[str] = None

class Customer(BaseModel):
    customer_id: int
    store_id: int
    first_name: str
    last_name: str
    email: Optional[str] = None
    address: Address
    location: Optional[dict] = None # {"latitude": float, "longitude": float} TODO check this
    active: bool
    create_date: str
    last_update: str

class queryCustomerOutput(BaseModel):
    status: int
    customers: Optional[List[Customer]]

class customerCreateOutput(BaseModel):
    status: int
    customer: Optional[Customer]

class customerEditOutput(BaseModel):
    status: int
    customer: Optional[Customer]

class customerDeleteOutput(BaseModel):
    status: int

class detailsCustomerOutput(BaseModel):
    status: int
    customer: Optional[Customer]
    rental_history: Optional[List[Rental]]
    outgoing_rentals: Optional[List[Rental]]

class returnOutput(BaseModel):
    status: int