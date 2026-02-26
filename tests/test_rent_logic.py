import pytest
from datetime import datetime

from src.alchemy.db import get_db
from src.alchemy.models import Inventory, Rental
from sqlalchemy import select, update
from src.api.routes import rent_film
from src.api.inputModels import rentInput


@pytest.mark.skipif(True, reason="requires real database; enable manually by editing test")
def test_prevent_double_rent():
    """Calling rent_film twice on same inventory returns 409 the second time."""
    # get a session from the dependency generator
    db = next(get_db())
    try:
        # pick any inventory row
        inv = db.execute(select(Inventory)).scalars().first()
        assert inv is not None, "No inventory rows in database"

        # make sure there are no active rentals on this copy
        db.execute(
            update(Rental)
            .where(Rental.inventory_id == inv.inventory_id, Rental.return_date.is_(None))
            .values(return_date=datetime.utcnow())
        )
        db.commit()

        payload = rentInput(inventory_id=inv.inventory_id, customer_id=1, staff_id=1)
        out1 = rent_film(payload, db)
        assert out1.status == 200
        assert out1.rental is not None

        # second attempt should be rejected
        out2 = rent_film(payload, db)
        assert out2.status == 409
        assert out2.rental is None
    finally:
        db.close()
