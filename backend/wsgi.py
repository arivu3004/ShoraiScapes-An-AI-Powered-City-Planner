"""
WSGI entry point for production-ready server
Run with: waitress-serve --host=0.0.0.0 --port=5000 wsgi:app
"""

from app import app

if __name__ == '__main__':
    app.run()
