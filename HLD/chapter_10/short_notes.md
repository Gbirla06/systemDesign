# 📝 Short Notes — Design a Notification System

---

## What Is It?
A centralized routing engine that accepts triggers from microservices, queries user contact info/settings, formats messages, and pushes them securely to external third-party delivery providers (Apple, Firebase, Twilio, Sendgrid) at massive scale.

---

## The 4 Third-Party Providers

You do not build the final delivery mechanism. You rely on:
| Notification Type | Third-Party Provider | Needed from DB |
|---|---|---|
| **iOS Push** | APNs (Apple Push Notification service) | `Device Token` |
| **Android Push** | FCM (Firebase Cloud Messaging) | `Device Token` |
| **SMS** | Twilio, Nexmo | `Phone Number` |
| **Email** | Sendgrid, Mailchimp | `Email Address` |

---

## The Architecture (Decoupling is Key!)

1. **Microservices (Billing/Shipping)** send a raw trigger/user_id to the Notification Server.
2. **Notification Server** fetches the device token, checks if the user opted-out, applies formatting templates, and pushes to a queue.
3. **Message Queues (Kafka/RabbitMQ)** act as shock absorbers. **CRITICAL:** Use a *separate* queue for each provider (iOS, Android, SMS, Email) to isolate failures.
4. **Workers** pull messages from the queues and call the 3rd-party APIs.

---

## Reliability & Scale (Deep Dive Topics)

| Problem | Solution |
|---|---|
| **Data Loss (Worker crashes)** | Use a **Notification Log DB**. Mark messages as `PENDING`, update to `SENT` only after receiving a `200 OK` from Twilio/APNs. Background sweeps re-queue stale pending items. |
| **3rd-Party Outage / Rate Limits** | Implement **Exponential Backoff** retries. Push failed messages into a separate retry queue to avoid hammering the recovering API. |
| **Spamming Users** | Apply **Receiver Rate Limiting** (e.g., max 5 pushes per hour). Drop or batch the rest. Always check DB **Opt-Out** settings before pushing to Kafka. |
| **Code Duplication** | Use **Templates**. Services send raw variables `{user: "John", status: "Shipped"}`, the server applies the localized UI template. |

> **Warning:** You can realistically only guarantee **At-Least-Once** delivery. Because network acks can be dropped by mobile carriers, users may rarely get the same notification twice. Exactly-once is theoretically impossible here.

---

## 🧠 Mnemonics

- **The FedEx Carriers:** 🚚 APNs, FCM, Twilio, Sendgrid.
- **The 3 R's:** 🔴
  - **R**etry (Exponential backoff)
  - **R**eliability (Log DB preventing loss)
  - **R**ate Limiting (Protecting the user)

---

> **📖 Detailed notes** → [design_a_notification_system.md](./design_a_notification_system.md)
