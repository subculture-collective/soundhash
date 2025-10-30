#!/usr/bin/env python3
"""
Advanced Audio Fingerprinting Demo

Demonstrates the optimized fingerprinting features:
- Batch processing
- GPU acceleration
- LSH indexing
- Multi-resolution fingerprinting
"""

import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import soundfile as sf

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.audio_fingerprinting_optimized import OptimizedAudioFingerprinter
from src.core.lsh_index import LSHIndex, MultiResolutionFingerprinter


def demo_basic_usage():
    """Demo basic optimized fingerprinting."""
    print("\n" + "="*80)
    print("DEMO 1: Basic Optimized Fingerprinting")
    print("="*80)
    
    # Create fingerprinter
    fingerprinter = OptimizedAudioFingerprinter()
    
    # Check device info
    device_info = fingerprinter.get_device_info()
    print(f"\nDevice Information:")
    print(f"  CPU Cores: {device_info['cpu_cores']}")
    print(f"  GPU Available: {device_info['gpu_available']}")
    print(f"  GPU Enabled: {device_info['gpu_enabled']}")
    
    # Generate test audio
    print("\nGenerating test audio (5 seconds)...")
    sample_rate = 22050
    duration = 5.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio = (np.sin(2 * np.pi * 220.0 * t) * 0.3 +
            np.sin(2 * np.pi * 440.0 * t) * 1.0 +
            np.sin(2 * np.pi * 880.0 * t) * 0.5)
    
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        sf.write(tmp.name, audio, sample_rate)
        
        try:
            # Extract fingerprint
            print("Extracting fingerprint...")
            start = time.time()
            fp = fingerprinter.extract_fingerprint(tmp.name)
            elapsed = (time.time() - start) * 1000
            
            print(f"\n✓ Extraction complete!")
            print(f"  Time: {elapsed:.2f}ms")
            print(f"  Peaks: {fp['peak_count']}")
            print(f"  Confidence: {fp['confidence_score']:.3f}")
            print(f"  Hash: {fp['fingerprint_hash'][:16]}...")
        finally:
            Path(tmp.name).unlink(missing_ok=True)


def demo_batch_processing():
    """Demo batch processing."""
    print("\n" + "="*80)
    print("DEMO 2: Batch Processing")
    print("="*80)
    
    # Generate test files
    print("\nGenerating 10 test audio files...")
    sample_rate = 22050
    duration = 2.0
    files = []
    
    for i in range(10):
        t = np.linspace(0, duration, int(sample_rate * duration))
        freq = 220 * (2 ** (i / 12))  # Chromatic scale
        audio = np.sin(2 * np.pi * freq * t)
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            sf.write(tmp.name, audio, sample_rate)
            files.append(tmp.name)
    
    try:
        # Sequential processing
        print("\nProcessing sequentially...")
        fingerprinter = OptimizedAudioFingerprinter(enable_batch_mode=False)
        start = time.time()
        for f in files:
            fingerprinter.extract_fingerprint(f)
        time_sequential = (time.time() - start) * 1000
        
        # Batch processing
        print("Processing in batch (multiprocessing)...")
        fingerprinter_batch = OptimizedAudioFingerprinter(
            enable_batch_mode=True,
            max_workers=4
        )
        start = time.time()
        fingerprints = fingerprinter_batch.batch_extract_fingerprints(
            files,
            use_multiprocessing=True
        )
        time_batch = (time.time() - start) * 1000
        
        print(f"\n✓ Batch processing complete!")
        print(f"  Sequential: {time_sequential:.2f}ms")
        print(f"  Batch: {time_batch:.2f}ms")
        print(f"  Speedup: {time_sequential/time_batch:.2f}x")
        print(f"  Processed: {len(fingerprints)} files")
    finally:
        for f in files:
            Path(f).unlink(missing_ok=True)


