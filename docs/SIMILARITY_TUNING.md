# Similarity Search Tuning Guide

This guide explains how to tune the similarity search system for optimal precision and recall.

## Overview

The similarity search system uses two complementary metrics to match audio fingerprints:

1. **Correlation coefficient**: Measures the linear relationship between fingerprints (shape similarity)
2. **Normalized L2 distance**: Measures the absolute difference between fingerprints (magnitude similarity)

These metrics are combined using a weighted mean to produce a final similarity score.

## Configuration Parameters

All parameters can be set via environment variables or in your `.env` file:

### Thresholds

- `SIMILARITY_CORRELATION_THRESHOLD` (default: 0.70)
  - Minimum correlation score for a match to be considered
  - Range: 0.0 to 1.0
  - Higher values = fewer but more confident matches

- `SIMILARITY_L2_THRESHOLD` (default: 0.70)
  - Minimum L2 similarity score for a match to be considered
  - Range: 0.0 to 1.0
  - Higher values = fewer but more confident matches

- `SIMILARITY_MIN_SCORE` (default: 0.70)
  - Minimum combined similarity score for a match
  - Range: 0.0 to 1.0
  - This is the final filter after combining correlation and L2

- `SIMILARITY_MIN_DURATION` (default: 5.0)
  - Minimum audio duration in seconds for a match
  - Filters out very short segments that may produce false positives

### Weights

- `SIMILARITY_CORRELATION_WEIGHT` (default: 0.5)
  - Weight for the correlation component in the combined score
  - Range: 0.0 to 1.0
  - Should sum to 1.0 with L2 weight

- `SIMILARITY_L2_WEIGHT` (default: 0.5)
  - Weight for the L2 similarity component in the combined score
  - Range: 0.0 to 1.0
  - Should sum to 1.0 with correlation weight

## Tuning Procedure

### Step 1: Generate Test Data

First, generate a small labeled dataset for evaluation:

```bash
python scripts/evaluate_similarity.py --generate-test-data --data-dir ./eval_data
```

This creates:
- `eval_data/queries/` - Query audio files
- `eval_data/candidates/` - Candidate audio files to match against
- `eval_data/labels.json` - Ground truth labels

### Step 2: Evaluate with Default Settings

Run the evaluation with default settings to get a baseline:

```bash
python scripts/evaluate_similarity.py --data-dir ./eval_data
```

This will print:
- Macro-averaged metrics (average per query)
- Micro-averaged metrics (aggregate across all queries)
- Per-query results with precision, recall, and F1 scores

### Step 3: Tune Thresholds

Experiment with different threshold values to optimize precision and recall:

```bash
# More strict (higher precision, lower recall)
python scripts/evaluate_similarity.py \
  --data-dir ./eval_data \
  --correlation-threshold 0.80 \
  --l2-threshold 0.80 \
  --min-score 0.75

# More lenient (higher recall, lower precision)
python scripts/evaluate_similarity.py \
  --data-dir ./eval_data \
  --correlation-threshold 0.60 \
  --l2-threshold 0.60 \
  --min-score 0.65
```

### Step 4: Tune Weights

Adjust the weights to emphasize correlation or L2 similarity:

```bash
# Emphasize correlation (better for shape similarity)
python scripts/evaluate_similarity.py \
  --data-dir ./eval_data \
  --correlation-weight 0.7 \
  --l2-weight 0.3

# Emphasize L2 (better for magnitude similarity)
python scripts/evaluate_similarity.py \
  --data-dir ./eval_data \
  --correlation-weight 0.3 \
  --l2-weight 0.7
```

### Step 5: Save Results

Save detailed results to a JSON file for analysis:

```bash
python scripts/evaluate_similarity.py \
  --data-dir ./eval_data \
  --correlation-threshold 0.75 \
  --l2-threshold 0.75 \
  --min-score 0.70 \
  --output results.json
```

### Step 6: Apply Best Settings

Once you've found optimal parameters, update your `.env` file:

```bash
# In .env
SIMILARITY_CORRELATION_THRESHOLD=0.75
SIMILARITY_L2_THRESHOLD=0.75
SIMILARITY_MIN_SCORE=0.70
SIMILARITY_CORRELATION_WEIGHT=0.6
SIMILARITY_L2_WEIGHT=0.4
SIMILARITY_MIN_DURATION=5.0
```

## Creating Custom Test Data

For best results, create a labeled dataset from your actual use case:

1. Create directories:
   ```bash
   mkdir -p my_eval_data/queries my_eval_data/candidates
   ```

2. Add audio files:
   - Place query clips in `my_eval_data/queries/`
   - Place candidate videos' audio in `my_eval_data/candidates/`

3. Create `my_eval_data/labels.json`:
   ```json
   {
     "query1.wav": {
       "true_matches": ["candidate1.wav", "candidate3.wav"],
       "false_matches": ["candidate2.wav"]
     },
     "query2.wav": {
       "true_matches": ["candidate4.wav"],
       "false_matches": []
     }
   }
   ```

4. Run evaluation:
   ```bash
   python scripts/evaluate_similarity.py --data-dir my_eval_data
   ```

## Understanding Metrics

### Precision
- Percentage of returned matches that are correct
- High precision = few false positives
- Increase thresholds to improve precision

### Recall
- Percentage of true matches that were found
- High recall = few false negatives
- Decrease thresholds to improve recall

