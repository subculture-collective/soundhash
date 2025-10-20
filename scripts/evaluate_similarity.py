#!/usr/bin/env python3
"""
Evaluation script for similarity search tuning.

This script evaluates the precision and recall of the similarity search system
using a labeled dataset. It helps tune thresholds and weights to achieve optimal
match quality.

Usage:
    python scripts/evaluate_similarity.py --data-dir <path> [--thresholds]
    python scripts/evaluate_similarity.py --generate-test-data

The script expects a directory structure:
    data_dir/
        queries/           # Query audio files
        candidates/        # Candidate audio files
        labels.json        # Ground truth labels

labels.json format:
{
    "query1.wav": {
        "true_matches": ["candidate1.wav", "candidate3.wav"],
        "false_matches": ["candidate2.wav"]
    },
    ...
}
"""

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

from config.settings import Config
from src.core.audio_fingerprinting import AudioFingerprinter


def generate_test_data(output_dir: str) -> None:
    """Generate synthetic test data for evaluation."""
    output_path = Path(output_dir)
    queries_dir = output_path / "queries"
    candidates_dir = output_path / "candidates"

    queries_dir.mkdir(parents=True, exist_ok=True)
    candidates_dir.mkdir(parents=True, exist_ok=True)

    # We'll create synthetic audio files using numpy
    import soundfile as sf

    sample_rate = Config.FINGERPRINT_SAMPLE_RATE
    duration = 5.0  # 5 seconds

    # Create a few base signals
    t = np.linspace(0, duration, int(sample_rate * duration))

    # Generate test files
    test_cases = [
        # Query 1: 440 Hz sine wave
        {
            "query": "query_440hz.wav",
            "signal": np.sin(2 * np.pi * 440 * t),
            "true_matches": [
                ("candidate_440hz_exact.wav", np.sin(2 * np.pi * 440 * t)),
                ("candidate_440hz_quiet.wav", np.sin(2 * np.pi * 440 * t) * 0.5),
            ],
            "false_matches": [
                ("candidate_880hz.wav", np.sin(2 * np.pi * 880 * t)),
            ],
        },
        # Query 2: 880 Hz sine wave
        {
            "query": "query_880hz.wav",
            "signal": np.sin(2 * np.pi * 880 * t),
            "true_matches": [
                ("candidate_880hz_exact.wav", np.sin(2 * np.pi * 880 * t)),
            ],
            "false_matches": [
                ("candidate_440hz.wav", np.sin(2 * np.pi * 440 * t)),
                ("candidate_1320hz.wav", np.sin(2 * np.pi * 1320 * t)),
            ],
        },
        # Query 3: Complex signal (two tones)
        {
            "query": "query_complex.wav",
            "signal": (np.sin(2 * np.pi * 440 * t) + np.sin(2 * np.pi * 880 * t)) / 2,
            "true_matches": [
                (
                    "candidate_complex_exact.wav",
                    (np.sin(2 * np.pi * 440 * t) + np.sin(2 * np.pi * 880 * t)) / 2,
                ),
            ],
            "false_matches": [
                ("candidate_single_440hz.wav", np.sin(2 * np.pi * 440 * t)),
            ],
        },
    ]

    labels = {}

    for test_case in test_cases:
        query_file = test_case["query"]
        query_path = queries_dir / query_file

        # Save query
        sf.write(str(query_path), test_case["signal"], sample_rate)

        # Save true matches
        true_match_names = []
        for match_name, match_signal in test_case["true_matches"]:
            match_path = candidates_dir / match_name
            sf.write(str(match_path), match_signal, sample_rate)
            true_match_names.append(match_name)

        # Save false matches
        false_match_names = []
        for match_name, match_signal in test_case["false_matches"]:
            match_path = candidates_dir / match_name
            sf.write(str(match_path), match_signal, sample_rate)
            false_match_names.append(match_name)

        labels[query_file] = {
            "true_matches": true_match_names,
            "false_matches": false_match_names,
        }

    # Save labels
    with open(output_path / "labels.json", "w") as f:
        json.dump(labels, f, indent=2)

    print(f"Generated test data in {output_path}")
    print(f"- {len(test_cases)} queries")
    total_candidates = sum(
        len(tc["true_matches"]) + len(tc["false_matches"]) for tc in test_cases
    )
    print(f"- {total_candidates} candidates")


