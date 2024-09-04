# app/
import pika
from dotenv import load_dotenv
import os

load_dotenv()

def get_rabbitmq_connection():
    # RabbitMQ connection parameters
    rabbitmq_host = os.getenv('RABBITMQ_HOST', 'localhost')
    rabbitmq_port = int(os.getenv('RABBITMQ_PORT', 5672))
    rabbitmq_user = os.getenv('RABBITMQ_USER', 'guest')
    rabbitmq_pass = os.getenv('RABBITMQ_PASS', 'guest')

    # Create a connection
    credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
    parameters = pika.ConnectionParameters(host=rabbitmq_host,
                                           port=rabbitmq_port,
                                           credentials=credentials)
    return pika.BlockingConnection(parameters)

def get_rabbitmq_channel():
    connection = get_rabbitmq_connection()
    return connection.channel()