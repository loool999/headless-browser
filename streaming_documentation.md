# High FPS Headless Browser Streaming Documentation

## Overview
This documentation covers the new high frame rate screenshot streaming feature added to the headless browser service. This feature allows you to view real-time updates of the browser content at up to 40 FPS (frames per second) using Motion JPEG streaming.

## Accessing the Streaming Service
The high FPS streaming headless browser service is now running and accessible at:

**URL:** http://8082-ik535ekmr6dzhapu09glc-5e719849.manus.computer

This is a temporary URL that will be available as long as the service is running.

## Features
- **Real-time Streaming**: View browser content in real-time with configurable frame rates up to 60 FPS
- **Motion JPEG Format**: Efficient streaming using MJPEG format for smooth visual updates
- **Adjustable Quality**: Configure JPEG quality to balance between image quality and performance
- **Interactive Controls**: Click elements and type text while watching real-time updates
- **JavaScript Execution**: Run custom JavaScript code and see immediate results
- **Responsive Design**: User-friendly interface that works on various screen sizes

## Using the Streaming Interface

### Getting Started
1. **Start the Browser**: Click the "Start Browser" button to initialize the browser engine
2. **Start Streaming**: Click the "Start Streaming" button to begin the real-time stream
3. **Navigate to a Website**: Enter a URL in the input field and click "Navigate"

### Streaming Controls
- **FPS Setting**: Adjust the frames per second (1-60) to control stream smoothness
- **Quality Setting**: Adjust the JPEG quality (10-100) to balance between image quality and performance
- **Update Settings**: Apply new FPS and quality settings while streaming
- **Stop Streaming**: Stop the stream when no longer needed to save resources

### Interacting with Pages
- **Click Elements**: Enter a CSS selector and click the "Click Element" button
- **Type Text**: Enter a selector and text, then click the "Type Text" button
- **Execute JavaScript**: Enter JavaScript code and click "Execute" to run it on the page

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

### Page Interaction
- `POST /api/click`: Click an element
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

### Python Example
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
base_url = "http://8082-ik535ekmr6dzhapu09glc-5e719849.manus.computer"

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

# To display the stream using OpenCV:
def display_stream():
    # Open the MJPEG stream
    stream = cv2.VideoCapture(f"{base_url}/api/stream/mjpeg")
    
    while True:
        ret, frame = stream.read()
        if not ret:
            break
            
        cv2.imshow('Headless Browser Stream', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    stream.release()
    cv2.destroyAllWindows()

# To interact with the page while streaming:
def click_element(selector):
    requests.post(
        f"{base_url}/api/click",
        json={"selector": selector}
    )

def type_text(selector, text):
    requests.post(
        f"{base_url}/api/type",
        json={"selector": selector, "text": text}
    )

def execute_js(script):
    response = requests.post(
        f"{base_url}/api/execute",
        json={"script": script}
    )
    return response.json()["result"]

# Stop streaming when done
def stop_streaming():
    requests.post(f"{base_url}/api/stream/stop")
```

### JavaScript/HTML Example
```html
<!DOCTYPE html>
<html>
<head>
    <title>Headless Browser Stream Viewer</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .stream-container { 
            max-width: 1200px; 
            margin: 0 auto;
            border: 1px solid #ddd;
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
    </style>
</head>
<body>
    <h1>Headless Browser Stream Viewer</h1>
    
    <div class="controls">
        <button id="startBtn">Start Browser</button>
        <button id="streamBtn">Start Streaming</button>
        <input id="urlInput" type="text" placeholder="https://example.com" value="https://example.com">
        <button id="navigateBtn">Navigate</button>
    </div>
    
    <div class="stream-container">
        <img id="streamImg" width="100%" src="">
    </div>
    
    <script>
        const baseUrl = "http://8082-ik535ekmr6dzhapu09glc-5e719849.manus.computer";
        const startBtn = document.getElementById('startBtn');
        const streamBtn = document.getElementById('streamBtn');
        const urlInput = document.getElementById('urlInput');
        const navigateBtn = document.getElementById('navigateBtn');
        const streamImg = document.getElementById('streamImg');
        
        let streaming = false;
        
        async function callApi(endpoint, data = {}) {
            const response = await fetch(`${baseUrl}/api/${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            return await response.json();
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
    </script>
</body>
</html>
```

## Performance Considerations

### Optimizing Stream Performance
- **Lower FPS for Complex Pages**: Reduce the FPS (e.g., to 15-20) when viewing complex, resource-intensive websites
- **Adjust Quality**: Lower the JPEG quality (e.g., to 50-70) to reduce bandwidth usage and improve performance
- **Browser Resources**: The headless browser uses significant CPU and memory resources, especially at high frame rates
- **Network Bandwidth**: High FPS streaming can consume substantial bandwidth, especially at high quality settings

### Recommended Settings
- **Smooth Animation**: 30-40 FPS with 70-80% quality
- **Balanced Performance**: 20 FPS with 70% quality
- **Resource-Constrained**: 10 FPS with 50% quality

## Technical Details
- **Backend**: Python with Flask, Playwright, and asyncio
- **Streaming Format**: Motion JPEG (MJPEG) for broad compatibility
- **Threading**: Dedicated thread for screenshot capture to maintain target FPS
- **Browser Engine**: Chromium (via Playwright)

## Troubleshooting

### Common Issues
1. **Stream Not Starting**: Ensure the browser is started before attempting to start the stream
2. **Low Frame Rate**: Check CPU usage; lower the quality setting if the server is struggling to maintain the target FPS
3. **High Latency**: Reduce FPS and quality settings to improve responsiveness
4. **Browser Crashes**: Some websites with heavy animations or WebGL content may cause stability issues

### Getting Help
If you encounter any issues or need assistance, please check the console output in the web interface for error messages.

## Security Considerations
- This service is intended for development and testing purposes
- The exposed URL is temporary and will not persist after the service is stopped
- No authentication is implemented, so anyone with the URL can access the service
