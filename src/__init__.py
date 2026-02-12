import os
from dotenv import load_dotenv

env_location = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))

load_dotenv(env_location)
print("geocoding key loaded ✅" if (geo_api_key := os.getenv("GEOCODING_API_KEY")) else f"geocoding key NOT located ❌\nTried at following location: \t>>> {env_location}")
