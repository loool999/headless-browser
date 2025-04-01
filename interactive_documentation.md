# Interactive Headless Browser Documentation

## Overview
This documentation covers the new interactive headless browser service with click-on-stream functionality. This enhanced version allows you to directly click on the live stream image, with your clicks being translated to the actual browser viewport.

## Accessing the Interactive Service
The interactive headless browser service is now running and accessible at:

**URL:** http://8083-ik535ekmr6dzhapu09glc-5e719849.manus.computer

This is a temporary URL that will be available as long as the service is running.

## New Features
- **Direct Click-on-Stream**: Click directly on the stream image to interact with web pages
- **Visual Click Indicator**: See where your clicks are registered with a visual indicator
- **Click Mode Toggle**: Switch between direct click mode and selector-based clicking
- **Coordinate Translation**: Automatic scaling between stream container and browser viewport
- **Real-time Feedback**: Immediate visual feedback of your interactions

## Using the Interactive Interface

### Getting Started
1. **Start the Browser**: Click the "Start Browser" button to initialize the browser engine
2. **Start Streaming**: Click the "Start Streaming" button to begin the real-time stream
3. **Navigate to a Website**: Enter a URL in the input field and click "Navigate"
4. **Interact Directly**: Click anywhere on the stream to interact with the web page

### Click Modes
- **Direct Click Mode** (default): Click directly on the stream to interact with the page
- **Selector Click Mode**: Use CSS selectors to target specific elements
- **Toggle**: Use the "Click Mode" toggle switch to change between modes

### Interaction Methods
- **Direct Clicking**: Simply click on any part of the stream image
- **Selector-based Clicking**: Enter a CSS selector and click the "Click Element" button
- **Text Input**: Enter a selector and text, then click the "Type Text" button
- **JavaScript Execution**: Enter JavaScript code and click "Execute" to run it on the page

## API Endpoints

### Browser Control
- `POST /api/start`: Start the browser engine

### Navigation
- `POST /api/navigate`: Navigate to a URL
  - Parameters: `url` (string)

### Streaming Control
- `POST /api/stream/start`: Start the screenshot stream
  - Parameters: `fps` (number, 1-60), `quality` (number, 10-100)
- `POST /api/stream/stop`: Stop the screenshot stream
- `POST /api/stream/settings`: Update stream settings
  - Parameters: `fps` (number, 1-60), `quality` (number, 10-100)
- `GET /api/stream/mjpeg`: Motion JPEG stream endpoint (access directly in img tag)

### Interactive Click
- `POST /api/click/stream`: Click at coordinates on the stream
  - Parameters: 
    - `x` (number): X coordinate on the stream container
    - `y` (number): Y coordinate on the stream container
    - `containerWidth` (number): Width of the stream container
    - `containerHeight` (number): Height of the stream container

### Page Interaction
- `POST /api/click`: Click an element using a CSS selector
  - Parameters: `selector` (string)
- `POST /api/type`: Type text into an element
  - Parameters: `selector` (string), `text` (string)
- `POST /api/execute`: Execute JavaScript
  - Parameters: `script` (string)
- `POST /api/content`: Get page content
  - Returns: `title`, `text`, `html`
- `POST /api/screenshot`: Take a single screenshot
  - Parameters: `quality` (number, 10-100)
  - Returns: Base64-encoded JPEG image

## API Usage Examples

### Python Example with Interactive Clicking
```python
import requests
import json
import time
import cv2
import numpy as np
import base64
from io import BytesIO
from PIL import Image

# Base URL of the service
base_url = "http://8083-ik535ekmr6dzhapu09glc-5e719849.manus.computer"

# Start the browser
requests.post(f"{base_url}/api/start")

# Navigate to a website
requests.post(
    f"{base_url}/api/navigate",
    json={"url": "https://example.com"}
)

# Start streaming with 40 FPS and 80% quality
requests.post(
    f"{base_url}/api/stream/start",
    json={"fps": 40, "quality": 80}
)

# Click at specific coordinates on the stream
def click_at_coordinates(x, y, container_width=1280, container_height=720):
    response = requests.post(
        f"{base_url}/api/click/stream",
        json={
            "x": x,
            "y": y,
            "containerWidth": container_width,
            "containerHeight": container_height
        }
    )
    return response.json()

# Example: Click at the center of the stream
result = click_at_coordinates(640, 360)
print(f"Clicked at browser coordinates: ({result['x']}, {result['y']})")

# Stop streaming when done
requests.post(f"{base_url}/api/stream/stop")
```

