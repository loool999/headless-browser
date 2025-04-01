#!/usr/bin/env python3
"""
Headless Browser Web Interface
This module provides a web interface for the headless browser service.
"""

import asyncio
import base64
import json
import os
import sys
import threading
import time
import uuid
from typing import Dict, List, Optional, Union

from flask import Flask, request, jsonify, render_template, send_file, Response, make_response
from flask_cors import CORS
import logging
import nest_asyncio

# Import our browser modules
from browser_core import HeadlessBrowser
from browser_optimizations import BrowserOptimizations

# Apply nest_asyncio to allow asyncio to work in Flask
nest_asyncio.apply()

# Create Flask app with CORS support
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create a global browser instance
browser = HeadlessBrowser()
browser_lock = threading.Lock()
browser_started = False

# Store active sessions
sessions = {}

def get_session_id():
    """Generate a unique session ID."""
    return str(uuid.uuid4())

def ensure_browser_started():
    """Ensure the browser is started."""
    global browser_started
    if not browser_started:
        with browser_lock:
            if not browser_started:
                asyncio.run(browser.start(headless=True))
                browser_started = True

# Add a middleware to ensure all API responses have proper headers
@app.after_request
def add_header(response):
    if request.path.startswith('/api/'):
        if not response.headers.get('Content-Type'):
            response.headers['Content-Type'] = 'application/json'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

@app.route('/')
def index():
    """Render the main interface."""
    return render_template('index.html')

