from src.api import app 
import src.api.routes #initializes routes in app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
