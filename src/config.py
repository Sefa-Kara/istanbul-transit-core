import os
from pathlib import Path

# Base project directories (Resolved dynamically)
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "static"
CACHE_DIR = BASE_DIR / "cache"

# Simple Zero-Dependency .env parser
env_file = BASE_DIR / ".env"
if env_file.exists():
    try:
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if key not in os.environ:
                        os.environ[key] = val
    except Exception:
        pass

# Service Endpoints and Settings
OTP_GRAPHQL_URL = os.getenv("OTP_GRAPHQL_URL", "http://localhost:8080/otp/routers/default/index/graphql")
IETT_API_URL = os.getenv("IETT_API_URL", "https://api.ibb.gov.tr/iett/FiloDurum/SeferGerceklesme.asmx?wsdl")
USER_AGENT = os.getenv("USER_AGENT", "IstanbulTransitCore/3.0 (contact: info@transit-navigator.local)")
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