@app.route('/api/browser/start', methods=['POST', 'OPTIONS'])
def start_browser():
    """Start the browser."""
    if request.method == 'OPTIONS':
        return jsonify({"success": True})
        
    try:
        logger.debug("API call: start_browser")
        ensure_browser_started()
        logger.debug("Browser started successfully")
        return jsonify({"success": True, "message": "Browser started successfully"})
    except Exception as e:
        logger.error(f"Error starting browser: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/browser/stop', methods=['POST', 'OPTIONS'])
def stop_browser():
    """Stop the browser."""
    if request.method == 'OPTIONS':
        return jsonify({"success": True})
        
    global browser_started
    try:
        logger.debug("API call: stop_browser")
        if browser_started:
            with browser_lock:
                if browser_started:
                    asyncio.run(browser.stop())
                    browser_started = False
        logger.debug("Browser stopped successfully")
        return jsonify({"success": True, "message": "Browser stopped successfully"})
    except Exception as e:
        logger.error(f"Error stopping browser: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/session/create', methods=['POST', 'OPTIONS'])
def create_session():
    """Create a new browser session."""
    if request.method == 'OPTIONS':
        return jsonify({"success": True})
        
    try:
        logger.debug("API call: create_session")
        ensure_browser_started()
        
        data = request.json or {}
        context_id = get_session_id()
        page_id = get_session_id()
        
        # Get optional parameters
        viewport = data.get('viewport', None)
        user_agent = data.get('userAgent', None)
        
        # Create context and page
        asyncio.run(browser.create_context(context_id, viewport=viewport, user_agent=user_agent))
        asyncio.run(browser.create_page(page_id, context_id))
        
        # Apply optimizations if requested
        if data.get('optimize', False):
            page = browser.pages[page_id]
            optimization_options = {
                'block_resources': data.get('blockResources', []),
                'viewport': viewport
            }
            asyncio.run(BrowserOptimizations.apply_all_optimizations(page, optimization_options))
        
        # Store session info
        sessions[page_id] = {
            'context_id': context_id,
            'created_at': time.time(),
            'last_used': time.time()
        }
        
        logger.debug(f"Session created successfully: {page_id}")
        return jsonify({
            "success": True, 
            "sessionId": page_id,
            "message": "Session created successfully"
        })
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/session/close', methods=['POST', 'OPTIONS'])
def close_session():
    """Close a browser session."""
    if request.method == 'OPTIONS':
        return jsonify({"success": True})
        
    try:
        logger.debug("API call: close_session")
        data = request.json or {}
        session_id = data.get('sessionId')
        
        if not session_id or session_id not in sessions:
            logger.warning(f"Invalid session ID: {session_id}")
            return jsonify({"success": False, "error": "Invalid session ID"}), 400
        
        context_id = sessions[session_id]['context_id']
        
        # Close the page and context
        asyncio.run(browser.close_page(session_id))
        asyncio.run(browser.close_context(context_id))
        
        # Remove session
        del sessions[session_id]
        
        logger.debug(f"Session closed successfully: {session_id}")
        return jsonify({"success": True, "message": "Session closed successfully"})
    except Exception as e:
        logger.error(f"Error closing session: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/navigate', methods=['POST', 'OPTIONS'])
def navigate():
    """Navigate to a URL."""
    if request.method == 'OPTIONS':
        return jsonify({"success": True})
        
    try:
        logger.debug("API call: navigate")
        data = request.json or {}
        session_id = data.get('sessionId')
        url = data.get('url')
        
        if not session_id or session_id not in sessions:
            logger.warning(f"Invalid session ID: {session_id}")
            return jsonify({"success": False, "error": "Invalid session ID"}), 400
        
        if not url:
            logger.warning("URL is required")
            return jsonify({"success": False, "error": "URL is required"}), 400
        
        # Update last used time
        sessions[session_id]['last_used'] = time.time()
        
        # Navigate to URL
        wait_until = data.get('waitUntil', 'load')
        timeout = data.get('timeout', 30000)
        result = asyncio.run(browser.navigate(session_id, url, wait_until=wait_until, timeout=timeout))
        
        logger.debug(f"Navigation result: {result}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error navigating: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/screenshot', methods=['POST', 'OPTIONS'])
def screenshot():
    """Take a screenshot."""
    if request.method == 'OPTIONS':
        return jsonify({"success": True})
        
    try:
        logger.debug("API call: screenshot")
        data = request.json or {}
        session_id = data.get('sessionId')
        full_page = data.get('fullPage', True)
        
        if not session_id or session_id not in sessions:
            logger.warning(f"Invalid session ID: {session_id}")
            return jsonify({"success": False, "error": "Invalid session ID"}), 400
        
        # Update last used time
        sessions[session_id]['last_used'] = time.time()
        
        # Take screenshot
        screenshot_data = asyncio.run(browser.screenshot(session_id, full_page=full_page))
        
        logger.debug("Screenshot taken successfully")
        return jsonify({
            "success": True,
            "screenshot": screenshot_data
        })
    except Exception as e:
        logger.error(f"Error taking screenshot: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/content', methods=['POST', 'OPTIONS'])
def get_content():
    """Get page content."""
    if request.method == 'OPTIONS':
        return jsonify({"success": True})
        
    try:
        logger.debug("API call: get_content")
        data = request.json or {}
        session_id = data.get('sessionId')
        include_html = data.get('includeHtml', False)
        
        if not session_id or session_id not in sessions:
            logger.warning(f"Invalid session ID: {session_id}")
            return jsonify({"success": False, "error": "Invalid session ID"}), 400
        
        # Update last used time
        sessions[session_id]['last_used'] = time.time()
        
        # Get content
        content = asyncio.run(browser.get_page_content(session_id, include_html=include_html))
        
        logger.debug("Content retrieved successfully")
        return jsonify(content)
    except Exception as e:
        logger.error(f"Error getting content: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/execute', methods=['POST', 'OPTIONS'])
def execute_javascript():
    """Execute JavaScript."""
    if request.method == 'OPTIONS':
        return jsonify({"success": True})
        
    try:
        logger.debug("API call: execute_javascript")
        data = request.json or {}
        session_id = data.get('sessionId')
        script = data.get('script')
        
        if not session_id or session_id not in sessions:
            logger.warning(f"Invalid session ID: {session_id}")
            return jsonify({"success": False, "error": "Invalid session ID"}), 400
        
        if not script:
            logger.warning("Script is required")
            return jsonify({"success": False, "error": "Script is required"}), 400
        
        # Update last used time
        sessions[session_id]['last_used'] = time.time()
        
        # Execute JavaScript
        result = asyncio.run(browser.execute_javascript(session_id, script))
        
        logger.debug(f"JavaScript execution result: {result}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error executing JavaScript: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/click', methods=['POST', 'OPTIONS'])
def click():
    """Click on an element."""
    if request.method == 'OPTIONS':
        return jsonify({"success": True})
        
    try:
        logger.debug("API call: click")
        data = request.json or {}
        session_id = data.get('sessionId')
        selector = data.get('selector')
        
        if not session_id or session_id not in sessions:
            logger.warning(f"Invalid session ID: {session_id}")
            return jsonify({"success": False, "error": "Invalid session ID"}), 400
        
        if not selector:
            logger.warning("Selector is required")
            return jsonify({"success": False, "error": "Selector is required"}), 400
        
        # Update last used time
        sessions[session_id]['last_used'] = time.time()
        
        # Click on element
        timeout = data.get('timeout', 5000)
        button = data.get('button', 'left')
        result = asyncio.run(browser.click(session_id, selector, timeout=timeout, button=button))
        
        logger.debug(f"Click result: {result}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error clicking element: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/type', methods=['POST', 'OPTIONS'])
def type_text():
    """Type text into an element."""
    if request.method == 'OPTIONS':
        return jsonify({"success": True})
        
    try:
        logger.debug("API call: type_text")
        data = request.json or {}
        session_id = data.get('sessionId')
        selector = data.get('selector')
        text = data.get('text')
        
        if not session_id or session_id not in sessions:
            logger.warning(f"Invalid session ID: {session_id}")
            return jsonify({"success": False, "error": "Invalid session ID"}), 400
        
        if not selector or not text:
            logger.warning("Selector and text are required")
            return jsonify({"success": False, "error": "Selector and text are required"}), 400
        
        # Update last used time
        sessions[session_id]['last_used'] = time.time()
        
        # Type text
        delay = data.get('delay', 50)
        result = asyncio.run(browser.type_text(session_id, selector, text, delay=delay))
        
        logger.debug(f"Type text result: {result}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error typing text: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/element', methods=['POST', 'OPTIONS'])
def get_element_text():
    """Get element text."""
    if request.method == 'OPTIONS':
        return jsonify({"success": True})
        
    try:
        logger.debug("API call: get_element_text")
        data = request.json or {}
        session_id = data.get('sessionId')
        selector = data.get('selector')
        
        if not session_id or session_id not in sessions:
            logger.warning(f"Invalid session ID: {session_id}")
            return jsonify({"success": False, "error": "Invalid session ID"}), 400
        
        if not selector:
            logger.warning("Selector is required")
            return jsonify({"success": False, "error": "Selector is required"}), 400
        
        # Update last used time
        sessions[session_id]['last_used'] = time.time()
        
        # Get element text
        result = asyncio.run(browser.get_element_text(session_id, selector))
        
        logger.debug(f"Get element text result: {result}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting element text: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

def run_server(host='0.0.0.0', port=5000):
    """Run the Flask server."""
    app.run(host=host, port=port, debug=False)

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs(os.path.join(os.path.dirname(__file__), 'templates'), exist_ok=True)
    
    # Run the server
    run_server()
