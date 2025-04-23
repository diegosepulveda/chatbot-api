# app/config/redis.py
import redis, os
from dotenv import load_dotenv
load_dotenv()

redis_instance = redis.StrictRedis(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT")),
    password=os.getenv("REDIS_PASSWORD"),
    decode_responses=True,
)