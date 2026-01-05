import sys
import os
from flask import Flask, jsonify, send_from_directory
import traceback

# Add the backend directory to Python path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

# Create a simple app first with static files in the api directory
app = Flask(__name__, static_folder='../frontend/dist', static_url_path='')
app.config['DEBUG'] = True

@app.route('/health')
def health():
    return {"status": "healthy", "backend_path": backend_path}

@app.route('/debug')
def debug():
    return {
        "status": "debug info",
        "backend_path": backend_path,
        "current_dir": os.getcwd(),
        "api_dir_files": os.listdir(os.path.dirname(__file__)),
        "backend_exists": os.path.exists(backend_path),
        "backend_files": os.listdir(backend_path) if os.path.exists(backend_path) else "not found",
        "static_path": app.static_folder,
        "static_exists": os.path.exists(app.static_folder) if app.static_folder else False
    }

# Simple route to serve the frontend
@app.route('/')
def index():
    try:
        # Try to serve from multiple possible locations
        static_dirs = [
            '../frontend/dist',
            '../backend/static', 
            './static',
            '../static'
        ]
        
        for static_dir in static_dirs:
            index_path = os.path.join(os.path.dirname(__file__), static_dir, 'index.html')
            if os.path.exists(index_path):
                return send_from_directory(os.path.join(os.path.dirname(__file__), static_dir), 'index.html')
        
        # If no static files found, return a basic HTML page
        return '''
        <!DOCTYPE html>
        <html>
        <head><title>Faucet Loading...</title></head>
        <body>
            <h1>Faucet is starting up...</h1>
            <p>Static files not found. Check <a href="/debug">/debug</a> for info.</p>
        </body>
        </html>
        '''
    except Exception as e:
        return f"Error serving index: {str(e)}", 500

try:
    # Try to import the main app's API routes
    from app import app as main_app
    
    # Copy the API routes from main app
    for rule in main_app.url_map.iter_rules():
        if rule.endpoint.startswith('api'):  # Only copy API routes
            app.add_url_rule(
                rule.rule, 
                rule.endpoint, 
                main_app.view_functions[rule.endpoint],
                methods=rule.methods
            )
    
    print("Successfully imported API routes from main app")
    
except Exception as e:
    print(f"Failed to import main app: {str(e)}")
    
    # Fallback API route
    @app.route('/api/faucet', methods=['POST'])
    def fallback_faucet():
        return {
            "error": "Main app failed to load",
            "details": str(e)
        }, 500
