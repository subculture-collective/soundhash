#!/usr/bin/env python3
"""
Comprehensive benchmarking suite for audio fingerprinting algorithms.

Compares original vs optimized implementations across various scenarios:
- Different audio lengths
- Batch processing
- Various audio complexities
- Memory usage
"""

import json
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import soundfile as sf
from tabulate import tabulate

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.audio_fingerprinting import AudioFingerprinter
from src.core.audio_fingerprinting_optimized import OptimizedAudioFingerprinter


def generate_test_audio(duration: float, sample_rate: int = 22050, complexity: str = "simple"):
    """
    Generate test audio with varying complexity.
    
    Args:
        duration: Audio duration in seconds
        sample_rate: Sample rate in Hz
        complexity: "simple" (sine wave), "complex" (harmonics), or "noise" (with noise)
    """
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    if complexity == "simple":
        audio = np.sin(2 * np.pi * 440.0 * t)
    elif complexity == "complex":
        # Multiple harmonics
        audio = (np.sin(2 * np.pi * 220.0 * t) * 0.5 +
                np.sin(2 * np.pi * 440.0 * t) * 1.0 +
                np.sin(2 * np.pi * 880.0 * t) * 0.3 +
                np.sin(2 * np.pi * 1760.0 * t) * 0.15)
    elif complexity == "noise":
        # Harmonics with noise
        audio = (np.sin(2 * np.pi * 440.0 * t) * 0.7 +
                np.random.randn(len(t)) * 0.3)
    else:
        audio = np.sin(2 * np.pi * 440.0 * t)
    
    # Normalize
    audio = audio / np.max(np.abs(audio))
    return audio


def benchmark_extraction_speed():
    """Benchmark fingerprint extraction speed for different durations."""
    print("\n" + "="*80)
    print("BENCHMARK 1: Extraction Speed vs Audio Duration")
    print("="*80)
    
    durations = [1.0, 5.0, 10.0, 30.0, 60.0]
    results = []
    
    original = AudioFingerprinter()
    optimized = OptimizedAudioFingerprinter()
    
    for duration in durations:
        audio = generate_test_audio(duration, complexity="complex")
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            sf.write(tmp.name, audio, 22050)
            
            try:
                # Original
                start = time.time()
                fp_orig = original.extract_fingerprint(tmp.name)
                time_orig = (time.time() - start) * 1000
                
                # Optimized
                start = time.time()
                fp_opt = optimized.extract_fingerprint(tmp.name)
                time_opt = (time.time() - start) * 1000
                
                # Calculate per-second metrics
                time_orig_per_sec = time_orig / duration
                time_opt_per_sec = time_opt / duration
                speedup = time_orig / time_opt if time_opt > 0 else 1.0
                
                results.append({
                    "duration": duration,
                    "original_ms": time_orig,
                    "optimized_ms": time_opt,
                    "original_per_sec": time_orig_per_sec,
                    "optimized_per_sec": time_opt_per_sec,
                    "speedup": speedup,
                    "meets_target": time_opt_per_sec < 16.7,  # <1s per minute = 16.7ms/sec
                })
            finally:
                Path(tmp.name).unlink(missing_ok=True)
    
    # Print results
    table_data = []
    for r in results:
        status = "✅ PASS" if r["meets_target"] else "❌ FAIL"
        table_data.append([
            f"{r['duration']:.0f}s",
            f"{r['original_ms']:.1f}",
            f"{r['optimized_ms']:.1f}",
            f"{r['original_per_sec']:.1f}",
            f"{r['optimized_per_sec']:.1f}",
            f"{r['speedup']:.2f}x",
            status,
        ])
    
    headers = ["Duration", "Original (ms)", "Optimized (ms)", 
               "Orig/sec", "Opt/sec", "Speedup", "Target (<16.7ms/s)"]
    print("\n" + tabulate(table_data, headers=headers, tablefmt="grid"))
    
    return results


