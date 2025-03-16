# Asteroid Frontier RPG
# Character System

import pygame
import json
import random

class Character:
    def __init__(self, name, sprite_sheet=None, x=0, y=0):
        self.name = name
        self.x = x
        self.y = y
        self.level = 1
        self.health = 100
        self.max_health = 100
        self.credits = 0
        
        # Equipment slots
        self.equipment = {
            "weapon": None,
            "armor": None,
            "accessory": None
        }
        
        # Basic stats
        self.stats = {
            "strength": 5,      # Physical damage
            "intelligence": 5,  # Tech/hacking ability
            "charm": 5,         # Dialogue options and prices
            "endurance": 5,     # Health and resistance
            "agility": 5        # Movement speed and evasion
        }
        
        # Skills (could be expanded greatly)
        self.skills = {
            "piloting": 0,       # Ship navigation
            "engineering": 0,    # Repair and crafting
            "combat": 0,         # Fighting effectiveness
            "negotiation": 0,    # Dialogue options
            "hacking": 0         # Accessing secure systems
        }
        
        # Inventory
        self.inventory = []
        self.inventory_capacity = 20
        
        # Sprite animation
        self.sprite_sheet = sprite_sheet
        self.animation_frames = {}
        self.animation_state = "idle_down"  # Default state
        self.animation_frame = 0
        self.animation_speed = 0.1
        self.animation_timer = 0
        
        # If a sprite sheet is provided, load animations
        if sprite_sheet:
            self.load_animations()
        else:
            # Create a placeholder sprite
            self.image = pygame.Surface((32, 32))
            self.image.fill((0, 0, 255))  # Blue rectangle
            self.rect = self.image.get_rect()
            self.rect.x = x
            self.rect.y = y
    
    def load_animations(self):
        """Load animation frames from sprite sheet"""
        # This would need to be customized based on your sprite sheet layout
        # For now, we'll just set up a structure for animations
        self.animation_frames = {
            "idle_down": [],
            "idle_up": [],
            "idle_left": [],
            "idle_right": [],
            "walk_down": [],
            "walk_up": [],
            "walk_left": [],
            "walk_right": []
        }
        
        # In a real implementation, you'd slice your sprite sheet here
        # For now, we'll use placeholder surfaces
        for state in self.animation_frames:
            # Create 4 frames for each animation state
            for i in range(4):
                frame = pygame.Surface((32, 32))
                if "down" in state:
                    frame.fill((0, 0, 255))  # Blue for down
                elif "up" in state:
                    frame.fill((0, 255, 0))  # Green for up
                elif "left" in state:
                    frame.fill((255, 0, 0))  # Red for left
                elif "right" in state:
                    frame.fill((255, 255, 0))  # Yellow for right
                
                # Add slight variation to show animation
                variation = pygame.Surface((8, 8))
                variation.fill((255, 255, 255))
                frame.blit(variation, (i*8, i*8))
                
                self.animation_frames[state].append(frame)
        
        # Set initial image
        self.image = self.animation_frames["idle_down"][0]
        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y
    
    def update_animation(self, dt, movement_direction=None):
        """Update character animation based on movement"""
        if not self.animation_frames:
            return
            
        # Update animation state based on movement
        if movement_direction:
            if movement_direction == "down":
                self.animation_state = "walk_down"
            elif movement_direction == "up":
                self.animation_state = "walk_up"
            elif movement_direction == "left":
                self.animation_state = "walk_left"
            elif movement_direction == "right":
                self.animation_state = "walk_right"
        else:
            # If not moving, use idle animation matching last direction
            if "walk_down" in self.animation_state:
                self.animation_state = "idle_down"
            elif "walk_up" in self.animation_state:
                self.animation_state = "idle_up"
            elif "walk_left" in self.animation_state:
                self.animation_state = "idle_left"
            elif "walk_right" in self.animation_state:
                self.animation_state = "idle_right"
        
        # Update animation timer
        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            self.animation_frame = (self.animation_frame + 1) % len(self.animation_frames[self.animation_state])
            self.image = self.animation_frames[self.animation_state][self.animation_frame]
    
    def gain_experience(self, amount):
        """Gain experience and possibly level up"""
        # Simple level up calculation - could be made more sophisticated
        experience_needed = self.level * 100
        if amount >= experience_needed:
            self.level_up()
    
    def level_up(self):
        """Increase character level and stats"""
        self.level += 1
        
        # Increase max health
        old_max_health = self.max_health
        self.max_health = 100 + (self.level - 1) * 20
        self.health += (self.max_health - old_max_health)
        
        # Increase stats (random for now, could be player choice)
        for stat in self.stats:
            self.stats[stat] += random.randint(1, 3)
    
    def add_to_inventory(self, item):
        """Add an item to inventory if space available"""
        if len(self.inventory) < self.inventory_capacity:
            self.inventory.append(item)
            return True
        return False
    
    def remove_from_inventory(self, item_index):
        """Remove an item from inventory by index"""
        if 0 <= item_index < len(self.inventory):
            return self.inventory.pop(item_index)
        return None
    
    def equip_item(self, item_index):
        """Equip an item from inventory"""
        if 0 <= item_index < len(self.inventory):
            item = self.inventory[item_index]
            if item.type in self.equipment:
                # Unequip current item if any
                if self.equipment[item.type]:
                    self.inventory.append(self.equipment[item.type])
                
                # Equip new item
                self.equipment[item.type] = item
                self.inventory.pop(item_index)
                
                # Apply stat changes
                # This would depend on your item implementation
                return True
        return False
    
    def unequip_item(self, slot):
        """Unequip an item from a specific slot"""
        if slot in self.equipment and self.equipment[slot]:
            if len(self.inventory) < self.inventory_capacity:
                self.inventory.append(self.equipment[slot])
                self.equipment[slot] = None
                # Remove stat bonuses
                return True
        return False
    
    def save_character(self, filename):
        """Save character data to a JSON file"""
        character_data = {
            "name": self.name,
            "level": self.level,
            "health": self.health,
            "max_health": self.max_health,
            "credits": self.credits,
            "stats": self.stats,
            "skills": self.skills,
            "equipment": {slot: (item.to_dict() if item else None) for slot, item in self.equipment.items()},
            "inventory": [item.to_dict() for item in self.inventory]
        }
        
        with open(filename, 'w') as f:
            json.dump(character_data, f, indent=4)
    
    @classmethod
    def load_character(cls, filename, sprite_sheet=None):
        """Load character data from a JSON file"""
        with open(filename, 'r') as f:
            data = json.load(f)
        
        character = cls(data["name"], sprite_sheet)
        character.level = data["level"]
        character.health = data["health"]
        character.max_health = data["max_health"]
        character.credits = data["credits"]
        character.stats = data["stats"]
        character.skills = data["skills"]
        
        # Load equipment and inventory
        # This would need Item class implementation
        # character.equipment = {slot: (Item.from_dict(item_data) if item_data else None) 
        #                        for slot, item_data in data["equipment"].items()}
        # character.inventory = [Item.from_dict(item_data) for item_data in data["inventory"]]
        
        return character


