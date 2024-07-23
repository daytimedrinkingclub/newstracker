import os
import sys
import unittest
import redis
from dotenv import load_dotenv

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_redis_connection():
    return redis.Redis(
        host="redis-17458.c98.us-east-1-4.ec2.redns.redis-cloud.com",
        port=17458,
        password="Kabeer@Seth@271998",
        decode_responses=True
    )

class TestRedisConnection(unittest.TestCase):
    def setUp(self):
        # Load environment variables
        load_dotenv()

    def test_redis_connection(self):
        try:
            redis_conn = get_redis_connection()
            redis_conn.ping()
            print("Successfully connected to Redis!")
        except Exception as e:
            self.fail(f"Failed to connect to Redis: {str(e)}")

if __name__ == '__main__':
    unittest.main()