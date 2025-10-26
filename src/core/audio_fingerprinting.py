import hashlib
import pickle
from typing import Any

import librosa
import numpy as np
from scipy.signal import find_peaks

from config.settings import Config


class AudioFingerprinter:
    """
    Audio fingerprinting system using spectral peak analysis.
    Creates unique signatures for audio segments that can be matched against a database.

    The fingerprinting process:
    1. Load audio and convert to mono at target sample rate
    2. Compute STFT (Short-Time Fourier Transform) with validated parameters
    3. Extract spectral peaks across frequency ranges
    4. Create normalized compact fingerprint vector
    5. Generate deterministic MD5 hash from quantized fingerprint

    Parameters validated to ensure robust operation:
    - sample_rate: Must be positive (typically 22050 Hz)
    - n_fft: Must be power of 2 and >= 256 for sufficient frequency resolution
    - hop_length: Must be positive and <= n_fft for proper overlap
    """

    def __init__(
        self, sample_rate: int | None = None, n_fft: int = 2048, hop_length: int = 512
    ) -> None:
<<<<<<< Updated upstream
        # Use config default if not specified (explicitly check for None, not falsy)
        if sample_rate is None:
            self.sample_rate = Config.FINGERPRINT_SAMPLE_RATE
        else:
            self.sample_rate = sample_rate

        # Validate parameters
        self._validate_parameters(self.sample_rate, n_fft, hop_length)

=======
        self.sample_rate = sample_rate or Config.FINGERPRINT_SAMPLE_RATE
