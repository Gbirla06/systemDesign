# 📝 Short Notes — Design a Unique ID Generator in Distributed Systems

---

## What Is It?
A system to generate **globally unique, 64-bit, time-sortable, numeric IDs** across multiple servers — without coordination. Auto-increment fails at scale because it's a **single point of failure** and causes **duplicate IDs** across servers.

---

## 4 Approaches

| Approach | Core Idea | Verdict |
|---|---|---|
| **Multi-Master** | Each DB increments by k (total servers). Server 1: 1,4,7… Server 2: 2,5,8… | ❌ Not time-sortable, hard to scale |
| **UUID** | 128-bit random ID, no coordination needed | ❌ Too long (need 64-bit), not sortable, has hex |
| **Ticket Server** | Centralized DB with auto-increment hands out IDs (Flickr used this) | ❌ SPOF + bottleneck |
| **Snowflake ⭐** | 64-bit ID = timestamp + datacenter + machine + sequence | ✅ **The winner!** |

---

## Twitter Snowflake — The 64-Bit Structure

```
┌───────┬──────────────┬──────────┬──────────┬────────────┐
│ Sign  │  Timestamp   │Datacenter│ Machine  │  Sequence  │
│ 1 bit │   41 bits    │  5 bits  │  5 bits  │  12 bits   │
└───────┴──────────────┴──────────┴──────────┴────────────┘
```

| Section | Bits | Range | Purpose |
|---|---|---|---|
| **Sign** | 1 | Always 0 | Keeps ID positive |
| **Timestamp** | 41 | ~69.7 years (ms since custom epoch) | Time-sorting (MSB = auto-sorted!) |
| **Datacenter** | 5 | 32 datacenters | Location identifier |
| **Machine** | 5 | 32 machines/DC (1,024 total) | Server identifier |
| **Sequence** | 12 | 4,096 IDs/ms/machine | Per-ms counter, resets each ms |

---

## Key Numbers

| Metric | Value |
|---|---|
| **Per machine** | 4,096 × 1,000 = **4,096,000 IDs/sec** |
| **Total system** | 4,096,000 × 1,024 = **4.2 BILLION IDs/sec** |
| **Max lifespan** | 41-bit timestamp = **~69.7 years** from custom epoch |
| **Custom epoch** | Start from YOUR launch date (not Unix 1970) → maximize lifespan |

---

## ID Composition (Code)

```
ID = (timestamp << 22) | (datacenterId << 17) | (machineId << 12) | sequence
```

- Timestamp shifted left by **22** (5+5+12)
- No network calls — pure local bit math → **< 1 microsecond** ⚡

---

## 2 Edge Cases

| Edge Case | Problem | Solution |
|---|---|---|
| **Sequence overflow** | 4,096 IDs exhausted in 1ms | **Wait** for next millisecond |
| **Clock backward** | NTP adjusts clock back → duplicate/unsorted IDs | **Reject** ID generation + alert. Use NTP "slew" mode |

---

## Tuning Bit Allocation

| Need | Adjust |
|---|---|
| Longer lifespan | ↑ timestamp bits (42 bits = ~139 years) |
| Higher concurrency | ↑ sequence bits (16 bits = 65,536/ms) |
| More machines | ↑ machine bits, ↓ datacenter bits |

> Total must always = **64 bits**

---

## 🧠 Mnemonics

- **4 Approaches:** "**M**y **U**ncle **T**exts **S**lowly" → Multi-master · UUID · Ticket Server · Snowflake
- **Snowflake layout:** "**S**ome **T**iny **D**ogs **M**ake **S**ounds" → Sign(1) · Timestamp(41) · Datacenter(5) · Machine(5) · Sequence(12)
- **Key formula:** 1 + 41 + 5 + 5 + 12 = **64 bits**

---

> 📖 **Detailed notes** → [design_a_unique_id_generator_in_distributed_systems.md](./design_a_unique_id_generator_in_distributed_systems.md)
