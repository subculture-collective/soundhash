# System Overview

This page provides a high-level overview of SoundHash's architecture, components, and data flow.

## System Architecture

The following diagram shows the main components and their interactions:

```mermaid
graph TB
    subgraph "Client Layer"
        USER[User/Bot]
        WEB[Web Interface]
    end
    
    subgraph "API Layer"
        API[FastAPI Server]
        AUTH[Authentication]
        RATE[Rate Limiter]
        CORS[CORS Middleware]
    end
    
    subgraph "Business Logic"
        INGEST[Channel Ingester]
        PROC[Video Processor]
        FP[Fingerprint Engine]
        MATCH[Matching Algorithm]
    end
    
    subgraph "Storage Layer"
        DB[(PostgreSQL)]
        CACHE[(Redis Cache)]
        FS[File System]
    end
    
    subgraph "External Services"
        YT[YouTube API]
        YTDL[yt-dlp]
        FFMPEG[FFmpeg]
    end
    
    USER --> API
    WEB --> API
    API --> AUTH
    API --> RATE
    API --> CORS
    
    AUTH --> DB
    API --> INGEST
    API --> MATCH
    
    INGEST --> YT
    INGEST --> DB
    INGEST --> PROC
    
    PROC --> YTDL
    PROC --> FFMPEG
    PROC --> FP
    PROC --> FS
    
    FP --> DB
    MATCH --> DB
    MATCH --> CACHE
    
    style API fill:#673ab7,color:#fff
    style DB fill:#336791,color:#fff
    style FP fill:#9c27b0,color:#fff
```

### Component Layers

#### 1. Client Layer

- **Users**: Direct API consumers
- **Bots**: Social media integration (Twitter, Reddit)
- **Web Interface**: Interactive documentation (Swagger/ReDoc)

#### 2. API Layer

- **FastAPI Server**: REST endpoints and WebSocket
- **Authentication**: JWT-based auth and API keys
- **Rate Limiter**: Request throttling per user/IP
- **CORS**: Cross-origin resource sharing

#### 3. Business Logic

- **Channel Ingester**: YouTube channel video fetching
- **Video Processor**: Audio download and conversion
- **Fingerprint Engine**: Spectral analysis and feature extraction
- **Matching Algorithm**: Similarity computation

#### 4. Storage Layer

- **PostgreSQL**: Fingerprints, videos, users, matches
- **Redis**: Query result caching (optional)
- **File System**: Temporary audio files

#### 5. External Services

- **YouTube API**: Channel and video metadata
- **yt-dlp**: Video/audio download
- **FFmpeg**: Audio format conversion

---

## Data Flow

### Ingestion Pipeline

The following sequence shows how videos are ingested and processed:

```mermaid
sequenceDiagram
    participant CLI as CLI Script
    participant ING as Channel Ingester
    participant YT as YouTube API
    participant DB as PostgreSQL
    participant PROC as Video Processor
    participant YTDL as yt-dlp
    participant FP as Fingerprinter
    
    CLI->>ING: Start ingestion
    ING->>YT: Fetch channel videos
    YT-->>ING: Video metadata
    
    loop For each video
        ING->>DB: Check if exists
        alt New video
            ING->>DB: Create video record
            ING->>DB: Create processing job
        end
    end
    
    ING->>PROC: Process pending jobs
    
    loop For each job
        PROC->>DB: Update job status: running
        PROC->>YTDL: Download audio
        YTDL-->>PROC: Audio file
        PROC->>PROC: Convert to WAV
        PROC->>PROC: Segment audio
        
        loop For each segment
            PROC->>FP: Extract fingerprint
            FP-->>PROC: Fingerprint data
            PROC->>DB: Store fingerprint
        end
        
        PROC->>DB: Update job status: complete
        PROC->>DB: Mark video as processed
    end
```

### Matching Pipeline

The following sequence shows how a query clip is matched:

