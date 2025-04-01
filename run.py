#!/usr/bin/env python3
"""
Headless Browser Service Launcher
This script starts the headless browser service and exposes it on a specified port.
"""

import os
import sys
import argparse
from app import run_server

def main():
    """Main entry point for the headless browser service."""
    parser = argparse.ArgumentParser(description='Start the headless browser service')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to listen on')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    print(f"Starting headless browser service on {args.host}:{args.port}")
    print("Press Ctrl+C to stop the service")
    
    # Run the server
    run_server(host=args.host, port=args.port)

if __name__ == '__main__':
    main()
