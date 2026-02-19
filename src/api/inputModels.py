import src

from pydantic import BaseModel, Field, constr # fields are for simple validation, constr for expressive validation
from typing import Optional
from enum import Enum

class top5RentalsInput(BaseModel):
    store_id: int = Field(gt=0)

class detailsFilmInput(BaseModel):
    film_id: int = Field(gt=0)

class top5ActorsInput(BaseModel):
    store_id: Optional[int] #if optional, we assume from ALL stores

class topNRentalsWithActorInput(BaseModel):
    actor_id: int #this is across ALL stores
    offset: int = Field(0, ge=0)
    top_n: int = Field(50, ge=1)

class filmsFilterEnum(str, Enum):
    NAME = "name"
    GENRE = "genre"
    ACTOR = "actor"

class queryFilmsInput(BaseModel):
    filter_var: Optional[filmsFilterEnum]
    filter_content: str
    offset: int = Field(0, ge=0)
    top_n: int = Field(5, ge=1)

class rentInput(BaseModel):
    store_id: int
    film_id: int
    customer_id: int
    staff_id: int

class customerFilterEnum(str, Enum):
    FIRST_NAME = "first_name"
    LAST_NAME = "last_name"
    CUSTOMER_ID = "customer_id"

class queryCustomerInput(BaseModel):
    filter_var: Optional[customerFilterEnum]
    filter_text: Optional[str]
    offset: int = Field(0, ge=0)
    top_n: int = Field(20, ge=1)

StrictEmail = constr(
    pattern=r'^[A-Za-z0-9]+(\.[A-Za-z0-9]+)*@[A-Za-z0-9]+(\.[A-Za-z0-9]+)+$',
    strip_whitespace=True
)
StrictPhoneNumber = constr(
    pattern=r"^(\+[0-9]{1,3}[ -]?)?[0-9]{3}[ |-]?[0-9]{3}( |-)?[0-9]{4}$",
    strip_whitespace=True,
)
class Address(BaseModel):
    address_line1: str
    address_line2: Optional[str]
    district: str # ~= state
    city: str
    country: str
    postal_code: Optional[str] = None

class customerCreateInput(BaseModel):
    store_id: int
    first_name: str
    last_name: str
    email: Optional[StrictEmail] = None  # type: ignore
    phone_number: StrictPhoneNumber # type: ignore
    address: Address

class customerEditInput(BaseModel):
    store_id: Optional[int] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[StrictEmail] = None  # type: ignore
    phone_number: Optional[StrictPhoneNumber] = None # type: ignore
    address: Optional[Address] = None
    customer_id: int

class customerDeleteInput(BaseModel):
    customer_id: int
    store_id: int

class detailsCustomerInput(BaseModel):
    customer_id: int
    store_id: int

class returnInput(BaseModel):
    rental_id: int
    staff_id: int