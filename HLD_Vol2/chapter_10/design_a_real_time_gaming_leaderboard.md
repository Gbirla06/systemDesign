# Volume 2 - Chapter 10: Design a Real-Time Gaming Leaderboard

> **Core Idea:** A gaming leaderboard ranks millions of players by score in real-time. When a player wins a match, their score updates and they see their new global rank instantly. The challenge is that **ranking is inherently a global operation** — to know you're ranked #54,231 out of 25 million players, the system must compare your score against everyone else's. Naive SQL `ORDER BY score` on 25 million rows is far too slow for real-time. The solution is Redis Sorted Sets — a data structure purpose-built for ranked scoring.

---

## 🎯 Step 1: Understand the Problem & Scope

### Clarifying the Requirements

```
You:  "How many players?"
Int:  "25 million monthly active players. 5 million DAU."

You:  "How often do scores update?"
Int:  "A player's score updates after every match. Average 10 matches per day per active user."

You:  "What queries do we need to support?"
Int:  "1. Get global top 100 players.
       2. Get a specific player's rank.  
       3. Get players around a specific player (e.g., rank 1000-1010)."

You:  "How real-time does the leaderboard need to be?"
Int:  "Within seconds of a match ending, the player should see their updated rank."
```

### 📋 Back-of-the-Envelope

| Metric | Calculation | Result |
|---|---|---|
| **Score updates/day** | 5M DAU × 10 matches | **50 Million updates/day** |
| **Score update QPS** | 50M / 86400 | **~580 QPS** |
| **Peak update QPS** | 580 × 5 | **~2,900 QPS** |
| **Leaderboard read QPS** | 5M DAU × 20 views/day / 86400 | **~1,160 QPS** |
| **Data size** | 25M players × 100 bytes (id + score + metadata) | **~2.5 GB** |

> **Takeaway:** The data is tiny (2.5 GB fits entirely in RAM). QPS is moderate. The hard problem is the **rank query** — every time a player asks "What is my rank?", we need to count how many players have a higher score. On 25 million rows, this is expensive in SQL but trivial in Redis Sorted Sets.

---

## ☠️ Step 2: Why SQL Fails for Real-Time Ranking

### The Naive Approach
```sql
-- Get player's rank
SELECT COUNT(*) + 1 AS rank FROM players WHERE score > (
    SELECT score FROM players WHERE player_id = 'alice'
);
```

**Problem:** This scans up to 25 million rows to count how many players have a higher score. Even with an index on `score`, the COUNT requires walking the B-tree. At 1,160 QPS, the database CPU would be 100% busy just counting.

### The Batch Approach (Pre-compute ranks)
Run a nightly batch job: `UPDATE players SET rank = ROW_NUMBER() OVER (ORDER BY score DESC)`.
- **Problem:** Ranks are stale until the next batch run. A player who just won a match won't see their updated rank for hours. Not "real-time."

> **The Solution:** Use **Redis Sorted Sets** — a data structure that maintains elements in sorted order and provides `O(log N)` rank queries natively.

---

## ⚡ Step 3: Redis Sorted Sets — The Perfect Data Structure

### What is a Sorted Set?
A Redis Sorted Set is a collection of unique members, each associated with a floating-point **score**. Members are always maintained in sorted order by score.

```redis
-- Add players with scores
ZADD leaderboard 1500 "alice"
ZADD leaderboard 2300 "bob"
ZADD leaderboard 1800 "charlie"
ZADD leaderboard 2100 "dave"

-- Internal state (always sorted by score):
-- Index 0: alice   (1500)
-- Index 1: charlie (1800)
-- Index 2: dave    (2100)
-- Index 3: bob     (2300)  ← Highest score
```

### The Key Operations (All O(log N))

| Operation | Command | Time | Example |
|---|---|---|---|
| **Update score** | `ZADD leaderboard 1900 "alice"` | O(log N) | Alice won a match, new score 1900 |
| **Get rank** | `ZREVRANK leaderboard "alice"` | O(log N) | Returns 2 (0-indexed, descending) |
| **Top K** | `ZREVRANGE leaderboard 0 9 WITHSCORES` | O(log N + K) | Returns top 10 players |
| **Players around rank** | `ZREVRANGE leaderboard 999 1009` | O(log N + K) | Ranks 1000-1010 |
| **Get score** | `ZSCORE leaderboard "alice"` | O(1) | Returns 1900 |

### How Does Redis Achieve O(log N) Ranking?

Internally, Redis Sorted Sets use a **Skip List** — a probabilistic data structure that's like a linked list with express lanes.

#### Beginner Example: The Express Train Analogy
Imagine a train line with 100 stations:
```
Local train:   Stops at EVERY station → 100 stops to get to station 100
Express train: Stops every 10th station → 10 stops, then switch to local for last few
Super express: Stops every 50th station → 2 stops, then express, then local
```

A skip list has multiple "lanes":
```
Level 3:  1 ─────────────────────────────── 50 ────────────────────── 100
Level 2:  1 ──── 10 ──── 20 ──── 30 ──── 50 ──── 70 ──── 90 ──── 100
Level 1:  1 ── 5 ── 10 ── 15 ── 20 ── 25 ── 30 ── 35 ── 40 ──...── 100
Level 0:  1  2  3  4  5  6  7  8  9  10  11 ... (every element)
```

