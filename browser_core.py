#!/usr/bin/env python3
"""
Headless Browser Core Module
This module provides the core functionality for the headless browser service.
"""

import asyncio
import base64
import json
import os
from typing import Dict, List, Optional, Union

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

class HeadlessBrowser:
    """
    A class that provides headless browser functionality using Playwright.
    """
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.contexts: Dict[str, BrowserContext] = {}
        self.pages: Dict[str, Page] = {}
        self.default_viewport = {"width": 1280, "height": 800}
        self.browser_type = "chromium"  # Default browser type
        self.headless = True  # Default headless mode

    async def start(self, browser_type: str = "chromium", headless: bool = True) -> None:
        """
        Start the headless browser service.
        
        Args:
            browser_type: Type of browser to use ('chromium', 'firefox', or 'webkit')
            headless: Whether to run in headless mode
        """
        self.browser_type = browser_type
        self.headless = headless
        
        self.playwright = await async_playwright().start()
        browser_instance = getattr(self.playwright, browser_type)
        
        # Launch browser with optimized settings for headless operation
        self.browser = await browser_instance.launch(
            headless=headless,
            args=[
                '--disable-gpu',
                '--disable-dev-shm-usage',
                '--disable-setuid-sandbox',
                '--no-sandbox',
                '--disable-web-security',  # Disable CORS for easier API access
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-site-isolation-trials',
            ]
        )
        
        # Create a default context and page
        await self.create_context("default")
        await self.create_page("default", "default")
        
        print(f"Browser started: {browser_type} (headless: {headless})")

    async def stop(self) -> None:
        """Stop the browser service and clean up resources."""
        if self.browser:
            for context_id in list(self.contexts.keys()):
                await self.close_context(context_id)
            
            await self.browser.close()
            self.browser = None
        
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
        
        print("Browser stopped")

    async def create_context(self, context_id: str, 
                           viewport: Optional[Dict[str, int]] = None,
                           user_agent: Optional[str] = None) -> None:
        """
        Create a new browser context with the given ID.
        
        Args:
            context_id: Unique identifier for the context
            viewport: Viewport dimensions (width and height)
            user_agent: Custom user agent string
        """
        if not self.browser:
            raise RuntimeError("Browser not started")
        
        if context_id in self.contexts:
            await self.close_context(context_id)
        
        context_options = {}
        
        if viewport:
            context_options["viewport"] = viewport
        else:
            context_options["viewport"] = self.default_viewport
            
        if user_agent:
            context_options["user_agent"] = user_agent
        
        # Add additional options for better performance and compatibility
        context_options.update({
            "ignore_https_errors": True,
            "java_script_enabled": True,
            "bypass_csp": True,  # Bypass Content Security Policy for better compatibility
        })
        
        self.contexts[context_id] = await self.browser.new_context(**context_options)
        print(f"Created context: {context_id}")

    async def close_context(self, context_id: str) -> None:
        """
        Close a browser context and all its pages.
        
        Args:
            context_id: ID of the context to close
        """
        if context_id in self.contexts:
            # Close all pages in this context
            page_ids = [pid for pid, page in self.pages.items() 
                      if page.context == self.contexts[context_id]]
            
            for page_id in page_ids:
                if page_id in self.pages:
                    del self.pages[page_id]
            
            # Close the context
            await self.contexts[context_id].close()
            del self.contexts[context_id]
            print(f"Closed context: {context_id}")

    async def create_page(self, page_id: str, context_id: str) -> None:
        """
        Create a new page with the given ID in the specified context.
        
        Args:
            page_id: Unique identifier for the page
            context_id: ID of the context to create the page in
        """
        if context_id not in self.contexts:
            raise ValueError(f"Context {context_id} does not exist")
        
        if page_id in self.pages:
            await self.close_page(page_id)
        
        self.pages[page_id] = await self.contexts[context_id].new_page()
        
        # Set up page event handlers for better monitoring
        self.pages[page_id].on("console", lambda msg: print(f"Console {page_id}: {msg.text}"))
        self.pages[page_id].on("pageerror", lambda err: print(f"Error {page_id}: {err}"))
        
        print(f"Created page: {page_id} in context: {context_id}")

    async def close_page(self, page_id: str) -> None:
        """
        Close a page.
        
        Args:
            page_id: ID of the page to close
        """
        if page_id in self.pages:
            await self.pages[page_id].close()
            del self.pages[page_id]
            print(f"Closed page: {page_id}")

    async def navigate(self, page_id: str, url: str, 
                     wait_until: str = "load", 
                     timeout: int = 30000) -> Dict:
        """
        Navigate to a URL in the specified page.
        
        Args:
            page_id: ID of the page to navigate
            url: URL to navigate to
            wait_until: Navigation wait condition ('load', 'domcontentloaded', 'networkidle')
            timeout: Navigation timeout in milliseconds
            
        Returns:
            Dict containing page information after navigation
        """
        if page_id not in self.pages:
            raise ValueError(f"Page {page_id} does not exist")
        
        page = self.pages[page_id]
        
        try:
            response = await page.goto(url, wait_until=wait_until, timeout=timeout)
            status = response.status if response else None
            
            # Wait a bit for JavaScript to execute
            await page.wait_for_timeout(500)
            
            title = await page.title()
            content = await page.content()
            
            return {
                "success": True,
                "url": page.url,
                "title": title,
                "status": status,
                "content_length": len(content)
            }
        except Exception as e:
            return {
                "success": False,
                "url": url,
                "error": str(e)
            }

    async def screenshot(self, page_id: str, 
                       full_page: bool = True,
                       path: Optional[str] = None) -> Optional[str]:
        """
        Take a screenshot of the specified page.
        
        Args:
            page_id: ID of the page to screenshot
            full_page: Whether to capture the full page or just the viewport
            path: Path to save the screenshot to (optional)
            
        Returns:
            Base64-encoded screenshot data if path is None, otherwise None
        """
        if page_id not in self.pages:
            raise ValueError(f"Page {page_id} does not exist")
        
        page = self.pages[page_id]
        
        screenshot_options = {
            "full_page": full_page,
            "type": "jpeg",
            "quality": 80
        }
        
        if path:
            screenshot_options["path"] = path
            await page.screenshot(**screenshot_options)
            return None
        else:
            screenshot_bytes = await page.screenshot(**screenshot_options)
            return base64.b64encode(screenshot_bytes).decode('utf-8')

    async def execute_javascript(self, page_id: str, script: str) -> Dict:
        """
        Execute JavaScript code in the specified page.
        
        Args:
            page_id: ID of the page to execute the script in
            script: JavaScript code to execute
            
        Returns:
            Dict containing the result of the script execution
        """
        if page_id not in self.pages:
            raise ValueError(f"Page {page_id} does not exist")
        
        page = self.pages[page_id]
        
        try:
            result = await page.evaluate(script)
            return {
                "success": True,
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def click(self, page_id: str, selector: str, 
                  timeout: int = 5000,
                  button: str = "left") -> Dict:
        """
        Click on an element in the specified page.
        
        Args:
            page_id: ID of the page to click in
            selector: CSS selector of the element to click
            timeout: Timeout in milliseconds
            button: Mouse button to use ('left', 'right', or 'middle')
            
        Returns:
            Dict indicating success or failure
        """
        if page_id not in self.pages:
            raise ValueError(f"Page {page_id} does not exist")
        
        page = self.pages[page_id]
        
        try:
            await page.click(selector, timeout=timeout, button=button)
            return {"success": True}
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def type_text(self, page_id: str, selector: str, 
                      text: str, delay: int = 50) -> Dict:
        """
        Type text into an element in the specified page.
        
        Args:
            page_id: ID of the page to type in
            selector: CSS selector of the element to type into
            text: Text to type
            delay: Delay between keystrokes in milliseconds
            
        Returns:
            Dict indicating success or failure
        """
        if page_id not in self.pages:
            raise ValueError(f"Page {page_id} does not exist")
        
        page = self.pages[page_id]
        
        try:
            await page.fill(selector, text, timeout=5000)
            return {"success": True}
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def get_page_content(self, page_id: str, 
                             include_html: bool = False) -> Dict:
        """
        Get the content of the specified page.
        
        Args:
            page_id: ID of the page to get content from
            include_html: Whether to include the full HTML content
            
        Returns:
            Dict containing page information and content
        """
        if page_id not in self.pages:
            raise ValueError(f"Page {page_id} does not exist")
        
        page = self.pages[page_id]
        
        try:
            title = await page.title()
            url = page.url
            
            # Extract text content
            text_content = await page.evaluate("""() => {
                return document.body.innerText;
            }""")
            
            result = {
                "success": True,
                "url": url,
                "title": title,
                "text_content": text_content
            }
            
            if include_html:
                html_content = await page.content()
                result["html_content"] = html_content
                
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def get_element_text(self, page_id: str, selector: str) -> Dict:
        """
        Get the text content of an element in the specified page.
        
        Args:
            page_id: ID of the page to get element from
            selector: CSS selector of the element
            
        Returns:
            Dict containing the element's text content
        """
        if page_id not in self.pages:
            raise ValueError(f"Page {page_id} does not exist")
        
        page = self.pages[page_id]
        
        try:
            text = await page.text_content(selector)
            return {
                "success": True,
                "text": text
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

# Example usage
async def example_usage():
    browser = HeadlessBrowser()
    await browser.start()
    
    try:
        await browser.navigate("default", "https://example.com")
        screenshot = await browser.screenshot("default")
        content = await browser.get_page_content("default")
        print(f"Page title: {content.get('title')}")
    finally:
        await browser.stop()

if __name__ == "__main__":
    asyncio.run(example_usage())
