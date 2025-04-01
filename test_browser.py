#!/usr/bin/env python3
"""
Headless Browser Test Script
This script tests the functionality of the headless browser core module.
"""

import asyncio
import os
import sys
from browser_core import HeadlessBrowser

async def test_browser():
    """Test the headless browser functionality."""
    print("Starting headless browser test...")
    
    # Create browser instance
    browser = HeadlessBrowser()
    
    try:
        # Start browser
        print("Starting browser...")
        await browser.start(headless=True)
        
        # Test navigation
        print("\nTesting navigation...")
        result = await browser.navigate("default", "https://example.com")
        print(f"Navigation result: {result}")
        
        # Test screenshot
        print("\nTesting screenshot...")
        screenshots_dir = os.path.join(os.getcwd(), "screenshots")
        os.makedirs(screenshots_dir, exist_ok=True)
        screenshot_path = os.path.join(screenshots_dir, "example_screenshot.jpg")
        await browser.screenshot("default", path=screenshot_path)
        print(f"Screenshot saved to: {screenshot_path}")
        
        # Test JavaScript execution
        print("\nTesting JavaScript execution...")
        js_result = await browser.execute_javascript("default", "document.title")
        print(f"JavaScript result: {js_result}")
        
        # Test content extraction
        print("\nTesting content extraction...")
        content = await browser.get_page_content("default")
        print(f"Page title: {content.get('title')}")
        print(f"Text content sample: {content.get('text_content')[:100]}...")
        
        # Test multiple contexts and pages
        print("\nTesting multiple contexts and pages...")
        await browser.create_context("mobile", viewport={"width": 375, "height": 667})
        await browser.create_page("mobile_page", "mobile")
        
        mobile_result = await browser.navigate("mobile_page", "https://example.com")
        print(f"Mobile navigation result: {mobile_result}")
        
        mobile_screenshot_path = os.path.join(screenshots_dir, "mobile_screenshot.jpg")
        await browser.screenshot("mobile_page", path=mobile_screenshot_path)
        print(f"Mobile screenshot saved to: {mobile_screenshot_path}")
        
        # Test element interaction
        print("\nTesting element interaction...")
        await browser.navigate("default", "https://example.com")
        
        # Get element text
        element_text = await browser.get_element_text("default", "h1")
        print(f"Element text: {element_text}")
        
        print("\nAll tests completed successfully!")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        raise
    finally:
        # Stop browser
        print("\nStopping browser...")
        await browser.stop()

if __name__ == "__main__":
    asyncio.run(test_browser())