def load_labels(labels_file: str) -> dict[str, Any]:
    """Load ground truth labels from JSON file."""
    with open(labels_file, "r") as f:
        return json.load(f)


def evaluate_similarity(
    data_dir: str,
    correlation_threshold: float | None = None,
    l2_threshold: float | None = None,
    min_score: float | None = None,
    min_duration: float | None = None,
    correlation_weight: float | None = None,
    l2_weight: float | None = None,
) -> dict[str, Any]:
    """
    Evaluate similarity search performance.

    Args:
        data_dir: Directory containing queries/, candidates/, and labels.json
        correlation_threshold: Minimum correlation score
        l2_threshold: Minimum L2 similarity score
        min_score: Minimum combined score
        min_duration: Minimum duration
        correlation_weight: Weight for correlation component
        l2_weight: Weight for L2 component

    Returns:
        Dictionary with precision, recall, F1 score, and detailed results
    """
    data_path = Path(data_dir)
    queries_dir = data_path / "queries"
    candidates_dir = data_path / "candidates"
    labels_file = data_path / "labels.json"

    if not labels_file.exists():
        raise FileNotFoundError(f"Labels file not found: {labels_file}")

    labels = load_labels(str(labels_file))

    # Initialize fingerprinter
    fingerprinter = AudioFingerprinter()

    # Extract fingerprints for all candidates
    print("Extracting candidate fingerprints...")
    candidate_fps = {}
    for candidate_file in candidates_dir.glob("*.wav"):
        try:
            fp = fingerprinter.extract_fingerprint(str(candidate_file))
            candidate_fps[candidate_file.name] = fp
        except Exception as e:
            print(f"Error processing {candidate_file.name}: {e}")

    # Evaluate each query
    results = []
    for query_file, ground_truth in labels.items():
        query_path = queries_dir / query_file

        if not query_path.exists():
            print(f"Query file not found: {query_path}")
            continue

        # Extract query fingerprint
        try:
            query_fp = fingerprinter.extract_fingerprint(str(query_path))
        except Exception as e:
            print(f"Error processing query {query_file}: {e}")
            continue

        # Rank candidates
        candidate_tuples = list(candidate_fps.items())
        matches = fingerprinter.rank_matches(
            query_fp,
            candidate_tuples,
            min_score=min_score,
            min_duration=min_duration,
            correlation_threshold=correlation_threshold,
            l2_threshold=l2_threshold,
        )

        # Extract match identifiers
        predicted_matches = [m["identifier"] for m in matches]
        true_positives = set(ground_truth["true_matches"])

        # Calculate metrics for this query
        tp = len([m for m in predicted_matches if m in true_positives])
        fp = len([m for m in predicted_matches if m not in true_positives])
        fn = len([m for m in true_positives if m not in predicted_matches])

        query_precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        query_recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        query_f1 = (
            2 * query_precision * query_recall / (query_precision + query_recall)
            if (query_precision + query_recall) > 0
            else 0.0
        )

        results.append(
            {
                "query": query_file,
                "precision": query_precision,
                "recall": query_recall,
                "f1": query_f1,
                "true_positives": tp,
                "false_positives": fp,
                "false_negatives": fn,
                "predicted_matches": predicted_matches,
                "match_details": matches,
            }
        )

    # Calculate aggregate metrics
    if results:
        avg_precision = np.mean([r["precision"] for r in results])
        avg_recall = np.mean([r["recall"] for r in results])
        avg_f1 = np.mean([r["f1"] for r in results])

        total_tp = sum(r["true_positives"] for r in results)
        total_fp = sum(r["false_positives"] for r in results)
        total_fn = sum(r["false_negatives"] for r in results)

        micro_precision = (
            total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
        )
        micro_recall = (
            total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
        )
        micro_f1 = (
            2 * micro_precision * micro_recall / (micro_precision + micro_recall)
            if (micro_precision + micro_recall) > 0
            else 0.0
        )
    else:
        avg_precision = avg_recall = avg_f1 = 0.0
        micro_precision = micro_recall = micro_f1 = 0.0

    return {
        "macro_precision": avg_precision,
        "macro_recall": avg_recall,
        "macro_f1": avg_f1,
        "micro_precision": micro_precision,
        "micro_recall": micro_recall,
        "micro_f1": micro_f1,
        "query_results": results,
    }


