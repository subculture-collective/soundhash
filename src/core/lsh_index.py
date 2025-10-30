"""
Locality-Sensitive Hashing (LSH) for fast fingerprint similarity search.

LSH allows O(1) approximate nearest neighbor search instead of O(n) linear search.
This is crucial for production systems with millions of fingerprints.
"""

from collections import defaultdict
from typing import Any

import numpy as np


class LSHIndex:
    """
    Locality-Sensitive Hashing index for fast audio fingerprint search.
    
    Uses random hyperplanes to partition the fingerprint space.
    Similar fingerprints are likely to fall into the same hash buckets.
    
    Performance:
    - Build time: O(n) for n fingerprints
    - Query time: O(1) average case (vs O(n) linear scan)
    - Memory: O(n * num_tables) 
    """
    
    def __init__(self, input_dim: int, num_tables: int = 5, hash_size: int = 12):
        """
        Initialize LSH index.
        
        Args:
            input_dim: Dimension of input fingerprints
            num_tables: Number of hash tables (more = better recall, slower)
            hash_size: Number of bits in each hash (2^hash_size buckets per table)
        """
        self.input_dim = input_dim
        self.num_tables = num_tables
        self.hash_size = hash_size
        
        # Generate random hyperplanes for each table
        # Note: Using fixed seed (42) ensures consistent hyperplanes across process restarts,
        # but means all LSH indexes will use identical hyperplanes. For distributed systems
        # or multiple independent indexes, consider making seed configurable.
        self.hyperplanes = []
        rng = np.random.RandomState(42)  # Fixed seed for reproducibility
        for _ in range(num_tables):
            planes = rng.randn(hash_size, input_dim)
            # Normalize hyperplanes
            planes = planes / np.linalg.norm(planes, axis=1, keepdims=True)
            self.hyperplanes.append(planes)
        
        # Hash tables: table_id -> hash_value -> list of (identifier, fingerprint)
        self.tables: list[dict[str, list[tuple[Any, np.ndarray]]]] = [
            defaultdict(list) for _ in range(num_tables)
        ]
        
        self.num_indexed = 0
    
    def _hash_fingerprint(self, fingerprint: np.ndarray, table_idx: int) -> str:
        """
        Compute LSH hash for a fingerprint.
        
        Args:
            fingerprint: Input vector
            table_idx: Which hash table to use
            
        Returns:
            Binary hash string
        """
        # Project onto hyperplanes
        projections = np.dot(self.hyperplanes[table_idx], fingerprint)
        
        # Convert to binary hash
        bits = (projections >= 0).astype(int)
        
        # Convert to string for dictionary key
        return ''.join(map(str, bits))
    
    def index_fingerprint(self, identifier: Any, fingerprint: np.ndarray) -> None:
        """
        Add a fingerprint to the index.
        
        Args:
            identifier: Unique identifier for this fingerprint
            fingerprint: Fingerprint vector (must be same dimension as input_dim)
        """
        if len(fingerprint) != self.input_dim:
            # Pad or truncate to match dimension
            if len(fingerprint) < self.input_dim:
                padded = np.zeros(self.input_dim)
                padded[:len(fingerprint)] = fingerprint
                fingerprint = padded
            else:
                fingerprint = fingerprint[:self.input_dim]
        
        # Add to each hash table
        for table_idx in range(self.num_tables):
            hash_val = self._hash_fingerprint(fingerprint, table_idx)
            self.tables[table_idx][hash_val].append((identifier, fingerprint))
        
        self.num_indexed += 1
    
    def query_candidates(
        self, 
        query_fingerprint: np.ndarray, 
        max_candidates: int = 100
    ) -> list[tuple[Any, np.ndarray]]:
        """
        Find candidate fingerprints for a query.
        
        Args:
            query_fingerprint: Query vector
            max_candidates: Maximum number of candidates to return
            
        Returns:
            List of (identifier, fingerprint) tuples
        """
        if len(query_fingerprint) != self.input_dim:
            # Pad or truncate to match dimension
            if len(query_fingerprint) < self.input_dim:
                padded = np.zeros(self.input_dim)
                padded[:len(query_fingerprint)] = query_fingerprint
                query_fingerprint = padded
            else:
                query_fingerprint = query_fingerprint[:self.input_dim]
        
        # Collect candidates from all tables
        # Use dict to deduplicate by identifier
        candidates_dict = {}
        
        for table_idx in range(self.num_tables):
            hash_val = self._hash_fingerprint(query_fingerprint, table_idx)
            
            # Get all fingerprints in the same bucket
            bucket = self.tables[table_idx].get(hash_val, [])
            
            for identifier, fingerprint in bucket:
                if identifier not in candidates_dict:
                    candidates_dict[identifier] = fingerprint
            
            if len(candidates_dict) >= max_candidates:
                break
        
        # Convert to list and limit
        result = [(id_, fp) for id_, fp in candidates_dict.items()][:max_candidates]
        return result
    
    def clear(self) -> None:
        """Clear the index."""
        self.tables = [defaultdict(list) for _ in range(self.num_tables)]
        self.num_indexed = 0
    
    def get_stats(self) -> dict[str, Any]:
        """Get index statistics."""
        bucket_sizes = []
        for table in self.tables:
            bucket_sizes.extend([len(bucket) for bucket in table.values()])
        
        return {
            "num_indexed": self.num_indexed,
            "num_tables": self.num_tables,
            "hash_size": self.hash_size,
            "avg_bucket_size": np.mean(bucket_sizes) if bucket_sizes else 0,
            "max_bucket_size": max(bucket_sizes) if bucket_sizes else 0,
            "total_buckets": sum(len(table) for table in self.tables),
        }


