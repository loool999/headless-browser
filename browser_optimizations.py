#!/usr/bin/env python3
"""
Headless Browser Optimizations Module
This module provides optimizations for the headless browser to handle complex websites.
"""

import asyncio
import json
import os
import time
from typing import Dict, List, Optional, Union

class BrowserOptimizations:
    """
    A class that provides optimizations for the headless browser.
    """
    
    @staticmethod
    async def optimize_page_for_complex_sites(page):
        """
        Apply optimizations to a page for handling complex websites.
        
        Args:
            page: Playwright page object
        """
        # Set default timeout to a higher value for complex sites
        page.set_default_timeout(60000)
        
        # Inject performance optimization script
        await page.add_init_script("""
            // Disable animations for better performance
            if (typeof document !== 'undefined') {
                const style = document.createElement('style');
                style.type = 'text/css';
                style.innerHTML = `
                    * {
                        animation-duration: 0.001s !important;
                        transition-duration: 0.001s !important;
                    }
                `;
                document.head.appendChild(style);
            }
        """)
        
        # Add script to handle common overlay/popup scenarios
        await page.add_init_script("""
            // Auto-dismiss common overlays and popups
            if (typeof window !== 'undefined') {
                window.addEventListener('load', () => {
                    // Function to remove common overlay elements
                    const removeOverlays = () => {
                        // Common selectors for overlays, cookie notices, etc.
                        const overlaySelectors = [
                            '[class*="cookie"]',
                            '[class*="popup"]',
                            '[class*="modal"]',
                            '[class*="overlay"]',
                            '[id*="cookie"]',
                            '[id*="popup"]',
                            '[id*="modal"]',
                            '[id*="overlay"]'
                        ];
                        
                        overlaySelectors.forEach(selector => {
                            document.querySelectorAll(selector).forEach(el => {
                                // Only remove if it appears to be an overlay
                                if (el.style.position === 'fixed' || 
                                    el.style.position === 'absolute' ||
                                    window.getComputedStyle(el).position === 'fixed' ||
                                    window.getComputedStyle(el).position === 'absolute') {
                                    el.remove();
                                }
                            });
                        });
                        
                        // Remove fixed/hidden body styles that prevent scrolling
                        if (document.body.style.overflow === 'hidden') {
                            document.body.style.overflow = 'auto';
                        }
                    };
                    
                    // Run initially and then periodically
                    removeOverlays();
                    setInterval(removeOverlays, 2000);
                });
            }
        """)
        
        return page
    
    @staticmethod
    async def setup_request_interception(page, block_resources=None):
        """
        Set up request interception to block unnecessary resources.
        
        Args:
            page: Playwright page object
            block_resources: List of resource types to block (e.g., ['image', 'font', 'media'])
        """
        if block_resources is None:
            block_resources = []
            
        # Set up route handler to block specified resource types
        await page.route('**/*', lambda route, request: 
            route.abort() if request.resource_type in block_resources else route.continue_()
        )
        
        return page
    
    @staticmethod
    async def inject_performance_monitoring(page):
        """
        Inject performance monitoring script into the page.
        
        Args:
            page: Playwright page object
        """
        # Add performance monitoring
        await page.add_init_script("""
            // Performance monitoring
            if (typeof window !== 'undefined' && window.performance) {
                window.addEventListener('load', () => {
                    setTimeout(() => {
                        const perfData = window.performance.timing;
                        const pageLoadTime = perfData.loadEventEnd - perfData.navigationStart;
                        const domReadyTime = perfData.domComplete - perfData.domLoading;
                        
                        console.log('Performance metrics:');
                        console.log(`Page load time: ${pageLoadTime}ms`);
                        console.log(`DOM ready time: ${domReadyTime}ms`);
                        
                        // Store metrics for later retrieval
                        window.__performanceMetrics = {
                            pageLoadTime,
                            domReadyTime,
                            timestamp: Date.now()
                        };
                    }, 0);
                });
            }
        """)
        
        return page
    
    @staticmethod
    async def optimize_for_javascript_heavy_sites(page):
        """
        Apply optimizations for JavaScript-heavy sites.
        
        Args:
            page: Playwright page object
        """
        # Increase JavaScript heap size
        await page.context.add_init_script("""
            // Attempt to increase memory limits where possible
            if (typeof window !== 'undefined' && window.performance) {
                try {
                    // Force garbage collection if exposed (Chrome DevTools only)
                    if (window.gc) {
                        window.gc();
                    }
                } catch (e) {
                    console.log('GC not available');
                }
            }
        """)
        
        # Add error handling for unhandled promise rejections
        await page.add_init_script("""
            // Catch unhandled promise rejections
            if (typeof window !== 'undefined') {
                window.addEventListener('unhandledrejection', event => {
                    console.warn('Unhandled promise rejection:', event.reason);
                    // Prevent the default handling (which would log to console)
                    event.preventDefault();
                });
            }
        """)
        
        # Monitor for memory leaks
        await page.add_init_script("""
            // Basic memory leak detection
            if (typeof window !== 'undefined' && window.performance && window.performance.memory) {
                const memoryUsage = [];
                const checkMemory = () => {
                    const memory = window.performance.memory;
                    memoryUsage.push({
                        usedJSHeapSize: memory.usedJSHeapSize,
                        totalJSHeapSize: memory.totalJSHeapSize,
                        timestamp: Date.now()
                    });
                    
                    // Keep only last 10 measurements
                    if (memoryUsage.length > 10) {
                        memoryUsage.shift();
                    }
                    
                    // Check for continuous growth (potential memory leak)
                    if (memoryUsage.length >= 5) {
                        const allIncreasing = memoryUsage.every((m, i, arr) => 
                            i === 0 || m.usedJSHeapSize >= arr[i-1].usedJSHeapSize
                        );
                        
                        if (allIncreasing) {
                            console.warn('Potential memory leak detected: continuously increasing heap size');
                        }
                    }
                };
                
                // Check memory usage periodically
                setInterval(checkMemory, 5000);
            }
        """)
        
        return page
    
    @staticmethod
    async def setup_viewport_optimization(page, viewport=None):
        """
        Set up viewport optimization for better rendering.
        
        Args:
            page: Playwright page object
            viewport: Custom viewport dimensions
        """
        if viewport:
            await page.set_viewport_size(viewport)
        
        # Add high DPI support
        await page.add_init_script("""
            // Optimize for high DPI displays
            if (typeof document !== 'undefined') {
                const meta = document.createElement('meta');
                meta.setAttribute('name', 'viewport');
                meta.setAttribute('content', 'width=device-width, initial-scale=1, maximum-scale=1');
                document.head.appendChild(meta);
            }
        """)
        
        return page
    
    @staticmethod
    async def apply_all_optimizations(page, options=None):
        """
        Apply all optimizations to a page.
        
        Args:
            page: Playwright page object
            options: Dictionary of optimization options
                - block_resources: List of resource types to block
                - viewport: Custom viewport dimensions
        """
        if options is None:
            options = {}
            
        # Apply all optimizations
        await BrowserOptimizations.optimize_page_for_complex_sites(page)
        await BrowserOptimizations.setup_request_interception(
            page, options.get('block_resources', [])
        )
        await BrowserOptimizations.inject_performance_monitoring(page)
        await BrowserOptimizations.optimize_for_javascript_heavy_sites(page)
        await BrowserOptimizations.setup_viewport_optimization(
            page, options.get('viewport', None)
        )
        
        return page
