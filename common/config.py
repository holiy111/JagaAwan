"""Environment-backed configuration shared by scanner and API."""

import os

from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SUPABASE_TABLE = os.getenv("JAGAAWAN_SUPABASE_TABLE", "scans")
API_URL = os.getenv("JAGAAWAN_API_URL", "data-contoh.json")
