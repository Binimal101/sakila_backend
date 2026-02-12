import asyncio
import pytest

from typing import Any
from pprint import pprint

from src.api.geo import reverse_geocode_structured


@pytest.mark.asyncio
async def test_reverse_geocode_live():
    data = await reverse_geocode_structured(
        country="United States",
        state="CA",
        address_line1="1600 Amphitheatre Parkway",
        city="Mountain View",
        postal_code="94043",
    )

    assert data is not None, "Expected a geocoding result from the live service"
    assert "latitude" in data and "longitude" in data
    
    pprint(data) # with -s enabled in pytest