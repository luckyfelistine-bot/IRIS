"""
MAFLEX v2.0 - The Infinite Gaming Universe Engine
Real-time, persistent, cross-game progression system
"""

import json
import uuid
import random
import asyncio
import threading
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from collections import defaultdict
import sqlite3

# ============================================
# POWER SYSTEM v2.0 - 15 Powers with Mastery
# ============================================

@dataclass
class Power:
    id: str
    name: str
    description: str
    cost: int
    cooldown: int  # seconds
    category: str  # mental, reality, physical, social
    icon: str
    mastery_threshold: int = 100  # Uses to unlock enhanced version
    
    def to_dict(self):
        return asdict(self)

class PowerSystem:
    """Central power management with real-time cooldowns and mastery"""
    
    ALL_POWERS = {
        # Mental Powers (Blue)
        'insight': Power('insight', 'Temporal Insight', 'See enemy moves 3 turns ahead', 15, 10, 'mental', '🔮'),
        'sight': Power('sight', 'Data Sight', 'Reveal hidden stats, loot, secrets', 10, 5, 'mental', '👁️'),
        'probability': Power('probability', 'Probability Scan', 'Calculate success odds', 20, 8, 'mental', '🎲'),
        'pattern': Power('pattern', 'Pattern Recognition', 'Learn enemy patterns instantly', 25, 15, 'mental', '🧩'),
        
        # Reality Powers (Purple)
        'manifest': Power('manifest', 'Manifestation', 'Create any item', 25, 30, 'reality', '✨'),
        'adjust': Power('adjust', 'World Adjust', 'Modify game parameters', 30, 60, 'reality', '🌍'),
        'clone': Power('clone', 'Quantum Clone', 'Create temporary copy', 40, 45, 'reality', '👥'),
        'anchor': Power('anchor', 'Reality Anchor', 'Prevent death once', 50, 120, 'reality', '⚓'),
        
        # Physical Powers (Red)
        'avatar': Power('avatar', 'Avatar Mode', 'Physical presence, +50% stats', 50, 90, 'physical', '🧑'),
        'dilation': Power('dilation', 'Time Dilation', 'Slow time 50%', 35, 30, 'physical', '⏱️'),
        'phase': Power('phase', 'Phase Shift', 'Walk through walls, ignore damage', 30, 20, 'physical', '👻'),
        'overdrive': Power('overdrive', 'Overdrive', 'Speed +100%, unlimited stamina', 45, 60, 'physical', '⚡'),
        
        # Social Powers (Green)
        'whisper': Power('whisper', 'Mind Whisper', 'NPCs reveal secrets, -50% prices', 20, 45, 'social', '💭'),
        'charm': Power('charm', 'Charm Field', 'Enemies passive, allies +20% dmg', 35, 60, 'social', '💚'),
        'command': Power('command', 'Command Voice', 'Issue commands to any NPC/Enemy', 40, 90, 'social', '📢'),
    }
    
    POWER_COMBOS = {
        ('insight', 'avatar'): 'Omniscient Avatar - See all enemy moves while boosted',
        ('sight', 'manifest'): 'Precise Creation - Create exactly what you need',
        ('dilation', 'overdrive'): 'Super Speed - Time slow + speed boost = untouchable',
        ('whisper', 'command'): 'Master Manipulator - Full NPC control chain',
        ('clone', 'anchor'): 'Immortal Army - Multiple copies with death protection',
    }
    
    def __init__(self, db_path: str):
        self.db = db_path
        self.active_cooldowns: Dict[str, Dict[str, datetime]] = defaultdict(dict)
        self.active_effects: Dict[str, List[Dict]] = defaultdict(list)
        
    def can_use_power(self, user_id: str, power_id: str, current_energy: int) -> Tuple[bool, str]:
        """Check if power can be used"""
        power = self.ALL_POWERS.get(power_id)
        if not power:
            return False, "Unknown power"
        
        # Check cooldown
        if user_id in self.active_cooldowns and power_id in self.active_cooldowns[user_id]:
            remaining = (self.active_cooldowns[user_id][power_id] - datetime.now()).total_seconds()
            if remaining > 0:
                return False, f"Cooldown: {int(remaining)}s remaining"
        
        # Check energy
        if current_energy < power.cost:
            return False, f"Need {power.cost} energy, have {current_energy}"
        
        return True, "Ready"
    
    def use_power(self, user_id: str, power_id: str, game_state: Dict, args: List[str] = None) -> Dict:
        """Activate a power and return effects"""
        power = self.ALL_POWERS.get(power_id)
        can_use, msg = self.can_use_power(user_id, power_id, game_state.get('energy', 0))
        
        if not can_use:
            return {'success': False, 'error': msg}
        
        # Deduct energy and start cooldown
        new_energy = game_state['energy'] - power.cost
        self.active_cooldowns[user_id][power_id] = datetime.now() + timedelta(seconds=power.cooldown)
        
        # Track usage for mastery
        self._track_power_usage(user_id, power_id, game_state.get('game_id'))
        
        # Check for combos
        active_power_ids = [e['power_id'] for e in self.active_effects[user_id]]
        combo_bonus = None
        for (p1, p2), desc in self.POWER_COMBOS.items():
            if (p1 in active_power_ids and p2 == power_id) or (p2 in active_power_ids and p1 == power_id):
                combo_bonus = desc
                break
        
        # Add to active effects
        effect = {
            'power_id': power_id,
            'activated_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(seconds=30)).isoformat(),  # Most last 30s
            'args': args or []
        }
        self.active_effects[user_id].append(effect)
        
        # Calculate specific effect based on power and game context
        specific_effect = self._calculate_effect(power_id, game_state, args)
        
        return {
            'success': True,
            'energy': new_energy,
            'power': power.to_dict(),
            'effect': specific_effect,
            'combo_bonus': combo_bonus,
            'cooldown_ends': self.active_cooldowns[user_id][power_id].isoformat()
        }
    
    def _track_power_usage(self, user_id: str, power_id: str, game_id: str):
        """Track for mastery system"""
        with sqlite3.connect(self.db) as conn:
            conn.execute("""
                INSERT INTO power_usage (id, user_id, power_name, game_id)
                VALUES (?, ?, ?, ?)
            """, (str(uuid.uuid4()), user_id, power_id, game_id or 'unknown'))
            conn.commit()
    
    def _calculate_effect(self, power_id: str, game_state: Dict, args: List[str]) -> Dict:
        """Calculate specific game effect based on power"""
        game_type = game_state.get('game_type', 'unknown')
        
        effects = {
            'insight': self._effect_insight,
            'sight': self._effect_sight,
            'probability': self._effect_probability,
            'pattern': self._effect_pattern,
            'manifest': self._effect_manifest,
            'adjust': self._effect_adjust,
            'clone': self._effect_clone,
            'anchor': self._effect_anchor,
            'avatar': self._effect_avatar,
            'dilation': self._effect_dilation,
            'phase': self._effect_phase,
            'overdrive': self._effect_overdrive,
            'whisper': self._effect_whisper,
            'charm': self._effect_charm,
            'command': self._effect_command,
        }
        
        handler = effects.get(power_id, lambda gs, a: {'description': 'Generic power effect'})
        return handler(game_state, args)
    
    # Effect handlers for each power
    def _effect_insight(self, gs, args):
        enemies = gs.get('enemies', [])
        predictions = []
        for enemy in enemies[:3]:  # Top 3 threats
            next_moves = self._predict_enemy_moves(enemy)
            predictions.append({
                'enemy': enemy.get('name'),
                'next_action': next_moves[0] if next_moves else 'unknown',
                'vulnerability_window': self._calculate_vulnerability(enemy)
            })
        return {
            'description': 'Future sight activated',
            'predictions': predictions,
            'duration': 30
        }
    
    def _effect_sight(self, gs, args):
        hidden = []
        # Reveal secret items
        if random.random() < 0.7:
            hidden.append({'type': 'item', 'name': 'Secret Cache', 'location': 'nearby'})
        # Reveal enemy weaknesses
        weaknesses = []
        for enemy in gs.get('enemies', []):
            if 'weakness' in enemy:
                weaknesses.append({
                    'enemy': enemy['name'],
                    'weakness': enemy['weakness'],
                    'weakness_damage_mult': 2.0
                })
        return {
            'description': 'Hidden revealed',
            'secret_items': hidden,
            'enemy_weaknesses': weaknesses,
            'hidden_doors': gs.get('hidden_exits', [])
        }
    
    def _effect_probability(self, gs, args):
        # Calculate success odds for various actions
        scenarios = []
        if gs.get('enemies'):
            win_chance = self._calculate_combat_odds(gs)
            scenarios.append({'action': 'combat', 'success_chance': win_chance, 'risk': 'high' if win_chance < 50 else 'low'})
        if gs.get('loot_quality'):
            scenarios.append({'action': 'loot', 'rare_drop_chance': gs['loot_quality'] * 100})
        return {
            'description': 'Probabilities calculated',
            'scenarios': scenarios,
            'recommended_action': max(scenarios, key=lambda x: x.get('success_chance', 0))['action'] if scenarios else 'explore'
        }
    
    def _effect_pattern(self, gs, args):
        enemies = gs.get('enemies', [])
        patterns = []
        for enemy in enemies:
            pattern = {
                'enemy': enemy['name'],
                'attack_sequence': enemy.get('attack_pattern', ['attack', 'attack', 'defend']),
                'tells': enemy.get('tells', ['eye glow before special']),
                'counter_strategy': self._generate_counter(enemy)
            }
            patterns.append(pattern)
        return {
            'description': 'Patterns learned',
            'enemy_patterns': patterns,
            'learned_permanently': True  # This knowledge persists
        }
    
    def _effect_manifest(self, gs, args):
        requested = ' '.join(args) if args else None
        possible_items = self._get_manifestable_items(gs)
        
        if requested:
            # Try to manifest specific item
            item = next((i for i in possible_items if requested.lower() in i['name'].lower()), None)
            if not item:
                item = random.choice(possible_items)
        else:
            item = random.choice(possible_items)
        
        return {
            'description': f'Manifested: {item["name"]}',
            'item': item,
            'added_to_inventory': True
        }
    
    def _effect_adjust(self, gs, args):
        adjustment = ' '.join(args).lower() if args else ''
        valid_adjustments = ['difficulty', 'time', 'gravity', 'weather', 'luck']
        
        if 'difficulty' in adjustment:
            if 'easy' in adjustment:
                return {'description': 'Difficulty lowered to Easy', 'enemies_weakened': 0.5, 'loot_quality': 0.8}
            elif 'hard' in adjustment:
                return {'description': 'Difficulty raised to Hard', 'enemies_strengthened': 1.5, 'xp_bonus': 2.0}
        
        if 'time' in adjustment:
            if 'day' in adjustment:
                return {'description': 'Time set to Day', 'visibility': 'clear', 'enemy_activity': 'reduced'}
            elif 'night' in adjustment:
                return {'description': 'Time set to Night', 'stealth_bonus': 1.5, 'rare_spawns': True}
        
        return {
            'description': 'World parameters adjustable',
            'available_adjustments': valid_adjustments,
            'current_settings': {k: gs.get(k) for k in valid_adjustments}
        }
    
    def _effect_clone(self, gs, args):
        return {
            'description': 'Quantum clone created',
            'clone_stats': {k: int(v * 0.7) for k, v in gs.get('player_stats', {}).items()},
            'clone_duration': 60,
            'clone_actions': ['attack', 'defend', 'use_item']
        }
    
    def _effect_anchor(self, gs, args):
        return {
            'description': 'Reality anchor deployed - death prevented once',
            'death_prevention_active': True,
            'hp_restore_on_trigger': gs.get('max_hp', 100) * 0.5,
            'expires_after': 'death or 30min'
        }
    
    def _effect_avatar(self, gs, args):
        return {
            'description': 'Avatar mode engaged - physical presence confirmed',
            'stat_boosts': {k: int(v * 0.5) for k, v in gs.get('player_stats', {}).items()},
            'damage_reduction': 0.25,
            'duration': 90
        }
    
    def _effect_dilation(self, gs, args):
        return {
            'description': 'Time dilated - world slowed 50%',
            'time_factor': 0.5,
            'player_speed_normal': True,  # You move at normal speed while world is slow
            'duration': 10
        }
    
    def _effect_phase(self, gs, args):
        return {
            'description': 'Phase shift active - intangible',
            'can_walk_through_walls': True,
            'damage_immunity': True,
            'duration': 3
        }
    
    def _effect_overdrive(self, gs, args):
        return {
            'description': 'Overdrive engaged - limits removed',
            'speed_multiplier': 2.0,
            'unlimited_stamina': True,
            'attack_speed': 2.0,
            'duration': 15
        }
    
    def _effect_whisper(self, gs, args):
        npcs = gs.get('nearby_npcs', [])
        secrets = []
        for npc in npcs:
            secrets.append({
                'npc': npc['name'],
                'secret': npc.get('secret', 'Has nothing to hide'),
                'price_reduction': 0.5
            })
        return {
            'description': 'Mind whispers heard',
            'npc_secrets': secrets,
            'merchant_discount': 0.5,
            'duration': 300  # 5 minutes
        }
    
    def _effect_charm(self, gs, args):
        return {
            'description': 'Charm field radiating',
            'enemies_passive': True,
            'allies_damage_boost': 1.2,
            'can_recruit_enemies': random.random() < 0.3,
            'duration': 60
        }
    
    def _effect_command(self, gs, args):
        target = ' '.join(args) if args else 'nearest_enemy'
        return {
            'description': f'Command voice issued to {target}',
            'target_controlled': True,
            'commands_available': ['attack_ally', 'defend_me', 'reveal_secrets', 'surrender'],
            'duration': 30
        }
    
    # Helper methods for effect calculations
    def _predict_enemy_moves(self, enemy: Dict) -> List[str]:
        pattern = enemy.get('attack_pattern', ['attack'])
        current_pos = enemy.get('pattern_position', 0)
        return [pattern[(current_pos + i) % len(pattern)] for i in range(3)]
    
    def _calculate_vulnerability(self, enemy: Dict) -> Dict:
        hp_percent = enemy.get('hp', 100) / enemy.get('max_hp', 100)
        if hp_percent < 0.3:
            return {'window': '3 seconds', 'damage_mult': 2.5, 'type': 'desperation'}
        return {'window': '1.5 seconds', 'damage_mult': 1.5, 'type': 'normal'}
    
    def _calculate_combat_odds(self, gs: Dict) -> float:
        player = gs.get('player_stats', {})
        enemies = gs.get('enemies', [])
        if not enemies:
            return 100.0
        
        player_power = player.get('strength', 10) + player.get('agility', 10) + player.get('intelligence', 10)
        enemy_power = sum(e.get('level', 1) * 10 for e in enemies)
        
        odds = (player_power / (player_power + enemy_power)) * 100
        return min(95, max(5, odds))
    
    def _generate_counter(self, enemy: Dict) -> str:
        weakness = enemy.get('weakness', 'none')
        counters = {
            'fire': 'Use water/ice attacks, fire-resistant gear',
            'ice': 'Use fire attacks, stay mobile',
            'lightning': 'Use earth/ground attacks, rubber insulation',
            'poison': 'Use cleansing items, keep distance',
            'physical': 'Use magic/piercing attacks',
            'magic': 'Use physical attacks, magic nullify'
        }
        return counters.get(weakness, 'Attack when vulnerable')
    
    def _get_manifestable_items(self, gs: Dict) -> List[Dict]:
        base_items = [
            {'name': 'Health Potion', 'type': 'consumable', 'rarity': 'common', 'value': 50},
            {'name': 'Energy Crystal', 'type': 'resource', 'rarity': 'uncommon', 'value': 100},
            {'name': 'Iron Sword', 'type': 'weapon', 'rarity': 'common', 'value': 150},
            {'name': 'Magic Scroll', 'type': 'consumable', 'rarity': 'rare', 'value': 300},
            {'name': 'Shield Generator', 'type': 'armor', 'rarity': 'uncommon', 'value': 200},
            {'name': 'Quantum Key', 'type': 'key', 'rarity': 'epic', 'value': 500},
        ]
        
        # Higher level = better items available
        level = gs.get('player_level', 1)
        if level > 5:
            base_items.append({'name': 'Plasma Rifle', 'type': 'weapon', 'rarity': 'rare', 'value': 800})
        if level > 10:
            base_items.append({'name': 'Dragon Scale', 'type': 'material', 'rarity': 'epic', 'value': 2000})
        
        return base_items
    
    def get_mastery_progress(self, user_id: str, power_id: str) -> Dict:
        """Get mastery progress for a power"""
        with sqlite3.connect(self.db) as conn:
            count = conn.execute("""
                SELECT COUNT(*) FROM power_usage 
                WHERE user_id = ? AND power_name = ?
            """, (user_id, power_id)).fetchone()[0]
        
        power = self.ALL_POWERS.get(power_id)
        threshold = power.mastery_threshold if power else 100
        
        return {
            'uses': count,
            'threshold': threshold,
            'percent': min(100, (count / threshold) * 100),
            'mastered': count >= threshold,
            'next_reward': f'Enhanced {power.name}' if count >= threshold else f'{threshold - count} more uses to master'
        }
    
    def get_all_cooldowns(self, user_id: str) -> Dict[str, float]:
        """Get remaining cooldowns for all powers"""
        now = datetime.now()
        result = {}
        for power_id, end_time in self.active_cooldowns.get(user_id, {}).items():
            remaining = (end_time - now).total_seconds()
            if remaining > 0:
                result[power_id] = remaining
        return result

