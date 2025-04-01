# Headless Browser Service Documentation

## Overview
This headless browser service provides a web-based interface for controlling a headless browser powered by Playwright. It allows you to navigate websites, take screenshots, extract content, interact with elements, and execute JavaScript code without needing a visible browser window.

## Accessing the Service
The headless browser service is now running and accessible at:

**URL:** http://8080-ik535ekmr6dzhapu09glc-5e719849.manus.computer

This is a temporary URL that will be available as long as the service is running.

## Features
- **Browser Control**: Start and stop the headless browser engine
- **Session Management**: Create and manage isolated browser sessions
- **Navigation**: Visit websites and control page loading behavior
- **Screenshots**: Capture full-page or viewport screenshots
- **Content Extraction**: Extract text and HTML content from pages
- **Element Interaction**: Click elements and type text using CSS selectors
- **JavaScript Execution**: Run custom JavaScript code in the browser context
- **Optimizations**: Special handling for complex and JavaScript-heavy websites

## Using the Web Interface
1. **Start the Browser**: Click the "Start Browser" button to initialize the browser engine
2. **Create a Session**: Configure viewport size and optimization options, then click "Create Session"
3. **Navigate to a Website**: Enter a URL in the navigation tab and click "Navigate"
4. **Interact with the Page**:
   - Take screenshots using the "Take Screenshot" button
   - Extract content using the "Get Content" button
   - Click elements by entering a CSS selector and clicking "Click"
   - Type text by entering a selector and text, then clicking "Type Text"
   - Execute JavaScript by entering code and clicking "Execute"

## API Endpoints
The service provides the following REST API endpoints for programmatic control:

### Browser Control
- `POST /api/browser/start`: Start the browser engine
- `POST /api/browser/stop`: Stop the browser engine

### Session Management
- `POST /api/session/create`: Create a new browser session
  - Parameters: `viewport`, `userAgent`, `optimize`, `blockResources`
- `POST /api/session/close`: Close a browser session
  - Parameters: `sessionId`

### Page Actions
- `POST /api/navigate`: Navigate to a URL
  - Parameters: `sessionId`, `url`, `waitUntil`, `timeout`
- `POST /api/screenshot`: Take a screenshot
  - Parameters: `sessionId`, `fullPage`
- `POST /api/content`: Get page content
  - Parameters: `sessionId`, `includeHtml`
- `POST /api/execute`: Execute JavaScript
  - Parameters: `sessionId`, `script`
- `POST /api/click`: Click an element
  - Parameters: `sessionId`, `selector`, `timeout`, `button`
- `POST /api/type`: Type text into an element
  - Parameters: `sessionId`, `selector`, `text`, `delay`
- `POST /api/element`: Get element text
  - Parameters: `sessionId`, `selector`

## API Usage Examples

### Python Example
```python
import requests
import json

# Base URL of the service
base_url = "http://8080-ik535ekmr6dzhapu09glc-5e719849.manus.computer"

# Start the browser
requests.post(f"{base_url}/api/browser/start")

# Create a session
session_response = requests.post(
    f"{base_url}/api/session/create",
    json={
        "viewport": {"width": 1280, "height": 800},
        "optimize": True
    }
)
session_data = session_response.json()
session_id = session_data["sessionId"]

# Navigate to a website
requests.post(
    f"{base_url}/api/navigate",
    json={
        "sessionId": session_id,
        "url": "https://example.com",
        "waitUntil": "networkidle"
    }
)

# Take a screenshot
screenshot_response = requests.post(
    f"{base_url}/api/screenshot",
    json={
        "sessionId": session_id,
        "fullPage": True
    }
)
screenshot_data = screenshot_response.json()
screenshot_base64 = screenshot_data["screenshot"]

# Get page content
content_response = requests.post(
    f"{base_url}/api/content",
    json={
        "sessionId": session_id,
        "includeHtml": True
    }
)
content_data = content_response.json()
text_content = content_data["text_content"]
html_content = content_data["html_content"]

# Close the session when done
requests.post(
    f"{base_url}/api/session/close",
    json={
        "sessionId": session_id
    }
)
```

### JavaScript/Node.js Example
```javascript
const fetch = require('node-fetch');

// Base URL of the service
const baseUrl = "http://8080-ik535ekmr6dzhapu09glc-5e719849.manus.computer";

async function runExample() {
    // Start the browser
    await fetch(`${baseUrl}/api/browser/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    });
    
    // Create a session
    const sessionResponse = await fetch(`${baseUrl}/api/session/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            viewport: { width: 1280, height: 800 },
            optimize: true
        })
    });
    const sessionData = await sessionResponse.json();
    const sessionId = sessionData.sessionId;
    
    // Navigate to a website
    await fetch(`${baseUrl}/api/navigate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            sessionId: sessionId,
            url: "https://example.com",
            waitUntil: "networkidle"
        })
    });
    
    // Execute JavaScript
    const jsResponse = await fetch(`${baseUrl}/api/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            sessionId: sessionId,
            script: "document.title"
        })
    });
    const jsResult = await jsResponse.json();
    console.log("Page title:", jsResult.result);
    
    // Close the session when done
    await fetch(`${baseUrl}/api/session/close`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            sessionId: sessionId
        })
    });
}

runExample().catch(console.error);
```

## Advanced Features

### Optimizations for Complex Websites
The service includes several optimizations for handling complex websites:

1. **Animation Disabling**: Reduces CPU usage by disabling animations
2. **Overlay Handling**: Automatically dismisses common overlays and popups
3. **Resource Blocking**: Optionally blocks unnecessary resources like fonts
4. **Performance Monitoring**: Tracks page load times and DOM ready times
5. **Memory Leak Detection**: Monitors for potential memory leaks
6. **Error Handling**: Catches unhandled promise rejections

### Custom Browser Configurations
When creating a session, you can customize:

- **Viewport Size**: Set custom width and height
- **User Agent**: Specify a custom user agent string
- **Resource Blocking**: Choose which resource types to block
- **Optimization Level**: Enable or disable optimizations

## Troubleshooting

### Common Issues
1. **Navigation Timeout**: Increase the timeout parameter when navigating to slow-loading sites
2. **Element Not Found**: Ensure your CSS selector is correct and the element is visible
3. **JavaScript Errors**: Check the console output for error messages
4. **Memory Usage**: Close unused sessions to free up memory

### Getting Help
If you encounter any issues or need assistance, please check the console output in the web interface for error messages.

## Technical Details
- **Backend**: Python with Flask and Playwright
- **Frontend**: HTML, CSS, and JavaScript
- **Browser Engine**: Chromium (via Playwright)

## Security Considerations
- This service is intended for development and testing purposes
- The exposed URL is temporary and will not persist after the service is stopped
- No authentication is implemented, so anyone with the URL can access the service
