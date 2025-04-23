import os
from dotenv import load_dotenv
load_dotenv()

REDIS_HOST     = os.getenv("REDIS_HOST")
REDIS_PORT     = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
LLM_API_URL    = os.getenv("LLM_API_URL")
FRONTEND_URL   = os.getenv("FRONTEND_URL", "http://localhost:3000")