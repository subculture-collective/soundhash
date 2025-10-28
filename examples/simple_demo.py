#!/usr/bin/env python3
"""
Simple console-based audio matching demo.

Captures audio from microphone and displays matches in real-time.

Usage:
    python simple_demo.py --api-url ws://localhost:8000 --api-key your-key
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add parent directory to path to import client SDK
sys.path.insert(0, str(Path(__file__).parent.parent / "client-sdk"))

from soundhash_client import SoundHashClient


class ConsoleDemoClient:
    """Console-based demo client with colored output."""
    
    # ANSI color codes
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    
    def __init__(self, api_url: str, api_key: str):
        self.client = SoundHashClient(api_url, api_key)
        self.match_count = 0
        
        # Set up callbacks
        self.client.on_match = self.handle_match
        self.client.on_status = self.handle_status
        self.client.on_error = self.handle_error
    
    def print_header(self):
        """Print demo header."""
        print(f"\n{self.BOLD}{'='*60}{self.ENDC}")
        print(f"{self.BOLD}{self.BLUE}🎵 SoundHash Real-Time Matching Demo 🎵{self.ENDC}")
        print(f"{self.BOLD}{'='*60}{self.ENDC}\n")
    
    def print_status(self, message: str):
        """Print status message."""
        print(f"{self.BLUE}ℹ️  {message}{self.ENDC}")
    
    def print_success(self, message: str):
        """Print success message."""
        print(f"{self.GREEN}✓ {message}{self.ENDC}")
    
    def print_error(self, message: str):
        """Print error message."""
        print(f"{self.RED}✗ {message}{self.ENDC}")
    
    def print_match(self, match: dict):
        """Print match information."""
        title = match.get('title', 'Unknown')
        score = match.get('similarity_score', 0) * 100
        url = match.get('url', '')
        
        print(f"\n{self.GREEN}{'─'*60}{self.ENDC}")
        print(f"{self.BOLD}{self.GREEN}🎯 MATCH FOUND #{self.match_count + 1}{self.ENDC}")
        print(f"{self.GREEN}{'─'*60}{self.ENDC}")
        print(f"  {self.BOLD}Title:{self.ENDC} {title}")
        print(f"  {self.BOLD}Confidence:{self.ENDC} {score:.1f}%")
        if url:
            print(f"  {self.BOLD}URL:{self.ENDC} {url}")
        print(f"{self.GREEN}{'─'*60}{self.ENDC}\n")
    
    def handle_match(self, match_data: dict):
        """Handle incoming match."""
        matches = match_data.get('matches', [])
        stats = match_data.get('stats', {})
        
        if matches:
            for match in matches:
                self.match_count += 1
                self.print_match(match)
            
            # Show processing stats
            if stats:
                buffer_pct = (stats.get('buffer_size', 0) / stats.get('buffer_capacity', 1)) * 100
                duration = stats.get('duration_seconds', 0)
                print(f"{self.BLUE}📊 Stats: Buffer {buffer_pct:.0f}% | "
                      f"Duration {duration:.1f}s | "
                      f"Total matches: {self.match_count}{self.ENDC}")
    
    def handle_status(self, status: str):
        """Handle status update."""
        self.print_status(status)
    
    def handle_error(self, error_message: str):
        """Handle error."""
        self.print_error(f"Error: {error_message}")
    
    async def run(self):
        """Run the demo."""
        self.print_header()
        
        try:
            self.print_status("Connecting to SoundHash API...")
            await self.client.connect()
            self.print_success("Connected!")
            
            self.print_status("Starting microphone...")
            await self.client.start_microphone()
            self.print_success("Microphone active!")
            
            print(f"\n{self.YELLOW}🎤 Listening for audio... (Press Ctrl+C to stop){self.ENDC}\n")
            
            # Listen for matches
            await self.client.listen_for_matches()
            
        except KeyboardInterrupt:
            print(f"\n\n{self.YELLOW}Stopping...{self.ENDC}")
        except Exception as e:
            self.print_error(f"Fatal error: {e}")
        finally:
            await self.client.disconnect()
            print(f"\n{self.GREEN}Disconnected. Total matches found: {self.match_count}{self.ENDC}\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="SoundHash real-time audio matching demo"
    )
    parser.add_argument(
        "--api-url",
        default="ws://localhost:8000",
        help="WebSocket API URL (default: ws://localhost:8000)"
    )
    parser.add_argument(
        "--api-key",
        default="demo-key",
        help="API key (default: demo-key)"
    )
    
    args = parser.parse_args()
    
    # Run demo
    demo = ConsoleDemoClient(args.api_url, args.api_key)
    asyncio.run(demo.run())


if __name__ == "__main__":
    main()
