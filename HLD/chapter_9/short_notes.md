# 📝 Short Notes — Design a Web Crawler

---

## What Is It?
A bot that systematically traverses the internet (using **Breadth-First Search**), downloading HTML pages, extracting links, and putting new links into a queue to continue the cycle. Used for Search Engines, Archiving, and Web Mining.

---

## The Crawler Loop

| Component | Function |
|---|---|
| **Seed URLs** | Starting points (e.g., `cnn.com`, `wikipedia.org`). |
| **URL Frontier** | The complex queue that prioritizes URLs and spaces out requests. |
| **DNS Resolver** | **MUST CATCH THIS:** Async layer that converts URL to IP. Extremely slow bottleneck if not cached properly! |
| **HTML Fetcher** | Connects to the IP and downloads the HTML. *(Always checks `robots.txt` first!)* |
| **Content Seen?** | Deduplication check. Hashes the HTML (MD5/SHA-1) and checks if the checksum already exists. |
| **URL Extractor** | Parses HTML to pull all `<a href>` tags out. |
| **URL Seen?** | Fast deduplication check using a **Bloom Filter** to see if we've already parsed this exact link. |

---

## The URL Frontier (The Hard Part)

The URL Frontier solves the two biggest problems in crawling:

| Problem | How to solve it in the Frontier |
|---|---|
| **Priority** | A "Prioritizer" sorts URLs into Front-End queues based on PageRank, freshness, and importance. Apple > spam blog. |
| **Politeness** | A "Router" ensures all requests for a single host (e.g., `wikipedia.org`) go into *one single Back-End queue*. A dedicated worker processes that queue sequentially, pausing for 2 seconds between hits to prevent DDoSing the server. |

---

## The 3 Key Tricks for Interviews

1. **Traversal Strategy:** Explicitly state you are using **BFS (Breadth-First Search)** with a FIFO queue. **DFS** gets trapped down infinite rabbit holes ("spider traps").
2. **Bloom Filters:** You cannot query a 10-billion row database for every single extracted URL. A Bloom filter operating in memory provides massive `O(1)` speedups for URL Deduplication.
3. **Robots.txt:** Always mention that you will cache and respect `robots.txt` before fetching pages.

---

## 🧠 Mnemonics

- **The Core Loop:** "S F H C U" 🔁
   - **S**eed -> **F**rontier -> **H**TML Fetcher -> **C**ontent Dedup -> **U**RL Dedup.
- **The 3 P's of the Frontier:** 🅿️
   - **P**riority (Crawl Google before a blog)
   - **P**oliteness (Don't DDoS)
   - **P**erformance (Multi-threading)

---

> **📖 Detailed notes** → [design_a_web_crawler.md](./design_a_web_crawler.md)