```mermaid
sequenceDiagram
    participant USER as User/Bot
    participant API as FastAPI
    participant AUTH as Auth Service
    participant CACHE as Redis
    participant FP as Fingerprinter
    participant DB as PostgreSQL
    participant MATCH as Matcher
    
    USER->>API: POST /matches/find
    API->>AUTH: Validate token
    AUTH-->>API: Token valid
    
    API->>CACHE: Check cache
    alt Cache hit
        CACHE-->>API: Cached results
        API-->>USER: Return matches
    else Cache miss
        API->>FP: Extract query fingerprint
        FP-->>API: Fingerprint data
        
        API->>DB: Query similar fingerprints
        DB-->>API: Candidate matches
        
        API->>MATCH: Compute similarity
        MATCH-->>API: Ranked matches
        
        API->>CACHE: Store results
        API-->>USER: Return matches
    end
```

---

## Processing Pipeline Details

### Stage 1: Video Download

```mermaid
graph LR
    A[Video URL] --> B[yt-dlp]
    B --> C{Format Select}
    C -->|Best Audio| D[Download Stream]
    D --> E[Audio File]
    
    style B fill:#ff6b6b
    style E fill:#4caf50
```

**Purpose**: Extract audio from video  
**Tools**: yt-dlp with cookie/proxy support  
**Output**: Audio file (various formats)

### Stage 2: Audio Conversion

```mermaid
graph LR
    A[Audio File] --> B[FFmpeg]
    B --> C{Convert}
    C -->|Mono| D[1 Channel]
    C -->|Resample| E[16kHz/22kHz]
    D --> F[WAV File]
    E --> F
    
    style B fill:#ff6b6b
    style F fill:#4caf50
```

**Purpose**: Standardize audio format  
**Tools**: FFmpeg  
**Output**: Mono WAV at configured sample rate

### Stage 3: Segmentation

```mermaid
graph LR
    A[WAV File] --> B[Segment]
    B --> C[Segment 1<br/>0-90s]
    B --> D[Segment 2<br/>90-180s]
    B --> E[Segment 3<br/>180-270s]
    B --> F[...]
    
    style B fill:#9c27b0
    style C fill:#4caf50
    style D fill:#4caf50
    style E fill:#4caf50
```

**Purpose**: Split into fixed-length chunks  
**Default**: 90-second segments  
**Overlap**: Optional overlap for better matching

### Stage 4: Fingerprinting

```mermaid
graph TB
    A[Audio Segment] --> B[STFT]
    B --> C[Spectrogram]
    C --> D[Peak Detection]
    D --> E[Feature Extraction]
    E --> F[Normalization]
    F --> G[Fingerprint Vector]
    G --> H[MD5 Hash]
    
    style A fill:#2196f3
    style G fill:#4caf50
    style H fill:#4caf50
```

**Purpose**: Extract spectral features  
**Algorithm**: Short-Time Fourier Transform (STFT) + peak detection  
**Output**: Compact feature vector + hash

### Stage 5: Storage

```mermaid
graph LR
    A[Fingerprint] --> B[PostgreSQL]
    B --> C[Indexed Storage]
    C --> D{Indexes}
    D --> E[Hash Index]
    D --> F[Video ID Index]
    D --> G[Timestamp Index]
    
    style B fill:#336791,color:#fff
    style C fill:#4caf50
```

**Purpose**: Efficient storage and retrieval  
**Database**: PostgreSQL with btree indexes  
**Optimization**: Vector similarity search

---

## Matching Algorithm

### Overview

```mermaid
graph TB
    A[Query Clip] --> B[Extract Fingerprint]
    B --> C[Database Search]
    C --> D{Candidate<br/>Matches}
    
    D --> E[Compute<br/>Correlation]
    D --> F[Compute<br/>Euclidean]
    
    E --> G[Combine Scores]
    F --> G
    
    G --> H[Rank Results]
    H --> I[Filter by<br/>Threshold]
    I --> J[Return Top N]
    
    style A fill:#2196f3
    style B fill:#9c27b0
    style C fill:#336791,color:#fff
    style J fill:#4caf50
```

### Similarity Metrics

1. **Spectral Correlation**
   ```
   correlation = mean(|corr(query, candidate)|)
   ```

