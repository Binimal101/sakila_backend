from typing import Dict, Any
from fastapi import Depends, HTTPException

from .inputModels import customerCreateInput, Address


class GeocoderClient:
    """Simple mock geocoder client. Replace with real client implementation."""

    async def validate_address(self, addr: Address) -> Dict[str, Any] | None:
        # Placeholder: in real code call external service with timeouts/retries.
        # For demo, consider any address_line longer than 5 chars as valid.
        if not addr or not addr.address_line or len(addr.address_line.strip()) < 5:
            return None
        # Return a normalized address dict with lat/lon stub
        return {
            "formatted": f"{addr.address_line}, {addr.city or ''} {addr.state or ''}".strip(', '),
            "latitude": 0.0,
            "longitude": 0.0,
            "components": {
                "address_line": addr.address_line,
                "city": addr.city,
                "state": addr.state,
                "postal_code": addr.postal_code,
                "country": addr.country,
            },
        }


def get_geocoder() -> GeocoderClient:
    return GeocoderClient()


async def validate_address_dep(
    payload: customerCreateInput = Depends(),
    geocoder: GeocoderClient = Depends(get_geocoder),
) -> Dict[str, Any]:
    """Dependency that validates and normalizes `payload.address`.

    - `payload` is parsed by FastAPI into `customerCreateInput`.
    - We extract `payload.address` and call the geocoder.
    - If validation fails, raise HTTPException(422).
    - Returns the normalized address dict for the route to use.
    """
    addr = payload.address
    normalized = await geocoder.validate_address(addr)
    if not normalized:
        raise HTTPException(status_code=422, detail="Address could not be validated")
    return normalized
