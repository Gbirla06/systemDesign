# 📝 Short Notes — Design a URL Shortener

---

## What Is It?
A service that converts extremely long URLs into concise, safe 7-character aliases (e.g., `tinyurl.com/aBc123X`). It is an extremely **read-heavy** system designed to prioritize fast redirects.

---

## The Core Concept

| Step | Mechanism |
|---|---|
| **1. The API** | Two main endpoints: `POST /shorten` and `GET /{short_url}`. |
| **2. Redirect Code** | Returns `HTTP 301` or `HTTP 302` with the `Location` header containing the original long URL. |
| **3. The Algorithm** | Assigns a sequential **Unique ID number** to the request, then converts that integer to a **Base-62 String**. |
| **4. Fast Retrieval** | Hits a **Redis Cache** first. If missing, it queries the sharded database. |

---

## 301 vs. 302 Redirect (Crucial Interview Detail!)

| Status Code | Meaning | Who Caches It? | Best Used For: |
|---|---|---|---|
| **301 Permanent** | "URL moved forever." | **Browser caches it.** | When you want to save your servers from extreme repetitive loads. |
| **302 Found** | "URL moved temporarily." | **Browser does NOT cache.** | When you care deeply about analytics (tracking every single click). |

---

## Base-62 Conversion vs. Hash + Collision

To get our 7-character string (which allows for `62^7 = 3.5 Trillion` links), there are two approaches:

| Approach | How it works | Verdict |
|---|---|---|
| **Hash + Collision** | Run `MD5(url)` -> truncate first 7 characters. Check DB if it exists. If it does, append random string and try again. | ❌ BAD at scale. Every collision requires expensive database trips. |
| **Base-62 ID ⭐** | Generate a unique incrementing integer ID (see chapter 7). Convert that integer mathematically into a Base-62 string. | ✅ PERFECT. Zero collisions, lighting fast `O(1)` generation. |

> **Security Note:** If you use predictable sequential IDs (like `ID 1 = a`, `ID 2 = b`), hackers can scrape all your links. Always mention shuffling the Base-62 alphabet or encrypting the ID!

---

## Scaling the System

1. **Read-Heavy Architecture:** Caching is mandatory. Put **Redis or Memcached** in front of the database with an **LRU (Least Recently Used)** eviction policy.
2. **Database Sharding:** Instead of one massive DB for 12 Billion links, split the data across databases using Consistent Hashing (see chapter 5) based on the short URL.
3. **Purging Expired Links:** Do not use active scheduled scans—it kills the database. Use **Lazy Cleanup**: delete an expired link only when a user clicks on it, paired with low-priority background sweeps at 3:00 AM.

---

## 🧠 Mnemonics

- **The system design steps:** "B.A.B.C" 👶
   - **B**ase-62 Converter (Core algorithm)
   - **A**PI (POST shorten, GET redirect)
   - **B**ack-of-the-envelope (1.2 TB storage, read-heavy)
   - **C**ache (Redis + LRU eviction for read speeds)

- **301 vs 302:** "Permanent vs Ping" 🏓
   - 301 = Permanent. Browser caches and goes straight there.
   - 302 = Ping. Browser pings your server first, allowing you to track analytics.

---

> **📖 Detailed notes** → [design_a_url_shortener.md](./design_a_url_shortener.md)
