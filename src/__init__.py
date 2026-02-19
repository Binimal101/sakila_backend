import os
from dotenv import load_dotenv

env_location = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(env_location)

DATABASE_URL = os.getenv("DATABASE_URL")

print("db url loaded ✅" if DATABASE_URL else f"db url NOT located\nTried at following location: \t>>> {env_location}")

if not all([DATABASE_URL, ...]):
    raise Exception("Missing required environment variables. Check logs for details.")