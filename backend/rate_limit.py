import redis
import os
import logging
from datetime import datetime, timedelta

# Set up logger
logger = logging.getLogger(__name__)

# Try to connect to Redis, fall back to in-memory storage for development
try:
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        redis_client = redis.Redis.from_url(redis_url)
        # Test the connection
        redis_client.ping()
        USE_REDIS = True
        logger.info("Connected to Redis")
    else:
        raise Exception("No REDIS_URL provided")
except Exception as e:
    logger.warning(f"Redis not available ({e}), using in-memory rate limiting")
    USE_REDIS = False
    # In-memory fallback for development
    memory_store = {}

def check_rate_limit(wallet):
    if USE_REDIS:
        key = f"faucet:{wallet.lower()}"
        if redis_client.exists(key):
            logger.info(f"Rate limit active for {wallet}")
            return False
        redis_client.set(key, "1", ex=60*60*24)  # 24 hours expiration
        logger.info(f"Rate limit set for {wallet} - expires in 24h")
        return True
    else:
        # In-memory fallback for development
        key = wallet.lower()
        now = datetime.now()
        
        if key in memory_store:
            if now < memory_store[key]:
                logger.info(f"Rate limit active for {wallet} until {memory_store[key]}")
                return False
        
        # Set expiration 24 hours from now
        expiry_time = now + timedelta(hours=24)
        memory_store[key] = expiry_time
        logger.info(f"Rate limit set for {wallet} until {expiry_time}")
        return True

def get_rate_limit_status(wallet):
    """Check if a wallet is rate limited and when it expires"""
    if USE_REDIS:
        key = f"faucet:{wallet.lower()}"
        if redis_client.exists(key):
            ttl = redis_client.ttl(key)
            return True, ttl
        return False, 0
    else:
        key = wallet.lower()
        now = datetime.now()
        
        if key in memory_store:
            if now < memory_store[key]:
                remaining_seconds = int((memory_store[key] - now).total_seconds())
                return True, remaining_seconds
        return False, 0

def clear_rate_limit(wallet):
    """Clear rate limit for a wallet (admin function)"""
    if USE_REDIS:
        key = f"faucet:{wallet.lower()}"
        deleted = redis_client.delete(key)
        logger.info(f"Cleared rate limit for {wallet}: {'success' if deleted else 'not found'}")
        return deleted > 0
    else:
        key = wallet.lower()
        if key in memory_store:
            del memory_store[key]
            logger.info(f"Cleared rate limit for {wallet}")
            return True
        return False
