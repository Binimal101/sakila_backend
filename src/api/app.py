from . import app, router

# Import package-relative `routes` so it can register endpoints on `router`
from . import routes

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
