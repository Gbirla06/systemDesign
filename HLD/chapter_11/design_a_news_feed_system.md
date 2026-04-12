# Chapter 11: Design a News Feed System

> **Core Idea:** A News Feed System (like Facebook's Timeline, Twitter's Home Feed, or Instagram's Feed) aggregates posts from people you follow and presents them to you in a ranked/chronological order. This chapter is a masterclass in **write-heavy vs. read-heavy tradeoffs**, the **Fanout Problem**, and **cache-first architecture**.

---

## 🧠 The Big Picture — What Are We Actually Building?

A News Feed System has exactly **two core operations**:

| Operation | Trigger | Example |
|---|---|---|
| **Feed Publishing** | User creates a post | You post a photo on Instagram |
| **News Feed Building** | User opens the app | You scroll and see posts from people you follow |

### 🍕 The Newspaper Analogy:
Imagine a newspaper company with 100 million subscribers.
- **Publishing (Writing):** A reporter files a story. The editor's desk assigns it to sections.
- **Reading:** Every morning, a subscriber picks up their personalized newspaper.

The challenge: **How do you get the right stories to the right 100 million people every morning?**
- Do you pre-print one newspaper per person the night before? (**Fanout on Write**)
- Or do you keep one master newspaper and let each person select their stories on demand? (**Fanout on Read**)

This is the **central design question** of this chapter.

---

## 🎯 Step 1: Understand the Problem & Scope

### Clarifying the Requirements:

```
You:  "Is this a mobile app, web app, or both?"
Int:  "Both."

You:  "What are the important features?"
Int:  "A user can publish posts and see their friends' posts in their news feed."

You:  "Is the news feed sorted by time or by some ranking/relevance?"
Int:  "Assume chronological order for simplicity."

You:  "How many friends can a user have?"
Int:  "Maximum 5,000 friends."

You:  "What is the traffic volume?"
Int:  "10 million DAU (Daily Active Users)."

You:  "Can posts contain images or videos?"
Int:  "Posts can contain media files (images, videos)."
```

### 🧮 Back-of-the-Envelope Estimates

| Metric | Calculation | Result |
|---|---|---|
| **Publish QPS** | 10M DAU × 1 post avg / 86,400 sec | `~115 writes/sec` |
| **Read QPS** | 10M DAU × 10 scroll sessions / 86,400 sec | `~1,157 reads/sec` |
| **Read : Write Ratio** | | `~10:1` — Read-heavy! |
| **Storage (media)** | 115 posts/sec × avg 1MB media | `~10 GB/sec of media` |

> **Takeaway:** This is a **heavily read-skewed** system. The # of users reading the feed vastly outnumbers users posting. Our architecture must optimize for fast reads above all else.

---

## 🏗️ Step 2: High-Level Design — Two Main Flows

The entire system decomposes into two independent flows.

### Flow 1: Feed Publishing (Write Path)
*User Alice creates a new post.*

```mermaid
graph LR
    A["📱 Alice's App"] -->|"POST /feed/publish"| LB["⚖️ Load Balancer"]
    LB --> WS["🖥️ Web Server\n(Auth, Rate Limit)"]
    WS --> PS["📝 Post Service\n(Save post)"]
    WS --> FS["📡 Fanout Service\n(Distribute to followers)"]
    
    PS --> PostDB[("💾 Post DB")]
    PS --> Cache["⚡ Post Cache"]
    
    FS --> MQ["📦 Message Queue"]
    MQ --> FW["👷 Fanout Workers"]
    FW --> FeedCache[("⚡ News Feed Cache")]

    style A fill:#2d3436,stroke:#636e72,color:#dfe6e9
    style FS fill:#0984e3,stroke:#74b9ff,color:#fff
    style FeedCache fill:#e17055,stroke:#fab1a0,color:#fff
    style MQ fill:#fdcb6e,stroke:#ffeaa7,color:#2d3436
```

### Flow 2: News Feed Building (Read Path)
*User Bob opens the app and sees his feed.*

```mermaid
graph LR
    B["📱 Bob's App"] -->|"GET /feed"| LB["⚖️ Load Balancer"]
    LB --> WS["🖥️ Web Server"]
    WS --> NS["📰 News Feed Service"]
    
    NS -->|"1. Get post IDs from cache"| FC["⚡ Feed Cache"]
    FC -->|"2. Fetch post data"| PC["⚡ Post Cache"]
    PC -->|"3. Fetch user info"| UC["⚡ User Cache"]
    PC -.->|"Cache miss only"| PostDB[("💾 Post DB")]
    UC -.->|"Cache miss only"| UserDB[("💾 User DB")]
    
    NS -->|"Feed assembled"| B

    style NS fill:#0984e3,stroke:#74b9ff,color:#fff
    style FC fill:#e17055,stroke:#fab1a0,color:#fff
    style PC fill:#e17055,stroke:#fab1a0,color:#fff
```

---

## 🔬 Step 3: The Deep Dive — The Fanout Problem (The Heart of This Chapter)

**Fanout** is the act of pushing one post to all followers of the poster. When Alice (who has 5,000 friends) posts something, that single post must effectively be "delivered" to 5,000 news feeds. This is the hardest engineering problem in this chapter.

There are **three approaches**. Let's build up the reasoning step by step.

---

### 🔴 Approach A: Fanout on Read (Pull Model)

**Naive Idea:** Don't do any work when Alice publishes. When Bob opens his feed, at that moment, go collect all posts from everyone Bob follows.

```mermaid
graph LR
    BOB["📱 Bob opens feed"] -->|"GET /feed"| NS["📰 News Feed Service"]
    NS -->|"1. Who does Bob follow?"| FollowDB[("Following DB")]
    NS -->|"2. Get latest posts from each person"| PostDB[("Post DB")]
    NS -->|"3. Merge + Sort + Return"| BOB
```

**Step-by-Step Fetch Logic:**
```
1. Query: SELECT followee_ids FROM follow_table WHERE follower_id = Bob   -> [Alice, Carol, Dave, ...]
2. Query: SELECT posts FROM post_table WHERE user_id IN (Alice, Carol, Dave...) 
          ORDER BY timestamp DESC LIMIT 20
3. Merge the N result sets together and sort by time again
4. Return to Bob
```

**✅ Pros:**
| Advantage | Why |
|---|---|
| Publishing is instant | Alice doesn't do any extra work when posting. Just write to `Post DB`. |
| Always fresh data | Bob always sees the most recent posts with no cache staleness issues. |
| Celebrity-safe | A celebrity with 5 million followers doesn't trigger any extra write work. |

**❌ Cons — Why It Breaks at Scale:**
| Problem | Explanation |
|---|---|
| **Massive read amplification** | Bob follows 500 people. Each "open feed" fires 500 database queries (or one massive JOIN). At 10M DAU each opening the app 10x/day = 100M heavy reads/sec. Catastrophic. |
| **Slow read latency** | Merging + sorting posts from 500 different people on every request makes feed loading feel sluggish. |
| **Cannot cache easily** | If Bob and Carol both follow Alice, they each re-query Alice's posts independently. No sharing. |

---

### 🟡 Approach B: Fanout on Write (Push Model)

**The Opposite Idea:** Do all the work at publish time. When Alice posts, immediately push her post ID into each of her 5,000 followers' "News Feed cache" so that reading is instant.

```mermaid
graph TB
    ALICE["📱 Alice publishes"] --> PS["📝 Post Service"]
    PS --> FS["📡 Fanout Service"]
    
    FS -->|"Get all of Alice's followers"| FollowDB[("Follow DB")]
    FS -->|"Push post ID to each follower's feed cache"| FeedCache1["⚡ Bob's Feed Cache"]
    FS --> FeedCache2["⚡ Carol's Feed Cache"]
    FS --> FeedCache3["⚡ Dave's Feed Cache"]
    FS --> FeedCacheN["⚡ 5000 followers..."]

    style FS fill:#0984e3,stroke:#74b9ff,color:#fff
    style FeedCache1 fill:#e17055,stroke:#fab1a0,color:#fff
    style FeedCache2 fill:#e17055,stroke:#fab1a0,color:#fff
    style FeedCache3 fill:#e17055,stroke:#fab1a0,color:#fff
    style FeedCacheN fill:#6c5ce7,stroke:#a29bfe,color:#fff
```

**The News Feed Cache structure per user (e.g. Bob's feed)**:
```
Redis Key: "feed:user_id:bob"
Value: Sorted Set of Post IDs ordered by timestamp

Example:
feed:bob → [ post_id_1847, post_id_1842, post_id_1839, post_id_1823 ... ]
(Bob only stores the ~20 most recent post IDs in his feed cache)
```

Bob reading his feed now costs only **one** Redis lookup instead of 500 DB queries!

**✅ Pros:**
| Advantage | Why |
|---|---|
| **Blazing fast reads** | Feed retrieval = one Redis key lookup. No DB calls, no joining, no sorting. |
| **Pre-computed & cacheable** | Each user's feed is pre-assembled and ready. |

**❌ Cons — The Celebrity / Hotspot Problem:**
| Problem | Explanation |
|---|---|
| **Write amplification** | A celebrity (e.g. Cristiano Ronaldo: 600M followers) posting one photo triggers **600 million** writes to Redis! This is a thundering herd problem. |
| **Wasted writes** | If a follower hasn't opened the app in 3 months, we still wrote to their feed cache. |
| **Cache coherency** | If a post is deleted, we need to find and remove it from millions of individual feed caches. |

---

### 🟢 Approach C: Hybrid Model (The Winner ⭐)

**Insight:** The Push model is perfect for "normal" users. The Pull model is perfect for "celebrity" users. Use both!

**The Rule:**
> - If the user being followed has **fewer than a threshold** (e.g., 10,000 followers) → **Fanout on Write** (Push)
> - If the user being followed has **more than the threshold** (e.g., celebrity) → **Fanout on Read** (Pull)

**How it works end-to-end:**

**At Publish Time:**
1. Alice posts (normal user, 2,000 followers) → Fanout service pushes to all 2,000 followers' Feed Caches immediately.
2. Ronaldo posts (celebrity, 600M followers) → **No fanout**. Post is only saved to `Post DB`.

**At Read Time (Bob opens his feed):**
1. News Feed Service fetches Bob's pre-built Feed Cache (contains posts from Alice, Carol, Dave...).
2. News Feed Service **also** queries: "Does Bob follow any celebrities?" → [Ronaldo, Messi, BTS...]
3. Fetches the latest posts from those celebrities directly from Post DB.
4. Merges the two lists, sorts by timestamp, and returns.

```mermaid
graph TB
    subgraph Write["✏️ Publish Path"]
        ALICE["Alice (2K followers)\n→ Fanout on Write"] --> FCACHE["⚡ 2000 Followers' feed caches updated instantly"]
        RONALDO["Ronaldo (600M followers)\n→ NO Fanout (just save to DB)"] --> POSTDB[("💾 Post DB")]
    end

    subgraph Read["📖 Read Path"]
        BOB["Bob opens Feed"]
        BOB -->|"1. My pre-built feed"| FEEDCACHE["⚡ Bob's Feed Cache\n(has Alice, Carol, Dave...)"]
        BOB -->|"2. Celebrity posts I follow"| POSTDB
        BOB -->|"3. Merge + return"| RESULT["✅ Bob's Feed"]
    end

    style ALICE fill:#00b894,stroke:#55efc4,color:#fff
    style RONALDO fill:#d63031,stroke:#ff7675,color:#fff
    style FCACHE fill:#e17055,stroke:#fab1a0,color:#fff
    style POSTDB fill:#2d3436,stroke:#636e72,color:#dfe6e9
```

---

## 🗄️ Step 4: Data Storage Design

Different types of data have different access patterns, so we use different storage solutions:

### SQL vs. NoSQL Choice:
| Data Type | Storage Choice | Reason |
|---|---|---|
| **User Data** (name, email, settings) | **MySQL** | Relational. Moderately sized. |
| **Follow Relationships** | **MySQL or Graph DB** | `follower_id -> followee_id` table. Simple JOIN. |
| **Posts** (text, metadata) | **MySQL** (or Cassandra for scale) | Posts are immutable once written; can be sharded by `user_id`. |
| **Media** (images, videos) | **CDN + Object Storage** (S3) | Binary files stored in cold storage, CDN for fast global delivery. |
| **Feed Caches** | **Redis** | Lightning fast sorted sets. Ephemeral data (can be rebuilt). |
| **Post Caches** | **Redis** | Key-value lookup. `post_id -> post_data`. |

### Database Schema Design

```sql
-- Users table
CREATE TABLE users (
    user_id     BIGINT PRIMARY KEY,        -- Snowflake ID (Chapter 7!)
    username    VARCHAR(100) UNIQUE NOT NULL,
    name        VARCHAR(200),
    avatar_url  VARCHAR(500),
    created_at  DATETIME
);

-- Posts table (write once, never updated)
CREATE TABLE posts (
    post_id     BIGINT PRIMARY KEY,        -- Snowflake ID (time-sortable = time order!)
    user_id     BIGINT NOT NULL,
    content     TEXT,
    media_url   VARCHAR(500),              -- S3/CDN URL for image/video
    created_at  DATETIME NOT NULL,
    INDEX idx_user_posts (user_id, post_id DESC)  -- "get all posts by user X, newest first"
);

-- Social graph: who follows whom
CREATE TABLE follows (
    follower_id BIGINT NOT NULL,
    followee_id BIGINT NOT NULL,
    created_at  DATETIME,
    PRIMARY KEY (follower_id, followee_id),
    INDEX idx_followee (followee_id)       -- "who follows this person" (for fanout)
);
```

> **Why use Snowflake ID (Chapter 7) as `post_id`?**
> Snowflake IDs are time-ordered. `SELECT * FROM posts WHERE user_id = X ORDER BY post_id DESC` gives posts in chronological order WITHOUT needing to store or sort by `created_at`. The ID itself encodes time!

---

### The Post Publishing — Full Sequence Diagram

```mermaid
sequenceDiagram
    participant Alice as 📱 Alice's App
    participant LB as ⚖️ Load Balancer
    participant API as ⚙️ Web Server
    participant PostSvc as 📝 Post Service
    participant FanoutSvc as 📡 Fanout Service
    participant MQ as 📦 Kafka
    participant FanoutWorker as 👷 Fanout Worker
    participant Redis as ⚡ Redis

    Alice->>LB: POST /feed/publish {content: "Hello World!", media: <img>}
    LB->>API: Route request
    API->>API: Authenticate JWT token
    API->>PostSvc: Create post
    PostSvc->>PostSvc: Generate Snowflake post_id
    PostSvc->>DB: INSERT INTO posts (post_id, user_id, content, created_at)
    PostSvc->>Redis: SET post:{post_id} = {content, media_url, author_id, timestamp}
    PostSvc-->>API: post_id = 1847293

    API->>FanoutSvc: Fanout event {post_id: 1847293, author_id: alice, follower_count: 2000}
    FanoutSvc->>Kafka: Publish to "fanout-jobs" topic
    API-->>Alice: 200 OK {"post_id": 1847293} (Instant! Fanout is async)

    Note over Kafka, FanoutWorker: Async processing — Alice sees success immediately

    Kafka->>FanoutWorker: Consume fanout job
    FanoutWorker->>DB: SELECT follower_id FROM follows WHERE followee_id = alice LIMIT 5000
    loop For each follower (batch of 100)
        FanoutWorker->>Redis: ZADD feed:bob 1847293 {score: timestamp}
        FanoutWorker->>Redis: ZADD feed:carol 1847293 {score: timestamp}
        FanoutWorker->>Redis: ZADD feed:dave 1847293 {score: timestamp}
        FanoutWorker->>Redis: ZREMRANGEBYRANK feed:bob 0 -501 (trim to 500 most recent)
    end
```

**Key details in the fanout worker:**
```python
def fanout_worker(fanout_job):
    post_id     = fanout_job["post_id"]
    author_id   = fanout_job["author_id"]
    timestamp   = fanout_job["timestamp"]
    
    # Get all follower IDs
    followers = db.query(
        "SELECT follower_id FROM follows WHERE followee_id = %s",
        author_id
    )
    
    # Batch Redis pipeline for performance (not one call per follower!)
    pipe = redis.pipeline()
    for batch in chunks(followers, 100):
        for follower_id in batch:
            feed_key = f"feed:{follower_id}"
            # ZADD: add post_id to sorted set with score=timestamp
            # ZREMRANGEBYRANK: trim to keep only 500 most recent posts in cache
            pipe.zadd(feed_key, {str(post_id): timestamp})
            pipe.zremrangebyrank(feed_key, 0, -501)
        pipe.execute()   # Batch execute → one network round-trip per 100 followers
```

---

## 🚀 Step 5: The Complete Cache Architecture

Caching is central to this design. We cache at multiple levels:

```
Level 1 (Hottest): News Feed Cache
  → Redis Sorted Set per user: "feed:user_X" = [post_id_1, post_id_2, ...]
  → Stores only the 20 most recent post IDs (not the content!)
  
Level 2: Post Content Cache
  → Redis Hash per post: "post:1234" = {text, media_url, author_id, timestamp}
  → Holds post data for recent/popular posts
  
Level 3: User Profile Cache
  → Redis Hash per user: "user:567" = {name, avatar_url, bio}
  → Author info needed to render any post
  
Level 4: Social Graph Cache
  → Redis Set: "followers:user_X" = {follower_1, follower_2, ...}
  → Needed for Fanout Service
```

**Why Not Store Full Posts in the Feed Cache?**
If Alice has 5,000 followers and posts 3 times a day, storing the full post in every follower's cache = `5,000 × 3 × avg 1KB = 15MB per day` extra cache usage. By storing only `post_id` (a tiny integer), we separate concerns: the Feed Cache stores *what* to show (IDs), and the Post Cache stores *how* to render it.

---

## 🛠️ Step 6: Handling Hot Keys (Advanced)

### Problem: Thundering Herd on Celebrity Post
Even with the Hybrid model, at *read time*, when Ronaldo posts, millions of users suddenly query `post_id = Ronaldo's_latest_post` from the Post Content Cache simultaneously. This single Redis key gets hammered.

> **Solution 1 - Consistent Hashing/Replication:** Replicate the hot post across multiple Redis nodes so different users hit different replicas.
>
> **Solution 2 - Local In-Process Cache:** The web server itself caches the single most-recent post from top celebrities in its own memory (`HashMap`) for 1 second. Absorbs the massive burst without any Redis calls.

---

## 🔄 Step 6: Feed Retrieval — Pagination & Cursor-Based Loading

### The Problem with Offset Pagination

A naive implementation might use offset-based pagination:
```sql
-- Page 1
SELECT post_id FROM feed_items WHERE user_id = bob ORDER BY post_id DESC LIMIT 20 OFFSET 0;
-- Page 2
SELECT post_id FROM feed_items WHERE user_id = bob ORDER BY post_id DESC LIMIT 20 OFFSET 20;
```

**Problems:**
| Problem | Explanation |
|---|---|
| **Skip penalty** | `OFFSET 1000` scans and discards 1000 rows to reach the 1001st row. Expensive at large offsets. |
| **Drift** | Between page 1 and page 2, new posts arrive. Page 2 may overlap with page 1 or skip posts. |

### Cursor-Based Pagination ⭐ (The Production Solution)

Use the `post_id` (Snowflake ID = time-ordered) as a cursor:

```
Initial load: GET /feed?limit=20
→ Returns 20 post_ids, "next_cursor": "1847293"

Next page: GET /feed?limit=20&before_cursor=1847293
→ Redis: ZRANGEBYSCORE feed:bob -inf (1847293-1) LIMIT 20
→ Returns the next 20 posts older than post 1847293

No scan penalty! Redis sorted set ZRANGEBYSCORE = O(log N + results)
No drift! "before_cursor" is a fixed point in time
```

---

## 📊 Step 7: Feed Ranking (Beyond Chronological Order)

So far we assumed chronological ordering. Real-world feeds (Facebook, Instagram) use **ranking algorithms** to promote more relevant posts.

### Simple Ranking Score Formula

```python
def rank_score(post):
    # Factors:
    time_decay  = math.exp(-lambda_ * hours_since_posted)  # Older → lower score
    engagement  = log(1 + post.likes + post.comments * 2)  # More liked → higher
    affinity    = affinity_score[viewer][post.author]       # Close friends → higher
    media_bonus = 1.5 if post.has_media else 1.0            # Photos/videos boosted
    
    return time_decay * engagement * affinity * media_bonus

# Sort posts in the feed by rank_score descending
ranked_feed = sorted(candidate_posts, key=rank_score, reverse=True)
```

**How to apply ranking to our cache system:**
1. Fanout workers still push `post_id` + `timestamp` to feed caches.
2. When assembling the feed for display, pull the top 100 candidate post IDs from the Feed Cache.
3. Fetch full post data (engagement counts, media type) from Post Cache.
4. Apply ranking formula to reorder those 100 candidates.
5. Return top 20 to the user.

> Note: The Feed Cache stores posts chronologically (sorted by time). The ranking re-sorts a small window of candidates at display time. This keeps the cache simple while still enabling ranking.

---



| Topic | Decision | Why |
|---|---|---|
| **Feed Publishing** | Write to Post DB + trigger Fanout | Single source of truth, then distribute |
| **Fanout Model** | **Hybrid** (Push for normal users, Pull for celebrities) | Balances write amplification vs. read latency |
| **Feed Storage** | Redis Sorted Sets | O(log N) insertion, O(1) retrieval. Cache only post IDs, not full content |
| **Celebrity Post Delivery** | On-demand pull at read time | Avoid 600M writes per Ronaldo post |
| **Post Content Storage** | MySQL + Cassandra for scale | Immutable writes, shardable by user_id |
| **Media Storage** | CDN + S3 Object Storage | Binary blobs don't belong in relational DB |
| **Hot Key Problem** | In-process cache + Redis replication | Absorb thundering herd at the app server level |

---

## 🧠 Memory Tricks

### The 3 Fanout Models: **"Read, Write, Hybrid"** 📖✏️ 🔀
- **Read (Pull):** "Gather posts when user opens app." Fast writes, slow reads.
- **Write (Push):** "Deliver to all followers when post is published." Slow writes, fast reads. But destroys Celebrity accounts.
- **Hybrid:** Normal users → Push. Celebrities → Pull. Best of both worlds. ✅

### The Cache Layers: **"Feed → Post → User"** (Top-Down) 🏆
1. **Feed Cache** = List of post IDs per user.
2. **Post Cache** = Post content per ID.
3. **User Cache** = Author info per user ID.

---

## ❓ Interview Quick-Fire Questions

**Q1: What is the core tradeoff between Fanout on Write vs Fanout on Read?**
> Fanout on Write (Push) pre-computes feeds at publish time = slow writes, very fast reads. Fanout on Read (Pull) computes feeds at read time = instant writes, slow and expensive reads. Neither is universally better — the optimal choice is always the hybrid model for systems with a mix of normal and celebrity users.

**Q2: Why do we store only `post_id` in the News Feed Cache instead of the full post content?**
> To separate concerns and minimize redundant data. If Alice has 5,000 followers, storing her full post in every follower's cache wastes enormous space and creates cache coherency nightmares (if Alice edits her post, you'd need to invalidate 5,000 cache entries). Storing just the `post_id` keeps the Feed Cache tiny, while a single shared `Post Content Cache` holds the actual content.

**Q3: How do you handle a celebrity with 100 million followers?**
> The Hybrid model. Famous accounts (identified by exceeding a follower threshold) are excluded from the Write Fanout process entirely. Their posts are only written to the Post DB. When a user reads their feed, the system supplements their pre-computed feed cache with a small, targeted real-time query for celebrity posts they follow.

**Q4: Why use a CDN for media?**
> User photos and videos (binary blob data) are extremely large files and accessed repeatedly. Storing them in a relational DB is wasteful and slow. CDNs distribute these large files across hundreds of global edge servers, ensuring a user in Mumbai pulls images from a Mumbai CDN node, not a server in the US — dramatically reducing latency for the most data-heavy part of the response.

**Q5: How do you know which users are "celebrities" vs. "normal" users?**
> A user's follower count is stored in the User DB and cached in the User Cache. The Fanout Service checks the follower count at the time of publishing. If it exceeds the threshold (e.g., 10,000), it skips the write fanout. Note: this threshold should be tunable based on system load; you don't hardcode it.

---

> **📖 Previous Chapter:** [← Chapter 10: Design a Notification System](/HLD/chapter_10/design_a_notification_system.md)
>
> **📖 Next Chapter:** [Chapter 12: Design a Chat System →](/HLD/chapter_12/)
