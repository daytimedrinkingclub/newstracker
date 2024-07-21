from dotenv import load_dotenv
import os

# Load environment variables before importing app
load_dotenv()

from app import create_app
from app.config import config

app = create_app()

if __name__ == '__main__':
    app.run(debug=config.DEBUG)