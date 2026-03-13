"""
MAFLEX Gaming Universe - Backend Integration
Enhanced games module with power system integration
"""

import json
import uuid
import random
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Any, Optional


class PowerSystem:
    """Central power management for Maflex"""

    POWER_COSTS = {
        'insight': 15,
        'sight': 10,
        'manifest': 25,
        'avatar': 50,
        'adjust': 30
    }

    @staticmethod
    def can_use_power(user_energy: int, power: str) -> bool:
        return user_energy >= PowerSystem.POWER_COSTS.get(power, 999)

    @staticmethod
    def use_power(user_energy: int, power: str) -> tuple:
        """Returns (success, new_energy, effect_description)"""
        if not PowerSystem.can_use_power(user_energy, power):
            return False, user_energy, "Insufficient energy"

        cost = PowerSystem.POWER_COSTS[power]
        new_energy = user_energy - cost

        effects = {
            'insight': PowerSystem._insight_effect,
            'sight': PowerSystem._sight_effect,
            'manifest': PowerSystem._manifest_effect,
            'avatar': PowerSystem._avatar_effect,
            'adjust': PowerSystem._adjust_effect
        }

        effect_desc = effects.get(power, lambda: "Unknown power")()
        return True, new_energy, effect_desc

    @staticmethod
    def _insight_effect() -> str:
        predictions = [
            "Victory is within reach if you strike now",
            "Retreat would be wise - danger approaches",
            "A hidden opportunity awaits in the east",
            "Your next action will have amplified effects",
            "Alliance suggested - enemies share a weakness"
        ]
        return f"Temporal Insight: {random.choice(predictions)}"

    @staticmethod
    def _sight_effect() -> str:
        return "Data Sight reveals: Enemy HP 73%, Weakness: Fire, Secret loot nearby"

    @staticmethod
    def _manifest_effect() -> str:
        items = ['Health Potion', 'Energy Crystal', 'Mystery Box', 'Power Shard', 'Time Fragment']
        return f"Manifested: {random.choice(items)}"

    @staticmethod
    def _avatar_effect() -> str:
        return "Avatar Mode: Physical presence in game world established"

    @staticmethod
    def _adjust_effect() -> str:
        return "World-State: Reality parameters now adjustable"


class Game(ABC):
    """Abstract base class for all Maflex games"""

    def __init__(self, game_id=None, user_id=None):
        self.game_id = game_id or str(uuid.uuid4())
        self.user_id = user_id
        self.created_at = datetime.now().isoformat()
        self.energy = 100
        self.active_powers = []
        self.game_state = {}
        self.history = []

    @abstractmethod
    def start(self) -> str:
        """Initialize game and return opening description"""
        pass

    @abstractmethod
    def process_action(self, user_id: str, action: str, args: List[str]) -> str:
        """Process a player action"""
        pass

    @abstractmethod
    def get_state(self, user_id: str) -> Dict[str, Any]:
        """Get current game state for display"""
        pass

    def use_power(self, user_id: str, power: str, args: List[str] = None) -> Dict:
        """Use a Maflex power"""
        success, new_energy, effect = PowerSystem.use_power(self.energy, power)

        if success:
            self.energy = new_energy
            self.active_powers.append({
                'power': power,
                'activated_at': datetime.now().isoformat(),
                'effect': effect
            })

            # Power-specific game modifications
            if power == 'insight':
                return self._apply_insight(args)
            elif power == 'sight':
                return self._apply_sight(args)
            elif power == 'manifest':
                return self._apply_manifest(args)
            elif power == 'avatar':
                return self._apply_avatar(args)
            elif power == 'adjust':
                return self._apply_adjust(args)

        return {
            'success': success,
            'energy': self.energy,
            'result': effect,
            'game_modified': False
        }

    def _apply_insight(self, args):
        """Override in subclasses for game-specific insight"""
        return {'success': True, 'energy': self.energy, 'result': 'Insight activated', 'game_modified': True}

    def _apply_sight(self, args):
        """Override in subclasses for game-specific sight"""
        return {'success': True, 'energy': self.energy, 'result': 'Sight activated', 'game_modified': True}

    def _apply_manifest(self, args):
        """Override in subclasses for game-specific manifestation"""
        return {'success': True, 'energy': self.energy, 'result': 'Item manifested', 'game_modified': True}

    def _apply_avatar(self, args):
        """Override in subclasses for game-specific avatar"""
        return {'success': True, 'energy': self.energy, 'result': 'Avatar mode active', 'game_modified': True}

    def _apply_adjust(self, args):
        """Override in subclasses for game-specific adjustment"""
        return {'success': True, 'energy': self.energy, 'result': 'World adjusted', 'game_modified': True}

    def to_dict(self) -> Dict:
        return {
            'game_id': self.game_id,
            'type': self.__class__.__name__,
            'energy': self.energy,
            'active_powers': self.active_powers,
            'game_state': self.game_state,
            'history': self.history[-50:]  # Keep last 50 actions
        }

    @classmethod
    def from_dict(cls, data: Dict):
        raise NotImplementedError


