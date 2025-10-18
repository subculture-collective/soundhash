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
    """

    def __init__(
        self, sample_rate: int | None = None, n_fft: int = 2048, hop_length: int = 512
    ) -> None:
        self.sample_rate = sample_rate or Config.FINGERPRINT_SAMPLE_RATE
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

    def load_audio(self, file_path: str) -> tuple[np.ndarray, int]:
        """Load audio file and resample to target sample rate"""
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
        """Create a compact numerical representation of the fingerprint"""
        if not fingerprint_data:
            return np.array([])

        # Create a time-frequency matrix representation
        time_bins = len(fingerprint_data)
        freq_ranges = len(self.freq_ranges)

        # Create matrix: rows = time, columns = frequency ranges
        fingerprint_matrix = np.zeros((time_bins, freq_ranges))

        for time_idx, frame_data in enumerate(fingerprint_data):
            for peak in frame_data["peaks"]:
                freq_range_idx = peak["freq_range"]
                # Use magnitude as the value
                fingerprint_matrix[time_idx, freq_range_idx] += peak["magnitude"]

        # Flatten and normalize
        compact = fingerprint_matrix.flatten()
        if np.max(compact) > 0:
            compact = compact / np.max(compact)

        return compact

    def _hash_fingerprint(self, compact_fingerprint: np.ndarray) -> str:
        """Create a hash of the fingerprint for quick lookup"""
        # Quantize to reduce sensitivity to small variations
        quantized = np.round(compact_fingerprint * 1000).astype(np.int32)
        return hashlib.md5(quantized.tobytes()).hexdigest()

    def compare_fingerprints(self, fp1: dict[str, Any], fp2: dict[str, Any]) -> float:
        """
        Compare two fingerprints and return similarity score (0-1).
        Uses multiple comparison methods for robustness.
        """
        compact1 = fp1.get("compact_fingerprint")
        compact2 = fp2.get("compact_fingerprint")

        if compact1 is None or compact2 is None:
            return 0.0
        if len(compact1) == 0 or len(compact2) == 0:
            return 0.0

        # Ensure same length
        min_len = min(len(compact1), len(compact2))
        if min_len == 0:
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

        # Combined similarity score
        similarity = (abs(correlation) + euclidean_similarity) / 2.0
        return max(0.0, min(1.0, similarity))

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
