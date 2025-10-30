"""
Fingerprinter factory for creating the appropriate fingerprinter based on configuration.

This module provides a unified interface for creating fingerprinters,
automatically selecting between original and optimized implementations
based on configuration settings.
"""

from typing import Any

from config.settings import Config
from src.core.audio_fingerprinting import AudioFingerprinter
from src.core.audio_fingerprinting_optimized import OptimizedAudioFingerprinter


def get_fingerprinter(**kwargs: Any) -> AudioFingerprinter | OptimizedAudioFingerprinter:
    """
    Get the appropriate fingerprinter based on configuration.
    
    This factory function automatically selects between the original and
    optimized implementations based on USE_OPTIMIZED_FINGERPRINTING config.
    
    Args:
        **kwargs: Additional arguments to pass to fingerprinter constructor.
                 Overrides config settings.
    
    Returns:
        Configured fingerprinter instance (either AudioFingerprinter or
        OptimizedAudioFingerprinter)
    
    Example:
        >>> # Use config defaults
        >>> fp = get_fingerprinter()
        >>> 
        >>> # Override config
        >>> fp = get_fingerprinter(use_gpu=True, max_workers=8)
    """
    # Check if we should use optimized version
    use_optimized = kwargs.pop("use_optimized", Config.USE_OPTIMIZED_FINGERPRINTING)
    
    if use_optimized:
        return _get_optimized_fingerprinter(**kwargs)
    else:
        return _get_standard_fingerprinter(**kwargs)


def _get_standard_fingerprinter(**kwargs: Any) -> AudioFingerprinter:
    """
    Create standard fingerprinter with config defaults.
    
    Args:
        **kwargs: Override config settings
        
    Returns:
        AudioFingerprinter instance
    """
    # Get config values with kwargs overrides
    sample_rate = kwargs.get("sample_rate", Config.FINGERPRINT_SAMPLE_RATE)
    n_fft = kwargs.get("n_fft", Config.FINGERPRINT_N_FFT)
    hop_length = kwargs.get("hop_length", Config.FINGERPRINT_HOP_LENGTH)
    
    return AudioFingerprinter(
        sample_rate=sample_rate,
        n_fft=n_fft,
        hop_length=hop_length,
    )


def _get_optimized_fingerprinter(**kwargs: Any) -> OptimizedAudioFingerprinter:
    """
    Create optimized fingerprinter with config defaults.
    
    Args:
        **kwargs: Override config settings
        
    Returns:
        OptimizedAudioFingerprinter instance
    """
    # Get config values with kwargs overrides
    sample_rate = kwargs.get("sample_rate", Config.FINGERPRINT_SAMPLE_RATE)
    n_fft = kwargs.get("n_fft", Config.FINGERPRINT_N_FFT)
    hop_length = kwargs.get("hop_length", Config.FINGERPRINT_HOP_LENGTH)
    
    # GPU settings
    use_gpu = kwargs.get("use_gpu", None)
    if use_gpu is None:
        # Auto-detect based on config
        gpu_config = Config.FINGERPRINT_USE_GPU
        if gpu_config == "auto":
            use_gpu = None  # Let OptimizedAudioFingerprinter auto-detect
        else:
            use_gpu = gpu_config == "true"
    
    # Batch processing settings
    enable_batch_mode = kwargs.get("enable_batch_mode", True)
    max_workers = kwargs.get("max_workers", Config.FINGERPRINT_MAX_WORKERS)
    
    return OptimizedAudioFingerprinter(
        sample_rate=sample_rate,
        n_fft=n_fft,
        hop_length=hop_length,
        use_gpu=use_gpu,
        enable_batch_mode=enable_batch_mode,
        max_workers=max_workers,
    )


def get_lsh_index_config() -> dict[str, Any]:
    """
    Get LSH index configuration from config.
    
    Returns:
        Dictionary with LSH configuration parameters
    """
    return {
        "enabled": Config.USE_LSH_INDEX,
        "num_tables": Config.LSH_NUM_TABLES,
        "hash_size": Config.LSH_HASH_SIZE,
        "max_candidates": Config.LSH_MAX_CANDIDATES,
    }


def is_multi_resolution_enabled() -> bool:
    """
    Check if multi-resolution fingerprinting is enabled.
    
    Returns:
        True if multi-resolution is enabled
    """
    return Config.USE_MULTI_RESOLUTION
