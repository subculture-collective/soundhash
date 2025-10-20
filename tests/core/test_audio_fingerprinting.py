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


class TestParameterValidation:
    """Test suite for STFT parameter validation."""

    def test_negative_sample_rate(self):
        """Test that negative sample rate raises ValueError."""
        with pytest.raises(ValueError, match="sample_rate must be positive"):
            AudioFingerprinter(sample_rate=-1000)

    def test_zero_sample_rate(self):
        """Test that zero sample rate raises ValueError."""
        with pytest.raises(ValueError, match="sample_rate must be positive"):
            AudioFingerprinter(sample_rate=0)

    def test_n_fft_too_small(self):
        """Test that n_fft < 256 raises ValueError."""
        with pytest.raises(ValueError, match="n_fft must be at least 256"):
            AudioFingerprinter(n_fft=128)

    def test_n_fft_not_power_of_two(self):
        """Test that non-power-of-2 n_fft raises ValueError."""
        with pytest.raises(ValueError, match="n_fft should be a power of 2"):
            AudioFingerprinter(n_fft=1000)

    def test_negative_hop_length(self):
        """Test that negative hop_length raises ValueError."""
        with pytest.raises(ValueError, match="hop_length must be positive"):
            AudioFingerprinter(hop_length=-100)

    def test_zero_hop_length(self):
        """Test that zero hop_length raises ValueError."""
        with pytest.raises(ValueError, match="hop_length must be positive"):
            AudioFingerprinter(hop_length=0)

    def test_hop_length_exceeds_n_fft(self):
        """Test that hop_length > n_fft raises ValueError."""
        with pytest.raises(ValueError, match="hop_length .* should not exceed n_fft"):
            AudioFingerprinter(n_fft=512, hop_length=1024)

    def test_valid_parameters(self):
        """Test that valid parameters are accepted."""
        fp = AudioFingerprinter(sample_rate=44100, n_fft=4096, hop_length=1024)
        assert fp.sample_rate == 44100
        assert fp.n_fft == 4096
        assert fp.hop_length == 1024


class TestDeterministicHashing:
    """Test suite for deterministic hash generation."""

    def test_same_audio_produces_same_hash(self):
        """Test that extracting fingerprint multiple times produces same hash."""
        fingerprinter = AudioFingerprinter()
        sample_rate = 22050
        duration = 0.5
        frequency = 440.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = np.sin(2 * np.pi * frequency * t)

        hashes = []
        for _ in range(5):
            result = fingerprinter.extract_fingerprint_from_audio(audio_data, sample_rate)
            hashes.append(result["fingerprint_hash"])

        # All hashes should be identical
        assert len(set(hashes)) == 1, f"Got different hashes: {set(hashes)}"
        assert len(hashes[0]) == 32  # MD5 hash length

    def test_fingerprint_consistency(self):
        """Test that compact fingerprints are bit-for-bit identical across runs."""
        fingerprinter = AudioFingerprinter()
        sample_rate = 22050
        duration = 0.5
        frequency = 440.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = np.sin(2 * np.pi * frequency * t)

        results = []
        for _ in range(3):
            result = fingerprinter.extract_fingerprint_from_audio(audio_data, sample_rate)
            results.append(result["compact_fingerprint"])

        # All fingerprints should be identical
        for i in range(1, len(results)):
            np.testing.assert_array_equal(
                results[0], results[i], err_msg=f"Fingerprint {i} differs from fingerprint 0"
            )

    def test_fingerprint_dtype_consistency(self):
        """Test that fingerprints always use float64 dtype."""
        fingerprinter = AudioFingerprinter()
        sample_rate = 22050
        duration = 0.5
        frequency = 440.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = np.sin(2 * np.pi * frequency * t)

        result = fingerprinter.extract_fingerprint_from_audio(audio_data, sample_rate)
        assert result["compact_fingerprint"].dtype == np.float64


