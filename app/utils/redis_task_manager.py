# backend/app/utils/redis_task_manager.py
from flask import current_app
from rq import Queue

def enqueue_task(task_func, *args, **kwargs):
    print(f"Entering enqueue_task for function: {task_func.__name__}")
    q = Queue('default', connection=current_app.redis)
    print(f"Queue created with connection: {current_app.redis}")
    # Set a very high timeout for the job
    job = q.enqueue(task_func, *args, **kwargs, timeout=86400)  # 24 hours timeout
    print(f"Job enqueued: {job.id}")
    return job

def get_task_status(job_id):
    q = Queue('default', connection=current_app.redis)
    job = q.fetch_job(job_id)
    if job:
        return job.get_status()
    return None