2. **Euclidean Distance**
   ```
   similarity = 1 - (distance / max_distance)
   ```

3. **Combined Score**
   ```
   confidence = (correlation + euclidean_similarity) / 2
   ```

---

## Deployment Architecture

### Single Server

```mermaid
graph TB
    subgraph "Single Host"
        API[API Server]
        DB[(PostgreSQL)]
        CACHE[(Redis)]
    end
    
    USERS[Users] --> API
    API --> DB
    API --> CACHE
    
    style API fill:#673ab7,color:#fff
    style DB fill:#336791,color:#fff
```

**Use case**: Development, small deployments  
**Limitations**: No redundancy, limited scaling

### Multi-Server (Recommended)

```mermaid
graph TB
    subgraph "Load Balancer"
        LB[Nginx/HAProxy]
    end
    
    subgraph "API Tier"
        API1[API Server 1]
        API2[API Server 2]
        API3[API Server 3]
    end
    
    subgraph "Storage Tier"
        DB[(PostgreSQL<br/>Primary)]
        DB_REPLICA[(PostgreSQL<br/>Replica)]
        CACHE[(Redis Cluster)]
    end
    
    USERS[Users] --> LB
    LB --> API1
    LB --> API2
    LB --> API3
    
    API1 --> DB
    API2 --> DB
    API3 --> DB
    
    API1 --> CACHE
    API2 --> CACHE
    API3 --> CACHE
    
    DB -.-> DB_REPLICA
    
    style LB fill:#ff9800
    style API1 fill:#673ab7,color:#fff
    style API2 fill:#673ab7,color:#fff
    style API3 fill:#673ab7,color:#fff
    style DB fill:#336791,color:#fff
```

**Use case**: Production deployments  
**Features**: High availability, horizontal scaling, read replicas

---

## Key Design Decisions

### Why PostgreSQL?

- **Rich indexing**: Btree, GiST for vector search
- **ACID compliance**: Data integrity guarantees
- **Scalability**: Proven at large scale
- **Extensions**: pgvector for similarity search

### Why FastAPI?

- **Performance**: Async support, fast execution
- **DX**: Auto-generated docs, type validation
- **Modern**: Python 3.11+ type hints
- **Ecosystem**: Rich middleware and plugin support

### Why Spectral Fingerprinting?

- **Robust**: Handles compression and noise
- **Fast**: Efficient computation and comparison
- **Accurate**: High precision for matching
- **Proven**: Used in Shazam-like systems

### Why Job Queue?

- **Reliability**: Retry failed operations
- **Tracking**: Monitor progress and status
- **Scalability**: Process videos independently
- **Idempotency**: Avoid duplicate work

---

## Performance Characteristics

| Operation | Typical Time | Scaling Factor |
|-----------|-------------|----------------|
| **Video Download** | 30-120s | Video length, network |
| **Fingerprinting** | 2-10s | Audio length |
| **Single Match Query** | 50-200ms | Database size |
| **Batch Match** | 500ms-2s | Query count |

### Bottlenecks

1. **Network I/O**: YouTube downloads
2. **CPU**: FFmpeg conversion, STFT computation
3. **Database**: Large table scans without indexes
4. **Disk**: Temporary file storage

### Optimization Strategies

- **Caching**: Redis for repeated queries
- **Indexing**: Database indexes on fingerprint hashes
- **Parallelization**: Multiple download workers
- **Connection Pooling**: Reuse database connections

---

## Next Steps

<div class="grid cards" markdown>

-   :material-cube-outline:{ .lg } **Components**
    
    ---
    
    Detailed component descriptions
    
    [Learn More →](components.md)

-   :material-database:{ .lg } **Database Schema**
    
    ---
    
    Tables and relationships
    
    [Learn More →](database-schema.md)

-   :material-waveform:{ .lg } **Fingerprinting**
    
    ---
    
    Algorithm deep dive
    
    [Learn More →](fingerprinting.md)

-   :material-speedometer:{ .lg } **Performance**
    
    ---
    
    Optimization guide
    
    [Learn More →](performance.md)

</div>
