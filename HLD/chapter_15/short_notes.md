# 📝 Short Notes — Design Google Drive

---

## What Is It?
A cloud file storage and sync service (Google Drive, Dropbox, OneDrive). Users upload files from any device and see changes synchronised seamlessly across all other devices. The four engineering pillars are: **Chunking, Deduplication, Delta Sync, and Conflict Resolution**.

---

## The 4 Pillars — "C-D-S-C" 🏛️

| Pillar | Concept | Benefit |
|---|---|---|
| **Chunking** | Split every file into fixed 4MB blocks. Identify each block by its **SHA-256 content hash**. | Enables the 3 pillars below |
| **Deduplication** | Before uploading, send fingerprints to the server. Upload ONLY blocks the server doesn't already have. | 10M users upload the same PDF → stored only **once** (2,500,000× saving!) |
| **Delta Sync** | On file edit, re-hash all local blocks. Upload ONLY the blocks with new hashes. | Change 1 paragraph in a 500MB file → upload only **4-8MB** instead of 500MB |
| **Conflict Resolution** | If two users edit the same offline file, preserve both versions as a "conflict copy." | No silent data loss |

---

## Upload Flow — The Correct Sequence

```
1. Client splits file → 4MB blocks → SHA-256 hash each block
2. Client → API: "Here are my block fingerprints"
3. API → Block Store: "Which of these already exist?"
4. API → Client: "You only need to upload blocks [X, Y, Z] — the rest exist!"
5. Client → S3 (pre-signed URL per block): PUT only missing blocks
6. Client → API: "Done uploading — here's the ordered list of all block fingerprints"
7. API → Metadata DB: Save file_version record (block_list = ordered fingerprint array)
8. API → Kafka: Publish CHANGE event
9. Kafka → Notification Service → WebSocket push to all other devices
```

---

## Sync Flow — How Other Devices get Updated

```
Device 2 (idle) → has open WebSocket to Notification Service
Server detects change → publishes to Kafka → Notification Service pushes lightweight event:
   { file_id: 987, new_version: 5 }

Device 2 receives push:
   GET /file/987/delta?from=4&to=5
   Response: { added_blocks: ["abc123"], removed_blocks: ["def456"] }
   Download only added_blocks from Block Store
   Reconstruct file locally using existing cached blocks + new blocks
```

---

## Conflict Resolution

| Scenario | Solution |
|---|---|
| **Regular files** (not live-collab) | Create a **conflict copy**. Notify both users. They merge manually. |
| **Google Docs** (live collaborative) | **Operational Transformation (OT)** — transforms concurrent edits mathematically so all changes merge without data loss. |

---

## Database Design (Key Tables)

```sql
-- file_nodes: unified tree (files + folders)
(node_id PK, parent_id, owner_id, name, node_type ENUM(FILE,FOLDER), is_deleted)

-- file_versions: immutable version log (block list per version)
(version_id PK, node_id, version_num, block_list JSON, created_at, created_by)

-- shares: access control
(node_id, grantee_id, permission ENUM(READ, WRITE, ADMIN))
```

**Soft Delete:** `is_deleted = TRUE` (user can restore from Trash for 30 days). A background GC job finds orphaned blocks (no active file_version pointing to them) and deletes from S3.

---

## Security — Envelope Encryption 🔐

```
                     ┌─ DEK (Data Encryption Key) ─┐
                     │   unique per block            │
4MB block  ──AES-256-GCM──► Encrypted block (stored in S3)
                     │
                     │  The DEK itself is encrypted  │
                     └─ by KEK (Key Encryption Key) ─┘
                            stored in AWS KMS

Key Rotation: Only re-encrypt DEKs with new KEK — NOT the petabytes of blocks!
```

---

## Advanced Concepts

| Concept | How |
|---|---|
| **Resumable uploads** | Track per-block upload progress. Network drop → resume from last successful block |
| **CDN for hot files** | Blocks are immutable (hash = content). No cache invalidation ever needed. CDN TTL = forever |
| **Kafka decoupling** | Upload → publishes event instantly → Sync Service consumes at own pace. 100K uploads don't crush Sync Service |
| **Quota tracking** | `UPDATE user_quotas SET used_bytes += {new_block_bytes}` on new block uploads |

---

## 🧠 Mnemonics

- **4 Pillars:** "**C-D-S-C**" → Chunk, Dedup, Sync (delta), Conflict-resolve
- **Block Lifecycle:** "**SHA → Store → List**"
  1. SHA: hash → fingerprint = identity
  2. Store: upload only if fingerprint is new
  3. List: file = ordered list of fingerprints in Metadata DB
- **Encryption:** "**DEK+KEK = Envelope**" — two-key system for easy rotation

---

> **📖 Detailed notes** → [design_google_drive.md](./design_google_drive.md)
>
> **🎉 This is the final HLD chapter from Alex Xu's System Design Interview Volume 1!**
