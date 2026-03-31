'''
    This is the first version of the Duck class. 
'''

from abc import ABC, abstractmethod

class Duck:
        
    def quack(self):
        print(f"quack")
    
    def swim(self):
        print(f"swimming")

    def fly(self):
        print(f"flying")
    
    @abstractmethod
    def display(self):
        pass


class MallardDuck(Duck):

    def display(self):
        print(f"I'm a mallard duck")


class RedHeadDuck(Duck):

    def display(self):
        print(f"I'm a red head duck")


class RubberDuck(Duck):

    def display(self):
        print(f"I'm a rubber duck")

    def quack(self):
        print(f"I can't quack, I can squeak")

    def fly(self):
        print(f"I can't fly")
    



'''
    ### Issues with This Design:

    1. **Violation of Open/Closed Principle (OCP):**
       The `Duck` class is not closed for modification. If we need to change how "flying" works, we might have to touch the base class, which impacts all subclasses. Conversely, adding new behaviors forces us to modify the base class and potentially many subclasses.

    2. **Inheritance Overuse/Abuse:**
       By putting `fly()` and `quack()` in the base class, we are assuming *all* ducks fly and quack. When we encounter a `RubberDuck` or a `DecoyDuck` (which doesn't fly OR quack), we are forced to override these methods to "do nothing" or "change behavior." 
       - This results in **Code Duplication**: If we add a `WoodenDuck`, we'll have to copy-paste the "can't fly" logic from `RubberDuck`.

    3. **Maintenance Nightmare:**
       In a large system with hundreds of Duck subclasses, it becomes impossible to track which ducks should fly and which shouldn't. A developer might add a `CloudDuck` and forget to override `quack()`, leading to a duck that quacks when it should have whistled.

    4. **Runtime Flexibility:**
       Behavior is locked in at compile-time (via inheritance). We cannot change a duck's flying behavior at runtime (e.g., if a duck's wing is injured).

    5. **Liskov Substitution Principle (LSP) Risks:**
       While technically we are overriding, we are often "breaking" the expected behavior of the base class. If a client expects all `Duck` objects to `fly()`, but calls it on a `RubberDuck` only to get a "I can't fly" print message, it might break the logical flow of a simulation that expects actual movement.
'''