def benchmark_batch_processing():
    """Benchmark batch processing performance."""
    print("\n" + "="*80)
    print("BENCHMARK 2: Batch Processing Performance")
    print("="*80)
    
    batch_sizes = [1, 5, 10, 20]
    results = []
    
    for batch_size in batch_sizes:
        # Create test files
        files = []
        audio = generate_test_audio(5.0, complexity="complex")
        
        for i in range(batch_size):
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                sf.write(tmp.name, audio, 22050)
                files.append(tmp.name)
        
        try:
            # Sequential (original)
            original = AudioFingerprinter()
            start = time.time()
            for f in files:
                original.extract_fingerprint(f)
            time_sequential = (time.time() - start) * 1000
            
            # Batch with multiprocessing
            optimized_mp = OptimizedAudioFingerprinter(enable_batch_mode=True, max_workers=4)
            start = time.time()
            optimized_mp.batch_extract_fingerprints(files, use_multiprocessing=True)
            time_batch_mp = (time.time() - start) * 1000
            
            # Batch with threading
            optimized_thread = OptimizedAudioFingerprinter(enable_batch_mode=True, max_workers=4)
            start = time.time()
            optimized_thread.batch_extract_fingerprints(files, use_multiprocessing=False)
            time_batch_thread = (time.time() - start) * 1000
            
            speedup_mp = time_sequential / time_batch_mp if time_batch_mp > 0 else 1.0
            speedup_thread = time_sequential / time_batch_thread if time_batch_thread > 0 else 1.0
            
            results.append({
                "batch_size": batch_size,
                "sequential_ms": time_sequential,
                "batch_mp_ms": time_batch_mp,
                "batch_thread_ms": time_batch_thread,
                "speedup_mp": speedup_mp,
                "speedup_thread": speedup_thread,
            })
        finally:
            for f in files:
                Path(f).unlink(missing_ok=True)
    
    # Print results
    table_data = []
    for r in results:
        table_data.append([
            r["batch_size"],
            f"{r['sequential_ms']:.1f}",
            f"{r['batch_mp_ms']:.1f}",
            f"{r['batch_thread_ms']:.1f}",
            f"{r['speedup_mp']:.2f}x",
            f"{r['speedup_thread']:.2f}x",
        ])
    
    headers = ["Batch Size", "Sequential (ms)", "Multiprocess (ms)", 
               "Threading (ms)", "MP Speedup", "Thread Speedup"]
    print("\n" + tabulate(table_data, headers=headers, tablefmt="grid"))
    
    return results


def benchmark_complexity_impact():
    """Benchmark impact of audio complexity on fingerprinting speed."""
    print("\n" + "="*80)
    print("BENCHMARK 3: Audio Complexity Impact")
    print("="*80)
    
    complexities = ["simple", "complex", "noise"]
    results = []
    
    optimized = OptimizedAudioFingerprinter()
    
    for complexity in complexities:
        audio = generate_test_audio(10.0, complexity=complexity)
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            sf.write(tmp.name, audio, 22050)
            
            try:
                start = time.time()
                fp = optimized.extract_fingerprint(tmp.name)
                time_ms = (time.time() - start) * 1000
                
                results.append({
                    "complexity": complexity,
                    "time_ms": time_ms,
                    "peak_count": fp["peak_count"],
                    "confidence": fp["confidence_score"],
                })
            finally:
                Path(tmp.name).unlink(missing_ok=True)
    
    # Print results
    table_data = []
    for r in results:
        table_data.append([
            r["complexity"].capitalize(),
            f"{r['time_ms']:.1f}",
            r["peak_count"],
            f"{r['confidence']:.3f}",
        ])
    
    headers = ["Complexity", "Time (ms)", "Peak Count", "Confidence"]
    print("\n" + tabulate(table_data, headers=headers, tablefmt="grid"))
    
    return results


def benchmark_comparison_speed():
    """Benchmark fingerprint comparison speed."""
    print("\n" + "="*80)
    print("BENCHMARK 4: Fingerprint Comparison Speed")
    print("="*80)
    
    # Generate test fingerprints
    audio = generate_test_audio(30.0, complexity="complex")
    
    original = AudioFingerprinter()
    optimized = OptimizedAudioFingerprinter()
    
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        sf.write(tmp.name, audio, 22050)
        
        try:
            fp_orig = original.extract_fingerprint(tmp.name)
            fp_opt = optimized.extract_fingerprint(tmp.name)
            
            # Benchmark comparisons
            iterations = 1000
            
            # Original
            start = time.time()
            for _ in range(iterations):
                original.compare_fingerprints(fp_orig, fp_orig)
            time_orig = (time.time() - start) * 1000 / iterations
            
            # Optimized
            start = time.time()
            for _ in range(iterations):
                optimized.compare_fingerprints(fp_opt, fp_opt)
            time_opt = (time.time() - start) * 1000 / iterations
            
            speedup = time_orig / time_opt if time_opt > 0 else 1.0
            
            print(f"\nComparison speed ({iterations} iterations):")
            print(f"  Original:  {time_orig:.4f} ms/comparison")
            print(f"  Optimized: {time_opt:.4f} ms/comparison")
            print(f"  Speedup:   {speedup:.2f}x")
            
            return {
                "original_ms": time_orig,
                "optimized_ms": time_opt,
                "speedup": speedup,
            }
        finally:
            Path(tmp.name).unlink(missing_ok=True)