>>>>>>> Stashed changes
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.freq_bins = n_fft // 2 + 1

        # Frequency ranges for peak detection (in Hz)
        self.freq_ranges: list[tuple[int, int]] = [
            (0, 250),  # Sub-bass
            (250, 500),  # Bass
            (500, 2000),  # Low midrange
            (2000, 4000),  # High midrange
            (4000, 8000),  # Presence
            (8000, 16000),  # Brilliance
        ]

        # Convert frequency ranges to bin indices
        self.bin_ranges: list[tuple[int, int]] = []
        for low_freq, high_freq in self.freq_ranges:
            low_bin = int(low_freq * self.n_fft / self.sample_rate)
            high_bin = int(high_freq * self.n_fft / self.sample_rate)
            self.bin_ranges.append((low_bin, high_bin))

    def _validate_parameters(self, sample_rate: int, n_fft: int, hop_length: int) -> None:
        """
        Validate STFT parameters for robustness.

        Args:
            sample_rate: Audio sample rate in Hz
            n_fft: FFT window size
            hop_length: Number of samples between successive frames

        Raises:
            ValueError: If any parameter is invalid
        """
        if sample_rate <= 0:
            raise ValueError(f"sample_rate must be positive, got {sample_rate}")

        if n_fft < 256:
            raise ValueError(
                f"n_fft must be at least 256 for sufficient frequency resolution, got {n_fft}"
            )

        if n_fft & (n_fft - 1) != 0:
            raise ValueError(
                f"n_fft should be a power of 2 for efficient FFT computation, got {n_fft}"
            )

        if hop_length <= 0:
            raise ValueError(f"hop_length must be positive, got {hop_length}")

        if hop_length > n_fft:
            raise ValueError(
                f"hop_length ({hop_length}) should not exceed n_fft ({n_fft}) "
                "to ensure proper frame overlap"
            )

    def load_audio(self, file_path: str) -> tuple[np.ndarray, int]:
        """
        Load audio file, convert to mono, and resample to target sample rate.

        Args:
            file_path: Path to audio file

        Returns:
            Tuple of (audio_data, sample_rate) where audio_data is mono float32

        Note:
            Librosa automatically converts to mono by averaging channels if stereo.
        """
        try:
            y, sr = librosa.load(file_path, sr=self.sample_rate)
            return y, sr
        except Exception as e:
            raise ValueError(f"Error loading audio file {file_path}: {str(e)}") from e

    def extract_fingerprint(self, audio_file: str) -> dict[str, Any]:
        """
        Extract audio fingerprint from file.
        Returns dictionary with fingerprint data and metadata.
        """
        y, sr = self.load_audio(audio_file)
        return self.extract_fingerprint_from_audio(y, sr)

    def extract_fingerprint_from_audio(self, y: np.ndarray, sr: int) -> dict[str, Any]:
        """Extract fingerprint from audio data"""

        # Compute STFT
        stft = librosa.stft(y, n_fft=self.n_fft, hop_length=self.hop_length)
        magnitude = np.abs(stft)

        # Extract spectral peaks for each time frame
        fingerprint_data: list[dict[str, Any]] = []
        confidence_scores: list[float] = []

        for frame_idx, frame in enumerate(magnitude.T):
            frame_peaks = self._extract_frame_peaks(frame)
            if frame_peaks:
                fingerprint_data.append(
                    {"time": frame_idx * self.hop_length / sr, "peaks": frame_peaks}
                )

                # Calculate confidence based on peak strength
                peak_strengths = [peak["magnitude"] for peak in frame_peaks]
                confidence = np.mean(peak_strengths) if peak_strengths else 0.0
                confidence_scores.append(float(confidence))

        # Create compact fingerprint representation
        compact_fingerprint = self._create_compact_fingerprint(fingerprint_data)

        # Generate hash for quick lookup
        fingerprint_hash = self._hash_fingerprint(compact_fingerprint)

        # Count peaks safely by iterating through fingerprint_data
        peak_count = sum(len(frame["peaks"]) for frame in fingerprint_data)

        return {
            "fingerprint_data": fingerprint_data,
            "compact_fingerprint": compact_fingerprint,
            "fingerprint_hash": fingerprint_hash,
            "confidence_score": float(np.mean(confidence_scores)) if confidence_scores else 0.0,
            "peak_count": peak_count,
            "duration": float(len(y) / sr),
            "sample_rate": sr,
        }

    def _extract_frame_peaks(
        self, frame: np.ndarray, max_peaks_per_range: int = 3
    ) -> list[dict[str, Any]]:
        """Extract spectral peaks from a single frame"""
        frame_peaks = []

        for range_idx, (low_bin, high_bin) in enumerate(self.bin_ranges):
            if high_bin >= len(frame):
                high_bin = len(frame) - 1

            range_data = frame[low_bin:high_bin]
            if len(range_data) == 0:
                continue

            # Find peaks in this frequency range
            threshold = np.mean(range_data) + 2 * np.std(range_data)
            peaks, properties = find_peaks(
                range_data, height=threshold, distance=5  # Minimum distance between peaks
            )

            if len(peaks) == 0:
                continue

            # Sort peaks by magnitude and take top ones
            peak_magnitudes = range_data[peaks]
            sorted_indices = np.argsort(peak_magnitudes)[::-1]
            top_peaks = sorted_indices[:max_peaks_per_range]

            for peak_idx in top_peaks:
                actual_bin = low_bin + peaks[peak_idx]
                frequency = actual_bin * self.sample_rate / self.n_fft

                frame_peaks.append(
                    {
                        "frequency": frequency,
                        "bin": actual_bin,
                        "magnitude": float(peak_magnitudes[peak_idx]),
                        "freq_range": range_idx,
                    }
                )

        return frame_peaks

    def _create_compact_fingerprint(self, fingerprint_data: list[dict[str, Any]]) -> np.ndarray:
        """
        Create a compact numerical representation of the fingerprint.

        Process:
        1. Creates time-frequency matrix (time_bins x freq_ranges)
        2. Accumulates peak magnitudes for each time-frequency cell
        3. Flattens matrix to 1D vector
        4. Normalizes to [0, 1] range by dividing by maximum value

        Normalization ensures:
        - Consistent scale across different audio volumes
        - Comparable fingerprints regardless of input amplitude
        - Deterministic hashing with quantization

        Args:
            fingerprint_data: List of frame data with peaks

        Returns:
            Normalized 1D numpy array (float64) in range [0, 1]
        """
        if not fingerprint_data:
            return np.array([], dtype=np.float64)

        # Create a time-frequency matrix representation
        time_bins = len(fingerprint_data)
        freq_ranges = len(self.freq_ranges)

        # Create matrix: rows = time, columns = frequency ranges
        fingerprint_matrix = np.zeros((time_bins, freq_ranges), dtype=np.float64)

        for time_idx, frame_data in enumerate(fingerprint_data):
            for peak in frame_data["peaks"]:
                freq_range_idx = peak["freq_range"]
                # Use magnitude as the value
                fingerprint_matrix[time_idx, freq_range_idx] += peak["magnitude"]

        # Flatten and normalize to [0, 1]
        compact = fingerprint_matrix.flatten()
        max_val = np.max(compact)
        if max_val > 0:
            compact = compact / max_val

        return compact

    def _hash_fingerprint(self, compact_fingerprint: np.ndarray) -> str:
        """
        Create a deterministic MD5 hash of the fingerprint for quick lookup.

        Process:
        1. Quantizes normalized values to integers (multiply by 1000, round)
        2. Converts to int32 array for consistent byte representation
        3. Generates MD5 hash from byte data

        Determinism guarantees:
        - Same input audio produces same hash across runs
        - Same hash across different platforms (same Python/NumPy version)
        - Quantization reduces sensitivity to tiny floating-point variations

        Args:
            compact_fingerprint: Normalized fingerprint vector

        Returns:
            32-character hexadecimal MD5 hash string
        """
        # Quantize to reduce sensitivity to small variations
        quantized = np.round(compact_fingerprint * 1000).astype(np.int32)
        return hashlib.md5(quantized.tobytes()).hexdigest()

    def compare_fingerprints(
        self,
        fp1: dict[str, Any],
        fp2: dict[str, Any],
        correlation_weight: float | None = None,
        l2_weight: float | None = None,
        return_components: bool = False,
    ) -> float | dict[str, float]:
        """
        Compare two fingerprints and return similarity score (0-1).
<<<<<<< Updated upstream

        The similarity metric combines two complementary approaches:
        1. Correlation coefficient: Measures linear relationship (shape similarity)
        2. Normalized Euclidean distance: Measures absolute difference (magnitude similarity)

        Final score = correlation_weight * |correlation| + l2_weight * euclidean_similarity

        Recommended thresholds for matching:
        - > 0.85: Very high confidence match (same audio)
        - 0.70-0.85: High confidence match (likely same audio, minor variations)
        - 0.50-0.70: Medium confidence (similar but may be different)
        - < 0.50: Low confidence (probably different audio)

        Args:
            fp1: First fingerprint dictionary with 'compact_fingerprint' key
            fp2: Second fingerprint dictionary with 'compact_fingerprint' key
            correlation_weight: Weight for correlation component
                (default from Config)
            l2_weight: Weight for L2 similarity component (default from Config)
            return_components: If True, return dict with individual components
                and combined score

        Returns:
            Similarity score between 0.0 (completely different) and 1.0
            (identical). Or dict with 'correlation', 'l2_similarity', and
            'combined_score' if return_components=True
        """
        # Use config defaults if not specified
        if correlation_weight is None:
            correlation_weight = Config.SIMILARITY_CORRELATION_WEIGHT
        if l2_weight is None:
            l2_weight = Config.SIMILARITY_L2_WEIGHT

        compact1 = fp1.get("compact_fingerprint")
        compact2 = fp2.get("compact_fingerprint")

        if compact1 is None or compact2 is None:
            if return_components:
                return {"correlation": 0.0, "l2_similarity": 0.0, "combined_score": 0.0}
            return 0.0
        if len(compact1) == 0 or len(compact2) == 0:
            if return_components:
                return {"correlation": 0.0, "l2_similarity": 0.0, "combined_score": 0.0}
            return 0.0