### JavaScript/HTML Example with Interactive Clicking
```html
<!DOCTYPE html>
<html>
<head>
    <title>Interactive Headless Browser Client</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .stream-container { 
            position: relative;
            max-width: 1200px; 
            margin: 0 auto;
            border: 1px solid #ddd;
            cursor: pointer;
        }
        .controls {
            margin: 20px 0;
        }
        button {
            padding: 8px 16px;
            margin-right: 10px;
        }
        input {
            padding: 8px;
            width: 300px;
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
    </style>
</head>
<body>
    <h1>Interactive Headless Browser Client</h1>
    
    <div class="controls">
        <button id="startBtn">Start Browser</button>
        <button id="streamBtn">Start Streaming</button>
        <input id="urlInput" type="text" placeholder="https://example.com" value="https://example.com">
        <button id="navigateBtn">Navigate</button>
    </div>
    
    <div class="stream-container" id="streamContainer">
        <div id="clickIndicator" class="click-indicator"></div>
        <img id="streamImg" width="100%" src="">
    </div>
    
    <div id="clickCoordinates" style="margin-top: 10px;"></div>
    
    <script>
        const baseUrl = "http://8083-ik535ekmr6dzhapu09glc-5e719849.manus.computer";
        const startBtn = document.getElementById('startBtn');
        const streamBtn = document.getElementById('streamBtn');
        const urlInput = document.getElementById('urlInput');
        const navigateBtn = document.getElementById('navigateBtn');
        const streamImg = document.getElementById('streamImg');
        const streamContainer = document.getElementById('streamContainer');
        const clickIndicator = document.getElementById('clickIndicator');
        const clickCoordinates = document.getElementById('clickCoordinates');
        
        let streaming = false;
        
        async function callApi(endpoint, data = {}) {
            const response = await fetch(`${baseUrl}/api/${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            return await response.json();
        }
        
        function showClickIndicator(x, y) {
            clickIndicator.style.left = `${x}px`;
            clickIndicator.style.top = `${y}px`;
            clickIndicator.style.opacity = '1';
            
            setTimeout(() => {
                clickIndicator.style.opacity = '0';
            }, 500);
        }
        
        startBtn.addEventListener('click', async () => {
            await callApi('start');
            alert('Browser started');
        });
        
        streamBtn.addEventListener('click', () => {
            if (!streaming) {
                streamImg.src = `${baseUrl}/api/stream/mjpeg`;
                streamBtn.textContent = 'Stop Streaming';
                streaming = true;
            } else {
                streamImg.src = '';
                streamBtn.textContent = 'Start Streaming';
                streaming = false;
                callApi('stream/stop');
            }
        });
        
        navigateBtn.addEventListener('click', async () => {
            const url = urlInput.value;
            await callApi('navigate', { url });
        });
        
        streamContainer.addEventListener('click', async (e) => {
            if (!streaming) return;
            
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
            }
        });
    </script>
</body>
</html>
```

## Performance Considerations

### Optimizing Interactive Performance
- **Lower FPS for Better Responsiveness**: Reduce the FPS (e.g., to 20-30) to improve click responsiveness
- **Adjust Quality**: Lower the JPEG quality (e.g., to 70) to reduce latency between clicks and visual feedback
- **Browser Resources**: The headless browser uses significant CPU and memory resources, especially with interactive features
- **Network Latency**: Lower latency connections will provide a more responsive interactive experience

### Recommended Settings for Interactive Use
- **Balanced Interactivity**: 30 FPS with 70% quality
- **Responsive Clicking**: 20 FPS with 80% quality
- **Resource-Constrained**: 15 FPS with 60% quality

## Technical Details
- **Backend**: Python with Flask, Playwright, and asyncio
- **Streaming Format**: Motion JPEG (MJPEG) for broad compatibility
- **Coordinate Translation**: Automatic scaling between stream container and browser viewport
- **Threading**: Dedicated thread for screenshot capture with thread-safe access
- **Browser Engine**: Chromium (via Playwright)

## Troubleshooting

### Common Issues
1. **Click Not Registering**: Ensure the browser and streaming are started before attempting to click
2. **Click Offset**: If clicks seem offset, try refreshing the page or restarting the stream
3. **High Latency**: Reduce FPS and quality settings to improve responsiveness
4. **Browser Crashes**: Some websites with heavy animations or WebGL content may cause stability issues

### Getting Help
If you encounter any issues or need assistance, please check the status messages in the web interface for error details.

## Security Considerations
- This service is intended for development and testing purposes
- The exposed URL is temporary and will not persist after the service is stopped
- No authentication is implemented, so anyone with the URL can access the service
