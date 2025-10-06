#!/usr/bin/env python3
"""
Authentication helper script for SoundHash.
Provides a simple interface for OAuth authentication setup.
"""

import sys
import os
import time
import webbrowser
import requests
from urllib.parse import urljoin

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_auth_server():
    """Check if authentication server is running"""
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        return response.status_code == 200
    except:
        return False

def check_auth_status():
    """Check current authentication status"""
    try:
        response = requests.get("http://localhost:8000/auth/status", timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def start_twitter_auth():
    """Start Twitter OAuth flow"""
    print("🐦 Starting Twitter authentication...")
    print("Opening browser for Twitter OAuth...")
    
    auth_url = "http://localhost:8000/auth/twitter"
    webbrowser.open(auth_url)
    
    print(f"If the browser doesn't open automatically, visit: {auth_url}")
    print("After completing authentication, your tokens will be displayed.")
    print("Copy them to your .env file.")

def start_reddit_auth():
    """Start Reddit OAuth flow"""
    print("🟠 Starting Reddit authentication...")
    print("Opening browser for Reddit OAuth...")
    
    auth_url = "http://localhost:8000/auth/reddit"
    webbrowser.open(auth_url)
    
    print(f"If the browser doesn't open automatically, visit: {auth_url}")
    print("After completing authentication, your refresh token will be displayed.")
    print("Copy it to your .env file.")

def print_status(status):
    """Print authentication status in a readable format"""
    print("\n📊 Authentication Status:")
    print("=" * 40)
    
    for platform, info in status.items():
        if platform == 'youtube':
            emoji = "🎥"
            name = "YouTube"
        elif platform == 'twitter':
            emoji = "🐦"
            name = "Twitter"
        elif platform == 'reddit':
            emoji = "🟠"
            name = "Reddit"
        else:
            emoji = "📱"
            name = platform.title()
        
        configured = "✅" if info.get('configured') else "❌"
        authenticated = "✅" if info.get('authenticated') else "❌"
        
        print(f"{emoji} {name}:")
        print(f"  Configured: {configured}")
        if 'authenticated' in info:
            print(f"  Authenticated: {authenticated}")
        print()

def main():
    """Main authentication helper"""
    print("🎵 SoundHash Authentication Helper")
    print("=" * 40)
    
    # Check if auth server is running
    if not check_auth_server():
        print("❌ Authentication server is not running!")
        print("Start it with: ./docker/manage.sh auth")
        sys.exit(1)
    
    print("✅ Authentication server is running")
    
    # Check current status
    status = check_auth_status()
    if status:
        print_status(status)
    
    while True:
        print("\nAvailable commands:")
        print("1. Twitter authentication")
        print("2. Reddit authentication") 
        print("3. Check status")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            start_twitter_auth()
        elif choice == '2':
            start_reddit_auth()
        elif choice == '3':
            status = check_auth_status()
            if status:
                print_status(status)
            else:
                print("❌ Failed to get authentication status")
        elif choice == '4':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")
        
        if choice in ['1', '2']:
            print("\nPress Enter after completing authentication to continue...")
            input()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)