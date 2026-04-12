# 📝 Short Notes — Design YouTube

---

## What Is It?
A video sharing platform with two completely separate concerns: the **Upload + Transcoding Pipeline** (write-heavy, latency-tolerant, CPU-intensive) and the **Streaming Pipeline** (read-heavy, latency-critical, bandwidth-intensive).

---

## The Two Core Pipelines

### Upload Pipeline — End to End
```
1. Creator → API Server: "I want to upload" (only metadata!)
2. API → S3: Generate Pre-Signed URL (expires 30 min)
3. Creator → S3 DIRECTLY: PUT raw_video.mp4  (API server NOT involved!)
4. S3 → Message Queue: "New raw video ready" event
5. Queue → Splitter: Cut video into 2-min chunks
6. Queue → Encoder Workers (parallel): Each chunk encoded at 360p / 480p / 720p / 1080p / 4K
7. All encoded chunks → Merger → Final videos saved to S3
8. Completion Queue → DB (status=READY) + Notify Creator + CDN Distribution
```

### Streaming Pipeline
```
1. Viewer → API Server: GET /video/123
2. API Server → DB: Fetch metadata, CDN manifest URL
3. Viewer ← manifest.m3u8: List of all quality levels and segment URLs
4. Player → CDN (nearest edge): Fetch segment_001 at best quality
5. CDN HIT: Served from local cache (< 2ms)
6. CDN MISS: Fetches from S3 origin, caches for all future viewers
7. Player repeats: check bandwidth → download next segment at best possible quality
```

---

## The Two Key Interview Concepts

### 1. Pre-Signed URL — Why Not Upload Through API?
| Naïve (via API) | Correct (Pre-Signed URL) |
|---|---|
| Video travels network **twice** (creator→API, API→S3) | Video travels network **once** (creator→S3 directly) |
| API thread blocked for minutes holding 1GB upload | API handles only KBs of metadata |
| 100 concurrent uploads = 100 frozen threads | S3 handles unlimited parallel uploads |

### 2. DAG Transcoding — Why Parallelism Matters
```
Without chunking:  1-hour video → 6 hours on 1 machine

With DAG chunking:
  1-hour video → 30 × 2-min chunks
  Each chunk encoded at 5 resolutions = 150 tasks
  150 tasks → 150 worker machines in parallel
  Result: ~12 MINUTES wall-clock time (30× faster!)
```
> **Error Handling:** Queue Visibility Timeout (15 min). If worker crashes → task re-appears → picked by next worker. After 5 failures → Dead Letter Queue (DLQ) → Alert engineers.

---

## Adaptive Bitrate Streaming (HLS/DASH)
The video is cut into **6-10 second segments** at each resolution. Player downloads one segment at a time, measures bandwidth, and picks the best quality for the next segment.
```
Fast WiFi   → 1080p (8 Mbps)
4G LTE      → 720p  (3 Mbps)
Subway 3G   → 480p  (0.5 Mbps)
```
> **No buffering** because quality degrades gracefully. The player maintains a 30-second buffer so brief drops don't cause stalls.

**Seeking:** Player requests specific segment by index. `1:23:45 = 5025sec ÷ 6sec/seg = segment_837`. Fetched directly — O(1).

---

## CDN Tiering Strategy (Cost Optimization)

| Video Popularity | CDN Strategy | Storage |
|---|---|---|
| **Hot (top 20%)** | Pushed to ALL 200+ edge nodes globally | S3 Standard |
| **Warm (next 30%)** | Cached at continent-level PoPs | S3 Infrequent Access (46% cheaper) |
| **Cold (bottom 50%)** | Served from S3 origin on demand | S3 Glacier (83% cheaper, hours retrieval) |

> Top 20% videos = 80% of all views (Pareto Principle). Cache them everywhere.

---

## Storage Choices

| Data | Storage | Why |
|---|---|---|
| Raw + Encoded video files | **S3 Object Storage** (tiered) | Binary blobs, massive scale, not for DB |
| Video metadata | **MySQL** | Structured, relational |
| View / Like counters | **Redis INCR** → periodic flush to MySQL | Lock-free vs SQL hot-row deadlock |
| Comments | **Cassandra** | Append-heavy time series `(video_id, comment_id PK)` |
| Video search | **Elasticsearch** | Full-text inverted index |

---

## Security

| Concern | Solution |
|---|---|
| **DRM** | Encrypt segments with AES-128. Client needs a license key from DRM License Server (Widevine/FairPlay). |
| **Copyright** | Audio/Video fingerprinting on every upload. Compare against Reference DB (Content ID). Match → Block / Monetize / Track. |

---

## 🧠 Mnemonics

- **Upload Pipeline:** "**P-S-D-T-C**" 🎬
  - **P**re-signed URL → **S**plitter → **D**AG Workers → **T**rigger completion queue → **C**DN distribute

- **Streaming:** "**Manifest → Segment → Adapt**"
  - Download manifest (the menu) → Fetch one segment at a time → Adapt quality every 6 seconds

- **Storage Tiers:** "**Hot-Warm-Cold = Standard-IA-Glacier**" 🌡️

---

> **📖 Detailed notes** → [design_youtube.md](./design_youtube.md)