class MedievalRPG(Game):
    """Enhanced Medieval RPG with full power integration"""

    def __init__(self, game_id=None, user_id=None):
        super().__init__(game_id, user_id)
        self.location = 'village'
        self.player = {
            'hp': 100,
            'max_hp': 100,
            'level': 1,
            'xp': 0,
            'inventory': ['rusty_sword', 'health_potion'],
            'equipment': {'weapon': 'rusty_sword', 'armor': None},
            'stats': {'strength': 10, 'agility': 10, 'intelligence': 10}
        }
        self.world = {
            'village': {
                'name': 'Oakhaven Village',
                'description': 'A peaceful village with a mysterious aura.',
                'connections': {'north': 'forest', 'east': 'cave'},
                'npcs': ['elder', 'merchant', 'mysterious_stranger'],
                'items': ['herbs'],
                'enemies': []
            },
            'forest': {
                'name': 'Whispering Woods',
                'description': 'Ancient trees whisper secrets of the past.',
                'connections': {'south': 'village', 'east': 'ruins', 'north': 'mountain'},
                'npcs': ['hermit'],
                'items': ['mushrooms', 'ancient_coin'],
                'enemies': [
                    {'name': 'goblin', 'hp': 30, 'max_hp': 30, 'damage': 8, 'xp': 15, 'weakness': 'fire'},
                    {'name': 'wolf', 'hp': 25, 'max_hp': 25, 'damage': 10, 'xp': 12, 'weakness': 'silver'}
                ]
            },
            'cave': {
                'name': 'Crystal Cavern',
                'description': 'Glowing crystals illuminate dark secrets.',
                'connections': {'west': 'village', 'down': 'depths'},
                'npcs': [],
                'items': ['crystal_shard'],
                'enemies': [
                    {'name': 'cave_bear', 'hp': 60, 'max_hp': 60, 'damage': 15, 'xp': 30, 'weakness': 'light'},
                    {'name': 'bat_swarm', 'hp': 20, 'max_hp': 20, 'damage': 5, 'xp': 8, 'weakness': 'fire'}
                ]
            },
            'ruins': {
                'name': 'Ancient Ruins',
                'description': 'Forgotten magic lingers in crumbling stones.',
                'connections': {'west': 'forest'},
                'npcs': ['ghost_king'],
                'items': ['magic_scroll', 'cursed_ring'],
                'enemies': [
                    {'name': 'skeleton', 'hp': 40, 'max_hp': 40, 'damage': 12, 'xp': 20, 'weakness': 'holy'},
                    {'name': 'shadow_wraith', 'hp': 35, 'max_hp': 35, 'damage': 14, 'xp': 25, 'weakness': 'light'}
                ]
            },
            'mountain': {
                'name': "Dragon's Peak",
                'description': 'Treacherous paths lead to legendary treasures.',
                'connections': {'south': 'forest'},
                'npcs': ['dragon_sage'],
                'items': ['dragon_scale'],
                'enemies': [
                    {'name': 'mountain_troll', 'hp': 80, 'max_hp': 80, 'damage': 20, 'xp': 50, 'weakness': 'fire'},
                    {'name': 'young_dragon', 'hp': 120, 'max_hp': 120, 'damage': 25, 'xp': 100, 'weakness': 'ice'}
                ]
            }
        }
        self.quests = {
            'main': {'name': 'The Prophecy', 'stage': 0, 'completed': False},
            'side': []
        }
        self.flags = {}

    def start(self) -> str:
        return """🏰 Welcome to Medieval RPG 🏰

You awaken in Oakhaven Village, a place of both peace and mystery. 
Legends speak of ancient powers slumbering beneath these lands...

Your journey begins here. Type 'help' for commands or ask IRIS for guidance.

Current Location: Village Square
HP: 100/100 | Energy: 100 | Level: 1

What do you do?"""

    def process_action(self, user_id: str, action: str, args: List[str]) -> str:
        action = action.lower().strip()

        # Movement
        if action in ['go', 'move', 'travel', 'walk']:
            return self._handle_movement(args[0] if args else '')

        # Combat
        if action in ['attack', 'fight', 'strike', 'kill']:
            return self._handle_combat(args[0] if args else '')

        # Items
        if action in ['use', 'consume', 'drink', 'eat']:
            return self._handle_use(' '.join(args))

        if action in ['take', 'get', 'pick', 'grab']:
            return self._handle_take(' '.join(args))

        if action in ['inventory', 'inv', 'i', 'items']:
            return self._show_inventory()

        if action in ['equip', 'wear', 'wield']:
            return self._handle_equip(' '.join(args))

        # Information
        if action in ['look', 'examine', 'inspect', 'l']:
            return self._handle_look(args[0] if args else None)

        if action in ['talk', 'speak', 'chat', 'ask']:
            return self._handle_talk(' '.join(args))

        if action in ['status', 'stats', 'character']:
            return self._show_status()

        if action in ['map', 'where', 'location']:
            return self._show_map()

        # Special
        if action in ['rest', 'sleep', 'recover']:
            return self._handle_rest()

        if action in ['help', '?', 'commands']:
            return self._show_help()

        if action in ['save']:
            return "Game saved! (Auto-save is enabled)"

        # IRIS integration commands
        if action in ['iris', 'guide', 'advice']:
            return "IRIS is listening. She can help you with tips, powers, or game mechanics."

        return f"Unknown command: '{action}'. Type 'help' for available commands."

    def _handle_movement(self, direction: str) -> str:
        if not direction:
            return "Go where? Available directions: " + ', '.join(self.world[self.location]['connections'].keys())

        direction = direction.lower()
        connections = self.world[self.location]['connections']

        if direction in connections:
            new_location = connections[direction]
            self.location = new_location
            loc_data = self.world[new_location]

            # Random encounter chance
            encounter = ""
            if loc_data['enemies'] and random.random() < 0.3:
                enemy = random.choice(loc_data['enemies'])
                encounter = f"\n\n⚠️ A {enemy['name'].replace('_', ' ')} appears! Prepare for battle or flee!"

            return f"You travel {direction} to {loc_data['name']}.\n\n{loc_data['description']}{encounter}"

        return f"You cannot go '{direction}'. Available: {', '.join(connections.keys())}"

    def _handle_combat(self, target: str) -> str:
        location = self.world[self.location]

        if not location['enemies']:
            return "There are no enemies here to fight."

        if not target:
            return "Attack what? Enemies present: " + ', '.join([e['name'].replace('_', ' ') for e in location['enemies']])

        # Find enemy
        enemy = None
        for e in location['enemies']:
            if target.lower() in e['name'].replace('_', ' ').lower():
                enemy = e
                break

        if not enemy:
            return f"No enemy matching '{target}' found."

        # Combat calculation
        weapon_damage = 10
        if self.player['equipment']['weapon']:
            weapon_damage = {'rusty_sword': 12, 'iron_sword': 18, 'magic_blade': 25}.get(self.player['equipment']['weapon'], 10)

        # Check weakness
        weakness_bonus = 0
        if 'active_powers' in dir(self):
            for power in self.active_powers:
                if power['power'] == 'sight':
                    weakness_bonus = weapon_damage * 0.5
                    break

        total_damage = weapon_damage + weakness_bonus + random.randint(-2, 3)
        enemy['hp'] -= total_damage

        result = f"⚔️ You strike the {enemy['name'].replace('_', ' ')} for {total_damage} damage!"

        if enemy['hp'] <= 0:
            # Enemy defeated
            location['enemies'].remove(enemy)
            xp_gain = enemy['xp']
            self.player['xp'] += xp_gain

            # Level up check
            level_up = ""
            if self.player['xp'] >= self.player['level'] * 100:
                self.player['level'] += 1
                self.player['max_hp'] += 20
                self.player['hp'] = self.player['max_hp']
                self.player['stats']['strength'] += 2
                self.player['stats']['agility'] += 2
                level_up = f"\n🎉 LEVEL UP! You are now level {self.player['level']}!"

            result += f"\n💀 Enemy defeated! Gained {xp_gain} XP.{level_up}"
        else:
            # Enemy counter-attack
            damage_taken = max(0, enemy['damage'] - random.randint(0, 3))
            if self.player['equipment']['armor']:
                damage_taken = max(0, damage_taken - 5)

            self.player['hp'] -= damage_taken
            result += f"\n🩸 Enemy hits you for {damage_taken} damage! Your HP: {self.player['hp']}/{self.player['max_hp']}"

            if self.player['hp'] <= 0:
                result += "\n\n💀 You have fallen! But death is not the end in Maflex... You awaken back in the village."
                self.player['hp'] = self.player['max_hp'] // 2
                self.location = 'village'

        return result

    def _handle_use(self, item: str) -> str:
        if not item:
            return "Use what? Check your inventory."

        item_key = item.lower().replace(' ', '_')

        if item_key not in self.player['inventory']:
            return f"You don't have '{item}'."

        if item_key == 'health_potion':
            heal = 30
            old_hp = self.player['hp']
            self.player['hp'] = min(self.player['max_hp'], self.player['hp'] + heal)
            actual_heal = self.player['hp'] - old_hp
            self.player['inventory'].remove(item_key)
            return f"🧪 You drink the health potion. Restored {actual_heal} HP! ({self.player['hp']}/{self.player['max_hp']})"

        if item_key == 'crystal_shard':
            self.energy = min(100, self.energy + 20)
            self.player['inventory'].remove(item_key)
            return f"💎 Crystal Shard absorbed! Energy +20 (Total: {self.energy})"

        if item_key == 'magic_scroll':
            self.player['stats']['intelligence'] += 3
            self.player['inventory'].remove(item_key)
            return "📜 Magic Scroll consumed! Intelligence +3"

        return f"You use the {item}. Nothing special happens."

    def _handle_take(self, item: str) -> str:
        location = self.world[self.location]

        if not item:
            available = location['items'] + [e['name'].replace('_', ' ') + ' (corpse)' for e in location['enemies'] if e['hp'] <= 0]
            return f"Take what? Available: {', '.join(available) if available else 'Nothing'}"

        item_key = item.lower().replace(' ', '_')

        if item_key in location['items']:
            self.player['inventory'].append(item_key)
            location['items'].remove(item_key)
            return f"✅ You picked up: {item}"

        return f"Cannot take '{item}'."

    def _show_inventory(self) -> str:
        inv = self.player['inventory']
        if not inv:
            return "📦 Your inventory is empty."

        items_formatted = [item.replace('_', ' ').title() for item in inv]
        return f"📦 Inventory ({len(inv)} items):\n" + '\n'.join([f"  • {i}" for i in items_formatted])

    def _handle_equip(self, item: str) -> str:
        if not item:
            return "Equip what?"

        item_key = item.lower().replace(' ', '_')

        if item_key not in self.player['inventory']:
            return f"You don't have '{item}'."

        # Determine slot
        weapons = ['rusty_sword', 'iron_sword', 'magic_blade', 'dagger', 'spear']
        armor = ['leather_armor', 'chain_mail', 'plate_armor', 'mage_robe']

        if item_key in weapons:
            old = self.player['equipment']['weapon']
            self.player['equipment']['weapon'] = item_key
            return f"⚔️ Equipped {item} as weapon." + (f" (Replaced {old.replace('_', ' ')})" if old else "")

        if item_key in armor:
            old = self.player['equipment']['armor']
            self.player['equipment']['armor'] = item_key
            return f"🛡️ Equipped {item} as armor." + (f" (Replaced {old.replace('_', ' ')})" if old else "")

        return f"Cannot equip '{item}'."

    def _handle_look(self, target: str) -> str:
        location = self.world[self.location]

        if not target:
            # Look at room
            enemies_desc = ""
            if location['enemies']:
                enemies_desc = "\n\nEnemies present: " + ', '.join([f"{e['name'].replace('_', ' ')} (HP: {e['hp']}/{e['max_hp']})" for e in location['enemies']])

            items_desc = ""
            if location['items']:
                items_desc = "\n\nItems here: " + ', '.join(location['items'])

            npcs_desc = ""
            if location['npcs']:
                npcs_desc = "\n\nPeople: " + ', '.join(location['npcs'])

            return f"📍 {location['name']}\n{location['description']}\n\nExits: {', '.join(location['connections'].keys())}{enemies_desc}{items_desc}{npcs_desc}"

        # Look at specific thing
        for enemy in location['enemies']:
            if target.lower() in enemy['name'].replace('_', ' ').lower():
                weakness_info = ""
                for power in self.active_powers:
                    if power['power'] == 'sight':
                        weakness_info = f"\n💡 WEAKNESS DETECTED: {enemy['weakness'].upper()}"
                        break
                return f"👁️ {enemy['name'].replace('_', ' ').title()}: HP {enemy['hp']}/{enemy['max_hp']}, Damage: {enemy['damage']}, XP: {enemy['xp']}{weakness_info}"

        return f"Don't see '{target}' here."

    def _handle_talk(self, npc: str) -> str:
        location = self.world[self.location]

        if not npc:
            return f"Talk to who? People here: {', '.join(location['npcs']) if location['npcs'] else 'No one'}"

        # NPC dialogues
        dialogues = {
            'elder': [
                "Elder: 'Welcome, traveler. Dark times approach. The ancient prophecy speaks of a hero...'",
                "Elder: 'Seek the Crystal Cavern to the east. There, you may find what you need.'",
                "Elder: 'Beware the dragon on the mountain. Only the worthy may challenge it.'"
            ],
            'merchant': [
                "Merchant: 'Got some fine wares today! Potions, weapons, mysteries...'",
                "Merchant: 'Rumor says there's treasure in the ruins. I'd go myself if I were younger!'",
                "Merchant: 'Your energy seems low. Buy a crystal shard? Only 50 gold!'"
            ],
            'mysterious_stranger': [
                "Stranger: *eyes glow* 'I know things. Things about the future. For a price...'",
                "Stranger: 'The infinity symbol... it appears to those who can reshape reality.'",
                "Stranger: 'Use your powers wisely, avatar. Energy is life here.'"
            ],
            'hermit': [
                "Hermit: 'Shhh! The trees are listening. They remember the old wars.'",
                "Hermit: 'I saw you in a dream. You wielded light against shadow.'"
            ],
            'ghost_king': [
                "Ghost King: 'MORTAL! Release me from this curse and I shall grant you my kingdom!'",
                "Ghost King: 'The cursed ring... it binds me. Take it if you dare.'"
            ],
            'dragon_sage': [
                "Dragon Sage: 'Young one, you smell of potential. And... something else. Power.'",
                "Dragon Sage: 'The five powers you wield are ancient. Older than this mountain.'"
            ]
        }

        for npc_key, texts in dialogues.items():
            if npc_key in location['npcs'] and npc.lower() in npc_key.replace('_', ' ').lower():
                return random.choice(texts)

        return f"Cannot talk to '{npc}'."

    def _show_status(self) -> str:
        p = self.player
        eq = p['equipment']
        return f"""📊 Character Status

Name: {self.user_id or 'Hero'}
Level: {p['level']} | XP: {p['xp']}/{p['level'] * 100}
HP: {p['hp']}/{p['max_hp']} | Energy: {self.energy}/100

Stats:
  STR: {p['stats']['strength']} | AGI: {p['stats']['agility']} | INT: {p['stats']['intelligence']}

Equipment:
  Weapon: {(eq['weapon'] or 'None').replace('_', ' ').title()}
  Armor: {(eq['armor'] or 'None').replace('_', ' ').title()}

Location: {self.world[self.location]['name']}
Active Powers: {len(self.active_powers)}"""

    def _show_map(self) -> str:
        return f"""🗺️ World Map

[Village] ← → [Cave]
    ↕
[Forest] ← → [Ruins]
    ↕
[Mountain]

Current: {self.world[self.location]['name']} ({self.location})

Use 'go <direction>' to travel."""

    def _handle_rest(self) -> str:
        if self.world[self.location]['enemies']:
            return "Cannot rest! Enemies are nearby!"

        heal = self.player['max_hp'] // 4
        old_hp = self.player['hp']
        self.player['hp'] = min(self.player['max_hp'], self.player['hp'] + heal)
        actual_heal = self.player['hp'] - old_hp

        # Energy regen
        old_energy = self.energy
        self.energy = min(100, self.energy + 10)

        return f"💤 You rest peacefully.\nHP +{actual_heal} | Energy +{self.energy - old_energy}"

    def _show_help(self) -> str:
        return """📜 Available Commands:

MOVEMENT:
  go <direction> - Move (north, south, east, west, up, down)
  map - Show world map

COMBAT:
  attack <enemy> - Fight an enemy

ITEMS:
  inventory - Show items
  use <item> - Consume/use item
  take <item> - Pick up item
  equip <item> - Wear/wield equipment

INFO:
  look - Examine location
  look <target> - Examine specific thing
  talk <npc> - Speak with someone
  status - Character stats

OTHER:
  rest - Recover HP and energy
  save - Save game
  iris - Call for IRIS guidance

POWERS (via IRIS panel):
  Temporal Insight, Data Sight, Manifestation, Avatar Mode, World Adjust"""

    def get_state(self, user_id: str) -> Dict:
        return {
            'location': self.location,
            'location_name': self.world[self.location]['name'],
            'player': self.player,
            'energy': self.energy,
            'active_powers': self.active_powers,
            'enemies_nearby': len(self.world[self.location]['enemies']) > 0,
            'quest_stage': self.quests['main']['stage']
        }

    # Power-specific overrides
    def _apply_insight(self, args):
        """Temporal Insight - predict combat outcomes"""
        location = self.world[self.location]
        if location['enemies']:
            enemy = location['enemies'][0]  # Predict for first enemy
            player_damage = 12 + self.player['stats']['strength'] // 2
            rounds_to_kill = enemy['hp'] // player_damage + 1
            rounds_to_die = self.player['hp'] // enemy['damage'] + 1

            if rounds_to_die > rounds_to_kill:
                prediction = f"Victory likely in {rounds_to_kill} rounds"
            else:
                prediction = "Warning: You may be defeated. Consider healing or fleeing."

            return {
                'success': True,
                'energy': self.energy,
                'result': f'🔮 {prediction}',
                'game_modified': True,
                'insight_data': {'enemy_hp': enemy['hp'], 'enemy_damage': enemy['damage']}
            }

        return {
            'success': True,
            'energy': self.energy,
            'result': '🔮 No immediate threats detected. Safe to explore.',
            'game_modified': False
        }

    def _apply_sight(self, args):
        """Data Sight - reveal hidden stats"""
        location = self.world[self.location]
        hidden_items = []

        # Reveal hidden items
        if self.location == 'forest' and 'hidden_cache' not in location['items']:
            location['items'].append('hidden_cache')
            hidden_items.append('hidden_cache')

        return {
            'success': True,
            'energy': self.energy,
            'result': f'👁️ Hidden revealed: Enemy weaknesses visible, secret items: {hidden_items}',
            'game_modified': True,
            'revealed_weaknesses': [e['weakness'] for e in location['enemies']],
            'secret_items': hidden_items
        }

    def _apply_manifest(self, args):
        """Controlled Manifestation - create items"""
        items = ['health_potion', 'crystal_shard', 'iron_sword', 'magic_scroll']
        if args and args[0].lower() in items:
            item = args[0].lower()
        else:
            item = random.choice(items)

        self.player['inventory'].append(item)

        return {
            'success': True,
            'energy': self.energy,
            'result': f'✨ Manifested: {item.replace("_", " ").title()}!',
            'game_modified': True,
            'manifested_item': item
        }

    def _apply_avatar(self, args):
        """Avatar Mode - enhanced presence"""
        # Boost stats temporarily
        self.player['stats']['strength'] += 5
        self.player['stats']['agility'] += 5

        return {
            'success': True,
            'energy': self.energy,
            'result': '🧑 Avatar Mode: Physical presence confirmed. Stats boosted!',
            'game_modified': True,
            'stat_boosts': {'strength': 5, 'agility': 5}
        }

    def _apply_adjust(self, args):
        """World-State Adjustment - change game parameters"""
        if args:
            adjustment = ' '.join(args).lower()

            if 'difficulty' in adjustment:
                if 'easy' in adjustment:
                    for e in self.world[self.location]['enemies']:
                        e['damage'] = max(1, e['damage'] // 2)
                    return {'success': True, 'energy': self.energy, 'result': '🌍 Difficulty lowered. Enemies weakened.', 'game_modified': True}

                if 'hard' in adjustment:
                    for e in self.world[self.location]['enemies']:
                        e['damage'] = int(e['damage'] * 1.5)
                    return {'success': True, 'energy': self.energy, 'result': '🌍 Difficulty raised. Enemies empowered.', 'game_modified': True}

            if 'heal' in adjustment or 'restore' in adjustment:
                self.player['hp'] = self.player['max_hp']
                return {'success': True, 'energy': self.energy, 'result': '🌍 World adjusted. Health fully restored.', 'game_modified': True}

        return {
            'success': True,
            'energy': self.energy,
            'result': '🌍 World-State ready. Options: difficulty easy/hard, heal, restore',
            'game_modified': False
        }

    def to_dict(self) -> Dict:
        data = super().to_dict()
        data.update({
            'location': self.location,
            'player': self.player,
            'world': self.world,
            'quests': self.quests
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict):
        game = cls(game_id=data['game_id'])
        game.energy = data.get('energy', 100)
        game.location = data.get('location', 'village')
        game.player = data.get('player', game.player)
        game.world = data.get('world', game.world)
        game.quests = data.get('quests', game.quests)
        game.active_powers = data.get('active_powers', [])
        return game


class GameManager:
    """Manages all active games in Maflex"""

    def __init__(self):
        self.active_games: Dict[str, Game] = {}
        self.game_registry = {
            'medieval-rpg': MedievalRPG,
            'cyber-arena': MedievalRPG,  # Placeholder - extend with actual classes
            'void-chess': MedievalRPG,
            'nebula-miner': MedievalRPG,
            'chronos-puzzle': MedievalRPG
        }

    def start_game(self, user_id: str, game_name: str, game_id: str = None) -> Optional[Game]:
        """Start a new game for a user"""
        if game_name not in self.game_registry:
            return None

        game_class = self.game_registry[game_name]
        game = game_class(game_id=game_id, user_id=user_id)
        self.active_games[user_id] = game
        return game

    def get_game(self, user_id: str) -> Optional[Game]:
        """Get user's active game"""
        return self.active_games.get(user_id)

    def end_game(self, user_id: str) -> bool:
        """End user's active game"""
        if user_id in self.active_games:
            del self.active_games[user_id]
            return True
        return False

    def save_game(self, user_id: str, db) -> bool:
        """Save game state to database"""
        game = self.active_games.get(user_id)
        if not game:
            return False

        state_json = json.dumps(game.to_dict())
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO game_saves (id, user_id, game_name, state, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET 
                state=excluded.state, 
                updated_at=CURRENT_TIMESTAMP
        """, (game.game_id, user_id, game.__class__.__name__, state_json))
        db.commit()
        return True

    def load_game(self, user_id: str, db, game_id: str = None) -> Optional[Game]:
        """Load game from database"""
        cursor = db.cursor()

        if game_id:
            cursor.execute(
                "SELECT * FROM game_saves WHERE id=? AND user_id=?", 
                (game_id, user_id)
            )
        else:
            cursor.execute(
                "SELECT * FROM game_saves WHERE user_id=? ORDER BY updated_at DESC LIMIT 1",
                (user_id,)
            )

        row = cursor.fetchone()
        if not row:
            return None

        game_name = row['game_name']
        state = json.loads(row['state'])

        # Restore appropriate class
        game_class = self.game_registry.get(game_name.lower().replace('rpg', '-rpg'), MedievalRPG)
        game = game_class.from_dict(state)
        self.active_games[user_id] = game
        return game

    def list_available_games(self) -> List[Dict]:
        """List all available game types"""
        return [
            {'id': 'medieval-rpg', 'name': 'Medieval RPG', 'description': 'Classic fantasy adventure'},
            {'id': 'cyber-arena', 'name': 'Cyber Arena', 'description': 'Neon combat simulation'},
            {'id': 'void-chess', 'name': 'Void Chess', 'description': 'Dimensional strategy'},
            {'id': 'nebula-miner', 'name': 'Nebula Miner', 'description': 'Space resource management'},
            {'id': 'chronos-puzzle', 'name': 'Chronos Puzzle', 'description': 'Time manipulation puzzles'}
        ]


# Global instance
game_manager = GameManager()