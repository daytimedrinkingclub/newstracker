# run_worker.py
import os
import sys
from redis import Redis
from rq import Worker, Queue, Connection
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory and the app directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, 'app'))

# Import your Flask app
from app import create_app

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        redis_url = app.config['REDIS_URL']
        print(f"Connecting to Redis at: {redis_url}")
        redis_connection = Redis.from_url(redis_url)

        with Connection(redis_connection):
            worker = Worker(['default'])
            print("Starting worker...")
            worker.work(with_scheduler=True)