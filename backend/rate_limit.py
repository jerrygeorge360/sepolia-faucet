import redis
import os

redis_client = redis.Redis.from_url(os.getenv("REDIS_URL"))

def check_rate_limit(wallet):
    key = f"faucet:{wallet.lower()}"
    if redis_client.exists(key):
        return False

    redis_client.set(key, "1", ex=60*60*24)  # 24 hours expiration
    return True
