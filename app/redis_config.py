# app/redis_config.py
import redis
from redis import ConnectionPool
from flask import current_app

def get_redis_connection():
    if not hasattr(current_app, 'redis_pool'):
        current_app.redis_pool = ConnectionPool(
            host=current_app.config['REDIS_HOST'],
            port=current_app.config['REDIS_PORT'],
            password=current_app.config['REDIS_PASSWORD'],
            decode_responses=True
        )
    return redis.Redis(connection_pool=current_app.redis_pool)