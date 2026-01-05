import sys
import os

# Simple test endpoint
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello from Vercel!"

@app.route('/test')
def test():
    return {
        "message": "Test endpoint working",
        "python_path": sys.path,
        "working_directory": os.getcwd(),
        "files": os.listdir('.')
    }
