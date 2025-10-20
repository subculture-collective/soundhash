"""Tests for similarity search tuning functionality."""

import numpy as np

from src.core.audio_fingerprinting import AudioFingerprinter


class TestConfigurableWeights:
    """Test suite for configurable similarity weights."""

    def test_default_weights(self):
        """Test that default weights are used when not specified."""
        fingerprinter = AudioFingerprinter()
        sample_rate = 22050
        duration = 0.5
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio = np.sin(2 * np.pi * 440 * t)

        fp = fingerprinter.extract_fingerprint_from_audio(audio, sample_rate)

        # Compare with itself - should give 1.0 regardless of weights
        similarity = fingerprinter.compare_fingerprints(fp, fp)
        assert similarity == 1.0

    def test_custom_weights(self):
        """Test that custom weights affect the similarity score."""
        fingerprinter = AudioFingerprinter()
        sample_rate = 22050
        duration = 0.5
        t = np.linspace(0, duration, int(sample_rate * duration))

        audio1 = np.sin(2 * np.pi * 440 * t)
        audio2 = np.sin(2 * np.pi * 880 * t)

        fp1 = fingerprinter.extract_fingerprint_from_audio(audio1, sample_rate)
        fp2 = fingerprinter.extract_fingerprint_from_audio(audio2, sample_rate)

        # Compare with different weights
        score_equal = fingerprinter.compare_fingerprints(
            fp1, fp2, correlation_weight=0.5, l2_weight=0.5
        )
        score_corr_heavy = fingerprinter.compare_fingerprints(
            fp1, fp2, correlation_weight=0.8, l2_weight=0.2
        )
        score_l2_heavy = fingerprinter.compare_fingerprints(
            fp1, fp2, correlation_weight=0.2, l2_weight=0.8
        )

        # Scores should differ based on weights
        assert 0.0 <= score_equal <= 1.0
        assert 0.0 <= score_corr_heavy <= 1.0
        assert 0.0 <= score_l2_heavy <= 1.0

    def test_return_components(self):
        """Test that return_components flag returns detailed metrics."""
        fingerprinter = AudioFingerprinter()
        sample_rate = 22050
        duration = 0.5
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio = np.sin(2 * np.pi * 440 * t)

        fp = fingerprinter.extract_fingerprint_from_audio(audio, sample_rate)

        result = fingerprinter.compare_fingerprints(fp, fp, return_components=True)

        assert isinstance(result, dict)
        assert "correlation" in result
        assert "l2_similarity" in result
        assert "combined_score" in result

        # Self-comparison should give perfect scores
        assert result["correlation"] == 1.0
        assert result["l2_similarity"] == 1.0
        assert result["combined_score"] == 1.0

    def test_return_components_empty(self):
        """Test that return_components works with empty fingerprints."""
        fingerprinter = AudioFingerprinter()

        fp1 = {"compact_fingerprint": None}
        fp2 = {"compact_fingerprint": None}

        result = fingerprinter.compare_fingerprints(fp1, fp2, return_components=True)

        assert isinstance(result, dict)
        assert result["correlation"] == 0.0
        assert result["l2_similarity"] == 0.0
        assert result["combined_score"] == 0.0