To find rank of element 73:
1. Start at Level 3: jump to 50 (count: 50 elements skipped)
2. Drop to Level 2: jump to 70 (count += 20)
3. Drop to Level 1: jump to 73 (count += 3)
4. **Rank = 73** (computed during traversal!)

Each level stores the **span** (number of elements between nodes), enabling rank calculation during traversal without scanning every element.

---

## 🏛️ Step 4: System Architecture

```mermaid
graph TD
    subgraph Game Servers
        GS["🎮 Game Server\n(match ends → score update)"]
    end

    subgraph API
        LBAPI["🌐 Leaderboard API"]
    end

    subgraph Storage
        Redis["⚡ Redis Sorted Set\n(Real-time ranking)"]
        MySQL["💾 MySQL\n(Player profiles, history)"]
    end

    GS -->|"Score update"| LBAPI
    LBAPI -->|"ZADD"| Redis
    LBAPI -->|"Save match history"| MySQL
    
    Player["📱 Player"] -->|"Get my rank"| LBAPI
    LBAPI -->|"ZREVRANK"| Redis
    LBAPI -->|"Get profile"| MySQL

    style Redis fill:#d63031,color:#fff
    style MySQL fill:#0984e3,color:#fff
```

### The Flow
1. **Match ends:** Game server calls `POST /api/scores` with `{player_id, new_score}`.
2. **API Server:** Runs `ZADD leaderboard {new_score} {player_id}` on Redis. Redis updates the sorted set in O(log N). Also writes match result to MySQL for history.
3. **Player views leaderboard:** `GET /api/leaderboard/top100` → `ZREVRANGE leaderboard 0 99 WITHSCORES`.
4. **Player checks own rank:** `GET /api/leaderboard/rank/alice` → `ZREVRANK leaderboard "alice"`.

---

## 🧑‍💻 Step 5: Advanced Scenarios

### Handling 25M Players in Redis
A single Redis Sorted Set with 25M members uses ~2.5 GB RAM. This easily fits in a single Redis instance (modern instances have 64–256 GB RAM). No sharding needed for the sorted set itself!

However, if we need **multiple leaderboards** (daily, weekly, monthly, per-game-mode), each is a separate sorted set:
```redis
ZADD leaderboard:global    1900 "alice"
ZADD leaderboard:weekly    400  "alice"
ZADD leaderboard:ranked    1200 "alice"
```

### Time-Based Leaderboards (Weekly Reset)
- **Weekly leaderboard:** Create a new sorted set each week: `leaderboard:week:2026-W18`.
- At the start of each week, a background job rotates: the old set is archived, a fresh empty set begins.
- Players who haven't played this week simply don't exist in the current week's set.

### Tie-Breaking
If two players have the same score, who ranks higher? Redis sorts ties by lexicographic order of the member name (alphabetical). This is rarely the desired behavior.

> **Solution:** Encode a tiebreaker into the score itself using decimal precision:
> ```
> score = actual_score + (1 - timestamp / max_timestamp)
> 
> Alice scored 2000 at 10:00:00 → 2000.999990
> Bob   scored 2000 at 10:05:00 → 2000.999985
> 
> Alice ranks higher (she achieved the score first)
> ```

### Relative Leaderboard ("Friends Only")
Instead of global rank, show rank among friends. Maintain a separate sorted set per user or use `ZRANGEBYSCORE` to filter. For small friend lists (<1000), this is fast. For large social graphs, precompute friend-relative ranks asynchronously.

### Sharding for Extreme Scale (100M+ Players)
If a single Redis instance can't hold all players (unlikely for most games):
- Shard by score range: Shard 1 holds scores 0-999, Shard 2 holds 1000-1999, etc.
- To get global rank: query the player's shard for their local rank, then add the total count of all higher-score shards.
- This requires a metadata layer tracking the count per shard.

---

## 📋 Summary — Quick Revision Table

| Component | Choice | Why |
|---|---|---|
| **Core data structure** | **Redis Sorted Set (Skip List)** | O(log N) for insert, rank query, and range query. Perfect for real-time ranking. |
| **Profile storage** | **MySQL** | Player details, match history, achievements. Queried by player_id. |
| **Rank query** | **`ZREVRANK`** | Returns rank in O(log N) without scanning. |
| **Top-K query** | **`ZREVRANGE 0 K`** | Returns top K players in O(log N + K). |
| **Tie-breaking** | **Encode timestamp in decimal score** | Earlier achievement of same score ranks higher. |

---

## 🧠 Memory Tricks

### **"The Express Train" for Skip Lists**
> A skip list is a linked list with express lanes. Instead of walking past every station (O(N)), you jump on the express train (O(log N)). Each lane stores how many stations you skip, so you can calculate rank during traversal.

### **"S.R.T." — Leaderboard Checklist**
1. **S**orted Set — Redis ZADD/ZREVRANK for real-time ranking
2. **R**ank = O(log N) — Skip list, not SQL COUNT
3. **T**ie-break — Encode timestamp in the decimal portion of the score

---

> **📖 Previous Chapter:** [← Chapter 9: Design S3 Object Storage](/HLD_Vol2/chapter_9/design_s3_object_storage.md)  
> **📖 Up Next:** Chapter 11 - Design a Payment System
