import os
import json
from pathlib import Path
import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from src.alchemy.models import Actor, Address, Customer, Film, Rental, Store
from src import DATABASE_URL

def dump_model_rows(session, model, outdir: Path, limit: int = 100):
    """Query `model` for up to `limit` rows and write JSON to `outdir/<Model>.json`."""
    outdir.mkdir(parents=True, exist_ok=True)
    stmt = select(model).limit(limit)
    
    row_instances = session.execute(stmt).scalars().all()
    items = []
    
    for row in row_instances:
        row_dict = {}
        for col in model.__table__.columns:
            v = getattr(row, col.name)
            try:
                json.dumps(v)
                row_dict[col.name] = v
            except:
                row_dict[col.name] = str(v)
        items.append(row_dict)

    out_path = outdir / f"{model.__name__}.json"
    with out_path.open("w") as f:
        json.dump(items, f, indent=2)


@pytest.mark.skipif(not DATABASE_URL, reason="DATABASE_URL not set")
def test_dump_models_to_logs():
    """Dump sample rows for models into tests/model_logs/."""
    engine = create_engine(DATABASE_URL) # type: ignore
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        outdir = Path("tests") / "model_logs"
        models = [Actor, Address, Customer, Film, Rental, Store]
        
        for model in models:
            dump_model_rows(session, model, outdir, limit=50)
    finally:
        session.close()
