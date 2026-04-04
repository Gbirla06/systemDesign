# 📝 Short Notes — Design a Rate Limiter

---

## What Is It?
A **rate limiter** controls the rate of traffic a client can send. If requests exceed the threshold, excess calls are **blocked (HTTP 429)**. It's the bouncer at the club door.

---

## Why Do We Need It?

| Reason | Example |
|---|---|
| **Prevent DoS attacks** | Block malicious flooding |
| **Reduce cost** | Fewer requests = less server load |
| **Prevent server overload** | Protect backend from traffic spikes |

---

## Where to Put It?

| Location | Verdict |
|---|---|
| **Client-side** | ❌ Unreliable — easily forged |
| **Server-side** | ✅ Works, direct control |
| **API Gateway (Middleware)** | ⭐ Best — built-in with cloud providers |

---

## 5 Algorithms

| Algorithm | Core Idea | Burst? | Memory | Flaw |
|---|---|---|---|---|
| **Token Bucket** | Tokens refill at fixed rate; consume 1 per request | ✅ Yes | Low | Tuning bucket size + refill rate |
| **Leaking Bucket** | FIFO queue; constant outflow rate | ❌ No | Low | Old requests may starve new ones |
| **Fixed Window** | Counter per time window; resets at boundary | ⚠️ At edges | Very low | 💥 Boundary burst (2× traffic at window edges!) |
| **Sliding Window Log** | Store timestamp of every request; sliding check | ❌ Strict | ❌ High | Stores ALL timestamps — memory hungry |
| **Sliding Window Counter** | Weighted avg of current + previous window | ⚠️ Smooth | Low | Approximation (~99.997% accurate) |

> **Most popular:** Token Bucket (Amazon, Stripe) · Sliding Window Counter (Cloudflare)

---

## Key Architecture

```
Client → Load Balancer → Rate Limiter Middleware → API Server
                              ↕
                     🔴 Redis (Counters)
                     📋 Rules Config (YAML)
```

- **Redis** = in-memory counter storage (INCR + EXPIRE, sub-ms latency)
- **Rules** = configurable limits per endpoint/user/IP (stored in config files)

---

## HTTP Response Headers

| Header | Meaning |
|---|---|
| `X-Ratelimit-Remaining` | Requests left in current window |
| `X-Ratelimit-Limit` | Max requests allowed per window |
| `X-Ratelimit-Retry-After` | Seconds to wait (when throttled) |

> **HTTP 429** = "Too Many Requests"

---

## 2 Distributed Challenges

| Challenge | Problem | Solution |
|---|---|---|
| **Race Condition** | Two servers read same counter → both allow → over-limit | ✅ Redis **Lua scripts** (atomic read+check+write) |
| **Synchronization** | Multiple rate limiters with separate counters | ✅ **Centralized Redis cluster** (single source of truth) |

---

## Monitoring

- Track **allowed vs dropped** rate → tune if too strict/lenient
- Watch **Redis latency** → must stay sub-millisecond
- Monitor **false positives** → legitimate users shouldn't be blocked

---

## Rate-Limited Request Handling

| Option | When |
|---|---|
| **Drop + 429** | Default — most APIs |
| **Enqueue for later** | Important requests (payments, orders) |
| **Drop + Log** | Analytics / abuse detection |

---

## 🧠 Mnemonics

- **5 Algorithms:** "**T**ony **L**ikes **F**ish **S**alad **S**andwiches" → Token · Leaking · Fixed · Sliding Log · Sliding Counter
- **2 Challenges:** **R**ace → Lua scripts · **S**ync → Centralized Redis
- **3 Headers:** Remaining · Limit · Retry-After

---

> 📖 **Detailed notes** → [design_a_rate_limiter.md](./design_a_rate_limiter.md)
