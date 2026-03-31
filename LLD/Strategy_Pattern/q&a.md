## Strategy Pattern – Interview Notes

### Q1. What is Strategy Pattern in one line?

Strategy Pattern allows you to define a family of algorithms, encapsulate each one, and make them interchangeable at runtime.

---

### Q2. When should I use Strategy Pattern?

Use it when:

* You have multiple ways to perform a task
* You want to avoid large if-else or switch statements
* You need to change behavior at runtime
* You want to follow the Open/Closed Principle

---

### Q3. Why did inheritance fail here?

Inheritance fails because:

* It creates rigid class hierarchies
* Behavior cannot be changed at runtime
* It leads to class explosion as variations increase
* It reduces flexibility and maintainability

In short: inheritance is static, but the problem requires dynamic behavior.

---

### Q4. What problem does Strategy Pattern solve?

Strategy Pattern solves:
How to switch between different algorithms or behaviors at runtime without using messy conditional logic.

It provides:

* Cleaner code
* Runtime flexibility
* Easy extensibility

---

### Q5. What is "composition over inheritance"?

Composition over inheritance means building classes using smaller, reusable components instead of relying on class hierarchies.

Instead of:

* IS-A relationship (inheritance)

Use:

* HAS-A relationship (composition)

---

### Q6. How is composition used in Strategy Pattern?

In Strategy Pattern:

* The Context HAS-A Strategy
* The strategy is injected and can be changed dynamically

This makes behavior pluggable and flexible.

---

### Q7. Where have I seen this in my own work (backend / Vengage-style)?

You’ve likely used Strategy Pattern in:

1. Data Processing

   * CSV, JSON, API processors
   * Each processor behaves like a strategy

2. Retry Mechanisms

   * Exponential backoff
   * Fixed retry
   * No retry

3. Filtering / Sorting Logic

   * Dynamic filters applied at runtime

4. Pricing / Rules Engine

   * Discounts, tax rules, region-based logic

5. Notification Systems

   * Email, SMS, Slack services

---

### Final Summary (Interview Ready)

Strategy Pattern encapsulates interchangeable behaviors and allows switching them at runtime using composition instead of inheritance, making systems flexible, extensible, and maintainable.
