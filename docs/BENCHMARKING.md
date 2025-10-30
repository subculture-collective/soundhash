# Benchmarking Guide

This guide explains how to benchmark the SoundHash audio fingerprinting system and interpret results.

## Quick Start

Run the comprehensive benchmark suite:

```bash
python scripts/benchmark_fingerprinting.py
```

This generates:
- `benchmark_results.json` - Raw performance data
- `benchmark_fingerprinting_report.md` - Human-readable summary

## Benchmark Categories

### 1. Extraction Speed

Tests fingerprint extraction performance across different audio durations (1s, 5s, 10s, 30s, 60s).

**Key Metrics:**
- **Time per second of audio**: Target < 16.7 ms/s (for <1s per minute goal)
- **Speedup**: Original vs Optimized implementation
- **Scalability**: How performance scales with audio length

**Example Output:**
```
Duration | Original (ms) | Optimized (ms) | Speedup | Status
---------|---------------|----------------|---------|--------
60s      | 1195.5        | 1267.2         | 0.94x   | ❌ FAIL
```

### 2. Batch Processing

Tests parallel processing performance with multiple files.

**Key Metrics:**
- **Sequential time**: Processing files one at a time
- **Batch time**: Processing files in parallel
- **Speedup**: Sequential / Batch time

**Example Output:**
```
Batch Size | Sequential (ms) | Multiprocess (ms) | Speedup
-----------|-----------------|-------------------|--------
20         | 2074            | 900               | 2.30x
```

### 3. Audio Complexity Impact

Tests how audio complexity affects performance.

**Complexity Types:**
- **Simple**: Single sine wave
- **Complex**: Multiple harmonics
- **Noise**: Audio with background noise

### 4. Fingerprint Comparison Speed

Tests how fast fingerprints can be compared.

**Key Metrics:**
- **Time per comparison**: In milliseconds
- **Comparisons per second**: For throughput estimation

### 5. GPU Acceleration

Tests GPU vs CPU performance (if GPU available).

**Key Metrics:**
- **GPU speedup**: How much faster than CPU
- **GPU memory usage**: Memory requirements

## Running Specific Benchmarks

You can run individual benchmark functions:

```python
from scripts.benchmark_fingerprinting import (
    benchmark_extraction_speed,
    benchmark_batch_processing,
    benchmark_lsh_indexing,
)

# Run specific benchmark
results = benchmark_extraction_speed()
```

## Comparing Versions

To compare performance across code changes:

1. Run benchmark before changes:
```bash
python scripts/benchmark_fingerprinting.py
cp benchmark_results.json benchmark_baseline.json
```

2. Make your changes

3. Run benchmark again:
```bash
python scripts/benchmark_fingerprinting.py
```

4. Compare results:
```bash
python scripts/compare_benchmarks.py benchmark_baseline.json benchmark_results.json
```

## Performance Targets

| Metric | Target | Priority |
|--------|--------|----------|
| Extraction Speed | < 1s per 60s audio | P0 |
| Batch Speedup | > 2x | P1 |
| GPU Speedup | > 10x | P2 |
| LSH Query Time | < 1ms for 1M fingerprints | P1 |

## Interpreting Results

### Good Performance Indicators

✅ **Extraction speed scales linearly** - Double audio length = double time
✅ **Batch speedup near number of workers** - 4 workers ≈ 4x speedup
✅ **GPU provides 10x+ speedup** - When CUDA available
✅ **LSH provides 100x+ query speedup** - For large databases

### Red Flags

❌ **Sub-linear scaling** - 2x audio takes > 2x time (memory issues?)
❌ **No batch speedup** - Might be I/O bound instead of CPU bound
❌ **GPU slower than CPU** - Data transfer overhead too high
❌ **LSH slower than linear** - Hash collisions or poor hyperparameters

## Profiling for Optimization

### CPU Profiling

Use cProfile to find bottlenecks:

```python
import cProfile
import pstats

from src.core.audio_fingerprinting_optimized import OptimizedAudioFingerprinter

fp = OptimizedAudioFingerprinter()

# Profile extraction
profiler = cProfile.Profile()
profiler.enable()

fp.extract_fingerprint("audio.wav")

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 functions
```

### Memory Profiling

