import os
import json
from pathlib import Path
import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.alchemy import models
from sqlalchemy import inspect, text
from inspect import isclass, getmembers

try:
    from geoalchemy2.shape import to_shape
    from geoalchemy2.elements import WKBElement
except Exception:
    to_shape = None
    WKBElement = None

try:
    from shapely import wkb as shapely_wkb
except Exception:
    shapely_wkb = None


DATABASE_URL = os.getenv("DATABASE_URL")

def dump_model_rows(session, model, outdir: Path, limit: int = 100):
    """Query `model` for up to `limit` rows and write JSON output to `outdir/<Model>.json`.

    Values are converted to strings when necessary to avoid JSON serialization errors.
    """
    outdir.mkdir(parents=True, exist_ok=True)
    # Use the DB to list real columns for the table to avoid model-vs-db mismatches
    from sqlalchemy import inspect, text

    engine = session.get_bind()
    inspector = inspect(engine)
    try:
        db_cols = [c["name"] for c in inspector.get_columns(model.__tablename__)]
    except Exception:
        # fallback: use model columns if inspector fails
        db_cols = [c.name for c in model.__table__.columns]

    if not db_cols:
        return

    sql = text(f"SELECT {', '.join(db_cols)} FROM {model.__tablename__} LIMIT :limit")
    conn = engine.connect()
    try:
        res = conn.execute(sql, {"limit": limit})
        # use .mappings() to get dict-like rows reliably across SQLAlchemy versions
        rows = [dict(r) for r in res.mappings()]
    finally:
        conn.close()

    items = []
    model_cols = {c.name for c in model.__table__.columns}
    for row in rows:
        # Instantiate a model and set attributes for columns that exist in the model
        inst = model()
        row_dict = {}
        for k, v in row.items():
            if k in model_cols:
                try:
                    setattr(inst, k, v)
                except Exception:
                    pass
            # Hotfix: convert geometry WKB/bytes into a usable lat/lng dict
            def _geom_to_lat_lng(val):
                if val is None:
                    return None
                try:
                    if WKBElement is not None and isinstance(val, WKBElement) and to_shape is not None:
                        geom = to_shape(val)
                        return {"lat": geom.y, "lng": geom.x}
                    if isinstance(val, (bytes, bytearray)) and shapely_wkb is not None:
                        geom = shapely_wkb.loads(bytes(val))
                        return {"lat": geom.y, "lng": geom.x}
                    if hasattr(val, "x") and hasattr(val, "y"):
                        return {"lat": getattr(val, "y"), "lng": getattr(val, "x")}
                except Exception:
                    return None
                return None

            geom_conv = _geom_to_lat_lng(v)
            if geom_conv is not None:
                row_dict[k] = geom_conv
            else:
                # normalize values for JSON output
                try:
                    json.dumps(v)
                    row_dict[k] = v
                except Exception:
                    row_dict[k] = str(v)
        items.append(row_dict)

    out_path = outdir / f"{model.__name__}.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)


@pytest.mark.skipif(not DATABASE_URL, reason="DATABASE_URL not set; skipping DB integration test")
def test_dump_models_to_logs():
    """Connect to DB and dump sample rows for a few models into tests/model_logs/."""

    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        outdir = Path("tests") / "model_logs"
        # Dump a small sample for inspection
        dump_model_rows(session, models.Film, outdir, limit=50)
        dump_model_rows(session, models.Actor, outdir, limit=50)
        dump_model_rows(session, models.Address, outdir, limit=50)

        # Basic sanity: files created and non-empty
        for m in (models.Film, models.Actor, models.Address):
            p = outdir / f"{m.__name__}.json"
            assert p.exists()
            assert p.stat().st_size > 0
    finally:
        session.close()
