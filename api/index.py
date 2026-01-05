import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Import your Flask app
from app import app

# Export the app for Vercel
def handler(request):
    return app.wsgi_app(request.environ, lambda status, headers: None)

# This is what Vercel will use
application = app
