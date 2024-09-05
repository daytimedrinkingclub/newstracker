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
        'job_id': str(uuid.uuid4()),  # Add this line
        'id': str(uuid.uuid4()),
        'func': func.__name__,
        'args': args,
        'kwargs': kwargs
    }
    logging.info(f"Enqueueing task: {task}")

    message = json.dumps(task)
    try:
        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            ))
        logging.info(f"Task enqueued successfully: {task['job_id']}")
    except Exception as e:
        logging.error(f"Error enqueueing task: {str(e)}")
        raise

    return task['job_id']