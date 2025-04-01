#!/usr/bin/env python3
"""
Interactive Headless Browser with Click-on-Stream Functionality
This module provides a headless browser service with real-time screenshot streaming
and the ability to click directly on the stream.
"""

import asyncio
import base64
import io
import json
import os
import sys
import time
import threading
from datetime import datetime
from flask import Flask, request, jsonify, render_template, Response, send_file
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
streaming_active = False
stream_fps = 30  # Default FPS
stream_quality = 80  # Default JPEG quality (0-100)
last_screenshot = None
screenshot_lock = threading.Lock()
viewport_width = 1280
viewport_height = 720

# Initialize the browser
async def init_browser():
    global playwright, browser, context, page, viewport_width, viewport_height
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context(viewport={"width": viewport_width, "height": viewport_height})
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
    if request.path.startswith('/api/') and not request.path.startswith('/api/stream'):
        response.headers['Content-Type'] = 'application/json'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

# Handle OPTIONS requests
@app.route('/api/<path:path>', methods=['OPTIONS'])
def options_handler(path):
    return jsonify({"success": True})

# Screenshot capture thread
def screenshot_capture_thread():
    global last_screenshot, streaming_active
    
    while streaming_active:
        try:
            if page:
                # Capture screenshot with specified quality
                screenshot_bytes = run_async(page.screenshot(type='jpeg', quality=stream_quality))
                
                # Update the last screenshot with thread safety
                with screenshot_lock:
                    last_screenshot = screenshot_bytes
                
                # Calculate sleep time to maintain target FPS
                sleep_time = 1.0 / stream_fps
                time.sleep(sleep_time)
            else:
                time.sleep(0.1)  # Sleep briefly if page is not available
        except Exception as e:
            print(f"Screenshot error: {str(e)}")
            time.sleep(0.5)  # Sleep on error to prevent CPU spinning

# Generate frames for MJPEG stream
def generate_frames():
    global last_screenshot
    
    while True:
        with screenshot_lock:
            if last_screenshot:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + last_screenshot + b'\r\n')
        
        # Sleep to control server load
        time.sleep(0.01)

