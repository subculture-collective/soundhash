#!/usr/bin/env python3
"""
Fresh Start Script for SoundHash
Clears all data and prepares for a fresh ingestion run.
"""

import os
import sys
import shutil
import logging
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.database.connection import db_manager
from src.database.models import Channel, Video, AudioFingerprint, MatchResult, ProcessingJob
from config.settings import Config

def setup_logging():
    """Setup logging for the fresh start script"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('fresh_start.log')
        ]
    )
    return logging.getLogger(__name__)

def clear_temp_files(logger):
    """Clear all temporary files"""
    temp_dir = Path(Config.TEMP_DIR)
    if temp_dir.exists():
        logger.info(f"Clearing temporary files from: {temp_dir}")
        file_count = len(list(temp_dir.iterdir()))
        shutil.rmtree(temp_dir)
        temp_dir.mkdir(exist_ok=True)
        logger.info(f"✅ Removed {file_count} temporary files")
    else:
        logger.info("✅ Temp directory doesn't exist, creating it")
        temp_dir.mkdir(parents=True, exist_ok=True)

def clear_logs(logger):
    """Clear log files"""
    log_files = [
        'ingestion.log',
        'fresh_start.log',
        'logs/app.log',
        'logs/ingestion.log',
        'logs/error.log'
    ]
    
    cleared_count = 0
    for log_file in log_files:
        if os.path.exists(log_file):
            os.remove(log_file)
            cleared_count += 1
            logger.info(f"Removed log file: {log_file}")
    
    logger.info(f"✅ Cleared {cleared_count} log files")

def clear_database_data(logger):
    """Clear all data from database tables"""
    try:
        db_manager.initialize()
        session = db_manager.get_session()
        
        try:
            # Get table counts before clearing
            counts = {
                'match_results': session.query(MatchResult).count(),
                'audio_fingerprints': session.query(AudioFingerprint).count(),
                'processing_jobs': session.query(ProcessingJob).count(),
                'videos': session.query(Video).count(),
                'channels': session.query(Channel).count()
            }
            
            # Clear tables in correct order (respecting foreign keys)
            logger.info("Clearing database tables...")
            
            session.query(MatchResult).delete()
            logger.info(f"Cleared {counts['match_results']} match results")
            
            session.query(AudioFingerprint).delete()
            logger.info(f"Cleared {counts['audio_fingerprints']} audio fingerprints")
            
            session.query(ProcessingJob).delete()
            logger.info(f"Cleared {counts['processing_jobs']} processing jobs")
            
            session.query(Video).delete()
            logger.info(f"Cleared {counts['videos']} videos")
            
            session.query(Channel).delete()
            logger.info(f"Cleared {counts['channels']} channels")
            
            session.commit()
            logger.info("✅ Database cleared successfully")
            
            # Show summary
            total_records = sum(counts.values())
            logger.info(f"📊 Total records removed: {total_records}")
            for table, count in counts.items():
                if count > 0:
                    logger.info(f"   - {table}: {count}")
                    
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"❌ Error clearing database: {e}")
        raise

def clear_python_cache(logger):
    """Clear Python cache files"""
    cache_patterns = ['**/__pycache__', '**/*.pyc', '**/*.pyo']
    cleared_count = 0
    
    for pattern in cache_patterns:
        for cache_path in Path('.').glob(pattern):
            if cache_path.is_file():
                cache_path.unlink()
                cleared_count += 1
            elif cache_path.is_dir():
                shutil.rmtree(cache_path)
                cleared_count += 1
    
    logger.info(f"✅ Cleared {cleared_count} Python cache files")

def verify_system_ready(logger):
    """Verify the system is ready for fresh ingestion"""
    logger.info("🔍 Verifying system readiness...")
    
    # Check database connection
    try:
        db_manager.initialize()
        session = db_manager.get_session()
        from sqlalchemy import text
        session.execute(text("SELECT 1"))
        session.close()
        logger.info("✅ Database connection working")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False
    
    # Check temp directory
    temp_dir = Path(Config.TEMP_DIR)
    if temp_dir.exists() and temp_dir.is_dir():
        logger.info("✅ Temp directory ready")
    else:
        logger.error(f"❌ Temp directory not accessible: {temp_dir}")
        return False
    
    # Check yt-dlp
    try:
        import subprocess
        result = subprocess.run(['yt-dlp', '--version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            logger.info(f"✅ yt-dlp ready (version: {result.stdout.strip()})")
        else:
            logger.error("❌ yt-dlp not working")
            return False
    except Exception as e:
        logger.error(f"❌ yt-dlp check failed: {e}")
        return False
    
    # Check ffmpeg
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            logger.info("✅ FFmpeg ready")
        else:
            logger.error("❌ FFmpeg not working")
            return False
    except Exception as e:
        logger.error(f"❌ FFmpeg check failed: {e}")
        return False
    
    logger.info("🎉 System is ready for fresh ingestion!")
    return True

def main():
    """Main fresh start function"""
    logger = setup_logging()
    
    logger.info("🚀 Starting fresh cleanup for SoundHash...")
    logger.info("=" * 60)
    
    try:
        # Confirm with user
        print("\n⚠️  WARNING: This will permanently delete all data!")
        print("   - All videos, channels, and audio segments")
        print("   - All temporary files and logs")
        print("   - All processing cache")
        
        response = input("\nAre you sure you want to continue? (type 'yes' to confirm): ")
        if response.lower() != 'yes':
            print("❌ Operation cancelled")
            return
        
        print("\n🧹 Starting cleanup...")
        
        # Step 1: Clear temp files
        logger.info("Step 1: Clearing temporary files...")
        clear_temp_files(logger)
        
        # Step 2: Clear logs
        logger.info("Step 2: Clearing log files...")
        clear_logs(logger)
        
        # Step 3: Clear Python cache
        logger.info("Step 3: Clearing Python cache...")
        clear_python_cache(logger)
        
        # Step 4: Clear database
        logger.info("Step 4: Clearing database data...")
        clear_database_data(logger)
        
        # Step 5: Verify system
        logger.info("Step 5: Verifying system readiness...")
        if not verify_system_ready(logger):
            logger.error("❌ System verification failed!")
            return
        
        logger.info("=" * 60)
        logger.info("✅ Fresh start completed successfully!")
        logger.info("🎯 System is ready for a fresh ingestion run")
        logger.info("Run: python scripts/ingest_channels.py --max-videos 10")
        
    except Exception as e:
        logger.error(f"❌ Fresh start failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()