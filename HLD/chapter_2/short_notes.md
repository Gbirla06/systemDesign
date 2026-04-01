# 📝 Short Notes — Back-of-the-Envelope Estimation

---

## What Is It?
Rough calculations on a napkin to estimate **QPS, storage, bandwidth, cache** — not exact, just the right **order of magnitude** (GB vs TB? Hundreds vs Millions?).

---

## 1. Power of Two

| 2¹⁰ = 1 KB | 2²⁰ = 1 MB | 2³⁰ = 1 GB | 2⁴⁰ = 1 TB | 2⁵⁰ = 1 PB |
|---|---|---|---|---|
| ~1 Thousand | ~1 Million | ~1 Billion | ~1 Trillion | ~1 Quadrillion |

> **Trick:** Every +10 in power = ×1000 → KB → MB → GB → TB → PB

---

## 2. Latency Numbers (Speed Hierarchy)

| Operation | Time | Speed |
|---|---|---|
| L1 cache | 0.5 ns | ⚡⚡⚡⚡⚡ |
| L2 cache | 7 ns | ⚡⚡⚡⚡ |
| RAM | 100 ns | ⚡⚡⚡ |
| SSD read | ~150 μs | ⚡⚡ |
| Disk seek | 10 ms | ⚡ |
| Network (same DC) | 500 μs | ⚡⚡ |
| Cross-continent | 150 ms | 🐌 |

**6 Golden Rules:**
1. Memory is fast, disk is slow
2. Avoid disk seeks
3. Compression is cheap — compress before sending
4. Minimize cross-DC calls (150ms!)
5. Sequential reads >> random reads
6. RAM ≈ 100× faster than disk

---

## 3. Availability (Nines)

| % | Name | Downtime/Year |
|---|---|---|
| 99% | Two nines | 3.65 days |
| 99.9% | Three nines | 8.77 hours |
| 99.99% | Four nines | 52.6 min |
| 99.999% | Five nines | 5.26 min |

> **⚠️ Series components multiply:** 3 components at 99.9% each → 0.999³ = 99.7% overall

---

## 4. Key Numbers to Remember

| Fact | Value |
|---|---|
| Seconds in a day | 86,400 ≈ **10⁵** |
| Seconds in a year | ~31.5M ≈ **3 × 10⁷** |
| Tweet text size | ~300 bytes |
| Photo (JPEG) | ~2-5 MB |
| 1 min video (HD) | ~150 MB |
| Peak QPS | 2-5× average QPS |
| Read : Write ratio | Usually ~10:1 or higher |

---

## 5. Essential Formulas

```
QPS       = DAU × actions_per_user / 86,400
Peak QPS  = QPS × 2~5
Storage   = daily_data × 365 × years
Cache     = 20% × daily_data  (80/20 rule)
Bandwidth = QPS × avg_response_size
Servers   = Peak QPS / capacity_per_server
```

---

## 6. Estimation Process (5 Steps)

```
1. 📝 STATE assumptions (DAU, actions, data sizes)
2. 🔢 ROUND numbers (86,400 → 10⁵)
3. 📊 CALCULATE (QPS → Storage → Bandwidth → Cache)
4. ✅ SANITY CHECK (does GB vs TB make sense?)
5. 📢 LABEL UNITS (always write: 500 QPS, not just 500)
```

---

## 7. Quick Twitter Example

```
150M DAU × 2 tweets = 300M tweets/day
QPS = 300M / 100K ≈ 3,000 QPS | Peak ≈ 6,000
Text: 300M × 300B = 90 GB/day
Media (10%): 30M × 3MB = 90 TB/day  ← media dominates!
5 years: ~164 PB total
```

---

## Common Mistakes
- ❌ Being too precise — just get the order of magnitude right
- ❌ Forgetting units — always label QPS, GB, TB
- ❌ Ignoring peak traffic — systems must handle peaks
- ❌ Mixing bits & bytes — bandwidth uses **bits**, storage uses **bytes**
- ❌ Forgetting media — text is tiny, images/videos dominate storage

---

## 🧠 Mnemonics

- **Units:** **K**ing **M**ega **G**ave **T**en **P**ets (KB → MB → GB → TB → PB)
- **Speed:** **L**ucy's **C**at **R**eally **D**islikes **N**apping (L1 → L2 → RAM → Disk → Network)
- **Steps:** **S**tate → **R**ound → **C**alculate → **C**heck → **L**abel

---

> 📖 **Detailed notes** → [back_of_the_envelope_estimation.md](./back_of_the_envelope_estimation.md)
