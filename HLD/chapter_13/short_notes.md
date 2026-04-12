# 📝 Short Notes — Design a Search Autocomplete System

---

## What Is It?
A typeahead/suggestion system that returns the top-5 most popular searches matching a prefix as the user types (e.g., Google's search bar). Core data structure: **Trie (prefix tree)**.

---

## Two Distinct Services

| Service | When | Job |
|---|---|---|
| **Data Gathering (Offline)** | Weekly batch | Collects search logs → computes frequencies → builds & refreshes the Trie |
| **Query Service (Online)** | Every keystroke | Returns top-5 suggestions for a prefix in < 100ms |

---

## The Trie — Core Concept

A tree where each **character is a node**. Each path from root → node = a prefix or complete word. Navigating to prefix "int" takes exactly **3 hops**, then reads suggestions — no scanning.

**The Critical Optimization: Cache top-5 at every node**

| Approach | Query Time | Problem |
|---|---|---|
| **Basic Trie** (DFS at read time) | O(p + c) | DFS on 'a' = millions of traversals. Too slow! |
| **Optimized Trie** (top-5 cached per node) | **O(p) only** | Pre-computed at write time; just read at query time ✅ |

---

## Data Gathering Service (Write Pipeline)

```
1. All search queries → Raw log files (Kafka stream)
2. Weekly Spark job → Aggregates logs → Frequency DB
   (e.g., "interview questions" → 12.4M searches/week)
3. Trie Builder → Reads Frequency DB → Builds optimized Trie with top-5 cached per node
4. Blue-Green Deploy → Atomic swap of old Trie with new Trie (zero downtime)
5. Real-Time Trending Layer → Hourly update for viral/breaking queries between weekly rebuilds
```

---

## Query Service (Read Pipeline — 3-Tier Caching)

```
User types "inter"
  ↓
Layer 1: Browser Cache → Hit? Return instantly (zero network call)
  ↓
Layer 2: Redis Cache → Hit? Return in < 1ms
  ↓
Layer 3: Trie Server → Navigate O(p) to node, read cached top-5, write back to Redis
  ↓
Return ["interview", "internet", "interesting", "interior", "interview tips"]
```

---

## Trie Sharding (Scaling)

**Naïve approach (by first character):** Creates hotspots ('s','t' very common).

**Smart approach (by prefix range):**
> Analyze historical data → split into ranges with equal query volumes.
> - Shard 1: `a` to `hm`
> - Shard 2: `hn` to `q`  
> - Shard 3: `r` to `z`
>
> **Shard Map stored in Zookeeper** tells API server which shard to route to.

---

## 🧠 Mnemonics

- **Two Services:** "**Gather → Serve**" (Offline batch → Online real-time)
- **The Big Optimization:** "**Pre-compute, Don't Compute**" 🏎️
  - Write time: compute top-5 & store at every node (expensive, done once/week)
  - Read time: just read the cached answer (O(p), done 23,000/sec)

---

> **📖 Detailed notes** → [design_a_search_autocomplete_system.md](./design_a_search_autocomplete_system.md)
