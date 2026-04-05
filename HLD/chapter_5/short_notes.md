# 📝 Short Notes — Design a Key-Value Store

---

## What Is It?
A **distributed non-relational database** that maps unique **keys → values**. Think of it as a giant dictionary — you look up a word (key) and get the meaning (value). Supports two operations: `put(key, value)` and `get(key)`.

> **Examples:** Redis, DynamoDB, Memcached, etcd, Cassandra

---

## CAP Theorem — The Foundational Trade-off

A distributed system can guarantee only **2 out of 3**:

| Property | Meaning |
|---|---|
| **C** — Consistency | All nodes see the SAME data at the SAME time |
| **A** — Availability | Every request gets a response (even if stale) |
| **P** — Partition Tolerance | System works despite network failures between nodes |

> **P is mandatory** (network failures WILL happen) → choose **CP** (consistent but may block) or **AP** (always available but may serve stale data)

| Choice | Trade-off | Example |
|---|---|---|
| **CP** | Block requests during partitions to stay consistent | Banks, MongoDB |
| **AP** | Always respond, even with stale data | Social feeds, Cassandra, DynamoDB |

> **Our design** → AP (high availability, eventual consistency)

---

## 7 Core Components — "**C**ats **R**un **C**razily, **V**ery **G**racefully **S**eeking **M**ice" 🐱

### 1️⃣ Consistent Hashing — Data Partition

| Concept | Detail |
|---|---|
| **Problem** | Modulo hashing (`hash % N`) reshuffles ALL keys on server add/remove |
| **Solution** | Hash ring — keys walk clockwise to find their server |
| **Virtual nodes** | Each server gets multiple positions on ring → even distribution |
| **Benefit** | Add/remove server → only **K/N keys** move (not all!) |

### 2️⃣ Replication

- Copy each key to **N servers** (next N clockwise on ring)
- If one server dies, N-1 others still have the data
- ⚠️ With virtual nodes, ensure replicas land on **unique physical servers**

### 3️⃣ Consistency — Quorum Consensus (W, R, N)

| Parameter | Meaning |
|---|---|
| **N** | Number of replicas |
| **W** | Write quorum — ACKs needed before write is "successful" |
| **R** | Read quorum — servers to read from |

> **Golden Rule:** `W + R > N` → **Strong consistency** (guaranteed overlap of at least 1 node with latest data)

| Config | W | R | Speed | Consistency |
|---|---|---|---|---|
| Fast writes | 1 | N | ⚡ Writes | Strong reads |
| Fast reads | N | 1 | ⚡ Reads | Strong writes |
| Balanced | 2 | 2 | Moderate | Strong |
| Max availability | 1 | 1 | ⚡⚡ Both | ⚠️ Eventual |

### 4️⃣ Versioning — Vector Clocks

- Track `[server, version]` pairs per data item → `D([S1, v1], [S2, v2])`
- **Ancestor detection:** If ALL counters of X ≤ Y → X is older, Y replaces X ✅
- **Conflict:** If NEITHER X ≤ Y nor Y ≤ X → concurrent siblings → **client must merge**
- ⚠️ Vectors can grow long → set a **threshold**, prune oldest pairs

### 5️⃣ Failure Detection — Gossip Protocol

- Each node maintains a **heartbeat list** for all nodes
- Periodically share lists with **random peers** (like rumor spreading)
- If a node's heartbeat is stale beyond threshold → **marked offline**
- Decentralized — no single point of failure, scales O(N log N)

### 6️⃣ Temporary Failures — Sloppy Quorum + Hinted Handoff

- If target node is down → write to a **healthy neighbor** instead
- Neighbor holds a **hint** (who should really have this data)
- When downed node recovers → neighbor **hands off the data** 🔄

### 7️⃣ Permanent Failures — Merkle Trees

- Hash tree: leaf = hash(data block), parent = hash(children)
- Compare roots of two replicas → same? All synced! ✅
- Different? Drill down to find **only the differing blocks**
- Syncing is **O(log N)** comparisons — not O(N)!

---

## Storage Engine (LSM-Tree)

### Write Path
```
Client → 1. Commit Log (WAL on disk - durability)
       → 2. MemTable (in-memory sorted - speed)
       → 3. SSTable (flush to disk when MemTable full - persistence)
```

### Read Path
```
Client → 1. Check MemTable (fastest!)
       → 2. Bloom Filter ("definitely NOT here" or "maybe here")
       → 3. Read from SSTable (disk)
```

> **Bloom Filter** = probabilistic "not here" check → avoids unnecessary disk reads

---

## Complete Architecture At-a-Glance

```
Client → Coordinator Node → N Replica Nodes
                              ↕ Gossip Protocol (failure detection)
                              ↕ Consistent Hash Ring (partitioning)

Inside Each Node:
  Commit Log → MemTable → SSTable
  Bloom Filter guides reads to correct SSTable
```

---

## 🧠 Mnemonics

- **7 Components:** "**C**ats **R**un **C**razily, **V**ery **G**racefully **S**eeking **M**ice" → Consistent hashing · Replication · Consistency (quorum) · Vector clocks · Gossip protocol · Sloppy quorum · Merkle trees
- **CAP:** P is mandatory → choose CP or AP
- **Quorum:** W + R > N = strong consistency
- **Write path:** "**D**iary → **S**ticky pad → **F**iling cabinet" → commit log → MemTable → SSTable
- **Read path:** MemTable → Bloom Filter → SSTable

---

> 📖 **Detailed notes** → [design_a_key_value_store.md](./design_a_key_value_store.md)
