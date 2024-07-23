# backend/run.py for local development
from app import create_app
from app.config import config

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)