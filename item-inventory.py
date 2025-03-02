# Asteroid Frontier RPG
# Item and Inventory System

import pygame
import json
import os

class Item:
    def __init__(self, item_id, name, description, value, icon=None):
        self.id = item_id
        self.name = name
        self.description = description
        self.value = value  # Value in credits
        self.icon = icon or pygame.Surface((32, 32))  # Default placeholder icon
        self.stackable = False
        self.max_stack = 1
        self.quantity = 1
        self.weight = 1  # Weight in inventory units
        
        # Load icon if provided as string
        if isinstance(icon, str):
            try:
                self.icon = pygame.image.load(os.path.join('assets', 'icons', icon)).convert_alpha()
                self.icon = pygame.transform.scale(self.icon, (32, 32))
            except pygame.error:
                # If icon can't be loaded, create a colored square
                self.icon = pygame.Surface((32, 32))
                self.icon.fill((200, 200, 200))
    
    def use(self, player):
        """Use the item - to be overridden by subclasses"""
        return False
    
    def to_dict(self):
        """Convert item to dictionary for saving"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "value": self.value,
            "stackable": self.stackable,
            "quantity": self.quantity,
            "weight": self.weight,
            "type": self.__class__.__name__
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create an item from a dictionary"""
        item_type = data.pop("type", "Item")
        
        # Determine which class to create based on type
        if item_type == "Weapon":
            item = Weapon(**data)
        elif item_type == "Armor":
            item = Armor(**data)
        elif item_type == "Consumable":
            item = Consumable(**data)
        else:
            item = cls(**data)
        
        return item


class Weapon(Item):
    def __init__(self, item_id, name, description, value, icon=None, 
                 damage=5, range=1, durability=100):
        super().__init__(item_id, name, description, value, icon)
        self.type = "weapon"
        self.damage = damage
        self.range = range  # 1 for melee, >1 for ranged
        self.durability = durability
        self.max_durability = durability
        self.effects = {}  # Special effects like "stun", "burn", etc.
    
    def use(self, player):
        """Equip the weapon"""
        player.equip_item(self, "weapon")
        return True
    
    def repair(self, amount):
        """Repair the weapon's durability"""
        self.durability = min(self.max_durability, self.durability + amount)


class Armor(Item):
    def __init__(self, item_id, name, description, value, icon=None,
                 defense=5, durability=100):
        super().__init__(item_id, name, description, value, icon)
        self.type = "armor"
        self.defense = defense
        self.durability = durability
        self.max_durability = durability
        self.resistance = {}  # Resistances to different damage types
    
    def use(self, player):
        """Equip the armor"""
        player.equip_item(self, "armor")
        return True
    
    def repair(self, amount):
        """Repair the armor's durability"""
        self.durability = min(self.max_durability, self.durability + amount)


class Consumable(Item):
    def __init__(self, item_id, name, description, value, icon=None,
                 effect_type="heal", effect_value=10):
        super().__init__(item_id, name, description, value, icon)
        self.type = "consumable"
        self.effect_type = effect_type  # "heal", "energy", "buff", etc.
        self.effect_value = effect_value
        self.stackable = True
        self.max_stack = 10
    
    def use(self, player):
        """Use the consumable item"""
        if self.effect_type == "heal":
            player.health = min(player.max_health, player.health + self.effect_value)
        elif self.effect_type == "energy":
            # If you have an energy system
            pass
        elif self.effect_type == "buff":
            # Apply temporary stat buffs
            pass
        
        # Reduce quantity or remove item
        self.quantity -= 1
        return self.quantity <= 0  # Return True if item should be removed


class QuestItem(Item):
    def __init__(self, item_id, name, description, value, icon=None,
                 quest_id=None):
        super().__init__(item_id, name, description, value, icon)
        self.type = "quest_item"
        self.quest_id = quest_id
        self.stackable = True
        self.max_stack = 99
    
    def use(self, player):
        """Quest items typically can't be used directly"""
        return False


class Currency(Item):
    def __init__(self, item_id="credits", name="Credits", description="Standard currency", 
                 value=1, icon=None, amount=1):
        super().__init__(item_id, name, description, value, icon)
        self.type = "currency"
        self.stackable = True
        self.max_stack = 9999999
        self.quantity = amount
    
    def use(self, player):
        """Add to player's credits"""
        player.credits += self.quantity * self.value
        return True  # Remove item after adding credits


