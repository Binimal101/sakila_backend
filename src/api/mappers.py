from sqlalchemy.orm import Session
from sqlalchemy import select

from pydantic import BaseModel
from geoalchemy2 import WKTElement
from src.alchemy.models import Country, City, Address
import src.api.inputModels as inmod
import src.api.outputModels as opmod


class AddressFullResult(BaseModel):
    country: opmod.Country
    city: opmod.City
    address: opmod.Address

def upsert_full_address(db: Session, addr: inmod.Address, phone: inmod.StrictPhoneNumber) -> AddressFullResult: # type: ignore
    """will try to update columns in Address, City, and Country if they exist, otherwise creates them."""

    country_name = addr.country.lower().title()
    city_name = addr.city.lower().title()
    line1 = addr.address_line1.lower().title()
    line2 = addr.address_line2.lower().title() if addr.address_line2 else None
    district = addr.district.lower().title()

    if (country := db.execute(
            select(Country).where(Country.country == country_name)
        ).scalars().first()) is None:
        country = Country(country=country_name)
        db.add(country)
        db.flush() # populate id

    if (city := db.execute(
            select(City).where(City.city == addr.city.lower().title())
        ).scalars().first()) is None:
        city = City(
            city=city_name,
            country_id=country.country_id
        )
        db.add(city)
        db.flush()

    address = db.execute(
        select(Address).where(
            Address.address == line1,
            Address.address2 == line2,
            Address.district == district,
            Address.city_id == city.city_id,
            Address.postal_code == addr.postal_code,
            Address.phone == phone,
        )
    ).scalars().first()

    if address is None:
        address = Address(
            address=line1,
            address2=line2,
            district=district,
            city_id=city.city_id,
            postal_code=addr.postal_code,
            phone=phone,
            location=WKTElement("POINT(0 0)") #hardcode bc geocoding with bad seeded db values is bad >:()
        )
        db.add(address)
        db.flush()
        
    [db.refresh(model) for model in (country, city, address)]

    return AddressFullResult(
        country=opmod.Country.model_validate(country),
        city=opmod.City.model_validate(city),
        address=opmod.Address.model_validate(address)
    )

    