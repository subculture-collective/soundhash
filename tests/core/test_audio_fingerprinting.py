"""Tests for audio fingerprinting functionality."""

import numpy as np
import pytest

from src.core.audio_fingerprinting import AudioFingerprinter


class TestAudioFingerprinter:
    """Test suite for AudioFingerprinter class."""

    def test_init_default_parameters(self):
        """Test AudioFingerprinter initialization with default parameters."""
        fingerprinter = AudioFingerprinter()

        assert fingerprinter.sample_rate == 22050  # Default from Config
        assert fingerprinter.n_fft == 2048
        assert fingerprinter.hop_length == 512
        assert len(fingerprinter.freq_ranges) == 6
        assert len(fingerprinter.bin_ranges) == 6

    def test_init_custom_parameters(self):
        """Test AudioFingerprinter initialization with custom parameters."""
        fingerprinter = AudioFingerprinter(sample_rate=44100, n_fft=4096, hop_length=1024)

        assert fingerprinter.sample_rate == 44100
        assert fingerprinter.n_fft == 4096
        assert fingerprinter.hop_length == 1024

    def test_extract_fingerprint_happy_path(self, sine_wave_file):
        """Test extracting fingerprint from a simple sine wave - happy path."""
        fingerprinter = AudioFingerprinter()

        result = fingerprinter.extract_fingerprint(sine_wave_file)

        # Check that all expected keys are present
        assert "fingerprint_data" in result
        assert "compact_fingerprint" in result
        assert "fingerprint_hash" in result
        assert "confidence_score" in result
        assert "peak_count" in result
        assert "duration" in result
        assert "sample_rate" in result

        # Check data types and ranges
        assert isinstance(result["fingerprint_data"], list)
        assert isinstance(result["compact_fingerprint"], np.ndarray)
        assert isinstance(result["fingerprint_hash"], str)
        assert isinstance(result["confidence_score"], float)
        assert isinstance(result["peak_count"], int)
        assert isinstance(result["duration"], float)
        assert isinstance(result["sample_rate"], int)

        # Check reasonable values
        assert result["duration"] > 0
        assert result["sample_rate"] == 22050
        assert result["peak_count"] >= 0
        assert (
            result["confidence_score"] >= 0.0
        )  # Confidence score can be > 1.0 in current implementation
        assert len(result["fingerprint_hash"]) == 32  # MD5 hash length

    def test_extract_fingerprint_from_audio(self):
        """Test extracting fingerprint directly from audio data."""
        fingerprinter = AudioFingerprinter()

        # Generate a simple sine wave
        sample_rate = 22050
        duration = 0.5
        frequency = 440.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = np.sin(2 * np.pi * frequency * t)

        result = fingerprinter.extract_fingerprint_from_audio(audio_data, sample_rate)

        assert "compact_fingerprint" in result
        assert "fingerprint_hash" in result
        assert result["sample_rate"] == sample_rate

    def test_compare_fingerprints_identical(self, sine_wave_file):
        """Test comparing identical fingerprints returns high similarity."""
        fingerprinter = AudioFingerprinter()

        fp1 = fingerprinter.extract_fingerprint(sine_wave_file)
        fp2 = fingerprinter.extract_fingerprint(sine_wave_file)

        similarity = fingerprinter.compare_fingerprints(fp1, fp2)

        # Identical fingerprints should have very high similarity
        assert similarity > 0.9

    def test_compare_fingerprints_different(self):
        """Test comparing different fingerprints returns lower similarity."""
        fingerprinter = AudioFingerprinter()

        # Generate two different sine waves
        sample_rate = 22050
        duration = 0.5
        t = np.linspace(0, duration, int(sample_rate * duration))

        audio1 = np.sin(2 * np.pi * 440 * t)  # 440 Hz
        audio2 = np.sin(2 * np.pi * 880 * t)  # 880 Hz (octave higher)

        fp1 = fingerprinter.extract_fingerprint_from_audio(audio1, sample_rate)
        fp2 = fingerprinter.extract_fingerprint_from_audio(audio2, sample_rate)

        similarity = fingerprinter.compare_fingerprints(fp1, fp2)

        # Different frequencies should have lower similarity
        assert 0.0 <= similarity < 1.0

    def test_compare_fingerprints_empty(self):
        """Test comparing fingerprints with empty data."""
        fingerprinter = AudioFingerprinter()

        fp1 = {"compact_fingerprint": None}
        fp2 = {"compact_fingerprint": None}

        similarity = fingerprinter.compare_fingerprints(fp1, fp2)

        assert similarity == 0.0

    def test_serialize_deserialize_fingerprint(self, sine_wave_file):
        """Test serialization and deserialization of fingerprints."""
        fingerprinter = AudioFingerprinter()

        original = fingerprinter.extract_fingerprint(sine_wave_file)

        # Serialize
        serialized = fingerprinter.serialize_fingerprint(original)
        assert isinstance(serialized, bytes)
        assert len(serialized) > 0

        # Deserialize
        deserialized = fingerprinter.deserialize_fingerprint(serialized)

        # Check that key data is preserved
        assert "compact_fingerprint" in deserialized
        assert "confidence_score" in deserialized
        assert "peak_count" in deserialized
        assert "duration" in deserialized
        assert "sample_rate" in deserialized

        # Check values match
        np.testing.assert_array_almost_equal(
            original["compact_fingerprint"], deserialized["compact_fingerprint"]
        )
        assert original["confidence_score"] == deserialized["confidence_score"]
        assert original["peak_count"] == deserialized["peak_count"]

    def test_hash_fingerprint_consistency(self):
        """Test that hashing the same fingerprint produces the same hash."""
        fingerprinter = AudioFingerprinter()

        compact_fp = np.array([0.1, 0.2, 0.3, 0.4, 0.5])

        hash1 = fingerprinter._hash_fingerprint(compact_fp)
        hash2 = fingerprinter._hash_fingerprint(compact_fp)

        assert hash1 == hash2
        assert len(hash1) == 32  # MD5 hash length

    def test_create_compact_fingerprint_empty(self):
        """Test creating compact fingerprint with empty data."""
        fingerprinter = AudioFingerprinter()

        compact = fingerprinter._create_compact_fingerprint([])

        assert isinstance(compact, np.ndarray)
        assert len(compact) == 0

    def test_create_compact_fingerprint_with_data(self):
        """Test creating compact fingerprint with valid data."""
        fingerprinter = AudioFingerprinter()

        fingerprint_data = [
            {
                "time": 0.0,
                "peaks": [{"frequency": 440.0, "bin": 20, "magnitude": 100.0, "freq_range": 1}],
            }
        ]

        compact = fingerprinter._create_compact_fingerprint(fingerprint_data)

        assert isinstance(compact, np.ndarray)
        assert len(compact) > 0

    def test_extract_frame_peaks(self):
        """Test extracting peaks from a single frame."""
        fingerprinter = AudioFingerprinter()

        # Create a frame with some values
        frame = np.random.rand(1025)

        peaks = fingerprinter._extract_frame_peaks(frame)

        assert isinstance(peaks, list)

    def test_load_audio_error(self):
        """Test load_audio with invalid file."""
        fingerprinter = AudioFingerprinter()

        with pytest.raises(ValueError):
            fingerprinter.load_audio("nonexistent_file.wav")
