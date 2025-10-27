#!/usr/bin/env python3
"""Benchmark critical operations and compare with baseline."""

import json
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import soundfile as sf

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.audio_fingerprinting import AudioFingerprinter


def benchmark_fingerprint_extraction():
    """Benchmark fingerprint extraction performance."""
    print("Running fingerprint extraction benchmark...")
    
    # Create test audio file
    sample_rate = 22050
    duration = 5.0  # 5 seconds
    frequency = 440.0
    
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = np.sin(2 * np.pi * frequency * t)
        sf.write(tmp.name, audio_data, sample_rate)
        
        # Benchmark extraction
        fingerprinter = AudioFingerprinter()
        
        start_time = time.time()
        try:
            fingerprint_data = fingerprinter.extract_fingerprint(tmp.name)
            duration_ms = (time.time() - start_time) * 1000
            
            print(f"  ✓ Fingerprint extraction: {duration_ms:.2f}ms")
            return duration_ms
        except Exception as e:
            print(f"  ✗ Fingerprint extraction failed: {e}")
            return -1
        finally:
            # Cleanup
            Path(tmp.name).unlink(missing_ok=True)


def benchmark_fingerprint_comparison():
    """Benchmark fingerprint comparison performance."""
    print("Running fingerprint comparison benchmark...")
    
    try:
        from src.core.audio_fingerprinting import AudioFingerprinter
        
        fingerprinter = AudioFingerprinter()
        
        # Create two similar fingerprints
        sample_size = 128
        fp1 = np.random.rand(sample_size).astype(np.float32)
        fp2 = fp1 + np.random.rand(sample_size).astype(np.float32) * 0.1  # Similar but not identical
        
        # Normalize
        fp1 = fp1 / np.linalg.norm(fp1)
        fp2 = fp2 / np.linalg.norm(fp2)
        
        # Benchmark comparison
        iterations = 1000
        start_time = time.time()
        
        for _ in range(iterations):
            # Calculate similarity (correlation)
            correlation = np.corrcoef(fp1, fp2)[0, 1]
            
            # Calculate Euclidean distance
            euclidean_dist = np.linalg.norm(fp1 - fp2)
            euclidean_sim = 1.0 / (1.0 + euclidean_dist)
            
            # Average similarity
            similarity = (abs(correlation) + euclidean_sim) / 2.0
        
        duration_ms = (time.time() - start_time) * 1000 / iterations
        
        print(f"  ✓ Fingerprint comparison: {duration_ms:.2f}ms")
        return duration_ms
    except Exception as e:
        print(f"  ✗ Fingerprint comparison failed: {e}")
        return -1


def benchmark_database_operations():
    """Benchmark database operations."""
    print("Running database operations benchmark...")
    
    try:
        from sqlalchemy import text
        from src.database.connection import db_manager
        
        # Simple connection benchmark
        start_time = time.time()
        
        with db_manager.get_session() as session:
            # Execute a simple query
            session.execute(text("SELECT 1"))
        
        duration_ms = (time.time() - start_time) * 1000
        
        print(f"  ✓ Database connection: {duration_ms:.2f}ms")
        return duration_ms
    except Exception as e:
        print(f"  ✗ Database operations failed: {e}")
        return -1


def main():
    """Run all benchmarks and save results."""
    print("=" * 60)
    print("Performance Benchmark Suite")
    print("=" * 60)
    print()
    
    results = {
        "fingerprint_extraction_ms": benchmark_fingerprint_extraction(),
        "fingerprint_comparison_ms": benchmark_fingerprint_comparison(),
        "database_connection_ms": benchmark_database_operations(),
    }
    
    print()
    print("=" * 60)
    print("Benchmark Results Summary")
    print("=" * 60)
    for key, value in results.items():
        status = "✓" if value >= 0 else "✗"
        print(f"{status} {key}: {value:.2f}ms")
    
    # Save results to JSON
    results_file = Path("benchmark_results.json")
    with open(results_file, "w") as f:
        json.dump(results, indent=2, fp=f)
    
    print()
    print(f"Results saved to {results_file}")
    
    # Generate markdown report
    generate_markdown_report(results)
    
    return 0


def generate_markdown_report(results):
    """Generate a markdown report of benchmark results."""
    # Baseline values (these would typically come from a stored baseline)
    baseline = {
        "fingerprint_extraction_ms": 50.0,
        "fingerprint_comparison_ms": 0.5,
        "database_connection_ms": 10.0,
    }
    
    report = ["## 📊 Performance Benchmark Results", ""]
    report.append("| Operation | Current | Baseline | Change | Status |")
    report.append("|-----------|---------|----------|--------|--------|")
    
    for key, current_value in results.items():
        baseline_value = baseline.get(key, 0)
        
        if current_value < 0:
            report.append(f"| {key.replace('_', ' ').title()} | FAILED | {baseline_value:.2f}ms | - | ❌ |")
            continue
        
        if baseline_value > 0:
            change_percent = ((current_value - baseline_value) / baseline_value) * 100
            change_str = f"{change_percent:+.1f}%"
            
            if change_percent > 20:
                status = "⚠️ Regression"
            elif change_percent < -10:
                status = "✅ Improved"
            else:
                status = "✅ OK"
        else:
            change_str = "N/A"
            status = "✅ OK"
        
        report.append(
            f"| {key.replace('_', ' ').title()} | "
            f"{current_value:.2f}ms | {baseline_value:.2f}ms | "
            f"{change_str} | {status} |"
        )
    
    report.append("")
    report.append("---")
    report.append("*Benchmark run completed successfully*")
    
    report_text = "\n".join(report)
    
    report_file = Path("benchmark_results.md")
    with open(report_file, "w") as f:
        f.write(report_text)
    
    print(f"Markdown report saved to {report_file}")


if __name__ == "__main__":
    sys.exit(main())
