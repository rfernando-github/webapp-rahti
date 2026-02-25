"""WSGI entry point for Gunicorn (used by Rahti S2I build)."""
from app import app

if __name__ == '__main__':
    app.run()
