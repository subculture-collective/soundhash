"""Shared pytest fixtures for all tests."""

import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.models import Base  # noqa: E402


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sine_wave_file(temp_dir):
    """Generate a simple sine wave audio file for testing."""
    # Generate 1 second of 440 Hz sine wave at 22050 Hz sample rate
    sample_rate = 22050
    duration = 1.0
    frequency = 440.0

    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_data = np.sin(2 * np.pi * frequency * t)

    # Save to WAV file
    wav_path = Path(temp_dir) / "test_sine.wav"
    sf.write(wav_path, audio_data, sample_rate)

    return str(wav_path)


@pytest.fixture
def multi_second_sine_wave(temp_dir):
    """Generate a longer sine wave for segmentation testing."""
    # Generate 3 seconds of sine wave
    sample_rate = 22050
    duration = 3.0
    frequency = 440.0

    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_data = np.sin(2 * np.pi * frequency * t)

    wav_path = Path(temp_dir) / "test_multi_second.wav"
    sf.write(wav_path, audio_data, sample_rate)

    return str(wav_path)


@pytest.fixture(scope="function")
def db_engine():
    """Create a test database engine."""
    # Use in-memory SQLite for tests
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create a test database session."""
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
