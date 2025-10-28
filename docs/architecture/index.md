# Architecture

Learn about SoundHash's system design, components, and data flow.

## Overview

This section provides a deep dive into how SoundHash works internally.

<div class="grid cards" markdown>

-   :material-sitemap:{ .lg } **[System Overview](overview.md)**
    
    ---
    
    High-level architecture and data flow diagrams

-   :material-cube-outline:{ .lg } **[Components](components.md)**
    
    ---
    
    Detailed component descriptions and interactions

-   :material-database:{ .lg } **[Database Schema](database-schema.md)**
    
    ---
    
    PostgreSQL schema and relationships

-   :material-waveform:{ .lg } **[Audio Fingerprinting](fingerprinting.md)**
    
    ---
    
    How spectral analysis and matching works

-   :material-speedometer:{ .lg } **[Performance](performance.md)**
    
    ---
    
    Optimization strategies and benchmarks

</div>

## Quick Links

- [System Architecture Diagram](overview.md#system-architecture)
- [Data Flow](overview.md#data-flow)
- [Processing Pipeline](components.md#processing-pipeline)
- [Matching Algorithm](fingerprinting.md#matching-algorithm)

## Key Concepts

### Audio Fingerprinting

SoundHash uses spectral analysis to create unique "fingerprints" of audio content that are:

- **Robust**: Resistant to compression, noise, and minor modifications
- **Compact**: Efficient storage and fast comparison
- **Distinctive**: Unique enough to identify specific content

### Processing Pipeline

Videos flow through a multi-stage pipeline:

1. **Ingestion**: Fetch metadata from YouTube
2. **Download**: Extract audio streams
3. **Segmentation**: Split into fixed-length chunks
4. **Fingerprinting**: Extract spectral features
5. **Storage**: Save to PostgreSQL with indexes

### Matching Strategy

Query clips are matched using:

- **Correlation**: Spectral correlation coefficient
- **Euclidean Distance**: Normalized feature vector distance
- **Combined Score**: Weighted average for final confidence

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **API** | FastAPI | REST API and WebSocket |
| **Database** | PostgreSQL | Fingerprint storage and queries |
| **Audio** | librosa, scipy | Spectral analysis |
| **Video** | yt-dlp, FFmpeg | Download and conversion |
| **Cache** | Redis | Query result caching |
| **Auth** | JWT | API authentication |
| **Monitoring** | Prometheus | Metrics and observability |

## Design Principles

### Scalability

- Horizontal scaling via stateless API
- Database connection pooling
- Async processing pipeline
- Optional Redis caching

### Reliability

- Idempotent operations
- Job status tracking
- Retry mechanisms
- Health check endpoints

### Performance

- Efficient database indexes
- Batch operations
- Parallel processing
- Query result caching

### Maintainability

- Modular architecture
- Type hints throughout
- Comprehensive logging
- Database migrations

## Further Reading

- [System Overview](overview.md) - Start here for the big picture
- [Components](components.md) - Dive into specific components
- [Fingerprinting](fingerprinting.md) - Understand the algorithm
- [Performance](performance.md) - Optimization techniques