# ============================================
# BASE GAME CLASS - All games inherit from this
# ============================================

class Game(ABC):
    """Abstract base for all Maflex games with real-time state"""
    
    def __init__(self, game_id: str, user_id: str, db_path: str):
        self.game_id = game_id
        self.user_id = user_id
        self.db = db_path
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        
        # Core state
        self.state = {
            'game_type': self.__class__.__name__,
            'status': 'active',  # active, paused, completed, failed
            'energy': 100,
            'max_energy': 100,
            'location': 'start',
            'player_stats': self._load_player_stats(),
            'inventory': [],
            'active_quests': [],
            'completed_quests': [],
            'enemies': [],
            'npcs': [],
            'discovered_areas': set(),
            'world_state': {},
            'turn': 0,
            'score': 0
        }
        
        # Event listeners for real-time updates
        self.event_listeners: List[callable] = []
        self.state_history: List[Dict] = []  # For undo/time travel
        
    def _load_player_stats(self) -> Dict:
        """Load persistent player stats from database"""
        with sqlite3.connect(self.db) as conn:
            row = conn.execute("""
                SELECT skill_tree, cross_game_inventory, credits_current 
                FROM player_progression WHERE user_id = ?
            """, (self.user_id,)).fetchone()
        
        if row:
            skill_tree = json.loads(row[0]) if row[0] else {}
            return {
                'strength': 10 + skill_tree.get('combat', 0) * 2,
                'agility': 10 + skill_tree.get('stealth', 0) * 2,
                'intelligence': 10 + skill_tree.get('hacking', 0) * 2,
                'charisma': 10 + skill_tree.get('trading', 0) * 2,
                'leadership': 10 + skill_tree.get('leadership', 0) * 2,
                'level': sum(skill_tree.values()) // 10 + 1,
                'xp': sum(skill_tree.values())
            }
        return {'strength': 10, 'agility': 10, 'intelligence': 10, 'charisma': 10, 'leadership': 10, 'level': 1, 'xp': 0}
    
    @abstractmethod
    def start(self) -> str:
        """Initialize and return opening description"""
        pass
    
    @abstractmethod
    def process_action(self, action: str, args: List[str]) -> Dict:
        """Process player action and return result with state update"""
        pass
    
    @abstractmethod
    def get_available_actions(self) -> List[Dict]:
        """Return currently available actions based on state"""
        pass
    
    def use_power(self, power_id: str, power_system: PowerSystem, args: List[str] = None) -> Dict:
        """Use a power in this game"""
        result = power_system.use_power(self.user_id, power_id, self.state, args)
        
        if result['success']:
            self.state['energy'] = result['energy']
            # Apply power-specific effects to game state
            self._apply_power_effect(result['effect'])
            self._save_state()
        
        return result
    
    def _apply_power_effect(self, effect: Dict):
        """Override in subclasses to handle power effects"""
        pass
    
    def update(self) -> Dict:
        """Called every second for real-time updates (regen, enemy AI, etc.)"""
        self.state['turn'] += 1
        
        # Energy regeneration
        if self.state['energy'] < self.state['max_energy']:
            self.state['energy'] = min(self.state['max_energy'], self.state['energy'] + 1)
        
        # Update enemies (AI)
        for enemy in self.state['enemies']:
            self._update_enemy_ai(enemy)
        
        # Check world events
        self._check_world_events()
        
        self.updated_at = datetime.now()
        return self.get_public_state()
    
    def _update_enemy_ai(self, enemy: Dict):
        """Override for enemy behavior"""
        pass
    
    def _check_world_events(self):
        """Check for random events, market changes, etc."""
        pass
    
    def get_public_state(self) -> Dict:
        """Get state safe to send to client"""
        return {
            'game_id': self.game_id,
            'game_type': self.state['game_type'],
            'status': self.state['status'],
            'energy': self.state['energy'],
            'max_energy': self.state['max_energy'],
            'location': self.state['location'],
            'player_stats': self.state['player_stats'],
            'inventory_count': len(self.state['inventory']),
            'active_quests': len(self.state['active_quests']),
            'enemies': [{'name': e['name'], 'hp': e.get('hp', 0), 'max_hp': e.get('max_hp', 100)} for e in self.state['enemies']],
            'available_actions': self.get_available_actions(),
            'turn': self.state['turn'],
            'score': self.state['score']
        }
    
    def _save_state(self):
        """Save to database for persistence"""
        with sqlite3.connect(self.db) as conn:
            conn.execute("""
                INSERT INTO game_sessions (session_id, user_id, game_id, current_state, energy, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    current_state = excluded.current_state,
                    energy = excluded.energy,
                    updated_at = excluded.updated_at
            """, (
                self.game_id, self.user_id, self.state['game_type'],
                json.dumps(self.state), self.state['energy'], datetime.now()
            ))
            conn.commit()
    
    def save_player_progress(self):
        """Update persistent player stats"""
        # Calculate XP gains
        xp_gains = {
            'combat': self.state.get('combat_xp_gained', 0),
            'stealth': self.state.get('stealth_xp_gained', 0),
            'hacking': self.state.get('hacking_xp_gained', 0),
            'trading': self.state.get('trading_xp_gained', 0),
            'leadership': self.state.get('leadership_xp_gained', 0)
        }
        
        with sqlite3.connect(self.db) as conn:
            # Get current
            row = conn.execute("""
                SELECT skill_tree, total_kills, total_deaths, credits_earned, secrets_found
                FROM player_progression WHERE user_id = ?
            """, (self.user_id,)).fetchone()
            
            if row:
                skill_tree = json.loads(row[0]) if row[0] else {}
                # Add new XP
                for skill, xp in xp_gains.items():
                    skill_tree[skill] = skill_tree.get(skill, 0) + xp
                
                conn.execute("""
                    UPDATE player_progression SET
                        skill_tree = ?,
                        total_kills = total_kills + ?,
                        total_deaths = total_deaths + ?,
                        credits_earned = credits_earned + ?,
                        secrets_found = secrets_found + ?,
                        last_active = ?
                    WHERE user_id = ?
                """, (
                    json.dumps(skill_tree),
                    self.state.get('kills', 0),
                    1 if self.state['status'] == 'failed' else 0,
                    self.state.get('credits_earned', 0),
                    len(self.state['discovered_areas']),
                    datetime.now(),
                    self.user_id
                ))
            else:
                # Create new progression
                conn.execute("""
                    INSERT INTO player_progression 
                    (user_id, skill_tree, total_kills, total_deaths, credits_earned, secrets_found, last_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.user_id, json.dumps(xp_gains),
                    self.state.get('kills', 0),
                    1 if self.state['status'] == 'failed' else 0,
                    self.state.get('credits_earned', 0),
                    len(self.state['discovered_areas']),
                    datetime.now()
                ))
            conn.commit()
    
    def to_dict(self) -> Dict:
        """Serialize full state"""
        return {
            'game_id': self.game_id,
            'user_id': self.user_id,
            'state': self.state,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict, db_path: str):
        """Restore from serialized state"""
        game = cls(data['game_id'], data['user_id'], db_path)
        game.state = data['state']
        game.created_at = datetime.fromisoformat(data['created_at'])
        game.updated_at = datetime.fromisoformat(data['updated_at'])
        return game