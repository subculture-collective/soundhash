#!/usr/bin/env python3
"""Compare benchmark results with baseline and previous runs."""

import json
import sys
from pathlib import Path


def load_results(filename="benchmark_results.json"):
    """Load benchmark results from JSON file."""
    results_file = Path(filename)

    if not results_file.exists():
        print(f"Error: {filename} not found")
        return None

    with open(results_file) as f:
        return json.load(f)


def load_baseline(filename="benchmark_baseline.json"):
    """Load baseline benchmark results."""
    baseline_file = Path(filename)

    # If no baseline exists, use default values
    if not baseline_file.exists():
        print(f"Warning: No baseline file found at {filename}")
        print("Using default baseline values")
        return {
            "fingerprint_extraction_ms": 50.0,
            "fingerprint_comparison_ms": 0.5,
            "database_connection_ms": 10.0,
        }

    with open(baseline_file) as f:
        return json.load(f)


def compare_results(current, baseline):
    """Compare current results with baseline."""
    print("=" * 70)
    print("Performance Benchmark Comparison")
    print("=" * 70)
    print()

    has_regression = False

    for key in current.keys():
        current_value = current[key]
        baseline_value = baseline.get(key, 0)

        if current_value < 0:
            print(f"❌ {key}: FAILED")
            has_regression = True
            continue

        if baseline_value > 0:
            change_percent = ((current_value - baseline_value) / baseline_value) * 100
            change_str = f"{change_percent:+.1f}%"

            if change_percent > 20:
                status = "⚠️  REGRESSION"
                has_regression = True
            elif change_percent < -10:
                status = "✅ IMPROVED"
            else:
                status = "✅ OK"
        else:
            change_str = "N/A"
            status = "✅ NEW"

        print(
            f"{status:15} {key:40} "
            f"Current: {current_value:7.2f}ms  "
            f"Baseline: {baseline_value:7.2f}ms  "
            f"Change: {change_str}"
        )

    print()
    print("=" * 70)

    if has_regression:
        print("⚠️  Performance regression detected!")
        print()
        print("Please investigate the performance changes before merging.")
        return 1
    else:
        print("✅ All benchmarks within acceptable range")
        return 0


def save_as_baseline():
    """Save current results as new baseline."""
    results_file = Path("benchmark_results.json")
    baseline_file = Path("benchmark_baseline.json")

    if not results_file.exists():
        print("Error: No benchmark results to save as baseline")
        return False

    with open(results_file) as f:
        results = json.load(f)

    with open(baseline_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"✅ Saved current results as baseline to {baseline_file}")
    return True


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Compare benchmark results")
    parser.add_argument(
        "--save-baseline",
        action="store_true",
        help="Save current results as new baseline",
    )
    parser.add_argument(
        "--results",
        default="benchmark_results.json",
        help="Path to current results file",
    )
    parser.add_argument(
        "--baseline",
        default="benchmark_baseline.json",
        help="Path to baseline results file",
    )

    args = parser.parse_args()

    if args.save_baseline:
        if save_as_baseline():
            return 0
        return 1

    # Load and compare results
    current = load_results(args.results)
    if current is None:
        return 1

    baseline = load_baseline(args.baseline)

    return compare_results(current, baseline)


if __name__ == "__main__":
    sys.exit(main())
