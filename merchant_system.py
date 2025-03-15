import pygame
import math

# Add this to GameState
# GameState.MERCHANT = 11 

class ShipUpgrade:
    """Class for upgrades that can be purchased for the ship"""
    def __init__(self, upgrade_id, name, description, base_price, max_level=3):
        self.id = upgrade_id
        self.name = name
        self.description = description
        self.base_price = base_price
        self.max_level = max_level
    
    def get_price(self, current_level):
        """Get the price for the next level"""
        if current_level >= self.max_level:
            return None  # Max level reached
        
        # Each level gets more expensive
        return self.base_price * (current_level + 1)
    
    def get_stats_text(self, current_level):
        """Get text describing what this upgrade will improve"""
        if current_level >= self.max_level:
            return f"MAX LEVEL REACHED ({current_level}/{self.max_level})"
        
        next_level = current_level + 1
        return f"Level {next_level}/{self.max_level}"
    
    def apply_upgrade(self, game, current_level):
        """Apply the effects of this upgrade to the game"""
        # Override in subclasses
        pass

class WeaponUpgrade(ShipUpgrade):
    """Upgrade for ship's weapons"""
    def __init__(self):
        super().__init__(
            "weapon",
            "Weapon Systems",
            "Upgrade your ship's weapons to deal more damage to asteroids",
            200, 
            3
        )
    
    def get_stats_text(self, current_level):
        if current_level >= self.max_level:
            return f"MAX LEVEL REACHED ({current_level}/{self.max_level})"
        
        next_level = current_level + 1
        damage_increase = 30 + (next_level - 1) * 15  # 30/45/60 damage
        
        return f"Level {next_level}/{self.max_level} - Damage: {damage_increase}"
    
    def apply_upgrade(self, game, current_level):
        """Apply weapon upgrade effects"""
        if not hasattr(game, 'space_travel') or not game.space_travel:
            return False
        
        next_level = current_level + 1
        
        # Update damage in space travel system
        # You'll need to add this attribute to your space travel class
        game.space_travel.weapon_damage = 30 + (next_level - 1) * 15
        
        return True

class EngineUpgrade(ShipUpgrade):
    """Upgrade for ship's engines"""
    def __init__(self):
        super().__init__(
            "engine",
            "Engine Systems",
            "Upgrade your ship's engines for better speed and maneuverability",
            150, 
            3
        )
    
    def get_stats_text(self, current_level):
        if current_level >= self.max_level:
            return f"MAX LEVEL REACHED ({current_level}/{self.max_level})"
        
        next_level = current_level + 1
        speed_increase = 1.0 + (next_level - 1) * 0.5  # 50% increases
        
        return f"Level {next_level}/{self.max_level} - Speed: +{int(speed_increase*100-100)}%"
    
    def apply_upgrade(self, game, current_level):
        """Apply engine upgrade effects"""
        if not hasattr(game, 'space_travel') or not game.space_travel:
            return False
        
        next_level = current_level + 1
        
        # Calculate speed multiplier
        speed_multiplier = 1.0 + (next_level - 1) * 0.5
        
        # Apply to space travel
        base_thrust = 0.1  # Base thrust value
        base_max_speed = 5.0  # Base max speed
        
        game.space_travel.thrust_power = base_thrust * speed_multiplier
        game.space_travel.max_speed = base_max_speed * speed_multiplier
        
        return True

class ShieldUpgrade(ShipUpgrade):
    """Upgrade for ship's shields"""
    def __init__(self):
        super().__init__(
            "shield",
            "Shield Systems",
            "Add shields to protect your ship from asteroid collisions",
            250, 
            3
        )
    
    def get_stats_text(self, current_level):
        if current_level >= self.max_level:
            return f"MAX LEVEL REACHED ({current_level}/{self.max_level})"
        
        next_level = current_level + 1
        shield_value = 25 * next_level  # 25/50/75 shield
        
        return f"Level {next_level}/{self.max_level} - Shield: {shield_value}"
    
    def apply_upgrade(self, game, current_level):
        """Apply shield upgrade effects"""
        if not hasattr(game, 'space_travel') or not game.space_travel:
            return False
        
        next_level = current_level + 1
        
        # Set shield value
        shield_value = 25 * next_level
        
        # Apply to ship
        if hasattr(game.space_travel, 'ship'):
            game.space_travel.ship.shield_strength = shield_value
            game.space_travel.ship.max_shield_strength = shield_value
        
        return True

