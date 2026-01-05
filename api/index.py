import sys
import os
from flask import Flask, jsonify, send_from_directory
import traceback

# Add the backend directory to Python path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

# Create a simple app first with static files in the backend/static directory
app = Flask(__name__, static_folder='../backend/static', static_url_path='')
app.config['DEBUG'] = True

@app.route('/health')
def health():
    return {"status": "healthy", "backend_path": backend_path}

@app.route('/debug')
def debug():
    static_info = {}
    static_dirs = ['../frontend/dist', '../backend/static', './static', '../static']
    
    for static_dir in static_dirs:
        full_path = os.path.join(os.path.dirname(__file__), static_dir)
        if os.path.exists(full_path):
            try:
                files = os.listdir(full_path)
                static_info[static_dir] = files
                # Also check assets subdirectory
                assets_path = os.path.join(full_path, 'assets')
                if os.path.exists(assets_path):
                    static_info[f"{static_dir}/assets"] = os.listdir(assets_path)
            except Exception as e:
                static_info[static_dir] = f"Error reading: {e}"
        else:
            static_info[static_dir] = "Does not exist"
    
    return {
        "status": "debug info",
        "backend_path": backend_path,
        "current_dir": os.getcwd(),
        "api_dir_files": os.listdir(os.path.dirname(__file__)),
        "backend_exists": os.path.exists(backend_path),
        "backend_files": os.listdir(backend_path) if os.path.exists(backend_path) else "not found",
        "static_path": app.static_folder,
        "static_exists": os.path.exists(app.static_folder) if app.static_folder else False,
        "static_directories": static_info
    }

# Simple route to serve the frontend
@app.route('/')
def index():
    try:
        # Try to serve from multiple possible locations (prioritize existing ones)
        static_dirs = [
            '../backend/static',  # This exists according to debug
            '../frontend/dist',
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

# Route to serve static assets (CSS, JS files)
@app.route('/assets/<path:filename>')
def serve_assets(filename):
    try:
        static_dirs = [
            '../backend/static/assets',  # This exists according to debug
            '../frontend/dist/assets',
            './static/assets', 
            '../static/assets'
        ]
        
        for static_dir in static_dirs:
            asset_path = os.path.join(os.path.dirname(__file__), static_dir, filename)
            if os.path.exists(asset_path):
                return send_from_directory(os.path.join(os.path.dirname(__file__), static_dir), filename)
        
        return f"Asset not found: {filename}", 404
    except Exception as e:
        return f"Error serving asset {filename}: {str(e)}", 500

# Catch-all route for any other static files
@app.route('/<path:filename>')
def serve_static_files(filename):
    # Skip API routes
    if filename.startswith('api/'):
        return "Not found", 404
    
    try:
        static_dirs = [
            '../frontend/dist',
            '../backend/static',
            './static',
            '../static'
        ]
        
        for static_dir in static_dirs:
            file_path = os.path.join(os.path.dirname(__file__), static_dir, filename)
            if os.path.exists(file_path):
                return send_from_directory(os.path.join(os.path.dirname(__file__), static_dir), filename)
        
        return f"File not found: {filename}", 404
    except Exception as e:
        return f"Error serving file {filename}: {str(e)}", 500

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
