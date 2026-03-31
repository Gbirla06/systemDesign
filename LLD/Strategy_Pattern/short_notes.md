# Strategy Pattern: Simple Summary

### 💡 What is it?
The **Strategy Pattern** is like having a **Swiss Army Knife**. Instead of a fixed tool, you have a handle (the Context) and you can swap the blades (the Strategies) depending on the task.

---

### 🧱 3 Main Parts
1.  **The Context (The Handle)**: The main class (e.g., `Duck`). It doesn't know *how* to fly; it just knows it has a "Fly Tool."
2.  **The Strategy (The Tool Interface)**: A common design for all tools (e.g., `FlyBehavior`).
3.  **The Concrete Strategies (The Blades)**: The actual tools (e.g., `FlyWithWings`, `FlyNoWay`, `FlyWithJet`).

---

### 🚀 Why use it?
-   **No More `if/else`**: You don't need a giant `if type == "Rubber": do_this` block.
-   **Swap at Runtime**: You can change a duck's flying style while the program is running (e.g., a power-up).
-   **Plug & Play**: Add a new flying style by just creating one new class. You don't have to touch any existing code.

---

### 🔑 Key Rule
> **Favor Composition Over Inheritance.**
> (A Duck **has a** FlyBehavior; it isn't just a "FlyingDuck".)


### IMP Points
1. Use the Strategy pattern when you want to use different variants of an algorithm within an object and be able to     switch from one algorithm to another during runtime.
2. Use the Strategy when you have a lot of similar classes that only differ in the way they execute some behavior.
3. Use the pattern to isolate the business logic of a class from the implementation details of algorithms that may not be as important in the context of that logic.
4. Use the pattern when your class has a massive conditional statement that switches between different variants of the same algorithm.


### Class Diagram
        +-------------------+
        |     Context       |
        +-------------------+
        | - strategy        |
        +-------------------+
        | + setStrategy()   |
        | + execute()       |
        +--------+----------+
                 |
                 v
        +-------------------+
        |   Strategy (I)    |  <-- Interface
        +-------------------+
        | + execute()       |
        +--------+----------+
                 |
     ----------------------------
     |            |             |
     v            v             v

+------------+ +------------+ +------------+
| StrategyA  | | StrategyB  | | StrategyC  |
+------------+ +------------+ +------------+
| execute()  | | execute()  | | execute()  |
+------------+ +------------+ +------------+
