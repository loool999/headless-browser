#!/usr/bin/env python3
"""
Simple Headless Browser Service
A simplified version that focuses on core functionality with proper API responses
"""

import asyncio
import base64
import json
import os
import sys
from flask import Flask, request, jsonify, render_template, send_file, Response
from flask_cors import CORS
import nest_asyncio
from playwright.async_api import async_playwright

# Apply nest_asyncio to allow asyncio to work in Flask
nest_asyncio.apply()

# Create Flask app with CORS support
app = Flask(__name__)
CORS(app)

# Global variables
playwright = None
browser = None
context = None
page = None
loop = None

# Initialize the browser
async def init_browser():
    global playwright, browser, context, page
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context()
    page = await context.new_page()
    return True

# Create a single event loop for all async operations
def get_event_loop():
    global loop
    if loop is None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop

# Run async function in the shared event loop
def run_async(coro):
    return get_event_loop().run_until_complete(coro)

# Ensure all API responses are JSON
@app.after_request
def add_header(response):
    if request.path.startswith('/api/'):
        response.headers['Content-Type'] = 'application/json'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

# Handle OPTIONS requests
@app.route('/api/<path:path>', methods=['OPTIONS'])
def options_handler(path):
    return jsonify({"success": True})

@app.route('/')
def index():
    return render_template('simple.html')

@app.route('/api/start', methods=['POST'])
def start_browser():
    try:
        success = run_async(init_browser())
        return jsonify({"success": success, "message": "Browser started"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/navigate', methods=['POST'])
def navigate():
    try:
        data = request.json
        url = data.get('url', 'https://example.com')
        
        if not page:
            return jsonify({"success": False, "error": "Browser not started"})
        
        run_async(page.goto(url))
        title = run_async(page.title())
        
        return jsonify({
            "success": True, 
            "url": url,
            "title": title
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/screenshot', methods=['POST'])
def take_screenshot():
    try:
        if not page:
            return jsonify({"success": False, "error": "Browser not started"})
        
        screenshot_bytes = run_async(page.screenshot())
        screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
        
        return jsonify({
            "success": True,
            "screenshot": screenshot_base64
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/content', methods=['POST'])
def get_content():
    try:
        if not page:
            return jsonify({"success": False, "error": "Browser not started"})
        
        content = run_async(page.content())
        text = run_async(page.evaluate("() => document.body.innerText"))
        title = run_async(page.title())
        
        return jsonify({
            "success": True,
            "title": title,
            "text": text,
            "html": content
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/execute', methods=['POST'])
def execute_js():
    try:
        data = request.json
        script = data.get('script', 'document.title')
        
        if not page:
            return jsonify({"success": False, "error": "Browser not started"})
        
        result = run_async(page.evaluate(script))
        
        return jsonify({
            "success": True,
            "result": result
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Create a simple HTML template
    with open('templates/simple.html', 'w') as f:
        f.write("""<!DOCTYPE html>
<html>
<head>
    <title>Simple Headless Browser</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        button { padding: 8px 16px; margin: 5px; }
        input { padding: 8px; width: 300px; }
        #screenshot { max-width: 100%; border: 1px solid #ccc; margin-top: 20px; }
        #output { white-space: pre-wrap; background: #f5f5f5; padding: 10px; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Simple Headless Browser</h1>
        
        <div>
            <button id="startBtn">Start Browser</button>
        </div>
        
        <div>
            <input id="urlInput" type="text" placeholder="https://example.com" value="https://example.com">
            <button id="navigateBtn">Navigate</button>
        </div>
        
        <div>
            <button id="screenshotBtn">Take Screenshot</button>
            <button id="contentBtn">Get Content</button>
        </div>
        
        <div>
            <input id="jsInput" type="text" placeholder="JavaScript code" value="document.title">
            <button id="executeBtn">Execute</button>
        </div>
        
        <img id="screenshot" style="display: none;">
        <pre id="output"></pre>
    </div>
    
    <script>
        // Helper function for API calls
        async function callApi(endpoint, data = {}) {
            try {
                const response = await fetch(`/api/${endpoint}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });
                
                return await response.json();
            } catch (error) {
                console.error('API Error:', error);
                return { success: false, error: error.message };
            }
        }
        
        // Display output
        function showOutput(data) {
            document.getElementById('output').textContent = JSON.stringify(data, null, 2);
        }
        
        // Event listeners
        document.getElementById('startBtn').addEventListener('click', async () => {
            const result = await callApi('start');
            showOutput(result);
        });
        
        document.getElementById('navigateBtn').addEventListener('click', async () => {
            const url = document.getElementById('urlInput').value;
            const result = await callApi('navigate', { url });
            showOutput(result);
        });
        
        document.getElementById('screenshotBtn').addEventListener('click', async () => {
            const result = await callApi('screenshot');
            if (result.success) {
                const img = document.getElementById('screenshot');
                img.src = `data:image/png;base64,${result.screenshot}`;
                img.style.display = 'block';
            }
            showOutput(result);
        });
        
        document.getElementById('contentBtn').addEventListener('click', async () => {
            const result = await callApi('content');
            showOutput(result);
        });
        
        document.getElementById('executeBtn').addEventListener('click', async () => {
            const script = document.getElementById('jsInput').value;
            const result = await callApi('execute', { script });
            showOutput(result);
        });
    </script>
</body>
</html>""")
    
    # Run the app
    app.run(host='0.0.0.0', port=8081, debug=False)