@app.route('/')
def index():
    return render_template('interactive.html')

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
        
        data = request.json or {}
        quality = data.get('quality', 80)
        
        screenshot_bytes = run_async(page.screenshot(type='jpeg', quality=quality))
        screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
        
        return jsonify({
            "success": True,
            "screenshot": screenshot_base64
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/stream/start', methods=['POST'])
def start_streaming():
    global streaming_active, stream_fps, stream_quality
    
    try:
        if not page:
            return jsonify({"success": False, "error": "Browser not started"})
        
        data = request.json or {}
        stream_fps = min(max(data.get('fps', 30), 1), 60)  # Limit FPS between 1-60
        stream_quality = min(max(data.get('quality', 80), 10), 100)  # Limit quality between 10-100
        
        if not streaming_active:
            streaming_active = True
            threading.Thread(target=screenshot_capture_thread, daemon=True).start()
        
        return jsonify({
            "success": True,
            "message": f"Streaming started at {stream_fps} FPS with quality {stream_quality}",
            "fps": stream_fps,
            "quality": stream_quality
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/stream/stop', methods=['POST'])
def stop_streaming():
    global streaming_active
    
    try:
        streaming_active = False
        return jsonify({
            "success": True,
            "message": "Streaming stopped"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/stream/settings', methods=['POST'])
def update_stream_settings():
    global stream_fps, stream_quality
    
    try:
        data = request.json or {}
        
        if 'fps' in data:
            stream_fps = min(max(data.get('fps'), 1), 60)  # Limit FPS between 1-60
            
        if 'quality' in data:
            stream_quality = min(max(data.get('quality'), 10), 100)  # Limit quality between 10-100
        
        return jsonify({
            "success": True,
            "message": f"Stream settings updated: {stream_fps} FPS, quality {stream_quality}",
            "fps": stream_fps,
            "quality": stream_quality
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/stream/mjpeg')
def mjpeg_stream():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/click/stream', methods=['POST'])
def click_on_stream():
    try:
        if not page:
            return jsonify({"success": False, "error": "Browser not started"})
        
        data = request.json or {}
        x = data.get('x', 0)
        y = data.get('y', 0)
        
        # Get the stream container dimensions
        container_width = data.get('containerWidth', viewport_width)
        container_height = data.get('containerHeight', viewport_height)
        
        # Calculate the scaling factor between the container and actual viewport
        scale_x = viewport_width / container_width
        scale_y = viewport_height / container_height
        
        # Calculate the actual coordinates in the browser viewport
        browser_x = x * scale_x
        browser_y = y * scale_y
        
        # Click at the calculated position
        run_async(page.mouse.click(browser_x, browser_y))
        
        return jsonify({
            "success": True,
            "message": f"Clicked at position ({browser_x}, {browser_y})",
            "x": browser_x,
            "y": browser_y
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

@app.route('/api/click', methods=['POST'])
def click_element():
    try:
        data = request.json
        selector = data.get('selector')
        
        if not page or not selector:
            return jsonify({"success": False, "error": "Browser not started or selector not provided"})
        
        run_async(page.click(selector))
        
        return jsonify({
            "success": True,
            "message": f"Clicked on {selector}"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/type', methods=['POST'])
def type_text():
    try:
        data = request.json
        selector = data.get('selector')
        text = data.get('text')
        
        if not page or not selector or not text:
            return jsonify({"success": False, "error": "Browser not started or missing parameters"})
        
        run_async(page.fill(selector, text))
        
        return jsonify({
            "success": True,
            "message": f"Typed text into {selector}"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Create an interactive HTML template
    with open('templates/interactive.html', 'w') as f:
        f.write("""<!DOCTYPE html>
<html>
<head>
    <title>Interactive Headless Browser</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 0; 
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            margin-top: 0;
        }
        .controls {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 20px;
        }
        .control-group {
            margin-bottom: 15px;
        }
        button {
            background-color: #4CAF50;
            border: none;
            color: white;
            padding: 8px 16px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 14px;
            margin: 4px 2px;
            cursor: pointer;
            border-radius: 4px;
        }
        button:hover {
            background-color: #45a049;
        }
        button:disabled {
            background-color: #cccccc;
            cursor: not-allowed;
        }
        button.danger {
            background-color: #f44336;
        }
        button.danger:hover {
            background-color: #d32f2f;
        }
        button.secondary {
            background-color: #2196F3;
        }
        button.secondary:hover {
            background-color: #0b7dda;
        }
        input[type="text"], input[type="number"] {
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        input[type="text"] {
            width: 300px;
        }
        input[type="number"] {
            width: 60px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        .stream-container {
            position: relative;
            margin-top: 20px;
            border: 1px solid #ddd;
            border-radius: 4px;
            overflow: hidden;
            background-color: #eee;
            min-height: 400px;
            cursor: pointer;
        }
        .stream-overlay {
            position: absolute;
            top: 10px;
            right: 10px;
            background-color: rgba(0,0,0,0.5);
            color: white;
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 12px;
        }
        .click-indicator {
            position: absolute;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background-color: rgba(255, 0, 0, 0.5);
            border: 2px solid red;
            transform: translate(-50%, -50%);
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.5s;
        }
        .stream-img {
            display: block;
            width: 100%;
        }
        .status {
            margin-top: 10px;
            padding: 10px;
            border-radius: 4px;
            background-color: #e8f5e9;
            color: #2e7d32;
        }
        .error {
            background-color: #ffebee;
            color: #c62828;
        }
        .hidden {
            display: none;
        }
        .flex {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .settings-panel {
            background-color: #f9f9f9;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 15px;
        }
        .interaction-panel {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 15px;
        }
        .click-mode-toggle {
            display: flex;
            align-items: center;
            margin-top: 10px;
        }
        .click-mode-toggle label {
            margin: 0 10px 0 0;
            font-weight: normal;
        }
        .toggle-switch {
            position: relative;
            display: inline-block;
            width: 60px;
            height: 34px;
        }
        .toggle-switch input {
            opacity: 0;
            width: 0;
            height: 0;
        }
        .toggle-slider {
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: #ccc;
            transition: .4s;
            border-radius: 34px;
        }
        .toggle-slider:before {
            position: absolute;
            content: "";
            height: 26px;
            width: 26px;
            left: 4px;
            bottom: 4px;
            background-color: white;
            transition: .4s;
            border-radius: 50%;
        }
        input:checked + .toggle-slider {
            background-color: #2196F3;
        }
        input:checked + .toggle-slider:before {
            transform: translateX(26px);
        }
        .mode-label {
            margin-left: 10px;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Interactive Headless Browser</h1>
        
        <div class="settings-panel">
            <div class="control-group">
                <button id="startBrowserBtn">Start Browser</button>
                <button id="startStreamBtn" disabled>Start Streaming</button>
                <button id="stopStreamBtn" class="danger" disabled>Stop Streaming</button>
            </div>
            
            <div class="control-group">
                <div class="flex">
                    <div>
                        <label for="urlInput">URL:</label>
                        <input type="text" id="urlInput" placeholder="https://example.com" value="https://example.com">
                    </div>
                    <button id="navigateBtn" disabled>Navigate</button>
                </div>
            </div>
            
            <div class="control-group">
                <div class="flex">
                    <div>
                        <label for="fpsInput">FPS:</label>
                        <input type="number" id="fpsInput" min="1" max="60" value="30">
                    </div>
                    <div>
                        <label for="qualityInput">Quality:</label>
                        <input type="number" id="qualityInput" min="10" max="100" value="80">
                    </div>
                    <button id="updateSettingsBtn" class="secondary" disabled>Update Settings</button>
                </div>
            </div>
            
            <div class="click-mode-toggle">
                <label for="clickModeToggle">Click Mode:</label>
                <label class="toggle-switch">
                    <input type="checkbox" id="clickModeToggle" checked>
                    <span class="toggle-slider"></span>
                </label>
                <span class="mode-label" id="clickModeLabel">Direct Click</span>
            </div>
        </div>
        
        <div class="stream-container" id="streamContainer">
            <div id="streamOverlay" class="stream-overlay hidden">
                FPS: <span id="currentFps">30</span> | Quality: <span id="currentQuality">80</span>
            </div>
            <div id="clickIndicator" class="click-indicator"></div>
            <img id="streamImg" class="stream-img hidden">
            <div id="placeholderText" style="padding: 20px; text-align: center; color: #666;">
                Start the browser and streaming to see live content here
            </div>
        </div>
        
        <div class="interaction-panel">
            <div>
                <label for="selectorInput">CSS Selector:</label>
                <input type="text" id="selectorInput" placeholder="button, input, .class, #id">
            </div>
            <button id="clickBtn" disabled>Click Element</button>
            
            <div>
                <label for="textInput">Text:</label>
                <input type="text" id="textInput" placeholder="Text to type">
            </div>
            <button id="typeBtn" disabled>Type Text</button>
            
            <div>
                <label for="jsInput">JavaScript:</label>
                <input type="text" id="jsInput" placeholder="document.title" value="document.title">
            </div>
            <button id="executeBtn" disabled>Execute</button>
        </div>
        
        <div id="statusMessage" class="status hidden"></div>
        <div id="clickCoordinates" style="margin-top: 10px; font-size: 12px; color: #666;"></div>
    </div>

    <script>
        // DOM Elements
        const startBrowserBtn = document.getElementById('startBrowserBtn');
        const startStreamBtn = document.getElementById('startStreamBtn');
        const stopStreamBtn = document.getElementById('stopStreamBtn');
        const navigateBtn = document.getElementById('navigateBtn');
        const updateSettingsBtn = document.getElementById('updateSettingsBtn');
        const urlInput = document.getElementById('urlInput');
        const fpsInput = document.getElementById('fpsInput');
        const qualityInput = document.getElementById('qualityInput');
        const streamContainer = document.getElementById('streamContainer');
        const streamImg = document.getElementById('streamImg');
        const placeholderText = document.getElementById('placeholderText');
        const streamOverlay = document.getElementById('streamOverlay');
        const currentFps = document.getElementById('currentFps');
        const currentQuality = document.getElementById('currentQuality');
        const statusMessage = document.getElementById('statusMessage');
        const selectorInput = document.getElementById('selectorInput');
        const textInput = document.getElementById('textInput');
        const jsInput = document.getElementById('jsInput');
        const clickBtn = document.getElementById('clickBtn');
        const typeBtn = document.getElementById('typeBtn');
        const executeBtn = document.getElementById('executeBtn');
        const clickModeToggle = document.getElementById('clickModeToggle');
        const clickModeLabel = document.getElementById('clickModeLabel');
        const clickIndicator = document.getElementById('clickIndicator');
        const clickCoordinates = document.getElementById('clickCoordinates');
        
        // State
        let browserStarted = false;
        let streamingActive = false;
        let directClickMode = true;
        
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
                showStatus(`Error: ${error.message}`, true);
                return { success: false, error: error.message };
            }
        }
        
        // Show status message
        function showStatus(message, isError = false) {
            statusMessage.textContent = message;
            statusMessage.className = isError ? 'status error' : 'status';
            statusMessage.classList.remove('hidden');
            
            // Auto-hide after 5 seconds
            setTimeout(() => {
                statusMessage.classList.add('hidden');
            }, 5000);
        }
        
        // Update button states
        function updateButtonStates() {
            startBrowserBtn.disabled = browserStarted;
            startStreamBtn.disabled = !browserStarted || streamingActive;
            stopStreamBtn.disabled = !streamingActive;
            navigateBtn.disabled = !browserStarted;
            updateSettingsBtn.disabled = !browserStarted;
            clickBtn.disabled = !browserStarted;
            typeBtn.disabled = !browserStarted;
            executeBtn.disabled = !browserStarted;
        }
        
        // Show click indicator
        function showClickIndicator(x, y) {
            clickIndicator.style.left = `${x}px`;
            clickIndicator.style.top = `${y}px`;
            clickIndicator.style.opacity = '1';
            
            setTimeout(() => {
                clickIndicator.style.opacity = '0';
            }, 500);
        }
        
        // Handle click on stream
        streamContainer.addEventListener('click', async (e) => {
            if (!streamingActive || !directClickMode) return;
            
            // Get click coordinates relative to the stream container
            const rect = streamContainer.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            // Show click indicator
            showClickIndicator(x, y);
            
            // Send click to the browser
            const containerWidth = streamContainer.clientWidth;
            const containerHeight = streamContainer.clientHeight;
            
            const result = await callApi('click/stream', {
                x: x,
                y: y,
                containerWidth: containerWidth,
                containerHeight: containerHeight
            });
            
            if (result.success) {
                clickCoordinates.textContent = `Clicked at: (${Math.round(result.x)}, ${Math.round(result.y)})`;
                showStatus(`Clicked at position (${Math.round(result.x)}, ${Math.round(result.y)})`);
            } else {
                showStatus(`Click failed: ${result.error}`, true);
            }
        });
        
        // Toggle click mode
        clickModeToggle.addEventListener('change', () => {
            directClickMode = clickModeToggle.checked;
            clickModeLabel.textContent = directClickMode ? 'Direct Click' : 'Selector Click';
            
            if (directClickMode) {
                streamContainer.style.cursor = 'pointer';
            } else {
                streamContainer.style.cursor = 'default';
            }
        });
        
        // Start browser
        startBrowserBtn.addEventListener('click', async () => {
            const result = await callApi('start');
            if (result.success) {
                browserStarted = true;
                showStatus('Browser started successfully');
                updateButtonStates();
            } else {
                showStatus(`Failed to start browser: ${result.error}`, true);
            }
        });
        
        // Navigate to URL
        navigateBtn.addEventListener('click', async () => {
            const url = urlInput.value;
            if (!url) {
                showStatus('Please enter a URL', true);
                return;
            }
            
            const result = await callApi('navigate', { url });
            if (result.success) {
                showStatus(`Navigated to ${result.url}`);
            } else {
                showStatus(`Navigation failed: ${result.error}`, true);
            }
        });
        
        // Start streaming
        startStreamBtn.addEventListener('click', async () => {
            const fps = parseInt(fpsInput.value) || 30;
            const quality = parseInt(qualityInput.value) || 80;
            
            const result = await callApi('stream/start', { fps, quality });
            if (result.success) {
                streamingActive = true;
                currentFps.textContent = result.fps;
                currentQuality.textContent = result.quality;
                streamOverlay.classList.remove('hidden');
                placeholderText.classList.add('hidden');
                
                // Start the MJPEG stream
                streamImg.src = '/api/stream/mjpeg';
                streamImg.classList.remove('hidden');
                
                showStatus(`Streaming started at ${result.fps} FPS`);
                updateButtonStates();
            } else {
                showStatus(`Failed to start streaming: ${result.error}`, true);
            }
        });
        
        // Stop streaming
        stopStreamBtn.addEventListener('click', async () => {
            const result = await callApi('stream/stop');
            if (result.success) {
                streamingActive = false;
                streamImg.classList.add('hidden');
                streamOverlay.classList.add('hidden');
                placeholderText.classList.remove('hidden');
                
                // Stop the stream by setting src to empty
                streamImg.src = '';
                
                showStatus('Streaming stopped');
                updateButtonStates();
            } else {
                showStatus(`Failed to stop streaming: ${result.error}`, true);
            }
        });
        
        // Update stream settings
        updateSettingsBtn.addEventListener('click', async () => {
            const fps = parseInt(fpsInput.value) || 30;
            const quality = parseInt(qualityInput.value) || 80;
            
            const result = await callApi('stream/settings', { fps, quality });
            if (result.success) {
                currentFps.textContent = result.fps;
                currentQuality.textContent = result.quality;
                showStatus(`Stream settings updated: ${result.fps} FPS, quality ${result.quality}`);
            } else {
                showStatus(`Failed to update settings: ${result.error}`, true);
            }
        });
        
        // Click element
        clickBtn.addEventListener('click', async () => {
            const selector = selectorInput.value;
            if (!selector) {
                showStatus('Please enter a CSS selector', true);
                return;
            }
            
            const result = await callApi('click', { selector });
            if (result.success) {
                showStatus(`Clicked on element: ${selector}`);
            } else {
                showStatus(`Failed to click element: ${result.error}`, true);
            }
        });
        
        // Type text
        typeBtn.addEventListener('click', async () => {
            const selector = selectorInput.value;
            const text = textInput.value;
            
            if (!selector) {
                showStatus('Please enter a CSS selector', true);
                return;
            }
            
            if (!text) {
                showStatus('Please enter text to type', true);
                return;
            }
            
            const result = await callApi('type', { selector, text });
            if (result.success) {
                showStatus(`Typed text into element: ${selector}`);
            } else {
                showStatus(`Failed to type text: ${result.error}`, true);
            }
        });
        
        // Execute JavaScript
        executeBtn.addEventListener('click', async () => {
            const script = jsInput.value;
            if (!script) {
                showStatus('Please enter JavaScript code', true);
                return;
            }
            
            const result = await callApi('execute', { script });
            if (result.success) {
                showStatus(`JavaScript executed. Result: ${JSON.stringify(result.result)}`);
            } else {
                showStatus(`Failed to execute JavaScript: ${result.error}`, true);
            }
        });
        
        // Initialize
        updateButtonStates();
        streamContainer.style.cursor = 'pointer';
    </script>
</body>
</html>""")
    
    # Run the app
    app.run(host='0.0.0.0', port=8083, debug=False, threaded=True)