### F1 Score
- Harmonic mean of precision and recall
- Balances both metrics
- Good for overall performance assessment

### Trade-offs

- **Higher thresholds** → Higher precision, lower recall (fewer false positives, more false negatives)
- **Lower thresholds** → Lower precision, higher recall (more false positives, fewer false negatives)
- **Balanced weights (0.5/0.5)** → Treats both metrics equally
- **Correlation emphasis** → Better for matching audio with similar structure
- **L2 emphasis** → Better for matching audio with similar magnitudes

## Recommended Settings by Use Case

### High Precision (minimize false positives)
```bash
SIMILARITY_CORRELATION_THRESHOLD=0.85
SIMILARITY_L2_THRESHOLD=0.85
SIMILARITY_MIN_SCORE=0.80
SIMILARITY_MIN_DURATION=10.0
```

### High Recall (minimize false negatives)
```bash
SIMILARITY_CORRELATION_THRESHOLD=0.60
SIMILARITY_L2_THRESHOLD=0.60
SIMILARITY_MIN_SCORE=0.60
SIMILARITY_MIN_DURATION=3.0
```

### Balanced (default)
```bash
SIMILARITY_CORRELATION_THRESHOLD=0.70
SIMILARITY_L2_THRESHOLD=0.70
SIMILARITY_MIN_SCORE=0.70
SIMILARITY_MIN_DURATION=5.0
```

## Ranking and Tie-Breaking

Matches are ranked by:
1. Combined similarity score (descending)
2. Correlation score (descending)
3. L2 similarity score (descending)
4. Duration (descending)

This ensures that:
- Higher quality matches appear first
- Ties are broken consistently
- Longer audio segments are preferred when scores are equal

## API Usage

### Comparing Fingerprints

```python
from src.core.audio_fingerprinting import AudioFingerprinter

fingerprinter = AudioFingerprinter()

# Extract fingerprints
fp1 = fingerprinter.extract_fingerprint("audio1.wav")
fp2 = fingerprinter.extract_fingerprint("audio2.wav")

# Simple comparison
score = fingerprinter.compare_fingerprints(fp1, fp2)

# Get detailed components
components = fingerprinter.compare_fingerprints(
    fp1, fp2, return_components=True
)
print(f"Correlation: {components['correlation']:.3f}")
print(f"L2 similarity: {components['l2_similarity']:.3f}")
print(f"Combined: {components['combined_score']:.3f}")

# Custom weights
score = fingerprinter.compare_fingerprints(
    fp1, fp2,
    correlation_weight=0.7,
    l2_weight=0.3
)
```

### Ranking Matches

```python
# Prepare candidates
candidates = [
    (id1, fp1),
    (id2, fp2),
    (id3, fp3),
]

# Rank with default thresholds
matches = fingerprinter.rank_matches(query_fp, candidates)

# Rank with custom thresholds
matches = fingerprinter.rank_matches(
    query_fp,
    candidates,
    min_score=0.75,
    min_duration=10.0,
    correlation_threshold=0.80,
    l2_threshold=0.80,
)

# Process results
for match in matches:
    print(f"ID: {match['identifier']}")
    print(f"Score: {match['score']:.3f}")
    print(f"Duration: {match['duration']:.1f}s")
```

## Troubleshooting

### Too many false positives
- Increase `SIMILARITY_MIN_SCORE`
- Increase `SIMILARITY_CORRELATION_THRESHOLD` and `SIMILARITY_L2_THRESHOLD`
- Increase `SIMILARITY_MIN_DURATION`

### Too many false negatives
- Decrease `SIMILARITY_MIN_SCORE`
- Decrease `SIMILARITY_CORRELATION_THRESHOLD` and `SIMILARITY_L2_THRESHOLD`
- Decrease `SIMILARITY_MIN_DURATION`

### Matches seem to favor wrong type
- Adjust weights to emphasize the metric that matters more
- If shape matters more (e.g., melody), increase correlation weight
- If magnitude matters more (e.g., loudness patterns), increase L2 weight

### Inconsistent results
- Check that audio segments are long enough (`SEGMENT_LENGTH_SECONDS`)
- Ensure audio quality is consistent across candidates
- Verify `FINGERPRINT_SAMPLE_RATE` is appropriate for your audio

## Advanced Topics

### Grid Search for Optimal Parameters

```python
import itertools
from scripts.evaluate_similarity import evaluate_similarity

# Define parameter grid
correlation_thresholds = [0.60, 0.70, 0.80]
l2_thresholds = [0.60, 0.70, 0.80]
min_scores = [0.65, 0.70, 0.75]

best_f1 = 0
best_params = None

for corr, l2, min_s in itertools.product(
    correlation_thresholds, l2_thresholds, min_scores
):
    eval_result = evaluate_similarity(
        "./eval_data",
        correlation_threshold=corr,
        l2_threshold=l2,
        min_score=min_s,
    )
    
    f1 = eval_result["macro_f1"]
    if f1 > best_f1:
        best_f1 = f1
        best_params = (corr, l2, min_s)

print(f"Best F1: {best_f1:.3f}")
print(f"Best params: corr={best_params[0]}, l2={best_params[1]}, min_score={best_params[2]}")
```

## Additional Resources

- See `src/core/audio_fingerprinting.py` for implementation details
- See `tests/core/test_audio_fingerprinting.py` for examples
- See `config/settings.py` for all available configuration options
