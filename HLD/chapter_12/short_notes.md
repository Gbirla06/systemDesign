# 📝 Short Notes — Design a Chat System

---

## What Is It?
A real-time messaging platform (WhatsApp, Messenger, Slack) that instantly delivers messages between users while persisting history and showing online presence. The core challenge is: **how does the server push data to a client that didn't ask for it?**

---

## The 3 Approaches to Real-Time Delivery

| Approach | How It Works | Verdict |
|---|---|---|
| **Short Polling** | Client asks "any messages?" every 3 seconds | ❌ 99% requests are empty. Wastes bandwidth at scale. |
| **Long Polling** | Client holds request open until server has a message | ⚠️ Better, but TCP teardown + re-connection overhead per message |
| **WebSocket ⭐** | One single persistent TCP connection after handshake. Server pushes any time. | ✅ 2-byte frame overhead. Native bidirectional. The winner. |

---

## High-Level Architecture — Key Components

| Component | Role |
|---|---|
| **Chat Server (WebSocket Server)** | Maintains persistent connections with all online clients. Receives and routes messages. |
| **Kafka (Message Queue)** | Each user has a Kafka topic `user:bob`. Decouples sending server from receiving server. |
| **Zookeeper (Service Discovery)** | Routes new client connections to the least-loaded Chat Server. |
| **Presence Service + Redis** | 5-second heartbeat. Redis TTL auto-expires to OFFLINE if heartbeat stops. |
| **Notification Service** | If recipient is OFFLINE → fires APNs/FCM push instead. |
| **HBase/Cassandra (Message DB)** | Write-optimized LSM-tree DB. Primary key: `(channel_id, message_id)` |

---

## Message Routing Flow (Alice → Bob, 1-on-1)

```
1. Alice sends over WebSocket → Chat Server 1
2. Chat Server 1 assigns Snowflake message_id, saves to Message DB
3. Chat Server 1 publishes to Kafka topic "user:bob"
4a. Bob is ONLINE  → Chat Server 2 (subscribed to "user:bob") pushes to Bob's WebSocket
4b. Bob is OFFLINE → Notification Service fires APNs/FCM push
```

---

## Key Design Decisions

| Problem | Solution |
|---|---|
| **Message ordering (no collisions)** | **Snowflake IDs** (Chapter 7) — unique + time-sortable. Safer than timestamps. |
| **Silent connection drop (mobile)** | **Heartbeat** every 5s. Redis TTL 30s. If no heartbeat → auto-marked OFFLINE. |
| **Multi-device sync** | Each device stores `last_message_id_seen`. On login: fetch all messages `AFTER` that ID. |
| **Write-heavy message storage** | **Cassandra/HBase** (LSM-trees handle 2B writes/day; horizontal sharding native). |
| **Presence fan-out (500 friends)** | Only notify friends currently on Bob's contact list. Use a **subscribe/unsubscribe** model. |

---

## 🧠 Mnemonics

- **3 Levels of Real-Time:** "**Poll → Long → Socket**"
  - Polling = "Are we there yet?" 
  - Long Polling = "I'll wait here"  
  - WebSocket = "Let's just leave the line open" ✅

- **4 Services around Chat Server:** "**ZPNK**"
  - **Z**ookeeper (Discovery)
  - **P**resence (Heartbeat)
  - **N**otification (Offline push)
  - **K**afka (Message routing)

---

> **📖 Detailed notes** → [design_a_chat_system.md](./design_a_chat_system.md)