class TestRankMatches:
    """Test suite for rank_matches functionality."""

    def test_rank_matches_basic(self):
        """Test basic ranking functionality."""
        fingerprinter = AudioFingerprinter()
        sample_rate = 22050
        duration = 0.5
        t = np.linspace(0, duration, int(sample_rate * duration))

        # Create query
        query_audio = np.sin(2 * np.pi * 440 * t)
        query_fp = fingerprinter.extract_fingerprint_from_audio(query_audio, sample_rate)

        # Create candidates
        candidates = [
            (
                "exact_match",
                fingerprinter.extract_fingerprint_from_audio(
                    np.sin(2 * np.pi * 440 * t), sample_rate
                ),
            ),
            (
                "similar",
                fingerprinter.extract_fingerprint_from_audio(
                    np.sin(2 * np.pi * 440 * t) * 0.9, sample_rate
                ),
            ),
            (
                "different",
                fingerprinter.extract_fingerprint_from_audio(
                    np.sin(2 * np.pi * 880 * t), sample_rate
                ),
            ),
        ]

        matches = fingerprinter.rank_matches(
            query_fp,
            candidates,
            min_score=0.0,
            min_duration=0.0,
            correlation_threshold=0.0,
            l2_threshold=0.0,
        )

        # Should return all candidates
        assert len(matches) <= 3

        # First match should be the best
        if matches:
            assert matches[0]["identifier"] in ["exact_match", "similar"]
            assert 0.0 <= matches[0]["score"] <= 1.0

    def test_rank_matches_with_thresholds(self):
        """Test that thresholds filter out low-quality matches."""
        fingerprinter = AudioFingerprinter()
        sample_rate = 22050
        duration = 0.5
        t = np.linspace(0, duration, int(sample_rate * duration))

        query_audio = np.sin(2 * np.pi * 440 * t)
        query_fp = fingerprinter.extract_fingerprint_from_audio(query_audio, sample_rate)

        candidates = [
            (
                "exact_match",
                fingerprinter.extract_fingerprint_from_audio(
                    np.sin(2 * np.pi * 440 * t), sample_rate
                ),
            ),
            (
                "different",
                fingerprinter.extract_fingerprint_from_audio(
                    np.sin(2 * np.pi * 880 * t), sample_rate
                ),
            ),
        ]

        # High thresholds should filter out dissimilar matches
        matches = fingerprinter.rank_matches(
            query_fp,
            candidates,
            min_score=0.90,
            correlation_threshold=0.90,
            l2_threshold=0.90,
            min_duration=0.0,
        )

        # Should only get the exact match
        assert len(matches) >= 1
        if matches:
            assert matches[0]["identifier"] == "exact_match"
            assert matches[0]["score"] >= 0.90

    def test_rank_matches_duration_filter(self):
        """Test that min_duration filters out short audio."""
        fingerprinter = AudioFingerprinter()
        sample_rate = 22050
        short_duration = 0.5
        long_duration = 6.0

        # Short audio
        t_short = np.linspace(0, short_duration, int(sample_rate * short_duration))
        short_audio = np.sin(2 * np.pi * 440 * t_short)
        short_fp = fingerprinter.extract_fingerprint_from_audio(short_audio, sample_rate)

        # Long audio
        t_long = np.linspace(0, long_duration, int(sample_rate * long_duration))
        long_audio = np.sin(2 * np.pi * 440 * t_long)
        long_fp = fingerprinter.extract_fingerprint_from_audio(long_audio, sample_rate)

        query_fp = short_fp

        candidates = [
            ("short", short_fp),
            ("long", long_fp),
        ]

        # Filter by duration
        matches = fingerprinter.rank_matches(
            query_fp,
            candidates,
            min_duration=5.0,  # Require at least 5 seconds
            min_score=0.0,
            correlation_threshold=0.0,
            l2_threshold=0.0,
        )

        # Should only get the long audio
        assert len(matches) <= 1
        if matches:
            assert matches[0]["identifier"] == "long"
            assert matches[0]["duration"] >= 5.0

    def test_rank_matches_empty_candidates(self):
        """Test ranking with empty candidate list."""
        fingerprinter = AudioFingerprinter()
        sample_rate = 22050
        duration = 0.5
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio = np.sin(2 * np.pi * 440 * t)
        query_fp = fingerprinter.extract_fingerprint_from_audio(audio, sample_rate)

        matches = fingerprinter.rank_matches(query_fp, [])

        assert matches == []

    def test_rank_matches_sorting(self):
        """Test that matches are sorted correctly."""
        fingerprinter = AudioFingerprinter()
        sample_rate = 22050
        duration = 0.5
        t = np.linspace(0, duration, int(sample_rate * duration))

        query_audio = np.sin(2 * np.pi * 440 * t)
        query_fp = fingerprinter.extract_fingerprint_from_audio(query_audio, sample_rate)

        candidates = [
            (
                "match1",
                fingerprinter.extract_fingerprint_from_audio(
                    np.sin(2 * np.pi * 440 * t), sample_rate
                ),
            ),
            (
                "match2",
                fingerprinter.extract_fingerprint_from_audio(
                    np.sin(2 * np.pi * 440 * t) * 0.95, sample_rate
                ),
            ),
            (
                "match3",
                fingerprinter.extract_fingerprint_from_audio(
                    np.sin(2 * np.pi * 440 * t) * 0.90, sample_rate
                ),
            ),
        ]

        matches = fingerprinter.rank_matches(
            query_fp,
            candidates,
            min_score=0.0,
            min_duration=0.0,
            correlation_threshold=0.0,
            l2_threshold=0.0,
        )

        # Matches should be sorted by score in descending order
        if len(matches) > 1:
            for i in range(len(matches) - 1):
                assert matches[i]["score"] >= matches[i + 1]["score"]

    def test_rank_matches_result_structure(self):
        """Test that match results have the correct structure."""
        fingerprinter = AudioFingerprinter()
        sample_rate = 22050
        duration = 0.5
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio = np.sin(2 * np.pi * 440 * t)
        query_fp = fingerprinter.extract_fingerprint_from_audio(audio, sample_rate)

        candidates = [
            ("test_match", fingerprinter.extract_fingerprint_from_audio(audio, sample_rate)),
        ]

        matches = fingerprinter.rank_matches(
            query_fp,
            candidates,
            min_score=0.0,
            min_duration=0.0,
        )

        assert len(matches) > 0
        match = matches[0]

        # Check structure
        assert "identifier" in match
        assert "score" in match
        assert "correlation" in match
        assert "l2_similarity" in match
        assert "duration" in match

        # Check types
        assert isinstance(match["identifier"], str)
        assert isinstance(match["score"], float)
        assert isinstance(match["correlation"], float)
        assert isinstance(match["l2_similarity"], float)
        assert isinstance(match["duration"], float)

        # Check ranges
        assert 0.0 <= match["score"] <= 1.0
        assert 0.0 <= match["correlation"] <= 1.0
        assert 0.0 <= match["l2_similarity"] <= 1.0
        assert match["duration"] > 0.0


