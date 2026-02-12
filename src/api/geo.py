import aiohttp
import os
from typing import Optional, Dict, Any
from pprint import pprint

BASE_URL = "https://geocode.maps.co/search"

AIO_SESSION: Optional[aiohttp.ClientSession] = None

async def reverse_geocode_structured(
    country: str,
    state: str,
    address_line1: str,
    city: str,
    postal_code: Optional[str] = None,
    address_line2: Optional[str] = None,
    timeout: float = 10.0,
) -> Optional[Dict[str, Any]]:
    
    street = address_line1.strip()
    if address_line2:
        address_line2 = address_line2.strip()
        if address_line2:
            street = f"{street} {address_line2}"

    api_key = os.getenv("GEOCODING_API_KEY")

    assert api_key is not None, "[ geo.py ] GEOCODING_API_KEY must be set in environment variables"

    params = {
        "api_key": api_key,
        "street": street,
        "city": city,
        "state": state,
        "country": country,
        "format": "json",
        "limit": 1,
    }

    if postal_code:
        params["postalcode"] = postal_code

    global AIO_SESSION #lazy load global instance (bad but works here)
    if AIO_SESSION is None:
        timeout_cfg = aiohttp.ClientTimeout(total=timeout)
        AIO_SESSION = aiohttp.ClientSession(timeout=timeout_cfg)
    session = AIO_SESSION

    try:
        async with session.get(BASE_URL, params=params) as resp:
            if resp.status != 200:
                return None
            
            data = await resp.json()

            if not data or not len(data): #zero results or invalid response
                return None
            
            most_relavent = data[0]

            return {
                "latitude": float(most_relavent.get("lat")),
                "longitude": float(most_relavent.get("lon")),
            }
        
    except Exception:
        return None