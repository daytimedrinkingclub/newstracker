import json
import pika
import uuid
from typing import Callable, Any
from ..rabbitmq_config import get_rabbitmq_channel
import logging

def enqueue_task(func: Callable, *args: Any, **kwargs: Any) -> str:
    channel = get_rabbitmq_channel()

    queue_name = 'task_queue'
    channel.queue_declare(queue=queue_name, durable=True)

    task = {
        'func': func.__name__,
        'args': args,
        'kwargs': kwargs,
        'job_id': str(uuid.uuid4())  # Generate a unique job_id
    }
    logging.info(f"Enqueueing task: {task}")

    message = json.dumps(task)
    channel.basic_publish(
        exchange='',
        routing_key=queue_name,
        body=message,
        properties=pika.BasicProperties(
            delivery_mode=2,  # make message persistent
        ))

    return task['job_id']  # Return the job_id instead of the message