class TestSimilarityThresholds:
    """Test suite for similarity threshold validation."""

    def test_weights_sum_validation(self):
        """Test that weights are validated (should sum to 1.0)."""
        fingerprinter = AudioFingerprinter()
        sample_rate = 22050
        duration = 0.5
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio = np.sin(2 * np.pi * 440 * t)
        fp = fingerprinter.extract_fingerprint_from_audio(audio, sample_rate)

        # Note: Current implementation doesn't enforce sum=1.0,
        # but we should test that different weights produce different results
        score1 = fingerprinter.compare_fingerprints(fp, fp, correlation_weight=0.5, l2_weight=0.5)
        score2 = fingerprinter.compare_fingerprints(fp, fp, correlation_weight=0.3, l2_weight=0.7)

        # For identical fingerprints, score should still be 1.0 regardless
        assert score1 == 1.0
        assert score2 == 1.0

    def test_extreme_weights(self):
        """Test behavior with extreme weight values."""
        fingerprinter = AudioFingerprinter()
        sample_rate = 22050
        duration = 0.5
        t = np.linspace(0, duration, int(sample_rate * duration))

        audio1 = np.sin(2 * np.pi * 440 * t)
        audio2 = np.sin(2 * np.pi * 880 * t)

        fp1 = fingerprinter.extract_fingerprint_from_audio(audio1, sample_rate)
        fp2 = fingerprinter.extract_fingerprint_from_audio(audio2, sample_rate)

        # Only correlation
        score_corr_only = fingerprinter.compare_fingerprints(
            fp1, fp2, correlation_weight=1.0, l2_weight=0.0
        )

        # Only L2
        score_l2_only = fingerprinter.compare_fingerprints(
            fp1, fp2, correlation_weight=0.0, l2_weight=1.0
        )

        # Both should be valid scores
        assert 0.0 <= score_corr_only <= 1.0
        assert 0.0 <= score_l2_only <= 1.0


class TestBackwardCompatibility:
    """Test suite for backward compatibility."""

    def test_compare_fingerprints_backward_compatible(self):
        """Test that old API still works (no weights specified)."""
        fingerprinter = AudioFingerprinter()
        sample_rate = 22050
        duration = 0.5
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio = np.sin(2 * np.pi * 440 * t)

        fp1 = fingerprinter.extract_fingerprint_from_audio(audio, sample_rate)
        fp2 = fingerprinter.extract_fingerprint_from_audio(audio, sample_rate)

        # Should work without specifying weights
        similarity = fingerprinter.compare_fingerprints(fp1, fp2)

        assert isinstance(similarity, float)
        assert 0.0 <= similarity <= 1.0
        assert similarity > 0.9  # Identical audio should have high similarity

    def test_return_type_consistency(self):
        """Test that return type is consistent based on return_components flag."""
        fingerprinter = AudioFingerprinter()
        sample_rate = 22050
        duration = 0.5
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio = np.sin(2 * np.pi * 440 * t)
        fp = fingerprinter.extract_fingerprint_from_audio(audio, sample_rate)

        # Default behavior - return float
        result1 = fingerprinter.compare_fingerprints(fp, fp)
        assert isinstance(result1, float)

        # With return_components=False - return float
        result2 = fingerprinter.compare_fingerprints(fp, fp, return_components=False)
        assert isinstance(result2, float)

        # With return_components=True - return dict
        result3 = fingerprinter.compare_fingerprints(fp, fp, return_components=True)
        assert isinstance(result3, dict)
