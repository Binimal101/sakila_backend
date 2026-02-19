from typing import Dict, Any
from fastapi import Depends, HTTPException

from .inputModels import customerCreateInput


async def validate_address_dep(
    payload: customerCreateInput = Depends(), #fastapi will inject http-body into pydantic model typed here
) -> Dict[str, Any]:
    """Validate `payload.address` locally and return a normalized dict.

    This removes external reverse-geocoding. The function returns
    deterministic dummy coordinates (0.0, 0.0) for all valid addresses.
    """
    addr = payload.address
    line = getattr(addr, "address_line1", None)
    if not addr or not line or len(line.strip()) < 5:
        raise HTTPException(status_code=-6, detail="Address could not be validated")

    line = line.strip()
    return {
        "formatted": f"{line}, {addr.city or ''} {addr.district or ''}".strip(', '),
        "latitude": 0.0,
        "longitude": 0.0,
        "components": {
            "address_line": line,
            "city": addr.city,
            "state": addr.district,
            "postal_code": addr.postal_code,
            "country": addr.country,
        },
    } #normalized serialization (dummy [lat, lng])
