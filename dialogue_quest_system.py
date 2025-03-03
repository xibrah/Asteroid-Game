# Asteroid Frontier RPG
# Dialogue and Quest System

import pygame
import json
import os

class DialogueNode:
    def __init__(self, text, responses=None, actions=None):
        self.text = text
        self.responses = responses or []  # List of (text, next_node_id) tuples
        self.actions = actions or {}  # Dictionary of actions to perform
    
    def get_actions(self):
        """Return the actions for this node"""
        return self.actions

    def choose_response(self, index):
        """Select a dialogue response"""
        if 0 <= index < len(self.responses):
            _, next_node_id = self.responses[index]
            return next_node_id
        return None

        # Possible actions include:
        # - 'quest_start': quest_id
        # - 'quest_complete': quest_id
        # - 'give_item': item_id
        # - 'take_item': item_id
        # - 'give_credits': amount
        # - 'take_credits': amount
        # - 'change_reputation': {'faction': amount}
        # - 'set_flag': flag_name
        # - 'check_flag': {'flag_name': next_node_if_true, 'else': next_node_if_false}

class DialogueTree:
    def __init__(self, npc_name):
        self.npc_name = npc_name
        self.nodes = {}
        self.current_node_id = None
        self.start_node_id = None
    
    def add_node(self, node_id, text, responses=None, actions=None):
        """Add a dialogue node to the tree"""
        self.nodes[node_id] = DialogueNode(text, responses, actions)
        if not self.start_node_id:
            self.start_node_id = node_id
    
    def get_node(self, node_id):
        """Get a node by ID"""
        return self.nodes.get(node_id)
    
    def start_dialogue(self):
        """Start the dialogue from the beginning"""
        self.current_node_id = self.start_node_id
        return self.get_current_node()
    
    def get_current_node(self):
        """Get the current dialogue node"""
        if self.current_node_id:
            return self.nodes.get(self.current_node_id)
        return None
    
    def choose_response(self, index):
        """Choose a response and move to the next node"""
        current_node = self.get_current_node()
        if not self.current_node:
            return None
            
        next_node_id = current_node.choose_response(index)
        if next_node_id:
            self.current_node = next_node_id
            return self.get_current_node()
        
        return None
    
    def get_actions(self):
        """Get actions from the current node"""
        if not self.current_node:
            return {}
            
        return self.nodes[self.current_node].actions
    
    @classmethod
    def load_from_json(cls, filename):
        """Load a dialogue tree from a JSON file"""
        with open(os.path.join('assets', 'dialogues', filename), 'r') as file:
            data = json.load(file)
        
        tree = cls(data['npc_name'])
        for node_id, node_data in data['nodes'].items():
            tree.add_node(
                node_id,
                node_data['text'],
                node_data.get('responses', []),
                node_data.get('actions', {})
            )
        
        tree.start_node = data['start_node']
        return tree


