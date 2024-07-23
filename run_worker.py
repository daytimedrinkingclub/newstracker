# run_worker.py
import os
import sys
from redis import Redis
from rq import SimpleWorker, Queue, Connection
from rq.job import Job

# Add the current directory and the app directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, 'app'))

# Import your Flask app
from app import create_app

# Create the Flask app
app = create_app()

# Custom worker class to disable job timeouts and handle long-running jobs
class LongRunningWorker(SimpleWorker):
    def execute_job(self, job, queue):
        self.prepare_job_execution(job)
        try:
            job.perform()
        except Exception:
            job.exc_info = sys.exc_info()
            self.handle_exception(job, *job.exc_info)
            self.handle_job_failure(job, queue=queue)
        else:
            self.handle_job_success(job=job, queue=queue)

    def handle_job_success(self, job, queue):
        super().handle_job_success(job, queue)
        print(f"Job {job.id} completed successfully after {job.ended_at - job.started_at}")

# Use the app context
with app.app_context():
    redis_url = app.config['REDIS_URL']
    print(f"Connecting to Redis at: {redis_url}")
    redis_connection = Redis.from_url(redis_url)

    with Connection(redis_connection):
        queue = Queue('default')
        worker = LongRunningWorker([queue], connection=redis_connection)
        print("Starting worker...")
        worker.work(with_scheduler=True, burst=False)  # Run continuously