# backend/app/redis_config.py
import redis
from flask import current_app


def get_redis_connection():
    return redis.Redis(
        host=current_app.config['REDIS_HOST'],
        port=current_app.config['REDIS_PORT'],
        password=current_app.config['REDIS_PASSWORD'],
        decode_responses=True
    )

def get_redis_queue():
    return current_app.task_queue