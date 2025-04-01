#!/usr/bin/env python3
"""
API Response Format Fix
This script adds proper CORS headers and ensures all API responses are in JSON format.
"""

import os
import sys
from flask import Flask, request, jsonify, render_template, send_file, Response, make_response
from flask_cors import CORS
import logging

# Add this to the top of app.py
def create_app():
    app = Flask(__name__)
    CORS(app)  # Enable CORS for all routes
    
    # Configure logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    
    # Add a middleware to ensure all API responses have proper headers
    @app.after_request
    def add_header(response):
        if request.path.startswith('/api/'):
            response.headers['Content-Type'] = 'application/json'
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    return app, logger

# Instructions to modify app.py:
"""
1. Replace the Flask app initialization with:
   app, logger = create_app()

2. Make sure all API endpoints return proper JSON:
   - Always use jsonify() for API responses
   - Handle exceptions properly and return JSON error messages
   - Set appropriate status codes for errors

3. Install flask-cors:
   pip install flask-cors

4. Restart the service after making changes
"""

print("To fix the API response format issue:")
print("1. Install flask-cors: pip install flask-cors")
print("2. Modify app.py to use the create_app() function")
print("3. Ensure all API endpoints return proper JSON responses")
print("4. Restart the service")
