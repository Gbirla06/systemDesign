# 📝 Short Notes — A Framework for System Design Interviews

---

## What Is It?
A **4-step repeatable framework** to tackle ANY system design interview question. It's a collaborative conversation, NOT an exam. There is **no single correct answer**.

---

## The 4 Steps

| Step | Time | Goal |
|---|---|---|
| **1. Understand & Scope** | 3-10 min | Ask questions, clarify requirements |
| **2. High-Level Design** | 10-15 min | Draw boxes & arrows, define APIs, get buy-in |
| **3. Deep Dive** | 10-25 min | Zoom into specific components, discuss trade-offs |
| **4. Wrap Up** | 3-5 min | Summarize, bottlenecks, improvements |

---

## Step 1 — Understand & Scope 🎯
- **NEVER** jump into a solution without asking questions (🚩 biggest red flag!)
- Ask about: **Features? Users? Scale (DAU)? Platforms? Constraints?**
- Write down requirements as you go

## Step 2 — High-Level Design 🏗️
- Draw key components (LB, servers, DB, cache, queue, CDN)
- Define API endpoints (`POST /feed`, `GET /feed`)
- Sketch data model (tables/collections)
- Walk through one use case end-to-end
- **Ask:** *"Does this look reasonable?"* → Get buy-in!

## Step 3 — Deep Dive 🔬
- Focus on what the **interviewer cares about** (follow their hints!)
- Discuss **trade-offs** (pros vs cons of each approach)
- Use **numbers** (QPS, storage, latency)
- Show depth: e.g., Push vs Pull vs Hybrid for feed generation

## Step 4 — Wrap Up 🎁
- Summarize your design in 2-3 sentences
- Point out **bottlenecks** & how you'd fix them
- Suggest **future improvements** (monitoring, analytics, rate limiting)
- Discuss **trade-offs** you made and why

---

## ✅ Top Do's
1. **Ask clarifying questions** — always
2. **Communicate** — think out loud
3. **Collaborate** — interviewer = teammate
4. **Start simple** — don't over-engineer
5. **Discuss trade-offs** — no design is perfect

## ❌ Top Don'ts
1. **Don't jump into solution** without understanding the problem
2. **Don't go silent** — interviewer can't read your mind
3. **Don't over-engineer** from the start
4. **Don't ignore hints** — if interviewer says "what about X?", discuss X
5. **Don't insist your design is perfect** — show self-awareness

---

## 🧰 Universal Building Blocks

| Component | When to Use |
|---|---|
| Load Balancer | Multiple servers |
| Cache (Redis) | Read-heavy workloads |
| Database (SQL) | Structured data, JOINs |
| Database (NoSQL) | Key-value, flexible schema |
| CDN | Static files globally |
| Message Queue | Async background tasks |
| Blob Storage (S3) | Images, videos, files |

---

## 🧠 Mnemonic

> **"Uncle Sam Digs Worms"** → **U**nderstand → **S**ketch → **D**eep dive → **W**rap up

---

> 📖 **Detailed notes** → [a_framework_for_system_design_interviews.md](./a_framework_for_system_design_interviews.md)