class Player(Character, pygame.sprite.Sprite):
    def __init__(self, name, sprite_sheet=None, x=0, y=0):
        Character.__init__(self, name, sprite_sheet, x, y)
        pygame.sprite.Sprite.__init__(self)
        
        # Player-specific attributes
        self.speed = 5
        self.last_direction = "down"
        self.quests = []
        self.credits = 100  # Start with 100 credits as a simple numeric property

        # Create a central inventory system
        from item_inventory import Inventory
        self.inventory = Inventory(capacity=30)
    
        # Start with some basic items
        from item_inventory import Weapon, Armor, Consumable, QuestItem, ItemFactory
        #self.inventory.add_item(ItemFactory.create_item("space_pistol"))
        #self.inventory.add_item(ItemFactory.create_item("light_armor"))
        #self.inventory.add_item(ItemFactory.create_item("Medkit"))
        #self.inventory.add_item(ItemFactory.create_item("ore_sample"))

        # Character progression
        self.level = 1
        self.experience = 0
        self.experience_to_level = 100  # First level threshold
        self.skill_points = 0
    
        # Skills
        self.skills = {
            "piloting": 1,       # Ship navigation
            "engineering": 1,    # Repair and crafting
            "combat": 1,         # Fighting effectiveness
            "negotiation": 1,    # Dialogue options
            "hacking": 1         # Accessing secure systems
    }
        
        # Reputation storage
        self.reputation = {
            "earth": 0,
            "mars": 0,
            "pallas": 0,
            "psyche_township": 0
        }

        # Property for easy access to credits
        @property
        def credits(self):
            for item in self.inventory.items:
                if item.id == "credits":
                    return item.quantity
            return 0

        # Method to add credits
        def add_credits(self, amount):
            for item in self.inventory.items:
                if item.id == "credits":
                    item.quantity += amount
                    return True
        
            # If no credits item found, create one
            from item_inventory import Currency
            self.inventory.add_item(Currency(amount=amount))
            return True
    
    def update(self, keys, dt, walls=None):
        """Update player position based on input, 3/8/25"""
        dx, dy = 0, 0
        movement_direction = None
    
        # Handle movement input
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -self.speed
            movement_direction = "left"
            self.last_direction = "left"
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = self.speed
            movement_direction = "right"
            self.last_direction = "right"
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -self.speed
            movement_direction = "up"
            self.last_direction = "up"
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = self.speed
            movement_direction = "down"
            self.last_direction = "down"
    
        # Move the player
        if dx != 0 or dy != 0:
            # Try moving horizontally
            old_x = self.rect.x
            self.rect.x += dx
            if walls:
                # Check each wall for collision
                wall_hits = pygame.sprite.spritecollide(self, walls, False)
                if wall_hits:
                    # Revert to previous position
                    if dx > 0:  # Moving right
                        self.rect.right = min(wall.rect.left for wall in wall_hits)
                    else:  # Moving left
                        self.rect.left = max(wall.rect.right for wall in wall_hits)
        
            # Try moving vertically
            old_y = self.rect.y
            self.rect.y += dy
            if walls:
                # Check each wall for collision
                wall_hits = pygame.sprite.spritecollide(self, walls, False)
                if wall_hits:
                    # Revert to previous position
                    if dy > 0:  # Moving down
                        self.rect.bottom = min(wall.rect.top for wall in wall_hits)
                    else:  # Moving up
                        self.rect.top = max(wall.rect.bottom for wall in wall_hits)
        
            # Update animation
            if hasattr(self, 'update_animation'):
                self.update_animation(dt, movement_direction)
            
        # Keep player within map boundaries
        # These checks would use the current level size if available
        if hasattr(self, 'current_level') and self.current_level:
            if self.rect.left < 0:
                self.rect.left = 0
            if self.rect.right > self.current_level.get("width", 2000):
                self.rect.right = self.current_level.get("width", 2000)
            if self.rect.top < 0:
                self.rect.top = 0
            if self.rect.bottom > self.current_level.get("height", 2000):
                self.rect.bottom = self.current_level.get("height", 2000)
    
    def interact(self, npcs):
        """Check for interaction with NPCs"""
        for npc in npcs:
            if pygame.sprite.collide_rect(self, npc):
                return npc
        return None
    
    def gain_experience(self, amount):
        """Award experience to the player and handle level ups, 3/16/25"""
        self.experience += amount
        print(f"Gained {amount} experience. Total: {self.experience}")
    
        # Check for level up
        while self.experience >= self.experience_to_level:
            self.level_up()

    def level_up(self):
        """Level up the character, 3/16/25"""
        self.level += 1
        self.experience -= self.experience_to_level
    
        # Increase next level threshold
        self.experience_to_level = self.level * 100
    
        # Increase stats
        self.max_health += 10
        self.health = self.max_health  # Heal on level up
    
        # Skill points for player to allocate
        self.skill_points = getattr(self, 'skill_points', 0) + 3
    
        print(f"Level up! Now level {self.level}")
        print(f"Gained 3 skill points, now have {self.skill_points} to spend")

    def increase_skill(self, skill_name):
        """Increase a skill if player has skill points, 3/16/25"""
        if self.skill_points > 0 and skill_name in self.skills:
            self.skills[skill_name] += 1
            self.skill_points -= 1
            return True
        return False

    def complete_quest(self, quest_id):
        """Mark a quest as completed and get rewards"""
        for quest in self.quests:
            if quest.id == quest_id and not quest.completed:
                quest.completed = True
                self.credits += quest.credit_reward
                self.gain_experience(quest.xp_reward)
                
                # Apply reputation changes
                for faction, change in quest.reputation_changes.items():
                    if faction in self.reputation:
                        self.reputation[faction] += change
                
                # Add item rewards to inventory
                for item in quest.item_rewards:
                    self.add_to_inventory(item)
                
                return True
        return False


