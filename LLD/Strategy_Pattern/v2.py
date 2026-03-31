# This is the second version of the Duck class.


from abc import ABC, abstractmethod

# Flyable interface
class Flyable(ABC):
    @abstractmethod
    def fly(self):
        pass

# Quackable interface
class Quackable(ABC):
    @abstractmethod
    def quack(self):
        pass

# FlyWithWings class Concrete implementation of Flyable interface
class FlyWithWings(Flyable):
    
    def fly(self):
        print(f"I'm flying with wings")

# FlyNoWay class Concrete implementation of Flyable interface
class FlyNoWay(Flyable):
    
    def fly(self):
        print(f"I can't fly")

# Quack class Concrete implementation of Quackable interface
class Quack(Quackable):
    
    def quack(self):
        print(f"I'm quacking")

# Squeak class Concrete implementation of Quackable interface
class Squeak(Quackable):
    
    def quack(self):
        print(f"I'm squeaking")

# MuteQuack class Concrete implementation of Quackable interface
class MuteQuack(Quackable):
    
    def quack(self):
        print(f"I can't quack")



# Duck class
class Duck:
    
    def __init__(self, flyable: Flyable, quackable: Quackable):
        self.flyable = flyable
        self.quackable = quackable
    
    def perform_fly(self):
        self.flyable.fly()
    
    def perform_quack(self):
        self.quackable.quack()


# MallardDuck class
class MallardDuck(Duck):
    
    def __init__(self):
        super().__init__(FlyWithWings(), Quack())
    
    def display(self):
        print(f"I'm a mallard duck")


# RedHeadDuck class
class RedHeadDuck(Duck):
    
    def __init__(self):
        super().__init__(FlyWithWings(), Quack())
    
    def display(self):
        print(f"I'm a red head duck")


# RubberDuck class
class RubberDuck(Duck):
    
    def __init__(self):
        super().__init__(FlyNoWay(), Squeak())
    
    def display(self):
        print(f"I'm a rubber duck")


# DecoyDuck class
class DecoyDuck(Duck):
    
    def __init__(self):
        super().__init__(FlyNoWay(), MuteQuack())
    
    def display(self):
        print(f"I'm a decoy duck")


# Client code
if __name__ == "__main__":
    
    mallard_duck = MallardDuck()
    red_head_duck = RedHeadDuck()
    rubber_duck = RubberDuck()
    decoy_duck = DecoyDuck()

    mallard_duck.display()
    mallard_duck.perform_fly()
    mallard_duck.perform_quack()

    red_head_duck.display()
    red_head_duck.perform_fly()
    red_head_duck.perform_quack()

    rubber_duck.display()
    rubber_duck.perform_fly()
    rubber_duck.perform_quack()

    decoy_duck.display()
    decoy_duck.perform_fly()
    decoy_duck.perform_quack()

'''
    ### How the Strategy Pattern Solves the Issues:

    1. **Encapsulation of Behavior:**
       Instead of hardcoding "how to fly" or "how to quack" inside the Duck class, we pulled these behaviors into their own set of classes (the "Strategy" classes).

    2. **Composition over Inheritance:**
       Instead of inheriting behavior, `Duck` now "has a" `Flyable` and "has a" `Quackable`. This is a classic example of **Composition**.
       - This allows different types of ducks to share the same behavior object (e.g., `RubberDuck` and `DecoyDuck` both use `FlyNoWay`) without duplicating code.

    3. **Open/Closed Principle (OCP) in Action:**
       The system is now **Open for Extension**: To add a new flying behavior (like `FlyWithRocketPower`), we just create a new class implementing `Flyable`.
       The system is **Closed for Modification**: We don't have to touch the `Duck` class or any existing subclasses/strategies to add this new behavior.

    4. **Runtime Flexibility (Dynamic Behavior):**
       Because behaviors are stored in instance variables, we could add methods like `set_fly_behavior(new_fly_strategy)` to change a duck's behavior on the fly.
         Example: `mallard.set_fly_behavior(FlyNoWay())` if the duck gets injured.

    5. **Clean Interfaces:**
       Subclasses like `DecoyDuck` no longer have to implement or override `fly()` and `quack()` with "do nothing" code; they simply choose the `FlyNoWay` and `MuteQuack` strategies upon initialization.
'''