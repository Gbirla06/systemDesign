# 📝 Short Notes — Design a News Feed System

---

## What Is It?
A system that aggregates posts from users you follow and surfaces them to you (Facebook Timeline, Instagram Feed, Twitter Home). Two core operations: **Feed Publishing** (write) and **News Feed Building** (read).

---

## The Core Tradeoff: The Fanout Problem

"**Fanout**" = the act of distributing one user's post to all their followers' feeds.

| Approach | When Work is Done | Pros | Cons |
|---|---|---|---|
| **Fanout on Read (Pull)** | At read time — collect posts from all followees | Fast writes, always fresh | Massively slow/expensive reads (500 queries per open) |
| **Fanout on Write (Push)** | At write time — push to all followers' caches | Blazing fast reads (1 Redis lookup) | **Celebrity Problem:** 100M followers → 100M cache writes per post |
| **Hybrid ⭐ (Winner)** | Normal users → Write. Celebrities → Read | Best of both worlds | Slightly more complex routing logic |

---

## Hybrid Model — The Key Decision Rule
> **If follower count ≤ 10,000:** Fanout on Write (pre-push to followers' feed caches).
>
> **If follower count > 10,000 (celebrity):** Skip fanout. At read time, supplement the user's pre-built feed with a live query for that celebrity's latest post.

---

## Cache Architecture (3 Layers)

```
Feed Cache   → Redis Sorted Set: "feed:bob" → [post_id_1, post_id_2, ...]
Post Cache   → Redis Hash: "post:1234" → {text, media_url, author_id, timestamp}
User Cache   → Redis Hash: "user:567" → {name, avatar_url}
```

> **Why store only post IDs in the Feed Cache, not full content?**
> Because 5,000 followers × full post content = enormous duplication. One shared Post Cache holds the content; feeds just store pointers (post IDs).

---

## Storage Choices

| Data | Storage |
|---|---|
| User, Follow Relationships, Post metadata | **MySQL** |
| Posts at massive scale | **Cassandra** (sharded by user_id) |
| Images, Videos | **CDN + S3 Object Storage** |
| Feed Caches, Post Caches | **Redis** |

---

## Advanced: Hot Key Problem
When Ronaldo posts, millions of people hit the **same Redis key** (`post:ronaldo_latest`).
- **Fix 1:** Replicate the hot post across multiple Redis nodes (consistent hashing).
- **Fix 2:** App server in-process cache for top celebrity posts (absorbs the burst in memory).

---

## 🧠 Mnemonics

- **The 3 Fanout Models:** "Read, Write, Hybrid" → Pull, Push, Hybrid 🔀
- **Cache Level Order:** "**Feed → Post → User**" (top-down, from IDs to content to author)

---

> **📖 Detailed notes** → [design_a_news_feed_system.md](./design_a_news_feed_system.md)