class Inventory:
    def __init__(self, capacity=20):
        self.items = []
        self.capacity = capacity
        self.weight = 0
        self.max_weight = 100  # Maximum weight the inventory can hold
    
    def add_item(self, item):
        """Add an item to the inventory"""
        # Check if inventory is full
        if len(self.items) >= self.capacity:
            return False
        
        # Check if item would exceed weight limit
        if self.weight + item.weight > self.max_weight:
            return False
        
        # If item is stackable, check if we already have it
        if item.stackable:
            for inv_item in self.items:
                if inv_item.id == item.id and inv_item.quantity < inv_item.max_stack:
                    # Calculate how many can be added to this stack
                    space_in_stack = inv_item.max_stack - inv_item.quantity
                    amount_to_add = min(space_in_stack, item.quantity)
                    
                    inv_item.quantity += amount_to_add
                    item.quantity -= amount_to_add
                    self.weight += item.weight * amount_to_add
                    
                    # If we've added all of the item, return success
                    if item.quantity <= 0:
                        return True
        
        # If we get here, either the item isn't stackable or we still have some left
        # Add as a new item in the inventory
        if item.quantity > 0:
            self.items.append(item)
            self.weight += item.weight * item.quantity
            return True
        
        return False
    
    def remove_item(self, index, quantity=1):
        """Remove an item from the inventory"""
        if 0 <= index < len(self.items):
            item = self.items[index]
            
            if item.stackable and item.quantity > quantity:
                item.quantity -= quantity
                self.weight -= item.weight * quantity
                return item.__class__(item.id, item.name, item.description, item.value, 
                                    item.icon, quantity=quantity)
            else:
                # Remove the entire item
                removed_item = self.items.pop(index)
                self.weight -= removed_item.weight * removed_item.quantity
                return removed_item
        
        return None
    
    def get_item(self, index):
        """Get an item without removing it"""
        if 0 <= index < len(self.items):
            return self.items[index]
        return None
    
    def has_item(self, item_id, quantity=1):
        """Check if the inventory has a specific item"""
        total_quantity = 0
        for item in self.items:
            if item.id == item_id:
                total_quantity += item.quantity
                if total_quantity >= quantity:
                    return True
        return False
    
    def use_item(self, index, player):
        """Use an item at the specified index"""
        if 0 <= index < len(self.items):
            item = self.items[index]
            should_remove = item.use(player)
            
            if should_remove:
                if item.stackable and item.quantity > 1:
                    item.quantity -= 1
                    self.weight -= item.weight
                else:
                    self.items.pop(index)
                    self.weight -= item.weight * item.quantity
            
            return True
        
        return False
    
    def sort(self, key="name"):
        """Sort inventory by the specified key"""
        if key == "name":
            self.items.sort(key=lambda x: x.name)
        elif key == "value":
            self.items.sort(key=lambda x: x.value, reverse=True)
        elif key == "type":
            self.items.sort(key=lambda x: x.type)
        elif key == "weight":
            self.items.sort(key=lambda x: x.weight)
    
    def clear(self):
        """Clear the inventory"""
        self.items = []
        self.weight = 0
    
    def to_dict(self):
        """Convert inventory to dictionary for saving"""
        return {
            "capacity": self.capacity,
            "max_weight": self.max_weight,
            "items": [item.to_dict() for item in self.items]
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create an inventory from a dictionary"""
        inventory = cls(data.get("capacity", 20))
        inventory.max_weight = data.get("max_weight", 100)
        
        for item_data in data.get("items", []):
            item = Item.from_dict(item_data)
            inventory.add_item(item)
        
        return inventory


class ItemFactory:
    @staticmethod
    def create_item(item_id, quantity=1):
        """Create an item from a predefined list based on ID"""
        # In a real game, these would probably be loaded from a database or file
        items = {
            "medkit": {
                "class": Consumable,
                "name": "Medkit",
                "description": "Restores 50 health points.",
                "value": 25,
                "effect_type": "heal",
                "effect_value": 50
            },
            "energy_pack": {
                "class": Consumable,
                "name": "Energy Pack",
                "description": "Restores 30 energy points.",
                "value": 20,
                "effect_type": "energy",
                "effect_value": 30
            },
            "space_pistol": {
                "class": Weapon,
                "name": "Space Pistol",
                "description": "Standard issue sidearm. Reliable but weak.",
                "value": 100,
                "damage": 15,
                "range": 5,
                "durability": 100
            },
            "mining_laser": {
                "class": Weapon,
                "name": "Mining Laser",
                "description": "Repurposed mining tool. High damage, short range.",
                "value": 250,
                "damage": 25,
                "range": 3,
                "durability": 80
            },
            "light_armor": {
                "class": Armor,
                "name": "Light Armor",
                "description": "Basic protection. Doesn't slow you down.",
                "value": 150,
                "defense": 10,
                "durability": 100
            },
            "ore_sample": {
                "class": QuestItem,
                "name": "Ore Sample",
                "description": "A sample of rare ore from the asteroid. Someone might want this.",
                "value": 50,
                "quest_id": "q002"
            },
            "credits": {
                "class": Currency,
                "name": "Credits",
                "description": "Standard currency used throughout the system.",
                "value": 1
            }
        }
        
        if item_id in items:
            item_info = items[item_id]
            item_class = item_info.pop("class")
            item = item_class(item_id=item_id, **item_info)
            
            if hasattr(item, "quantity"):
                item.quantity = quantity
            
            return item
        
        return None
    
    @staticmethod
    def load_items_from_json(filename):
        """Load item definitions from a JSON file"""
        with open(os.path.join('assets', 'items', filename), 'r') as file:
            data = json.load(file)
        
        # This would parse the JSON and add items to the factory's items dictionary
        # Not implemented here for brevity
        pass


# Example usage:
# inventory = Inventory(capacity=30)
# inventory.add_item(ItemFactory.create_item("medkit", 3))
# inventory.add_item(ItemFactory.create_item("space_pistol"))
# inventory.use_item(0, player)  # Use the medkit