class DialogueManager:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.active_dialogue = None
        self.current_npc = None
        self.player = None
        self.game_flags = {}  # Store game state flags here
        self.font = pygame.font.Font(None, 28)
        self.name_font = pygame.font.Font(None, 32)
    
    def start_dialogue(self, npc, player):
        """Start a dialogue with an NPC"""
        self.current_npc = npc
        self.player = player
        
        # Check if NPC has full dialogue data from JSON
        if hasattr(npc, 'full_dialogue') and npc.full_dialogue:
            print(f"Using full dialogue data for {npc.name}")
            # Create a dialogue tree using the full dialogue data
            self.dialogue_tree = DialogueTree(npc.name)
        
            # Add nodes based on full dialogue
            dialogue_data = npc.full_dialogue
        
            # Start node
            start_text = dialogue_data.get("default", ["Hello!"])[0]
        
            # Check for different dialogue options based on NPC state
            has_quest = hasattr(npc, 'quest') and npc.quest
            quest_offered = getattr(npc, 'quest_offered', False)
            quest_completed = has_quest and getattr(npc.quest, 'completed', False)
            has_shop = getattr(npc, 'has_shop', False)
        
            # Create appropriate dialogue options
            responses = []
            if "about" in dialogue_data:
                responses.append(("Tell me about yourself.", "about"))
            if "events" in dialogue_data:
                responses.append(("What's going on around here?", "events"))
            if has_quest and not quest_offered:
                responses.append(("I heard you might have work for me?", "quest_offer"))
            if has_shop:
                responses.append(("I'd like to see your wares.", "shop"))
            responses.append(("Goodbye.", "exit"))
        
            # Add the start node
            self.dialogue_tree.add_node("start", start_text, responses)
        
            # Add other dialogue nodes
            for node_id, dialogue_lines in dialogue_data.items():
                if node_id != "default":
                    # Skip "default" as we already used it for the start node
                    if isinstance(dialogue_lines, list) and dialogue_lines:
                        # Use first line as the text
                        node_text = dialogue_lines[0]
                        # Add a way back to the start
                        node_responses = [("Let's talk about something else.", "start")]
                        self.dialogue_tree.add_node(node_id, node_text, node_responses)
        
            # Add special nodes for quests, shops, etc.
            if has_quest and not quest_offered:
                quest_desc = npc.quest.description if hasattr(npc.quest, 'description') else "I need help with something."
                self.dialogue_tree.add_node("quest_offer", quest_desc, [
                    ("I'll help you out.", "quest_accept"),
                    ("I'm not interested right now.", "quest_decline")
                ])
            
                self.dialogue_tree.add_node("quest_accept", "Excellent! Thank you so much.", [
                    ("I'll get right on it.", "exit")
                ], {"quest_start": npc.quest.id if hasattr(npc.quest, 'id') else "quest_1"})
            
                self.dialogue_tree.add_node("quest_decline", "I understand. If you change your mind, I'll be here.", [
                    ("Let's talk about something else.", "start"),
                    ("Goodbye for now.", "exit")
                ])
        
            if has_shop:
                self.dialogue_tree.add_node("shop", "Take a look at what I have available.", [
                    ("Let me see.", "shop_open"),
                    ("Maybe later.", "start")
                ])
            
                self.dialogue_tree.add_node("shop_open", "Here's what I have in stock.", [
                    ("Let's talk about something else.", "start"),
                    ("Goodbye.", "exit")
                ], {"open_shop": True})
        
            self.dialogue_tree.add_node("exit", "See you around!", [], {"end_dialogue": True})
        
            # Start the dialogue
            self.active_dialogue = self.dialogue_tree.get_node("start")
            return self.active_dialogue
    
        else:
            # Use the original method for NPCs without full dialogue data
            # Your existing dialogue creation code here...
            # Create a dialogue tree for this NPC
            self.dialogue_tree = DialogueTree(npc.name)
        
            # Add nodes to the dialogue tree
            # Start node
            start_text = "Hello there! What can I do for you today?"
        
            # Different dialogue based on whether NPC has a quest
            if hasattr(npc, 'quest') and npc.quest and not getattr(npc, 'quest_offered', False):
                self.dialogue_tree.add_node("start", start_text, [
                    ("Tell me about yourself.", "about"),
                    ("What's going on around here?", "events"),
                    ("I heard you might have work for me?", "quest_offer")
                ])
            elif hasattr(npc, 'quest') and npc.quest and getattr(npc.quest, 'completed', False):
                self.dialogue_tree.add_node("start", "Thanks again for your help!", [
                    ("Tell me about yourself.", "about"),
                    ("What's going on around here?", "events"),
                    ("Goodbye.", "exit")
                ])
            elif hasattr(npc, 'has_shop') and npc.has_shop:
                self.dialogue_tree.add_node("start", start_text, [
                    ("Tell me about yourself.", "about"),
                    ("What's going on around here?", "events"),
                    ("I'd like to see your wares.", "shop"),
                    ("Goodbye.", "exit")
                ])
            else:
                self.dialogue_tree.add_node("start", start_text, [
                    ("Tell me about yourself.", "about"),
                    ("What's going on around here?", "events"),
                    ("Goodbye.", "exit")
                ])
        
            # Add remaining dialogue nodes
            self.dialogue_tree.add_node("about", f"I'm {npc.name}. I've been living here on {npc.faction if npc.faction else 'this asteroid'} for quite some time now.", [
                ("What do you do here?", "occupation"),
                ("Let's talk about something else.", "start")
            ])
        
            self.dialogue_tree.add_node("occupation", "I'm a [occupation]. It's not glamorous, but it pays the bills.", [
                ("Interesting. Let's talk about something else.", "start")
            ])
        
            self.dialogue_tree.add_node("events", "Things have been tense lately with the Earth garrison. Mayor Gus is doing his best to keep the peace.", [
                ("Tell me more about the Earth garrison.", "garrison"),
                ("What do you know about Mayor Gus?", "gus"),
                ("Let's talk about something else.", "start")
            ])
        
            self.dialogue_tree.add_node("garrison", "The Earth Republic sent troops here, supposedly to protect the station. But there's been trouble... fights breaking out.", [
                ("What does Mayor Gus think about this?", "gus"),
                ("Let's talk about something else.", "start")
            ])
        
            self.dialogue_tree.add_node("gus", "Gus is a good man. Used to be union leader before becoming mayor. He's trying to balance everyone's interests, but it's not easy.", [
                ("What do you know about the Earth garrison?", "garrison"),
                ("Let's talk about something else.", "start")
            ])
        
            if hasattr(npc, 'quest') and npc.quest and not getattr(npc, 'quest_offered', False):
                quest_desc = npc.quest.description if hasattr(npc.quest, 'description') else "I need some help with something."
                self.dialogue_tree.add_node("quest_offer", f"Actually, yes! {quest_desc}", [
                    ("I'll help you out.", "quest_accept"),
                    ("I'm not interested right now.", "quest_decline")
                ])
        
                self.dialogue_tree.add_node("quest_accept", "Excellent! Thank you so much.", [
                    ("I'll get right on it.", "exit")
                ], {"quest_start": npc.quest.id if hasattr(npc.quest, 'id') else "quest_1"})
        
                self.dialogue_tree.add_node("quest_decline", "I understand. If you change your mind, I'll be here.", [
                    ("Let's talk about something else.", "start"),
                    ("Goodbye for now.", "exit")
                ])
        
            if hasattr(npc, 'has_shop') and npc.has_shop:
                self.dialogue_tree.add_node("shop", "Take a look at what I have available.", [
                    ("Let me see.", "shop_open"),
                    ("Maybe later.", "start")
                ])
        
                self.dialogue_tree.add_node("shop_open", "Here's what I have in stock.", [
                    ("Let's talk about something else.", "start"),
                    ("Goodbye.", "exit")
                ], {"open_shop": True})
    
            self.dialogue_tree.add_node("exit", "See you around!", [], {"end_dialogue": True})
        
            self.active_dialogue = self.dialogue_tree.get_node("start")
            return self.active_dialogue
    
    def choose_response(self, index):
        """Select a dialogue response"""
        if not self.active_dialogue or not self.dialogue_tree:
            return None
        
        # Get actions from current node
        actions = self.active_dialogue.get_actions()
        self.process_actions(actions)
    
        # Get next dialogue node
        next_node = None
        if 0 <= index < len(self.active_dialogue.responses):
            _, next_node_id = self.active_dialogue.responses[index]
            next_node = self.dialogue_tree.get_node(next_node_id)
    
        # Update active dialogue
        self.active_dialogue = next_node
        
        # Process actions from new node
        if self.active_dialogue:
            actions = self.active_dialogue.get_actions()
            self.process_actions(actions)
    
        return self.active_dialogue

    def process_actions(self, actions):
        """Process any actions from the dialogue"""
        if not actions:
            return
            
        if "quest_start" in actions and self.current_npc and self.player:
            quest_id = actions["quest_start"]
            self.current_npc.offer_quest(self.player)
            # In a real game, you'd find the quest by ID
            
        if "quest_complete" in actions and self.player:
            quest_id = actions["quest_complete"]
            self.player.complete_quest(quest_id)
            
        if "give_item" in actions and self.player:
            item_id = actions["give_item"]
            # In a real game, you'd create the item and add it to inventory
            # item = Item.create(item_id)
            # self.player.add_to_inventory(item)
            
        if "give_credits" in actions and self.player:
            amount = actions["give_credits"]
            self.player.credits += amount
            
        if "take_credits" in actions and self.player:
            amount = actions["take_credits"]
            if self.player.credits >= amount:
                self.player.credits -= amount
                
        if "change_reputation" in actions and self.player:
            for faction, amount in actions["change_reputation"].items():
                if faction in self.player.reputation:
                    self.player.reputation[faction] += amount
                    
        if "set_flag" in actions:
            flag_name = actions["set_flag"]
            self.game_flags[flag_name] = True
            
        if "check_flag" in actions:
            flag_check = actions["check_flag"]
            flag_name = list(flag_check.keys())[0]
            if flag_name != "else":
                if flag_name in self.game_flags and self.game_flags[flag_name]:
                    # Set current node to the next node if flag is true
                    self.active_dialogue.current_node = flag_check[flag_name]
                else:
                    # Set current node to else path
                    self.active_dialogue.current_node = flag_check["else"]
        
        if "open_shop" in actions and self.current_npc:
            # In a real game, you'd open the shop interface
            pass
            
        if "end_dialogue" in actions:
            self.end_dialogue()
    
    def end_dialogue(self):
        """End the current dialogue"""
        self.active_dialogue = None
        self.current_npc = None
    
    def is_dialogue_active(self):
        """Check if a dialogue is currently active"""
        return self.active_dialogue is not None
    
    def draw(self, screen):
        """Draw the dialogue UI"""
        if not self.active_dialogue:
            return
            
        node = self.active_dialogue
        
        # Create dialogue box
        box_width = self.screen_width - 100
        text_height = self.font.get_height() * len(node.responses)
        box_height = 150 + text_height
        
        box_x = 50
        box_y = self.screen_height - box_height - 20
        
        # Draw dialogue box background
        dialogue_box = pygame.Rect(box_x, box_y, box_width, box_height)
        pygame.draw.rect(screen, (0, 0, 0), dialogue_box)
        pygame.draw.rect(screen, (255, 255, 255), dialogue_box, 2)
        
        # Draw NPC name
        if self.current_npc:
            name_text = self.name_font.render(self.current_npc.name, True, (255, 255, 255))
            screen.blit(name_text, (box_x + 20, box_y + 15))
        
        # Draw dialogue text
        text_lines = self._wrap_text(node.text, box_width - 40)
        for i, line in enumerate(text_lines):
            text_surface = self.font.render(line, True, (255, 255, 255))
            screen.blit(text_surface, (box_x + 20, box_y + 50 + i * 30))
        
        # Draw response options
        y_offset = 50 + len(text_lines) * 30 + 20
        for i, (response_text, _) in enumerate(node.responses):
            # Highlight the option if mouse is hovering over it
            color = (200, 200, 200)
            response_rect = pygame.Rect(box_x + 20, box_y + y_offset + i * 30, box_width - 40, 30)
            
            mouse_x, mouse_y = pygame.mouse.get_pos()
            if response_rect.collidepoint(mouse_x, mouse_y):
                color = (255, 255, 0)
                pygame.draw.rect(screen, (50, 50, 50), response_rect)
            
            response_surface = self.font.render(f"{i+1}. {response_text}", True, color)
            screen.blit(response_surface, (box_x + 20, box_y + y_offset + i * 30))
    
    def handle_click(self, pos):
        """Handle mouse clicks on dialogue options"""
        if not self.active_dialogue:
            return False
            
        node = self.active_dialogue
        box_width = self.screen_width - 100
        text_height = self.font.get_height() * len(node.responses)
        box_height = 150 + text_height
        
        box_x = 50
        box_y = self.screen_height - box_height - 20
        
        # Calculate where response options start
        text_lines = self._wrap_text(node.text, box_width - 40)
        y_offset = 50 + len(text_lines) * 30 + 20
        
        # Check each response option
        for i, _ in enumerate(node.responses):
            response_rect = pygame.Rect(box_x + 20, box_y + y_offset + i * 30, box_width - 40, 30)
            if response_rect.collidepoint(pos):
                self.choose_response(i)
                return True
        
        return False
    
    def handle_key(self, key):
        """Handle keyboard input for dialogue"""
        if not self.active_dialogue:
            return False
            
        # Number keys 1-9 for selecting responses
        if pygame.K_1 <= key <= pygame.K_9:
            index = key - pygame.K_1
            if index < len(self.active_dialogue.responses):
                self.choose_response(index)
                return True
        
        return False
    
    def _wrap_text(self, text, max_width):
        """Wrap text to fit within width"""
        words = text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            if self.font.size(test_line)[0] <= max_width:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines


