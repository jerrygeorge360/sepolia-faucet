import sys
import os
from flask import Flask, jsonify

# Add the backend directory to Python path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

# Create a simple app first
app = Flask(__name__)

@app.route('/health')
def health():
    return {"status": "healthy", "backend_path": backend_path}

try:
    # Try to import the main app
    from app import app as main_app
    # Replace our simple app with the main app
    app = main_app
    
except Exception as e:
    # Keep the simple app and add an error route
    @app.route('/')
    def error():
        return {
            "error": f"Failed to import main app: {str(e)}",
            "python_path": sys.path,
            "backend_path": backend_path,
            "files_in_backend": os.listdir(backend_path) if os.path.exists(backend_path) else "backend not found"
        }, 500
