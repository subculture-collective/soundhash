"""Tests for fingerprinter factory."""

import pytest

from config.settings import Config
from src.core.audio_fingerprinting import AudioFingerprinter
from src.core.audio_fingerprinting_optimized import OptimizedAudioFingerprinter
from src.core.fingerprinter_factory import (
    get_fingerprinter,
    get_lsh_index_config,
    is_multi_resolution_enabled,
)


class TestFingerprinterFactory:
    """Test suite for fingerprinter factory."""

    def test_get_standard_fingerprinter(self):
        """Test getting standard fingerprinter."""
        fp = get_fingerprinter(use_optimized=False)
        
        assert isinstance(fp, AudioFingerprinter)
        assert not isinstance(fp, OptimizedAudioFingerprinter)

    def test_get_optimized_fingerprinter(self):
        """Test getting optimized fingerprinter."""
        fp = get_fingerprinter(use_optimized=True)
        
        assert isinstance(fp, OptimizedAudioFingerprinter)

    def test_default_uses_config(self):
        """Test that default uses config setting."""
        # Save original config
        original = Config.USE_OPTIMIZED_FINGERPRINTING
        
        try:
            # Test with optimized enabled
            Config.USE_OPTIMIZED_FINGERPRINTING = True
            fp = get_fingerprinter()
            assert isinstance(fp, OptimizedAudioFingerprinter)
            
            # Test with optimized disabled
            Config.USE_OPTIMIZED_FINGERPRINTING = False
            fp = get_fingerprinter()
            assert isinstance(fp, AudioFingerprinter)
            assert not isinstance(fp, OptimizedAudioFingerprinter)
        finally:
            # Restore original config
            Config.USE_OPTIMIZED_FINGERPRINTING = original

    def test_custom_parameters(self):
        """Test passing custom parameters."""
        fp = get_fingerprinter(
            use_optimized=True,
            sample_rate=44100,
            n_fft=4096,
            hop_length=1024,
        )
        
        assert isinstance(fp, OptimizedAudioFingerprinter)
        assert fp.sample_rate == 44100
        assert fp.n_fft == 4096
        assert fp.hop_length == 1024

    def test_gpu_configuration(self):
        """Test GPU configuration."""
        # Explicit GPU enable
        fp = get_fingerprinter(use_optimized=True, use_gpu=True)
        assert isinstance(fp, OptimizedAudioFingerprinter)
        # Note: use_gpu might be False if CuPy not available
        
        # Explicit GPU disable
        fp = get_fingerprinter(use_optimized=True, use_gpu=False)
        assert isinstance(fp, OptimizedAudioFingerprinter)
        assert fp.use_gpu is False

    def test_batch_configuration(self):
        """Test batch processing configuration."""
        fp = get_fingerprinter(
            use_optimized=True,
            enable_batch_mode=True,
            max_workers=8,
        )
        
        assert isinstance(fp, OptimizedAudioFingerprinter)
        assert fp.enable_batch_mode is True
        assert fp.max_workers == 8

    def test_get_lsh_config(self):
        """Test getting LSH configuration."""
        config = get_lsh_index_config()
        
        assert "enabled" in config
        assert "num_tables" in config
        assert "hash_size" in config
        assert "max_candidates" in config
        
        assert isinstance(config["enabled"], bool)
        assert isinstance(config["num_tables"], int)
        assert isinstance(config["hash_size"], int)
        assert isinstance(config["max_candidates"], int)

    def test_multi_resolution_check(self):
        """Test multi-resolution enabled check."""
        enabled = is_multi_resolution_enabled()
        assert isinstance(enabled, bool)