def benchmark_gpu_acceleration():
    """Benchmark GPU acceleration if available."""
    print("\n" + "="*80)
    print("BENCHMARK 5: GPU Acceleration")
    print("="*80)
    
    optimized_cpu = OptimizedAudioFingerprinter(use_gpu=False)
    optimized_gpu = OptimizedAudioFingerprinter(use_gpu=True)
    
    device_info = optimized_gpu.get_device_info()
    print(f"\nDevice Information:")
    print(f"  CPU Cores: {device_info['cpu_cores']}")
    print(f"  GPU Available: {device_info['gpu_available']}")
    print(f"  GPU Enabled: {device_info['gpu_enabled']}")
    
    if device_info.get('gpu_name'):
        print(f"  GPU Name: {device_info['gpu_name']}")
        print(f"  GPU Memory: {device_info['gpu_memory_gb']:.2f} GB")
    
    if not device_info['gpu_enabled']:
        print("\n⚠️  GPU acceleration not available (CuPy not installed)")
        print("   Install with: pip install cupy-cuda12x (for CUDA 12.x)")
        return None
    
    # Benchmark with GPU
    audio = generate_test_audio(30.0, complexity="complex")
    
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        sf.write(tmp.name, audio, 22050)
        
        try:
            # CPU
            start = time.time()
            fp_cpu = optimized_cpu.extract_fingerprint(tmp.name)
            time_cpu = (time.time() - start) * 1000
            
            # GPU
            start = time.time()
            fp_gpu = optimized_gpu.extract_fingerprint(tmp.name)
            time_gpu = (time.time() - start) * 1000
            
            speedup = time_cpu / time_gpu if time_gpu > 0 else 1.0
            
            print(f"\nGPU vs CPU (30s audio):")
            print(f"  CPU:     {time_cpu:.1f} ms")
            print(f"  GPU:     {time_gpu:.1f} ms")
            print(f"  Speedup: {speedup:.2f}x")
            
            return {
                "cpu_ms": time_cpu,
                "gpu_ms": time_gpu,
                "speedup": speedup,
            }
        finally:
            Path(tmp.name).unlink(missing_ok=True)


def generate_report(all_results: dict):
    """Generate comprehensive markdown report."""
    report_lines = [
        "# Audio Fingerprinting Performance Benchmark Report",
        "",
        f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Summary",
        "",
    ]
    
    # Extraction speed summary
    if "extraction" in all_results:
        results = all_results["extraction"]
        # Find 60s result
        result_60s = next((r for r in results if r["duration"] == 60.0), None)
        if result_60s:
            status = "✅ PASS" if result_60s["meets_target"] else "❌ FAIL"
            report_lines.extend([
                "### Extraction Speed Goal: <1s per minute of audio",
                f"- **Status**: {status}",
                f"- **Achieved**: {result_60s['optimized_ms']:.0f}ms for 60s audio ({result_60s['optimized_per_sec']:.1f}ms/sec)",
                f"- **Target**: <1000ms for 60s audio (<16.7ms/sec)",
                f"- **Speedup over original**: {result_60s['speedup']:.2f}x",
                "",
            ])
    
    # Batch processing summary
    if "batch" in all_results:
        results = all_results["batch"]
        if results:
            best = max(results, key=lambda x: x["speedup_mp"])
            report_lines.extend([
                "### Batch Processing",
                f"- **Best speedup**: {best['speedup_mp']:.2f}x (batch size: {best['batch_size']})",
                "",
            ])
    
    # GPU acceleration summary
    if "gpu" in all_results and all_results["gpu"]:
        gpu_result = all_results["gpu"]
        report_lines.extend([
            "### GPU Acceleration",
            f"- **Speedup**: {gpu_result['speedup']:.2f}x",
            "",
        ])
    
    report_lines.extend([
        "## Detailed Results",
        "",
        "See benchmark_results.json for full data",
    ])
    
    report_path = Path("benchmark_fingerprinting_report.md")
    with open(report_path, "w") as f:
        f.write("\n".join(report_lines))
    
    print(f"\n\n📊 Full report saved to: {report_path}")


def main():
    """Run all benchmarks."""
    print("="*80)
    print("Audio Fingerprinting Performance Benchmark Suite")
    print("="*80)
    
    all_results = {}
    
    # Run benchmarks
    all_results["extraction"] = benchmark_extraction_speed()
    all_results["batch"] = benchmark_batch_processing()
    all_results["complexity"] = benchmark_complexity_impact()
    all_results["comparison"] = benchmark_comparison_speed()
    all_results["gpu"] = benchmark_gpu_acceleration()
    
    # Save results
    results_file = Path("benchmark_results.json")
    with open(results_file, "w") as f:
        # Convert numpy types to native Python types
        def convert(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            return obj
        
        json.dump(all_results, f, indent=2, default=convert)
    
    print(f"\n\n💾 Results saved to: {results_file}")
    
    # Generate report
    generate_report(all_results)
    
    print("\n" + "="*80)
    print("✅ Benchmark suite completed!")
    print("="*80)
    
    return 0


if __name__ == "__main__":
    try:
        from tabulate import tabulate
    except ImportError:
        print("Installing tabulate for better output formatting...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "tabulate"])
        from tabulate import tabulate
    
    sys.exit(main())