class NPC(Character, pygame.sprite.Sprite):
    def __init__(self, name, sprite_sheet=None, x=0, y=0, dialogue=None, quest=None):
        Character.__init__(self, name, sprite_sheet, x, y)
        pygame.sprite.Sprite.__init__(self)
        
        self.dialogue = dialogue or ["Hello!"]
        self.quest = quest
        self.quest_offered = False
        self.has_shop = False
        self.shop_inventory = []
        self.movement_pattern = None  # Could be "stationary", "patrol", or "follow"
        self.patrol_points = []
        self.current_patrol_index = 0
        self.faction = None  # Could be "earth", "mars", "pallas", etc.
    
    def update(self, dt, player=None):
        """Update NPC behavior"""
        # Handle movement based on pattern
        if self.movement_pattern == "patrol" and self.patrol_points:
            target = self.patrol_points[self.current_patrol_index]
            direction = pygame.math.Vector2(target[0] - self.rect.x, target[1] - self.rect.y)
            if direction.length() > 0:
                direction = direction.normalize() * 2  # Movement speed
                self.rect.x += direction.x
                self.rect.y += direction.y
                
                # Determine animation direction
                if abs(direction.x) > abs(direction.y):
                    if direction.x > 0:
                        movement_direction = "right"
                    else:
                        movement_direction = "left"
                else:
                    if direction.y > 0:
                        movement_direction = "down"
                    else:
                        movement_direction = "up"
                
                # Update animation
                self.update_animation(dt, movement_direction)
                
                # Check if reached patrol point
                if pygame.math.Vector2(self.rect.center).distance_to(target) < 5:
                    self.current_patrol_index = (self.current_patrol_index + 1) % len(self.patrol_points)
            
        elif self.movement_pattern == "follow" and player:
            # Follow the player but keep a distance
            direction = pygame.math.Vector2(player.rect.centerx - self.rect.centerx, 
                                           player.rect.centery - self.rect.centery)
            distance = direction.length()
            
            if 50 < distance < 200:  # Only follow within this range
                direction = direction.normalize() * 1.5  # Slower than player
                self.rect.x += direction.x
                self.rect.y += direction.y
                
                # Determine animation direction
                if abs(direction.x) > abs(direction.y):
                    if direction.x > 0:
                        movement_direction = "right"
                    else:
                        movement_direction = "left"
                else:
                    if direction.y > 0:
                        movement_direction = "down"
                    else:
                        movement_direction = "up"
                
                # Update animation
                self.update_animation(dt, movement_direction)
        else:
            # Stationary NPCs still animate at idle
            self.update_animation(dt)
    
    def offer_quest(self, player):
        """Offer a quest to the player if available"""
        if self.quest and not self.quest_offered:
            self.quest_offered = True
            player.quests.append(self.quest)
            return self.quest
        return None
    
    def open_shop(self):
        """Open shop interface if NPC is a merchant"""
        if self.has_shop:
            return self.shop_inventory
        return None