class CargoUpgrade(ShipUpgrade):
    """Upgrade for ship's cargo capacity"""
    def __init__(self):
        super().__init__(
            "cargo",
            "Cargo Holds",
            "Expand your ship's cargo capacity to carry more resources",
            200, 
            3
        )
    
    def get_stats_text(self, current_level):
        if current_level >= self.max_level:
            return f"MAX LEVEL REACHED ({current_level}/{self.max_level})"
        
        next_level = current_level + 1
        cargo_increase = 100 * next_level  # 100/200/300 capacity
        
        return f"Level {next_level}/{self.max_level} - Capacity: {cargo_increase}"
    
    def apply_upgrade(self, game, current_level):
        """Apply cargo upgrade effects"""
        next_level = current_level + 1
        
        # Set cargo capacity
        cargo_capacity = 100 * next_level
        
        # Store in game state
        game.cargo_capacity = cargo_capacity
        
        return True

class MerchantSystem:
    """System for managing merchants and trading"""
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.font_large = pygame.font.Font(None, 36)
        self.font = pygame.font.Font(None, 28)
        self.font_small = pygame.font.Font(None, 22)
        
        # Initialize available upgrades
        self.available_upgrades = [
            WeaponUpgrade(),
            EngineUpgrade(),
            ShieldUpgrade(),
            CargoUpgrade()
        ]
        
        # Menu state
        self.selected_tab = "upgrades"  # "upgrades" or "resources"
        self.selected_index = 0
        self.scroll_offset = 0
        self.max_visible_items = 6
        
        # Resource price multipliers (different per location)
        self.resource_price_multipliers = {
            "psyche_township": {
                "iron": 1.0,
                "copper": 1.2,
                "titanium": 1.5,
                "gold": 0.9,
                "platinum": 1.1,
                "uranium": 0.8,
                "neodymium": 1.2,
                "alien_alloy": 1.5,
                "dark_matter": 1.0
            },
            "rusty_rocket": {
                "iron": 0.8,
                "copper": 1.0,
                "titanium": 1.2,
                "gold": 1.5,
                "platinum": 1.3,
                "uranium": 1.0,
                "neodymium": 0.9,
                "alien_alloy": 1.2,
                "dark_matter": 2.0
            }
            # Add other locations as needed
        }
    
    def get_resource_price(self, resource_id, location_id="psyche_township"):
        """Get the price for a resource at a specific location"""
        # Get base value from resource registry
        resource_registry = None
        
        # Try to get resource registry from the game
        if hasattr(self, 'game') and hasattr(self.game, 'space_travel') and hasattr(self.game.space_travel, 'asteroid_field'):
            resource_registry = self.game.space_travel.asteroid_field.resource_registry
        
        if not resource_registry:
            # Create a temporary registry if needed
            from asteroid_resources import ResourceRegistry
            resource_registry = ResourceRegistry()

        resource = resource_registry.get_resource(resource_id)
        if not resource:
            return 0
        
        # Get base price
        base_price = resource.value
        
        # Apply location-specific multiplier
        multiplier = 1.0
        if location_id in self.resource_price_multipliers and resource_id in self.resource_price_multipliers[location_id]:
            multiplier = self.resource_price_multipliers[location_id][resource_id]
        
        return int(base_price * multiplier)

    def get_upgrades(self, game):
        """Get list of available upgrades with their levels"""
        upgrade_list = []
        
        for upgrade in self.available_upgrades:
            # Get current level from game state
            current_level = self.get_upgrade_level(game, upgrade.id)
            
            # Get price for next level
            price = upgrade.get_price(current_level)
            
            upgrade_list.append({
                "upgrade": upgrade,
                "current_level": current_level,
                "price": price,
                "stats_text": upgrade.get_stats_text(current_level),
                "can_afford": price is not None and game.player.credits >= price,
                "max_level": current_level >= upgrade.max_level
            })
        
        return upgrade_list
    
    def get_upgrade_level(self, game, upgrade_id):
        """Get current level of an upgrade from game state"""
        # Check if game has upgrades dictionary
        if not hasattr(game, 'ship_upgrades'):
            game.ship_upgrades = {}
        
        # Return current level, defaulting to 0
        return game.ship_upgrades.get(upgrade_id, 0)
    
    def purchase_upgrade(self, game, upgrade_id):
        """Purchase an upgrade if possible"""
        # Find the upgrade
        upgrade = next((u for u in self.available_upgrades if u.id == upgrade_id), None)
        if not upgrade:
            return False
        
        # Get current level
        current_level = self.get_upgrade_level(game, upgrade_id)
        
        # Check if max level reached
        if current_level >= upgrade.max_level:
            return False
        
        # Get price
        price = upgrade.get_price(current_level)
        
        # Check if affordable
        if game.player.credits < price:
            return False
        
        # Deduct credits
        game.player.credits -= price
        
        # Increase upgrade level
        if not hasattr(game, 'ship_upgrades'):
            game.ship_upgrades = {}
        game.ship_upgrades[upgrade_id] = current_level + 1
        
        # Apply upgrade effects
        upgrade.apply_upgrade(game, current_level)
        
        return True
    
    def sell_resource(self, game, resource_id, amount=1, location_id="psyche_township"):
        """Sell a resource to the merchant"""
        # Check if we have space travel with asteroid field
        if hasattr(game, 'space_travel') and hasattr(game.space_travel, 'asteroid_field'):
            resources = game.space_travel.asteroid_field.collected_resources
        
            if resource_id in resources and resources[resource_id] >= amount:
                # Calculate sale value
                price_per_unit = self.get_resource_price(resource_id, location_id)
                total_price = price_per_unit * amount
            
                # Add credits to player
                game.player.credits += total_price
            
                # Remove resource
                resources[resource_id] -= amount
                if resources[resource_id] <= 0:
                    del resources[resource_id]
            
                # Force refresh of display items
                self.refresh_items_list(game)
            
                return total_price
    
        return False

    def refresh_items_list(self, game):
        """Refresh the list of items after changes"""
        # Force recalculation of visible items on next draw
        if hasattr(self, '_cached_items'):
            del self._cached_items
    
    def get_player_resources(self, game):
        """Get player's collected resources"""
        # Check if game has space travel with asteroid field
        if hasattr(game, 'space_travel') and hasattr(game.space_travel, 'asteroid_field'):
            return game.space_travel.asteroid_field.get_collected_resources()
        
        # Fall back to empty dictionary
        if not hasattr(game, 'collected_resources'):
            game.collected_resources = {}
        
        return game.collected_resources
    
    def set_player_resources(self, game, resources):
        """Set player's collected resources"""
        # Update in asteroid field if available
        if hasattr(game, 'space_travel') and hasattr(game.space_travel, 'asteroid_field'):
            game.space_travel.asteroid_field.collected_resources = resources
        
        # Also store in game state as backup
        game.collected_resources = resources
    
    def handle_event(self, event, game):
        """Handle events for the merchant interface"""
        if event.type == pygame.KEYDOWN:
            # Close merchant with Escape
            if event.key == pygame.K_ESCAPE:
                game.game_state = 1
                return True
            
            # Tab switching
            if event.key == pygame.K_TAB:
                if self.selected_tab == "upgrades":
                    self.selected_tab = "resources"
                else:
                    self.selected_tab = "upgrades"
                self.selected_index = 0
                self.scroll_offset = 0
            
            # # Tab switching with number keys
            # if event.key == pygame.K_1:
            #     self.selected_tab = "upgrades"
            #     self.selected_index = 0
            #     self.scroll_offset = 0
            # elif event.key == pygame.K_2:
            #     self.selected_tab = "resources"
            #     self.selected_index = 0
            #     self.scroll_offset = 0
            
            # Navigation
            if event.key == pygame.K_UP:
                self.selected_index = max(0, self.selected_index - 1)
                # Scroll up if needed
                if self.selected_index < self.scroll_offset:
                    self.scroll_offset = self.selected_index
            elif event.key == pygame.K_DOWN:
                max_index = len(self.get_visible_items(game)) - 1
                self.selected_index = min(max_index, self.selected_index + 1) if max_index >= 0 else 0
                # Scroll down if needed
                if self.selected_index >= self.scroll_offset + self.max_visible_items:
                    self.scroll_offset = self.selected_index - self.max_visible_items + 1
            
            # Perform action - handle Enter/Return and Space keys
            if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                print("Enter/Space pressed, performing selected action")
                return self.perform_selected_action(game)
            
            # Selling with specific quantity
            if self.selected_tab == "resources" and pygame.K_1 <= event.key <= pygame.K_9:
                quantity = event.key - pygame.K_0  # 1-9
                self.sell_selected_resource(game, quantity)
        
        return True
    
    def get_visible_items(self, game):
        """Get list of items to display based on selected tab"""
        if self.selected_tab == "upgrades":
            return self.get_upgrades(game)
        else:  # "resources"
            resources = self.get_player_resources(game)
            items = []
            
            for resource_id, amount in resources.items():
                # Get price info
                price = self.get_resource_price(resource_id, game.current_level.get("name", "psyche_township"))
                
                items.append({
                    "id": resource_id,
                    "name": resource_id.replace("_", " ").title(),
                    "amount": amount,
                    "price": price,
                    "total_value": price * amount
                })
            
            # Sort by name
            items.sort(key=lambda x: x["name"])
            
            return items
    
    def perform_selected_action(self, game):
        """Perform action for selected item"""
        print("Performing action for selected item")
        visible_items = self.get_visible_items(game)
    
        if 0 <= self.selected_index < len(visible_items):
            selected_item = visible_items[self.selected_index]
        
            if self.selected_tab == "upgrades":
                # Purchase upgrade
                if not selected_item["max_level"] and selected_item["can_afford"]:
                    success = self.purchase_upgrade(game, selected_item["upgrade"].id)
                    if success:
                        print(f"Purchased {selected_item['upgrade'].name} upgrade!")
                        return True
        
            elif self.selected_tab == "resources":
                # Sell all of the selected resource
                success = self.sell_selected_resource(game)
                return success
    
        return False
    
    def sell_selected_resource(self, game, quantity=None):
        """Sell selected resource"""
        print("Attempting to sell selected resource")
        visible_items = self.get_visible_items(game)
    
        if 0 <= self.selected_index < len(visible_items):
            selected_item = visible_items[self.selected_index]
        
            # Get resource ID and amount
            resource_id = selected_item["id"]
            available = selected_item["amount"]
        
            # Determine quantity to sell
            if quantity is None or quantity > available:
                quantity = available
        
            # Sell the resource
            location_id = game.current_level.get("name", "psyche_township")
            credits_earned = self.sell_resource(game, resource_id, quantity, location_id)
        
            if credits_earned:
                print(f"Sold {quantity} {selected_item['name']} for {credits_earned} credits!")
                return True
    
        return False
    
    def draw(self, screen, game):
        """Draw the merchant interface"""
        # Draw semi-transparent background
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))  # Black with alpha
        screen.blit(overlay, (0, 0))
        
        # Draw merchant panel
        panel_width = self.screen_width - 200
        panel_height = self.screen_height - 150
        panel_rect = pygame.Rect(100, 75, panel_width, panel_height)
        pygame.draw.rect(screen, (50, 50, 50), panel_rect)
        pygame.draw.rect(screen, (200, 200, 200), panel_rect, 2)
        
        # Draw merchant title
        merchant_name = "Psyche Trading Post"
        if game.current_level and "name" in game.current_level:
            location = game.current_level["name"].replace("_", " ").title()
            merchant_name = f"{location} Trading Post"
        
        title = self.font_large.render(merchant_name, True, (255, 255, 255))
        screen.blit(title, (panel_rect.centerx - title.get_width() // 2, panel_rect.y + 20))
        
        # Draw player credits
        credits_text = self.font.render(f"Your Credits: {game.player.credits}", True, (255, 255, 0))
        screen.blit(credits_text, (panel_rect.right - credits_text.get_width() - 20, panel_rect.y + 20))
        
        # Draw tabs
        tab_y = panel_rect.y + 60
        tab_width = panel_width // 2 - 10
        
        # Upgrades tab
        upgrades_tab_rect = pygame.Rect(panel_rect.x + 10, tab_y, tab_width, 40)
        pygame.draw.rect(screen, (70, 70, 100) if self.selected_tab == "upgrades" else (30, 30, 50), upgrades_tab_rect)
        pygame.draw.rect(screen, (200, 200, 200), upgrades_tab_rect, 2)
        
        upgrades_text = self.font.render("1. Ship Upgrades", True, (255, 255, 255))
        screen.blit(upgrades_text, (upgrades_tab_rect.centerx - upgrades_text.get_width() // 2, tab_y + 10))
        
        # Resources tab
        resources_tab_rect = pygame.Rect(panel_rect.x + panel_width // 2 + 5, tab_y, tab_width, 40)
        pygame.draw.rect(screen, (70, 70, 100) if self.selected_tab == "resources" else (30, 30, 50), resources_tab_rect)
        pygame.draw.rect(screen, (200, 200, 200), resources_tab_rect, 2)
        
        resources_text = self.font.render("2. Sell Resources", True, (255, 255, 255))
        screen.blit(resources_text, (resources_tab_rect.centerx - resources_text.get_width() // 2, tab_y + 10))
        
        # Draw content based on selected tab
        content_rect = pygame.Rect(panel_rect.x + 20, tab_y + 50, panel_width - 40, panel_height - 120)
        
        if self.selected_tab == "upgrades":
            self.draw_upgrades_tab(screen, game, content_rect)
        else:  # "resources"
            self.draw_resources_tab(screen, game, content_rect)
        
        # Draw controls hint
        controls = self.font_small.render(
            "↑/↓: Navigate | Tab: Switch Tabs | Enter: Buy/Sell | 1-9: Sell Specific Amount | Esc: Exit",
            True, (200, 200, 200)
        )
        screen.blit(controls, (panel_rect.centerx - controls.get_width() // 2, panel_rect.bottom - 30))
    
    def draw_upgrades_tab(self, screen, game, content_rect):
        """Draw the upgrades tab content"""
        upgrades = self.get_upgrades(game)
        
        # Handle empty list
        if not upgrades:
            empty_text = self.font.render("No upgrades available", True, (200, 200, 200))
            screen.blit(empty_text, (content_rect.centerx - empty_text.get_width() // 2, content_rect.y + 50))
            return
        
        # Draw column headers
        header_y = content_rect.y
        pygame.draw.line(screen, (150, 150, 150), (content_rect.x, header_y + 30), (content_rect.right, header_y + 30), 1)
        
        header_upgrade = self.font.render("Upgrade", True, (200, 200, 200))
        header_stats = self.font.render("Stats", True, (200, 200, 200))
        header_price = self.font.render("Price", True, (200, 200, 200))
        
        screen.blit(header_upgrade, (content_rect.x + 10, header_y))
        screen.blit(header_stats, (content_rect.x + 200, header_y))
        screen.blit(header_price, (content_rect.right - header_price.get_width() - 10, header_y))
        
        # Draw visible upgrades with scrolling
        visible_upgrades = upgrades[self.scroll_offset:self.scroll_offset + self.max_visible_items]
        
        for i, upgrade_info in enumerate(visible_upgrades):
            # Calculate actual index in the full list
            actual_index = i + self.scroll_offset
            
            # Row position
            row_y = header_y + 40 + i * 50
            
            # Highlight if selected
            if self.selected_index == actual_index:
                row_rect = pygame.Rect(content_rect.x, row_y - 5, content_rect.width, 50)
                pygame.draw.rect(screen, (70, 70, 100), row_rect)
            
            # Draw upgrade info
            upgrade = upgrade_info["upgrade"]
            
            # Name and description
            name_text = self.font.render(upgrade.name, True, (255, 255, 255))
            screen.blit(name_text, (content_rect.x + 10, row_y))
            
            desc_text = self.font_small.render(upgrade.description, True, (200, 200, 200))
            screen.blit(desc_text, (content_rect.x + 10, row_y + 25))
            
            # Stats
            stats_text = self.font.render(upgrade_info["stats_text"], True, 
                                        (255, 255, 255) if not upgrade_info["max_level"] else (150, 150, 150))
            screen.blit(stats_text, (content_rect.x + 200, row_y + 10))
            
            # Price
            if upgrade_info["max_level"]:
                price_text = self.font.render("MAXED", True, (150, 150, 150))
            else:
                price_text = self.font.render(f"{upgrade_info['price']} credits", True, 
                                           (0, 255, 0) if upgrade_info["can_afford"] else (255, 0, 0))
            
            screen.blit(price_text, (content_rect.right - price_text.get_width() - 10, row_y + 10))
        
        # Draw scroll indicators if needed
        self.draw_scroll_indicators(screen, content_rect, len(upgrades))
    
    def draw_resources_tab(self, screen, game, content_rect):
        """Draw the resources tab content"""
        resources = self.get_visible_items(game)
        
        # Handle empty list
        if not resources:
            empty_text = self.font.render("No resources to sell", True, (200, 200, 200))
            screen.blit(empty_text, (content_rect.centerx - empty_text.get_width() // 2, content_rect.y + 50))
            return
        
        # Draw column headers
        header_y = content_rect.y
        pygame.draw.line(screen, (150, 150, 150), (content_rect.x, header_y + 30), (content_rect.right, header_y + 30), 1)
        
        header_resource = self.font.render("Resource", True, (200, 200, 200))
        header_amount = self.font.render("Amount", True, (200, 200, 200))
        header_price = self.font.render("Price (ea.)", True, (200, 200, 200))
        header_total = self.font.render("Total Value", True, (200, 200, 200))
        
        screen.blit(header_resource, (content_rect.x + 10, header_y))
        screen.blit(header_amount, (content_rect.x + 200, header_y))
        screen.blit(header_price, (content_rect.x + 300, header_y))
        screen.blit(header_total, (content_rect.right - header_total.get_width() - 10, header_y))
        
        # Draw visible resources with scrolling
        visible_resources = resources[self.scroll_offset:self.scroll_offset + self.max_visible_items]
        
        for i, resource in enumerate(visible_resources):
            # Calculate actual index in the full list
            actual_index = i + self.scroll_offset
            
            # Row position
            row_y = header_y + 40 + i * 40
            
            # Highlight if selected
            if self.selected_index == actual_index:
                row_rect = pygame.Rect(content_rect.x, row_y - 5, content_rect.width, 40)
                pygame.draw.rect(screen, (70, 70, 100), row_rect)
            
            # Draw resource info
            name_text = self.font.render(resource["name"], True, (255, 255, 255))
            screen.blit(name_text, (content_rect.x + 10, row_y + 5))
            
            amount_text = self.font.render(str(resource["amount"]), True, (255, 255, 255))
            screen.blit(amount_text, (content_rect.x + 200, row_y + 5))
            
            price_text = self.font.render(f"{resource['price']} credits", True, (255, 255, 0))
            screen.blit(price_text, (content_rect.x + 300, row_y + 5))
            
            total_text = self.font.render(f"{resource['total_value']} credits", True, (0, 255, 0))
            screen.blit(total_text, (content_rect.right - total_text.get_width() - 10, row_y + 5))
            
            # Draw "sell" prompt for selected item
            if self.selected_index == actual_index:
                sell_text = self.font_small.render("Press Enter to sell all, or 1-9 to sell specific amount", 
                                                 True, (255, 200, 0))
                screen.blit(sell_text, (content_rect.centerx - sell_text.get_width() // 2, row_y + 28))
        
        # Draw scroll indicators if needed
        self.draw_scroll_indicators(screen, content_rect, len(resources))
    
    def draw_scroll_indicators(self, screen, content_rect, total_items):
        """Draw scroll indicators if there are more items than visible"""
        if self.scroll_offset > 0:
            pygame.draw.polygon(screen, (255, 255, 255), [
                (content_rect.centerx - 10, content_rect.y + 35),
                (content_rect.centerx + 10, content_rect.y + 35),
                (content_rect.centerx, content_rect.y + 25)
            ])
        
        max_offset = max(0, total_items - self.max_visible_items)
        if self.scroll_offset < max_offset:
            pygame.draw.polygon(screen, (255, 255, 255), [
                (content_rect.centerx - 10, content_rect.bottom - 15),
                (content_rect.centerx + 10, content_rect.bottom - 15),
                (content_rect.centerx, content_rect.bottom - 5)
            ])