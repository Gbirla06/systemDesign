# 📝 Short Notes — Design Consistent Hashing

---

## What Is It?
A mapping technique that distributes data evenly among servers. Unlike traditional `% N` hashing, when a server is added or removed, only a very small fraction of data (`k/n` keys) needs to be moved. It solves the massive rehashing problem in horizontal scaling.

---

## The Core Concept

| Step | Mechanism |
|---|---|
| **1. The Hash Ring** | Both servers and data keys are hashed (e.g., using SHA-1) onto a circular ring (`0` to `2^160 - 1`). |
| **2. Finding a Server** | A key maps to the first server found by walking **clockwise** on the ring. |
| **3. Adding a Server** | Only keys located between the new server and the counter-clockwise preceding server move to the new server. |
| **4. Removing a Server** | Only the keys owned by the crashed server move clockwise to the next available server. |

---

## Two Major Flaws (Without Virtual Nodes)

| Flaw | Description |
|---|---|
| **Uneven Partitions** | Servers placed randomly on the ring create vastly unequal gaps between each other (some servers get huge chunks of the ring, others tiny ones). |
| **Data Hotspots** | Real-world data is non-uniform (e.g., "Celebrity Problem"). A cluster of heavily-accessed keys might fall into a single server's partition, crushing it. |

---

## The Solution: Virtual Nodes (V-Nodes)

**Concept:** Instead of hashing a physical server onto the ring once, hash it **multiple times** (`s0_1`, `s0_2`, `s0_3`...).

| Benefit | How it works |
|---|---|
| **Balanced Distribution** | Many random, small partitions distribute the load fairly across all physical machines safely. |
| **Resilience** | If a physical server dies, its load is scattered evenly across all remaining servers (instead of crushing just one neighbor). |
| **Weighted Scaling** | Assign more virtual nodes to powerful servers, and fewer virtual nodes to weaker servers. |

> **Pro Tip:** In production, systems run about ~100 to 200 virtual nodes per server to keep variance under 5-10%.

---

## Code Implementation (Lookup)

```
1. Hash all virtual nodes and store them in an array.
2. Sort the array.
3. Hash the key. Use Binary Search O(log(V)) to find the first node hash >= key hash.
4. Wrap around directly to index 0 if the key hash is greater than all nodes.
```

---

## 🚀 Advanced Production Nuances
- **Hash Algorithm:** Don't use SHA-1/MD5 in production. Use **MurmurHash** or **CityHash** for vastly faster, non-cryptographic uniform distribution.
- **Data Replication:** When replicating factor `N=3`, walk clockwise to drop copies into the first 3 *distinct physical servers* (ignoring duplicate virtual nodes).
- **Cascading Failures:** Without V-Nodes, a crashed server sends 100% of its massive load to one neighbor, crushing it like dominos. V-nodes safely spray a dead server's load evenly across the *entire* remaining cluster.

---

## 🏛️ Real-World Users
- **Amazon DynamoDB** (Data partitioning)
- **Apache Cassandra** (Cluster data routing)
- **Discord** (Message routing)
- **Akamai CDN** (Original inventors for caching)

---

## 🧠 Mnemonics

- **Core Idea:** "Clockwise Pizzeria" — if a pizza shop closes, customers walk clockwise to the very next open shop.
- **Flaws & Fixes:** "Clone the Waiters" — don't have just a few waiters standing around; clone them and stand them everywhere to handle the rush (Virtual Nodes).

---

> 📖 **Detailed notes** → [design_consistent_hashing.md](./design_consistent_hashing.md)
