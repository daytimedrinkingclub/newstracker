# worker.py
import pika
import json
import importlib
import os
import time
import logging
from app.services.agent import AnthropicChat

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# RabbitMQ connection parameters
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'guest')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASS', 'guest')

def get_rabbitmq_connection():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=credentials,
        heartbeat=600,
        blocked_connection_timeout=300
    )
    logger.info(f"Attempting to connect to RabbitMQ with parameters: {parameters}")
    return pika.BlockingConnection(parameters)

def callback(ch, method, properties, body):
    try:
        logging.info(f"Received message: {body}")
        task = json.loads(body)
        logging.info(f"Parsed task: {task}")
        job_id = task['id']  # Change this line
        func_name = task['func']
        args = task['args']
        kwargs = task['kwargs']

        # Dynamically import the function
        module_parts = func_name.split('.')
        module = __import__(module_parts[0], fromlist=module_parts[1:])
        for part in module_parts[1:]:
            module = getattr(module, part)
        func = module

        # Execute the function
        if func_name == 'app.services.agent.AnthropicChat.handle_chat':
            result = AnthropicChat.handle_chat(*args, **kwargs)
        else:
            result = func(*args, **kwargs)
        logger.info(f"Processed task: {func_name}, Job ID: {job_id}, Result: {result}")

        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        logger.error(f"Error processing task: {str(e)}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

def main():
    while True:
        try:
            connection = get_rabbitmq_connection()
            channel = connection.channel()

            queue_name = 'task_queue'
            channel.queue_declare(queue=queue_name, durable=True)

            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=queue_name, on_message_callback=callback)

            logger.info(' [*] Waiting for messages. To exit press CTRL+C')
            channel.start_consuming()
        except pika.exceptions.AMQPConnectionError:
            logger.error("Connection was closed, retrying...")
            time.sleep(5)
        except KeyboardInterrupt:
            logger.info("Worker stopped")
            break
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            time.sleep(5)

if __name__ == "__main__":
    main()