def demo_lsh_indexing():
    """Demo LSH indexing for fast search."""
    print("\n" + "="*80)
    print("DEMO 3: LSH Indexing for Fast Search")
    print("="*80)
    
    print("\nCreating synthetic fingerprint database...")
    
    # Create fingerprinter
    fingerprinter = OptimizedAudioFingerprinter()
    
    # Generate test audio library
    sample_rate = 22050
    duration = 3.0
    num_songs = 100
    
    print(f"Generating {num_songs} synthetic songs...")
    library = []
    for i in range(num_songs):
        t = np.linspace(0, duration, int(sample_rate * duration))
        # Random frequencies in musical range
        freq1 = 220 * (2 ** (np.random.randint(0, 24) / 12))
        freq2 = freq1 * (2 ** (np.random.randint(1, 4) / 12))
        audio = (np.sin(2 * np.pi * freq1 * t) * 0.7 +
                np.sin(2 * np.pi * freq2 * t) * 0.3)
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            sf.write(tmp.name, audio, sample_rate)
            fp = fingerprinter.extract_fingerprint(tmp.name)
            library.append((f"song_{i:03d}", fp))
            Path(tmp.name).unlink(missing_ok=True)
    
    print(f"✓ Generated {len(library)} fingerprints")
    
    # Create LSH index
    print("\nBuilding LSH index...")
    fp_dim = len(library[0][1]["compact_fingerprint"])
    lsh_index = LSHIndex(
        input_dim=fp_dim,
        num_tables=5,
        hash_size=10
    )
    
    start = time.time()
    for song_id, fp in library:
        lsh_index.index_fingerprint(song_id, fp["compact_fingerprint"])
    index_time = (time.time() - start) * 1000
    
    stats = lsh_index.get_stats()
    print(f"✓ Index built in {index_time:.2f}ms")
    print(f"  Indexed: {stats['num_indexed']} fingerprints")
    print(f"  Tables: {stats['num_tables']}")
    print(f"  Avg bucket size: {stats['avg_bucket_size']:.1f}")
    print(f"  Max bucket size: {stats['max_bucket_size']}")
    
    # Query with LSH
    print("\nQuerying with LSH (fast approximate search)...")
    query_fp = library[42][1]  # Use one from the library
    
    start = time.time()
    candidates = lsh_index.query_candidates(
        query_fp["compact_fingerprint"],
        max_candidates=20
    )
    lsh_time = (time.time() - start) * 1000
    
    print(f"✓ LSH query completed in {lsh_time:.4f}ms")
    print(f"  Candidates found: {len(candidates)}")
    
    # Compare with linear search
    print("\nComparing with linear search...")
    start = time.time()
    linear_matches = []
    for song_id, fp in library:
        similarity = fingerprinter.compare_fingerprints(query_fp, fp)
        if similarity > 0.7:
            linear_matches.append((song_id, similarity))
    linear_time = (time.time() - start) * 1000
    
    print(f"✓ Linear search completed in {linear_time:.2f}ms")
    print(f"  Matches found: {len(linear_matches)}")
    print(f"  LSH speedup: {linear_time/lsh_time:.2f}x")
    
    # Refine LSH candidates
    print("\nRefining LSH candidates with exact comparison...")
    start = time.time()
    lsh_matches = []
    for song_id, candidate_fp_compact in candidates:
        # Find full fingerprint
        full_fp = next((fp for sid, fp in library if sid == song_id), None)
        if full_fp:
            similarity = fingerprinter.compare_fingerprints(query_fp, full_fp)
            if similarity > 0.7:
                lsh_matches.append((song_id, similarity))
    refine_time = (time.time() - start) * 1000
    
    print(f"✓ Refinement completed in {refine_time:.2f}ms")
    print(f"  Total LSH + refine: {lsh_time + refine_time:.2f}ms")
    print(f"  Final matches: {len(lsh_matches)}")
    print(f"  Overall speedup: {linear_time/(lsh_time + refine_time):.2f}x")


def demo_multi_resolution():
    """Demo multi-resolution fingerprinting."""
    print("\n" + "="*80)
    print("DEMO 4: Multi-Resolution Fingerprinting")
    print("="*80)
    
    # Generate test audio
    sample_rate = 22050
    duration = 3.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Create audio with frequencies across spectrum
    audio_original = (
        np.sin(2 * np.pi * 220.0 * t) * 0.3 +
        np.sin(2 * np.pi * 440.0 * t) * 0.5 +
        np.sin(2 * np.pi * 880.0 * t) * 0.3 +
        np.sin(2 * np.pi * 1760.0 * t) * 0.2
    )
    
    # Create slightly modified version (simulating different quality)
    audio_modified = audio_original + np.random.randn(len(audio_original)) * 0.05
    
    # Multi-resolution fingerprinter
    mrf = MultiResolutionFingerprinter(sample_rate=sample_rate)
    
    print("\nExtracting multi-resolution fingerprints...")
    print("  Original audio...")
    start = time.time()
    fps_original = mrf.extract_multi_resolution(
        audio_original,
        OptimizedAudioFingerprinter
    )
    time_original = (time.time() - start) * 1000
    
    print("  Modified audio...")
    start = time.time()
    fps_modified = mrf.extract_multi_resolution(
        audio_modified,
        OptimizedAudioFingerprinter
    )
    time_modified = (time.time() - start) * 1000
    
    print(f"\n✓ Multi-resolution extraction complete")
    print(f"  Original: {time_original:.2f}ms")
    print(f"  Modified: {time_modified:.2f}ms")
    print(f"  Resolutions: {len(fps_original)}")
    
    # Compare
    print("\nComparing fingerprints...")
    fingerprinter = OptimizedAudioFingerprinter()
    
    # Single resolution comparison (medium)
    single_score = fingerprinter.compare_fingerprints(
        fps_original[1],  # Medium resolution
        fps_modified[1]
    )
    
    # Multi-resolution comparison
    multi_score = mrf.compare_multi_resolution(
        fps_original,
        fps_modified,
        fingerprinter
    )
    
    print(f"\n✓ Comparison complete")
    print(f"  Single resolution score: {single_score:.3f}")
    print(f"  Multi-resolution score: {multi_score:.3f}")
    print(f"  Improvement: {((multi_score - single_score) / single_score * 100):+.1f}%")


def main():
    """Run all demos."""
    print("="*80)
    print("Advanced Audio Fingerprinting Demo")
    print("="*80)
    print("\nThis demo showcases the optimized fingerprinting features:")
    print("  1. Basic optimized fingerprinting with device detection")
    print("  2. Batch processing with multiprocessing")
    print("  3. LSH indexing for fast approximate search")
    print("  4. Multi-resolution fingerprinting")
    
    try:
        demo_basic_usage()
        demo_batch_processing()
        demo_lsh_indexing()
        demo_multi_resolution()
        
        print("\n" + "="*80)
        print("✅ All demos completed successfully!")
        print("="*80)
        print("\nFor more information, see:")
        print("  - docs/PERFORMANCE_OPTIMIZATION.md")
        print("  - scripts/benchmark_fingerprinting.py")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
