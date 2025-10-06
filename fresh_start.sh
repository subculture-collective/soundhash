#!/bin/bash

# SoundHash Fresh Start Script
# Clears all data and prepares for fresh ingestion

echo "🚀 SoundHash Fresh Start"
echo "======================="

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment and run fresh start
source .venv/bin/activate
python scripts/fresh_start.py

echo ""
echo "🎯 Next steps:"
echo "   1. Run: python scripts/ingest_channels.py --max-videos 10"
echo "   2. Check logs for any issues"
echo "   3. Scale up max-videos as needed"