Use memory_profiler to track memory usage:

```bash
pip install memory_profiler

python -m memory_profiler scripts/benchmark_fingerprinting.py
```

### Line-by-Line Profiling

Profile specific functions:

```python
from line_profiler import LineProfiler

from src.core.audio_fingerprinting_optimized import OptimizedAudioFingerprinter

fp = OptimizedAudioFingerprinter()

lp = LineProfiler()
lp_wrapper = lp(fp.extract_fingerprint_from_audio)

# Run profiled code
import numpy as np
audio = np.random.randn(22050 * 10)
lp_wrapper(audio, 22050)

lp.print_stats()
```

## Continuous Benchmarking

### In CI/CD

Add benchmark tests to CI pipeline:

```yaml
# .github/workflows/benchmark.yml
name: Performance Benchmarks

on: [push, pull_request]

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run benchmarks
        run: python scripts/benchmark_fingerprinting.py
      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: benchmark-results
          path: benchmark_results.json
```

### Performance Regression Tests

Create tests that fail if performance degrades:

```python
import pytest
import time

def test_extraction_performance():
    """Test that extraction meets performance target."""
    from src.core.audio_fingerprinting_optimized import OptimizedAudioFingerprinter
    import numpy as np
    
    fp = OptimizedAudioFingerprinter()
    
    # 60 seconds of audio
    audio = np.random.randn(22050 * 60)
    
    start = time.time()
    fp.extract_fingerprint_from_audio(audio, 22050)
    elapsed = time.time() - start
    
    # Should complete in < 1 second
    assert elapsed < 1.0, f"Extraction took {elapsed:.2f}s, expected < 1.0s"
```

## Hardware Considerations

### CPU Recommendations

For best performance:
- **Cores**: More cores = better batch processing
- **Frequency**: Higher clock speed = faster single-file processing
- **Cache**: Larger L3 cache helps with audio buffers

### GPU Recommendations

For GPU acceleration:
- **NVIDIA GPU**: CUDA support required (GTX 1060+, RTX series)
- **VRAM**: 4GB+ recommended
- **CUDA Compute**: 6.0+ (Maxwell architecture or newer)

### Memory Requirements

Approximate memory per fingerprint:
- **Standard**: ~1KB per second of audio
- **Multi-resolution**: ~3KB per second of audio
- **LSH index**: ~2KB per indexed fingerprint

For 100,000 30-second songs:
- Fingerprints: ~3GB
- LSH index: ~6GB
- Total: ~9GB RAM recommended

## Optimization Checklist

When optimizing performance:

- [ ] Profile first - identify actual bottlenecks
- [ ] Measure baseline - document current performance
- [ ] Make targeted changes - optimize hot paths only
- [ ] Benchmark after each change - verify improvement
- [ ] Test accuracy - ensure quality maintained
- [ ] Document results - help future optimization

## Common Issues

### Slow Extraction

**Symptoms**: Extraction much slower than target

**Possible Causes:**
- Large FFT size (n_fft=8192)
- Small hop length (hop_length=128)
- Disk I/O bottleneck
- Not using optimized version

**Solutions:**
- Reduce n_fft to 2048
- Increase hop_length to 512
- Process from memory
- Enable USE_OPTIMIZED_FINGERPRINTING

### Poor Batch Speedup

**Symptoms**: Batch processing not much faster than sequential

**Possible Causes:**
- I/O bound (disk too slow)
- Too few workers
- Too many workers (overhead)
- GIL contention (use multiprocessing, not threading)

**Solutions:**
- Load files to memory first
- Adjust max_workers
- Use multiprocessing
- Profile to identify bottleneck

### GPU Not Helping

**Symptoms**: GPU slower than CPU

**Possible Causes:**
- Data transfer overhead
- Small audio files
- CuPy not installed correctly

**Solutions:**
- Use larger batch sizes
- Batch multiple files together
- Verify CuPy installation

## References

- [Python Performance Tips](https://wiki.python.org/moin/PythonSpeed/PerformanceTips)
- [NumPy Performance](https://numpy.org/doc/stable/user/c-info.html)
- [CuPy Documentation](https://docs.cupy.dev/)
- [Line Profiler](https://github.com/pyutils/line_profiler)