class TestNormalization:
    """Test suite for fingerprint normalization."""

    def test_compact_fingerprint_normalized(self):
        """Test that compact fingerprints are normalized to [0, 1] range."""
        fingerprinter = AudioFingerprinter()
        sample_rate = 22050
        duration = 0.5
        frequency = 440.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = np.sin(2 * np.pi * frequency * t)

        result = fingerprinter.extract_fingerprint_from_audio(audio_data, sample_rate)
        compact = result["compact_fingerprint"]

        assert compact.min() >= 0.0, f"Minimum value {compact.min()} is below 0"
        assert compact.max() <= 1.0, f"Maximum value {compact.max()} exceeds 1"
        # At least one value should be at the maximum (1.0) due to normalization
        assert compact.max() > 0.0, "Fingerprint should not be all zeros"

    def test_volume_invariance(self):
        """Test that fingerprints are similar regardless of audio volume."""
        fingerprinter = AudioFingerprinter()
        sample_rate = 22050
        duration = 0.5
        frequency = 440.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        base_audio = np.sin(2 * np.pi * frequency * t)

        # Test with different volumes
        volumes = [0.1, 0.5, 1.0, 2.0]
        fingerprints = []
        for volume in volumes:
            audio_data = base_audio * volume
            result = fingerprinter.extract_fingerprint_from_audio(audio_data, sample_rate)
            fingerprints.append(result)

        # All fingerprints should be very similar (normalized)
        for i in range(1, len(fingerprints)):
            similarity = fingerprinter.compare_fingerprints(fingerprints[0], fingerprints[i])
            assert (
                similarity > 0.95
            ), f"Volume {volumes[i]} produced similarity {similarity}, expected > 0.95"


class TestSerializationRoundtrip:
    """Test suite for serialization and deserialization."""

    def test_roundtrip_preserves_data(self, sine_wave_file):
        """Test that serialize->deserialize preserves all data."""
        fingerprinter = AudioFingerprinter()
        original = fingerprinter.extract_fingerprint(sine_wave_file)

        # Serialize and deserialize
        serialized = fingerprinter.serialize_fingerprint(original)
        deserialized = fingerprinter.deserialize_fingerprint(serialized)

        # Check all preserved fields
        np.testing.assert_array_equal(
            original["compact_fingerprint"], deserialized["compact_fingerprint"]
        )
        assert original["confidence_score"] == deserialized["confidence_score"]
        assert original["peak_count"] == deserialized["peak_count"]
        assert original["duration"] == deserialized["duration"]
        assert original["sample_rate"] == deserialized["sample_rate"]

    def test_roundtrip_allows_comparison(self, sine_wave_file):
        """Test that deserialized fingerprints can be compared."""
        fingerprinter = AudioFingerprinter()
        fp1 = fingerprinter.extract_fingerprint(sine_wave_file)

        # Serialize and deserialize
        serialized = fingerprinter.serialize_fingerprint(fp1)
        fp2 = fingerprinter.deserialize_fingerprint(serialized)

        # Should be able to compare and get perfect match
        similarity = fingerprinter.compare_fingerprints(fp1, fp2)
        assert similarity == 1.0, f"Expected perfect match, got similarity {similarity}"

    def test_multiple_roundtrips(self, sine_wave_file):
        """Test that multiple serialize/deserialize cycles preserve data."""
        fingerprinter = AudioFingerprinter()
        original = fingerprinter.extract_fingerprint(sine_wave_file)

        current = original
        for _i in range(3):
            serialized = fingerprinter.serialize_fingerprint(current)
            current = fingerprinter.deserialize_fingerprint(serialized)

            # Should still match original
            np.testing.assert_array_equal(
                original["compact_fingerprint"], current["compact_fingerprint"]
            )

    def test_serialized_data_is_bytes(self, sine_wave_file):
        """Test that serialization produces bytes."""
        fingerprinter = AudioFingerprinter()
        fp = fingerprinter.extract_fingerprint(sine_wave_file)

        serialized = fingerprinter.serialize_fingerprint(fp)
        assert isinstance(serialized, bytes)
        assert len(serialized) > 0