=======
        Uses multiple comparison methods for robustness.
        """
        if not fp1.get("compact_fingerprint") or not fp2.get("compact_fingerprint"):
            return 0.0

        compact1 = fp1["compact_fingerprint"]
        compact2 = fp2["compact_fingerprint"]
>>>>>>> Stashed changes

        # Ensure same length
        min_len = min(len(compact1), len(compact2))
        if min_len == 0:
            if return_components:
                return {"correlation": 0.0, "l2_similarity": 0.0, "combined_score": 0.0}
            return 0.0

        compact1 = compact1[:min_len]
        compact2 = compact2[:min_len]

        # Calculate correlation coefficient
        correlation = np.corrcoef(compact1, compact2)[0, 1]
        if np.isnan(correlation):
            correlation = 0.0

        # Calculate normalized euclidean distance
        euclidean = np.linalg.norm(compact1 - compact2)
        max_distance = np.sqrt(2 * min_len)  # Maximum possible distance
        euclidean_similarity = 1.0 - (euclidean / max_distance)

        # Combined similarity score using weighted mean
        similarity = (abs(correlation) * correlation_weight) + (
            euclidean_similarity * l2_weight
        )
        similarity = max(0.0, min(1.0, similarity))

        if return_components:
            return {
                "correlation": abs(correlation),
                "l2_similarity": euclidean_similarity,
                "combined_score": similarity,
            }

        return similarity

    def serialize_fingerprint(self, fingerprint: dict[str, Any]) -> bytes:
        """Serialize fingerprint for database storage"""
        # Only serialize the compact representation and metadata
        serializable = {
            "compact_fingerprint": fingerprint["compact_fingerprint"],
            "confidence_score": fingerprint["confidence_score"],
            "peak_count": fingerprint["peak_count"],
            "duration": fingerprint["duration"],
            "sample_rate": fingerprint["sample_rate"],
        }
        return pickle.dumps(serializable)

    def deserialize_fingerprint(self, data: bytes) -> dict[str, Any]:
        """Deserialize fingerprint from database"""
        return pickle.loads(data)

    def rank_matches(
        self,
        query_fp: dict[str, Any],
        candidate_fps: list[tuple[Any, dict[str, Any]]],
        min_score: float | None = None,
        min_duration: float | None = None,
        correlation_threshold: float | None = None,
        l2_threshold: float | None = None,
    ) -> list[dict[str, Any]]:
        """
        Rank candidate fingerprints against a query fingerprint.

        Filters candidates based on thresholds and ranks by combined similarity score.
        Applies tie-breaking rules: higher correlation > higher L2 > longer duration.

        Args:
            query_fp: Query fingerprint dictionary
            candidate_fps: List of (identifier, fingerprint_dict) tuples
            min_score: Minimum combined similarity score (default from Config)
            min_duration: Minimum duration in seconds (default from Config)
            correlation_threshold: Minimum correlation score (default from Config)
            l2_threshold: Minimum L2 similarity score (default from Config)

        Returns:
            List of match dictionaries sorted by relevance, each containing:
            - identifier: The candidate identifier
            - score: Combined similarity score
            - correlation: Correlation component
            - l2_similarity: L2 similarity component
            - duration: Candidate duration
        """
        # Use config defaults if not specified
        if min_score is None:
            min_score = Config.SIMILARITY_MIN_SCORE
        if min_duration is None:
            min_duration = Config.SIMILARITY_MIN_DURATION
        if correlation_threshold is None:
            correlation_threshold = Config.SIMILARITY_CORRELATION_THRESHOLD
        if l2_threshold is None:
            l2_threshold = Config.SIMILARITY_L2_THRESHOLD

        matches = []
        for identifier, candidate_fp in candidate_fps:
            # Check minimum duration
            candidate_duration = candidate_fp.get("duration", 0.0)
            if candidate_duration < min_duration:
                continue

            # Compare fingerprints
            components = self.compare_fingerprints(query_fp, candidate_fp, return_components=True)

            # Apply thresholds
            if components["correlation"] < correlation_threshold:
                continue
            if components["l2_similarity"] < l2_threshold:
                continue
            if components["combined_score"] < min_score:
                continue

            matches.append(
                {
                    "identifier": identifier,
                    "score": components["combined_score"],
                    "correlation": components["correlation"],
                    "l2_similarity": components["l2_similarity"],
                    "duration": candidate_duration,
                }
            )

        # Sort by: score (desc), correlation (desc), l2_similarity (desc), duration (desc)
        matches.sort(
            key=lambda m: (
                m["score"],
                m["correlation"],
                m["l2_similarity"],
                m["duration"],
            ),
            reverse=True,
        )

        return matches