class Quest:
    def __init__(self, quest_id, title, description, objectives):
        self.id = quest_id
        self.title = title
        self.description = description
        self.objectives = objectives  # List of objective descriptions
        self.objective_progress = [0] * len(objectives)  # Progress for each objective
        self.objective_targets = [1] * len(objectives)   # Target value for each objective
        self.completed = False
        self.credit_reward = 0
        self.xp_reward = 0
        self.item_rewards = []
        self.reputation_changes = {}  # {"faction": change_value}
        self.prerequisite_quests = []  # List of quest IDs that must be completed first
    
    def update_objective(self, index, progress):
        """Update progress on a specific objective"""
        if 0 <= index < len(self.objectives):
            self.objective_progress[index] += progress
            if self.objective_progress[index] > self.objective_targets[index]:
                self.objective_progress[index] = self.objective_targets[index]
            
            # Check if all objectives are complete
            if all(self.objective_progress[i] >= self.objective_targets[i] for i in range(len(self.objectives))):
                self.completed = True
                return True
        return False
    
    def is_available(self, completed_quests):
        """Check if this quest is available based on prerequisites"""
        for quest_id in self.prerequisite_quests:
            if quest_id not in completed_quests:
                return False
        return True


# Example usage:
# player = Player("Leo", x=100, y=100)
# npc = NPC("Stella", x=200, y=200, dialogue=["Hello!", "Welcome to Psyche Township."])
# quest = Quest("q001", "First Steps", "Get familiar with Psyche Township", ["Talk to Mayor Gus"])
# quest.credit_reward = 100
# quest.xp_reward = 50
# npc.quest = quest