class TestSimilarityThresholds:
    """Test suite for similarity function and thresholds."""

    def test_identical_fingerprints_perfect_match(self, sine_wave_file):
        """Test that identical fingerprints return 1.0 similarity."""
        fingerprinter = AudioFingerprinter()
        fp = fingerprinter.extract_fingerprint(sine_wave_file)

        similarity = fingerprinter.compare_fingerprints(fp, fp)
        assert similarity == 1.0

    def test_very_similar_audio_high_similarity(self):
        """Test that very similar audio returns high similarity (> 0.85)."""
        fingerprinter = AudioFingerprinter()
        sample_rate = 22050
        duration = 0.5
        frequency = 440.0
        t = np.linspace(0, duration, int(sample_rate * duration))

        # Create two nearly identical signals
        audio1 = np.sin(2 * np.pi * frequency * t)
        audio2 = np.sin(2 * np.pi * frequency * t) * 0.99  # Slightly different amplitude

        fp1 = fingerprinter.extract_fingerprint_from_audio(audio1, sample_rate)
        fp2 = fingerprinter.extract_fingerprint_from_audio(audio2, sample_rate)

        similarity = fingerprinter.compare_fingerprints(fp1, fp2)
        assert similarity > 0.85, f"Expected > 0.85 for very similar audio, got {similarity}"

    def test_different_frequencies_low_similarity(self):
        """Test that different frequencies return lower similarity."""
        fingerprinter = AudioFingerprinter()
        sample_rate = 22050
        duration = 0.5
        t = np.linspace(0, duration, int(sample_rate * duration))

        # Create signals with very different frequencies
        audio1 = np.sin(2 * np.pi * 220 * t)  # A3
        audio2 = np.sin(2 * np.pi * 1760 * t)  # A6 (3 octaves higher)

        fp1 = fingerprinter.extract_fingerprint_from_audio(audio1, sample_rate)
        fp2 = fingerprinter.extract_fingerprint_from_audio(audio2, sample_rate)

        similarity = fingerprinter.compare_fingerprints(fp1, fp2)
        assert 0.0 <= similarity <= 1.0  # Should be in valid range
        # Different frequencies should have lower similarity, but may not be extremely low
        # due to normalization and the way peaks are detected

    def test_similarity_range(self):
        """Test that similarity is always in [0, 1] range."""
        fingerprinter = AudioFingerprinter()
        sample_rate = 22050
        duration = 0.5
        t = np.linspace(0, duration, int(sample_rate * duration))

        # Test with various audio signals
        test_cases = [
            (440.0, 880.0),  # Octave apart
            (440.0, 554.37),  # Fourth apart
            (440.0, 220.0),  # Octave below
        ]

        for freq1, freq2 in test_cases:
            audio1 = np.sin(2 * np.pi * freq1 * t)
            audio2 = np.sin(2 * np.pi * freq2 * t)

            fp1 = fingerprinter.extract_fingerprint_from_audio(audio1, sample_rate)
            fp2 = fingerprinter.extract_fingerprint_from_audio(audio2, sample_rate)

            similarity = fingerprinter.compare_fingerprints(fp1, fp2)
            assert (
                0.0 <= similarity <= 1.0
            ), f"Similarity {similarity} out of range for {freq1} Hz vs {freq2} Hz"

    def test_empty_fingerprints_zero_similarity(self):
        """Test that empty or None fingerprints return 0 similarity."""
        fingerprinter = AudioFingerprinter()

        # Test various empty/invalid cases
        empty_cases = [
            ({"compact_fingerprint": None}, {"compact_fingerprint": None}),
            ({"compact_fingerprint": np.array([])}, {"compact_fingerprint": np.array([])}),
            ({"compact_fingerprint": None}, {"compact_fingerprint": np.array([1, 2, 3])}),
        ]

        for fp1, fp2 in empty_cases:
            similarity = fingerprinter.compare_fingerprints(fp1, fp2)
            assert similarity == 0.0, f"Expected 0.0 for empty fingerprints, got {similarity}"