def print_evaluation_summary(evaluation: dict[str, Any]) -> None:
    """Print a summary of evaluation results."""
    print("\n" + "=" * 60)
    print("SIMILARITY SEARCH EVALUATION SUMMARY")
    print("=" * 60)

    print("\nMacro-averaged Metrics (average per query):")
    print(f"  Precision: {evaluation['macro_precision']:.3f}")
    print(f"  Recall:    {evaluation['macro_recall']:.3f}")
    print(f"  F1 Score:  {evaluation['macro_f1']:.3f}")

    print("\nMicro-averaged Metrics (aggregate across all queries):")
    print(f"  Precision: {evaluation['micro_precision']:.3f}")
    print(f"  Recall:    {evaluation['micro_recall']:.3f}")
    print(f"  F1 Score:  {evaluation['micro_f1']:.3f}")

    print("\nPer-Query Results:")
    for result in evaluation["query_results"]:
        print(f"\n  {result['query']}:")
        print(f"    Precision: {result['precision']:.3f}")
        print(f"    Recall:    {result['recall']:.3f}")
        print(f"    F1 Score:  {result['f1']:.3f}")
        tp_val = result["true_positives"]
        fp_val = result["false_positives"]
        fn_val = result["false_negatives"]
        print(f"    TP: {tp_val}, FP: {fp_val}, FN: {fn_val}")

        if result["match_details"]:
            print("    Top matches:")
            for match in result["match_details"][:3]:
                print(
                    f"      - {match['identifier']}: score={match['score']:.3f}, "
                    f"corr={match['correlation']:.3f}, l2={match['l2_similarity']:.3f}"
                )

    print("\n" + "=" * 60)


def main():
    """Main entry point for evaluation script."""
    parser = argparse.ArgumentParser(
        description="Evaluate similarity search performance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--data-dir",
        type=str,
        default="./eval_data",
        help="Directory containing queries/, candidates/, and labels.json",
    )

    parser.add_argument(
        "--generate-test-data",
        action="store_true",
        help="Generate synthetic test data and exit",
    )

    parser.add_argument(
        "--correlation-threshold",
        type=float,
        help=f"Minimum correlation score (default: {Config.SIMILARITY_CORRELATION_THRESHOLD})",
    )

    parser.add_argument(
        "--l2-threshold",
        type=float,
        help=f"Minimum L2 similarity score (default: {Config.SIMILARITY_L2_THRESHOLD})",
    )

    parser.add_argument(
        "--min-score",
        type=float,
        help=f"Minimum combined similarity score (default: {Config.SIMILARITY_MIN_SCORE})",
    )

    parser.add_argument(
        "--min-duration",
        type=float,
        help=f"Minimum duration in seconds (default: {Config.SIMILARITY_MIN_DURATION})",
    )

    parser.add_argument(
        "--correlation-weight",
        type=float,
        help=f"Weight for correlation component (default: {Config.SIMILARITY_CORRELATION_WEIGHT})",
    )

    parser.add_argument(
        "--l2-weight",
        type=float,
        help=f"Weight for L2 component (default: {Config.SIMILARITY_L2_WEIGHT})",
    )

    parser.add_argument(
        "--output",
        type=str,
        help="Output JSON file for detailed results",
    )

    args = parser.parse_args()

    if args.generate_test_data:
        generate_test_data(args.data_dir)
        return

    # Run evaluation
    evaluation = evaluate_similarity(
        args.data_dir,
        correlation_threshold=args.correlation_threshold,
        l2_threshold=args.l2_threshold,
        min_score=args.min_score,
        min_duration=args.min_duration,
        correlation_weight=args.correlation_weight,
        l2_weight=args.l2_weight,
    )

    # Print summary
    print_evaluation_summary(evaluation)

    # Save detailed results if requested
    if args.output:
        with open(args.output, "w") as f:
            json.dump(evaluation, f, indent=2)
        print(f"\nDetailed results saved to {args.output}")


if __name__ == "__main__":
    main()