class MultiResolutionFingerprinter:
    """
    Multi-resolution fingerprinting for better matching across different audio qualities.
    
    Creates fingerprints at multiple FFT resolutions to capture both
    fine-grained and coarse-grained spectral features.
    """
    
    def __init__(self, sample_rate: int = 22050):
        """
        Initialize multi-resolution fingerprinter.
        
        Args:
            sample_rate: Audio sample rate
        """
        self.sample_rate = sample_rate
        
        # Multiple resolutions: coarse, medium, fine
        self.resolutions = [
            {"n_fft": 1024, "hop_length": 256, "weight": 0.3},   # Coarse
            {"n_fft": 2048, "hop_length": 512, "weight": 0.5},   # Medium (default)
            {"n_fft": 4096, "hop_length": 1024, "weight": 0.2},  # Fine
        ]
    
    def extract_multi_resolution(
        self, 
        audio_data: np.ndarray,
        fingerprinter_class
    ) -> list[dict[str, Any]]:
        """
        Extract fingerprints at multiple resolutions.
        
        Args:
            audio_data: Audio samples
            fingerprinter_class: Fingerprinter class to use
            
        Returns:
            List of fingerprint dictionaries, one per resolution
        """
        fingerprints = []
        
        for resolution in self.resolutions:
            fp = fingerprinter_class(
                sample_rate=self.sample_rate,
                n_fft=resolution["n_fft"],
                hop_length=resolution["hop_length"],
            )
            
            result = fp.extract_fingerprint_from_audio(audio_data, self.sample_rate)
            result["resolution"] = resolution
            fingerprints.append(result)
        
        return fingerprints
    
    def compare_multi_resolution(
        self,
        query_fps: list[dict[str, Any]],
        candidate_fps: list[dict[str, Any]],
        fingerprinter
    ) -> float:
        """
        Compare multi-resolution fingerprints with weighted average.
        
        Args:
            query_fps: List of query fingerprints at different resolutions
            candidate_fps: List of candidate fingerprints at different resolutions
            fingerprinter: Fingerprinter instance for comparison
            
        Returns:
            Weighted similarity score
        """
        if len(query_fps) != len(candidate_fps):
            return 0.0
        
        total_score = 0.0
        total_weight = 0.0
        
        for query_fp, candidate_fp in zip(query_fps, candidate_fps):
            weight = query_fp["resolution"]["weight"]
            score = fingerprinter.compare_fingerprints(query_fp, candidate_fp)
            total_score += score * weight
            total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.0
