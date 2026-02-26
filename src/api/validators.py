from typing import Dict, Any
from fastapi import Depends, HTTPException

from .inputModels import customerCreateInput


def normalize_address(payload: customerCreateInput) -> Dict[str, Any]:
    """Normalize + validate the `payload.address` and return a deterministic
    normalized dict (used by create/update customer endpoints)"""
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