class QuestManager:
    def __init__(self):
        self.quests = {}
        self.active_quests = []
        self.completed_quests = []
    
    def add_quest(self, quest):
        """Add a quest to the manager"""
        self.quests[quest.id] = quest
    
    def start_quest(self, quest_id, player):
        """Start a quest for the player"""
        if quest_id in self.quests and quest_id not in self.active_quests:
            quest = self.quests[quest_id]
            if quest.is_available([q.id for q in self.completed_quests]):
                self.active_quests.append(quest_id)
                player.quests.append(quest)
                return True
        return False
    
    def complete_quest(self, quest_id, player):
        """Complete a quest and give rewards"""
        if quest_id in self.active_quests:
            quest = self.quests[quest_id]
            if player.complete_quest(quest_id):
                self.active_quests.remove(quest_id)
                self.completed_quests.append(quest)
                return True
        return False
    
    def update_objective(self, quest_id, objective_index, progress, player):
        """Update progress on a quest objective"""
        if quest_id in self.active_quests:
            quest = self.quests[quest_id]
            if quest.update_objective(objective_index, progress):
                # Quest is complete
                return self.complete_quest(quest_id, player)
        return False
    
    def load_quests_from_json(self, filename):
        """Load quests from a JSON file"""
        with open(os.path.join('assets', 'quests', filename), 'r') as file:
            data = json.load(file)
        
        for quest_data in data["quests"]:
            quest = Quest(
                quest_data["id"],
                quest_data["title"],
                quest_data["description"],
                quest_data["objectives"]
            )
            
            quest.objective_targets = quest_data.get("objective_targets", [1] * len(quest.objectives))
            quest.credit_reward = quest_data.get("credit_reward", 0)
            quest.xp_reward = quest_data.get("xp_reward", 0)
            quest.reputation_changes = quest_data.get("reputation_changes", {})
            quest.prerequisite_quests = quest_data.get("prerequisite_quests", [])
            
            # Would also handle item rewards here
            
            self.add_quest(quest)


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
# dialogue_manager = DialogueManager(800, 600)
# dialogue_manager.start_dialogue(npc, player)
# 
# quest_manager = QuestManager()
# quest = Quest("q001", "Helping Hand", "Help the locals with their problems", ["Talk to Mayor Gus", "Collect 5 supplies"])
# quest_manager.add_quest(quest)
# quest_manager.start_quest("q001", player)
