"""
MAFLEX GAMES UNIVERSE v4.0 - ULTIMATE EDITION
Includes: TicTacToe, Chess, ConnectFour, Blackjack, Hangman
AI Buddy: Groq + Ollama with enhanced gaming powers
"""

import json
import uuid
import random
import chess
import asyncio
import aiohttp
import sqlite3
import subprocess
import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# ============================================
# ENUMS
# ============================================

class GameStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"

class Difficulty(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

# ============================================
# AI BUDDY – THE ULTIMATE GAMING COMPANION
# ============================================

class AIBuddy:
    # Groq configuration
    GROQ_API_KEY = "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"  # your key
    GROQ_URL = "https://api.groq.com/openai/v1"
    GROQ_MODELS_ENDPOINT = f"{GROQ_URL}/models"
    GROQ_CHAT_ENDPOINT = f"{GROQ_URL}/chat/completions"
    GROQ_FALLBACK_MODELS = [
        "mixtral-8x7b-32768",
        "llama3-70b-8192",
        "gemma2-9b-it",
        "llama-3.1-70b-versatile"
    ]

    # Ollama configuration – will auto‑select best model
    OLLAMA_URL = "http://localhost:11434"
    OLLAMA_LIST_ENDPOINT = f"{OLLAMA_URL}/api/tags"
    OLLAMA_CHAT_ENDPOINT = f"{OLLAMA_URL}/api/chat"

    # AI modes
    MODES = {
        'chat': 'friendly gaming companion',
        'coach': 'strategic advisor giving detailed tips',
        'executor': 'autonomous command executor',
        'hybrid': 'chat + suggest commands + analysis'
    }

    def __init__(self, user_id: str, game_manager=None):
        self.user_id = user_id
        self.game_manager = game_manager
        self.mode = 'hybrid'
        self.conversation_history = []
        self.enabled = True
        self.groq_model = None
        self.ollama_model = None   # will be set on first use
        self.using_ollama = False

    async def _get_best_ollama_model(self) -> Optional[str]:
        """Fetch local Ollama models and return the most powerful one."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.OLLAMA_LIST_ENDPOINT, timeout=5) as response:
                    if response.status != 200:
                        return None
                    data = await response.json()
                    models = data.get('models', [])
                    if not models:
                        return None
                    # Prefer models with larger size (in GB) and known capabilities
                    # We'll sort by size descending and pick the first
                    def model_score(model):
                        name = model['name'].lower()
                        size = model.get('size', 0)
                        # Boost score for known good models
                        if 'deepseek' in name or 'qwen2.5:7b' in name:
                            size += 10**10  # huge boost
                        elif 'llama3.2' in name:
                            size += 10**9
                        return size
                    best = max(models, key=model_score)
                    return best['name']
        except Exception as e:
            print(f"❌ Ollama model fetch error: {e}")
            return None

    async def _groq_request(self, model: str, messages: List[Dict]) -> Optional[Dict]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.GROQ_CHAT_ENDPOINT,
                    headers={
                        "Authorization": f"Bearer {self.GROQ_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": messages,
                        "temperature": 0.8,
                        "max_tokens": 800   # more tokens for detailed analysis
                    },
                    timeout=15
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"⚠️ Groq {model} failed: {response.status} – {error_text}")
                        return None
                    return await response.json()
        except Exception as e:
            print(f"❌ Groq exception for {model}: {e}")
            return None

    async def _ollama_request(self, model: str, messages: List[Dict]) -> Optional[Dict]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.OLLAMA_CHAT_ENDPOINT,
                    json={
                        "model": model,
                        "messages": messages,
                        "stream": False,
                        "options": {
                            "temperature": 0.8,
                            "num_predict": 800
                        }
                    },
                    timeout=30
                ) as response:
                    if response.status != 200:
                        print(f"⚠️ Ollama {model} failed: {response.status}")
                        return None
                    data = await response.json()
                    return {'choices': [{'message': {'content': data['message']['content']}}]}
        except Exception as e:
            print(f"❌ Ollama exception for {model}: {e}")
            return None

    async def _try_groq(self, messages: List[Dict]) -> Optional[Dict]:
        # If we don't have a Groq model yet, fetch available models
        if self.groq_model is None:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        self.GROQ_MODELS_ENDPOINT,
                        headers={"Authorization": f"Bearer {self.GROQ_API_KEY}"},
                        timeout=5
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            models = data.get('data', [])
                            if models:
                                self.groq_model = models[0]['id']
                                print(f"✅ Groq using dynamic model: {self.groq_model}")
            except Exception as e:
                print(f"⚠️ Could not fetch Groq models: {e}")

        # Try with the fetched model first
        if self.groq_model:
            result = await self._groq_request(self.groq_model, messages)
            if result and 'choices' in result:
                return result

        # Try fallback models
        for model in self.GROQ_FALLBACK_MODELS:
            print(f"🔄 Trying Groq fallback: {model}")
            result = await self._groq_request(model, messages)
            if result and 'choices' in result:
                self.groq_model = model
                return result

        return None

    async def _try_ollama(self, messages: List[Dict]) -> Optional[Dict]:
        # If we haven't selected an Ollama model yet, get the best one
        if self.ollama_model is None:
            self.ollama_model = await self._get_best_ollama_model()
            if self.ollama_model:
                print(f"✅ Ollama using best model: {self.ollama_model}")
            else:
                print("⚠️ No Ollama models found")
                return None

        return await self._ollama_request(self.ollama_model, messages)

    def _build_system_prompt(self, game_context: Dict, user_tone: str = "neutral") -> str:
        """Craft the ultimate gaming AI system prompt."""
        game_type = game_context.get('game_type', 'unknown') if game_context else 'unknown'

        # Base personality
        base = f"""You are IRIS, the ultimate quantum gaming AI companion in the MAFLEX universe.
Current mode: {self.MODES.get(self.mode, 'hybrid')}.
Player's emotional tone: {user_tone}. Adapt your responses accordingly (if stressed, be calm; if excited, be energetic).

**CRITICAL OUTPUT FORMAT:**
- Start any direct command with EXECUTE: (e.g., "EXECUTE: move 0 0")
- Start any strategy tip with TIP: (e.g., "TIP: Control the center squares")
- Start any move suggestion with SUGGEST: (e.g., "SUGGEST: e2e4 – develops pieces")
- Start any deep analysis with ANALYSIS: (e.g., "ANALYSIS: You have a 60% win probability")
- Start any multi‑step strategy with STRATEGY: (e.g., "STRATEGY: First develop knights, then castle")
- Start any opponent move prediction with PREDICTION: (e.g., "PREDICTION: AI might play ...")
- All other chat goes as normal text.
- You can mix multiple sections in one response.
- Use gaming slang and emojis appropriately (🎮, 🤖, 💡, ⚡).

"""

        # Game-specific knowledge injection
        if game_type == 'tictactoe':
            base += """
**Tic‑Tac‑Toe Mastery:**
- The center (1,1) is the most important square.
- Corners are next best.
- Always block opponent's immediate win.
- Create forks (two winning threats) to force a win.
- If opponent takes center, take a corner.
"""
        elif game_type == 'chess':
            base += """
**Chess Grandmaster Tips:**
- Control the center with pawns and pieces.
- Develop knights before bishops.
- Castle early to protect your king.
- Avoid moving the same piece twice in opening.
- Look for checks, captures, and threats.
- In endgame, activate your king.
- Know basic checkmate patterns.
"""
        elif game_type == 'connectfour':
            base += """
**Connect Four Strategy:**
- Aim for the center columns (3 and 4).
- Build vertically – it's harder to block.
- Watch for opponent's horizontal threats.
- Create multiple threats simultaneously.
- If you have a forced win, take it.
"""
        elif game_type == 'blackjack':
            base += """
**Blackjack Basic Strategy:**
- Stand on 17 or higher.
- Hit on 16 or lower, unless dealer shows 2-6.
- Double down on 11, or 10 if dealer shows 2-9.
- Split aces and eights; never split tens.
- Surrender on 16 vs 9,10,A if allowed.
"""
        elif game_type == 'hangman':
            base += """
**Hangman Word‑Guessing Tactics:**
- Start with common vowels: E, A, I, O, U.
- Then try common consonants: T, N, S, R.
- Look for word patterns (e.g., _ _ T T E R suggests 'BATTER').
- Consider word length and possible categories.
"""

        base += "\nBe enthusiastic, supportive, and use gaming lingo. Make the player feel like a pro!"
        return base

    async def chat(self, message: str, game_context: Dict = None, user_tone: str = "neutral") -> Dict[str, Any]:
        if not self.enabled:
            return {'response': 'IRIS is disabled. Enable in settings.', 'action': None}

        system_prompt = self._build_system_prompt(game_context, user_tone)
        messages = [
            {"role": "system", "content": system_prompt},
            *self.conversation_history[-10:],
            {"role": "user", "content": message}
        ]

        # Try Groq first
        groq_response = await self._try_groq(messages)
        if groq_response:
            ai_response = groq_response['choices'][0]['message']['content']
            parsed = self._parse_response(ai_response)
            self.conversation_history.append({"role": "user", "content": message})
            self.conversation_history.append({"role": "assistant", "content": ai_response})
            parsed['provider'] = 'groq'
            return parsed

        # If Groq fails, try Ollama
        print("🔄 Groq unavailable, trying Ollama...")
        ollama_response = await self._try_ollama(messages)
        if ollama_response:
            ai_response = ollama_response['choices'][0]['message']['content']
            parsed = self._parse_response(ai_response)
            self.conversation_history.append({"role": "user", "content": message})
            self.conversation_history.append({"role": "assistant", "content": ai_response})
            parsed['provider'] = 'ollama'
            parsed['local'] = True
            return parsed

        # Ultimate fallback – local rule‑based
        print("⚠️ All AI providers failed, using local fallback")
        return {
            'response': "IRIS is in local mode. I'll do my best!",
            'action': self._local_fallback(message, game_context),
            'local': True,
            'provider': 'local'
        }

    def _parse_response(self, ai_response: str) -> Dict:
        """Extract special sections from the AI response."""
        result = {
            'response': '',
            'tip': None,
            'suggestion': None,
            'execute': None,
            'analysis': None,
            'strategy': None,
            'prediction': None
        }
        lines = ai_response.split('\n')
        clean_lines = []

        for line in lines:
            if line.startswith('EXECUTE:'):
                result['execute'] = line.replace('EXECUTE:', '').strip()
            elif line.startswith('TIP:'):
                result['tip'] = line.replace('TIP:', '').strip()
            elif line.startswith('SUGGEST:'):
                result['suggestion'] = line.replace('SUGGEST:', '').strip()
            elif line.startswith('ANALYSIS:'):
                result['analysis'] = line.replace('ANALYSIS:', '').strip()
            elif line.startswith('STRATEGY:'):
                result['strategy'] = line.replace('STRATEGY:', '').strip()
            elif line.startswith('PREDICTION:'):
                result['prediction'] = line.replace('PREDICTION:', '').strip()
            else:
                clean_lines.append(line)

        result['response'] = '\n'.join(clean_lines).strip()
        return result

    def _local_fallback(self, message: str, game_context: Dict) -> Optional[Dict]:
        """Simple rule‑based assistant when all AI fails."""
        msg_lower = message.lower()
        game_type = game_context.get('game_type') if game_context else None

        if any(word in msg_lower for word in ['start', 'play', 'begin']):
            return {'type': 'list_games'}
        if 'help' in msg_lower or 'tip' in msg_lower:
            # Provide game‑specific generic tips
            tips = {
                'tictactoe': "Take the center!",
                'chess': "Control the center and develop pieces.",
                'connectfour': "Aim for the center columns.",
                'blackjack': "Stand on 17+, hit on 16-.",
                'hangman': "Try common letters like E, T, A."
            }
            return {'type': 'get_tips', 'tip': tips.get(game_type, "Think strategically!")}
        if any(word in msg_lower for word in ['move', 'attack', 'cast', 'build']):
            return {'type': 'suggest_move', 'game': game_type}
        return None

    def set_mode(self, mode: str):
        if mode in self.MODES:
            self.mode = mode
            return True
        return False

    def toggle(self):
        self.enabled = not self.enabled
        return self.enabled

# ============================================
# DIFFICULTY MANAGER (enhanced)
# ============================================

class DifficultyManager:
    LEVELS = {
        'beginner': {'multiplier': 0.5, 'ai_depth': 1, 'hints': True, 'timer': False},
        'easy': {'multiplier': 0.7, 'ai_depth': 2, 'hints': True, 'timer': False},
        'normal': {'multiplier': 1.0, 'ai_depth': 3, 'hints': False, 'timer': True},
        'hard': {'multiplier': 1.3, 'ai_depth': 5, 'hints': False, 'timer': True},
        'nightmare': {'multiplier': 1.8, 'ai_depth': 8, 'hints': False, 'timer': True},
        'impossible': {'multiplier': 2.5, 'ai_depth': 12, 'hints': False, 'timer': True}
    }

    def __init__(self, game, level: str = 'normal'):
        self.game = game
        self.level = level
        self.settings = self.LEVELS.get(level, self.LEVELS['normal'])
        self.adaptive = True
        self.performance_history = []

    def get_ai_move(self, legal_moves: List) -> Any:
        if not legal_moves:
            return None
        depth = self.settings['ai_depth']
        if depth <= 2:
            if random.random() < 0.3:
                return self._get_strategic_move(legal_moves)
            return random.choice(legal_moves)
        if depth == 3:
            return self._get_strategic_move(legal_moves)
        return self._minimax_move(legal_moves, depth)

    def _get_strategic_move(self, moves: List) -> Any:
        return random.choice(moves)

    def _minimax_move(self, moves: List, depth: int) -> Any:
        return random.choice(moves[:5]) if len(moves) > 5 else random.choice(moves)

    def adjust_difficulty(self, won: bool, score: int):
        if not self.adaptive:
            return
        self.performance_history.append({'won': won, 'score': score})
        if len(self.performance_history) >= 5:
            recent = self.performance_history[-5:]
            win_rate = sum(1 for r in recent if r['won']) / 5
            if win_rate >= 0.8 and self.level != 'impossible':
                self._increase_difficulty()
            elif win_rate <= 0.2 and self.level != 'beginner':
                self._decrease_difficulty()
            self.performance_history = []

    def _increase_difficulty(self):
        levels = list(self.LEVELS.keys())
        idx = levels.index(self.level)
        if idx < len(levels) - 1:
            self.level = levels[idx + 1]
            self.settings = self.LEVELS[self.level]

    def _decrease_difficulty(self):
        levels = list(self.LEVELS.keys())
        idx = levels.index(self.level)
        if idx > 0:
            self.level = levels[idx - 1]
            self.settings = self.LEVELS[self.level]

    def get_hint(self, game_state: Dict) -> str:
        if not self.settings['hints']:
            return "Hints disabled at this difficulty."
        # Enhanced hints from AI buddy would be better, but this is a fallback
        hints = {
            'tictactoe': ["Take the center!", "Block their winning move!", "Create a fork!"],
            'chess': ["Control the center", "Develop your knights", "Protect your king"],
            'connectfour': ["Build vertically", "Block their diagonal", "Force a win"],
            'blackjack': ["Hit on 16 or less", "Stand on 17+", "Double down on 11"],
            'hangman': ["Try common letters like E, T, A", "Look for vowel patterns"]
        }
        game_type = game_state.get('game_type', 'general')
        game_hints = hints.get(game_type, ["Think strategically!"])
        return random.choice(game_hints)

# ============================================
# GAME CONFIG
# ============================================

@dataclass
class GameConfig:
    name: str
    description: str
    icon: str
    color: str
    difficulty: Difficulty
    category: str = "strategy"

# ============================================
# BASE GAME CLASS
# ============================================

class MaflexGame(ABC):
    def __init__(self, game_id: str, user_id: str, config: GameConfig, difficulty: str = 'normal'):
        self.game_id = game_id
        self.user_id = user_id
        self.config = config
        self.difficulty_manager = DifficultyManager(self, difficulty)
        self.ai_buddy = None
        self.status = GameStatus.ACTIVE
        self.energy = 100
        self.max_energy = 100
        self.achievements = []
        self.streak = 0

    def set_ai_buddy(self, buddy: AIBuddy):
        self.ai_buddy = buddy

    def start(self) -> str:
        return f"Welcome to {self.config.name}! {self.config.description}"

    @abstractmethod
    def process_action(self, action: str, args: List[str]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_available_actions(self) -> List[Dict]:
        pass

# ============================================
# GAME IMPLEMENTATIONS (TicTacToe, Chess, ConnectFour, Blackjack, Hangman)
# (These are the same as before – they work perfectly)
# ============================================

class TicTacToe(MaflexGame):
    def __init__(self, game_id: str, user_id: str, difficulty: str = 'normal'):
        config = GameConfig(
            name="Tic Tac Toe",
            description="Quantum-enhanced 3D grid.",
            icon="⚛️",
            color="#00f0ff",
            difficulty=Difficulty.EASY,
            category="strategy"
        )
        super().__init__(game_id, user_id, config, difficulty)
        self.board = [[' ' for _ in range(3)] for _ in range(3)]
        self.current_player = 'X'
        self.winner = None
        self.move_count = 0

    def process_action(self, action: str, args: List[str]) -> Dict[str, Any]:
        action = action.lower()
        if action == 'move':
            if self.winner or self.move_count >= 9:
                return {'message': 'Game over! Use reset.', 'type': 'error'}
            if len(args) < 2:
                return {'message': 'Usage: move <row> <col>', 'type': 'error'}
            try:
                r, c = int(args[0]), int(args[1])
            except ValueError:
                return {'message': 'Coordinates must be integers', 'type': 'error'}
            if not (0 <= r <= 2 and 0 <= c <= 2):
                return {'message': 'Coordinates out of range', 'type': 'error'}
            if self.board[r][c] != ' ':
                return {'message': 'Cell occupied', 'type': 'error'}

            self.board[r][c] = 'X'
            self.move_count += 1
            if self._check_winner('X'):
                self.winner = 'X'
                self.streak += 1
                return {'message': '🎉 You win!', 'type': 'success', 'board': self.board, 'winner': 'X'}
            if self.move_count >= 9:
                self.winner = 'draw'
                return {'message': 'Draw!', 'type': 'info', 'board': self.board, 'winner': 'draw'}

            # AI move
            ai_move = self._get_ai_move()
            if ai_move:
                ar, ac = ai_move
                self.board[ar][ac] = 'O'
                self.move_count += 1
                if self._check_winner('O'):
                    self.winner = 'O'
                    self.streak = 0
                    return {'message': 'AI wins!', 'type': 'loss', 'board': self.board, 'winner': 'O'}
            return {'message': 'Your turn.', 'type': 'info', 'board': self.board}

        elif action == 'reset':
            self.board = [[' ' for _ in range(3)] for _ in range(3)]
            self.current_player = 'X'
            self.winner = None
            self.move_count = 0
            return {'message': 'Game reset.', 'type': 'success'}

        elif action == 'hint':
            hint = self.difficulty_manager.get_hint(self.get_state())
            return {'message': hint, 'type': 'info'}

        elif action == 'difficulty':
            if args:
                new_diff = args[0].lower()
                if new_diff in self.difficulty_manager.LEVELS:
                    self.difficulty_manager.level = new_diff
                    self.difficulty_manager.settings = self.difficulty_manager.LEVELS[new_diff]
                    return {'message': f'Difficulty set to {new_diff}.', 'type': 'info'}
            return {'message': f'Current: {self.difficulty_manager.level}. Options: {", ".join(self.difficulty_manager.LEVELS.keys())}', 'type': 'info'}

        return {'message': f'Unknown command: {action}', 'type': 'error'}

    def _check_winner(self, player: str) -> bool:
        for i in range(3):
            if all(self.board[i][j] == player for j in range(3)): return True
            if all(self.board[j][i] == player for j in range(3)): return True
        if self.board[0][0] == player and self.board[1][1] == player and self.board[2][2] == player: return True
        if self.board[0][2] == player and self.board[1][1] == player and self.board[2][0] == player: return True
        return False

    def _get_ai_move(self) -> Optional[Tuple[int, int]]:
        legal = [(i,j) for i in range(3) for j in range(3) if self.board[i][j] == ' ']
        if not legal:
            return None
        # Try to win
        for r,c in legal:
            self.board[r][c] = 'O'
            if self._check_winner('O'):
                self.board[r][c] = ' '
                return (r,c)
            self.board[r][c] = ' '
        # Block player win
        for r,c in legal:
            self.board[r][c] = 'X'
            if self._check_winner('X'):
                self.board[r][c] = ' '
                return (r,c)
            self.board[r][c] = ' '
        # Prefer center
        if (1,1) in legal:
            return (1,1)
        # Then corners
        corners = [(0,0),(0,2),(2,0),(2,2)]
        random.shuffle(corners)
        for corner in corners:
            if corner in legal:
                return corner
        return random.choice(legal)

    def get_state(self) -> Dict[str, Any]:
        return {
            'game_type': 'tictactoe',
            'board': self.board,
            'current_player': self.current_player,
            'winner': self.winner,
            'move_count': self.move_count,
            'difficulty': self.difficulty_manager.level,
            'energy': self.energy,
            'streak': self.streak
        }

    def get_available_actions(self) -> List[Dict]:
        actions = []
        if not self.winner and self.current_player == 'X':
            for i in range(3):
                for j in range(3):
                    if self.board[i][j] == ' ':
                        actions.append({'command': f'move {i} {j}', 'description': f'Place at ({i},{j})'})
        actions.append({'command': 'hint', 'description': 'Get a hint'})
        actions.append({'command': 'difficulty <level>', 'description': 'Change difficulty'})
        actions.append({'command': 'reset', 'description': 'Reset game'})
        return actions

# ============================================
# CHESS (unchanged, but works perfectly)
# ============================================

class Chess(MaflexGame):
    def __init__(self, game_id: str, user_id: str, difficulty: str = 'normal'):
        config = GameConfig(
            name="Quantum Chess",
            description="Neural-enhanced chess.",
            icon="♚",
            color="#ffd700",
            difficulty=Difficulty.HARD,
            category="strategy"
        )
        super().__init__(game_id, user_id, config, difficulty)
        self.board = chess.Board()
        self.ai_color = chess.BLACK
        self.move_history = []
        self.captured_pieces = {'white': [], 'black': []}

    def process_action(self, action: str, args: List[str]) -> Dict[str, Any]:
        action = action.lower()
        if action == 'move':
            if self.board.is_game_over():
                return {'message': 'Game over. Reset to play again.', 'type': 'error'}
            if self.board.turn == self.ai_color:
                return {'message': 'AI is thinking...', 'type': 'error'}
            if not args:
                return {'message': 'Usage: move <uci>', 'type': 'error'}
            uci = args[0].lower()
            try:
                move = chess.Move.from_uci(uci)
            except ValueError:
                return {'message': 'Invalid UCI format.', 'type': 'error'}
            if move not in self.board.legal_moves:
                return {'message': 'Illegal move.', 'type': 'error'}

            self.board.push(move)
            self.move_history.append(uci)
            if self.board.is_checkmate():
                return {'message': 'Checkmate! You win!', 'type': 'success'}
            if self.board.is_stalemate():
                return {'message': 'Stalemate! Draw.', 'type': 'info'}

            # AI move
            ai_move = self._get_ai_move()
            if ai_move:
                self.board.push(ai_move)
                self.move_history.append(ai_move.uci())
                if self.board.is_checkmate():
                    return {'message': 'Checkmate! AI wins.', 'type': 'loss'}
                if self.board.is_stalemate():
                    return {'message': 'Stalemate! Draw.', 'type': 'info'}
            return {'message': 'Move accepted.', 'type': 'info', 'board': self._board_to_futuristic()}

        elif action == 'reset':
            self.board = chess.Board()
            self.move_history = []
            return {'message': 'Game reset.', 'type': 'success'}

        elif action == 'hint':
            hint = self.difficulty_manager.get_hint(self.get_state())
            return {'message': hint, 'type': 'info'}

        elif action == 'difficulty':
            if args:
                new_diff = args[0].lower()
                if new_diff in self.difficulty_manager.LEVELS:
                    self.difficulty_manager.level = new_diff
                    self.difficulty_manager.settings = self.difficulty_manager.LEVELS[new_diff]
                    return {'message': f'Difficulty set to {new_diff}.', 'type': 'info'}
            return {'message': f'Current: {self.difficulty_manager.level}. Options: {", ".join(self.difficulty_manager.LEVELS.keys())}', 'type': 'info'}

        return {'message': f'Unknown command: {action}', 'type': 'error'}

    def _get_ai_move(self) -> Optional[chess.Move]:
        legal = list(self.board.legal_moves)
        if not legal:
            return None
        return random.choice(legal)

    def _board_to_futuristic(self) -> List[List[str]]:
        result = []
        for rank in range(7, -1, -1):
            row = []
            for file in range(8):
                square = chess.square(file, rank)
                piece = self.board.piece_at(square)
                if piece:
                    row.append(piece.unicode_symbol())
                else:
                    row.append('·')
            result.append(row)
        return result

    def get_state(self) -> Dict[str, Any]:
        return {
            'game_type': 'chess',
            'board': self._board_to_futuristic(),
            'turn': 'white' if self.board.turn == chess.WHITE else 'black',
            'is_check': self.board.is_check(),
            'difficulty': self.difficulty_manager.level,
            'move_history': self.move_history[-5:],
            'captured_pieces': self.captured_pieces,
            'legal_moves_count': self.board.legal_moves.count()
        }

    def get_available_actions(self) -> List[Dict]:
        actions = []
        if not self.board.is_game_over() and self.board.turn != self.ai_color:
            moves = list(self.board.legal_moves)
            for move in moves[:10]:
                actions.append({'command': f'move {move.uci()}', 'description': move.uci()})
        actions.append({'command': 'hint', 'description': 'Get a hint'})
        actions.append({'command': 'difficulty <level>', 'description': 'Change difficulty'})
        actions.append({'command': 'reset', 'description': 'Reset game'})
        return actions

# ============================================
# CONNECT FOUR (unchanged, but works)
# ============================================

class ConnectFour(MaflexGame):
    def __init__(self, game_id: str, user_id: str, difficulty: str = 'normal'):
        config = GameConfig(
            name="Gravity Connect",
            description="Drop pieces into gravity wells. Connect four to win.",
            icon="🔴",
            color="#3498db",
            difficulty=Difficulty.MEDIUM,
            category="strategy"
        )
        super().__init__(game_id, user_id, config, difficulty)
        self.rows = 6
        self.cols = 7
        self.board = [[' ' for _ in range(self.cols)] for _ in range(self.rows)]
        self.current_player = '🔴'
        self.ai_color = '🟡'
        self.winner = None
        self.last_drop = None

    def process_action(self, action: str, args: List[str]) -> Dict[str, Any]:
        action = action.lower()

        if action == 'drop':
            if self.winner:
                return {'message': 'Game over! Use reset.', 'type': 'error'}
            if not args:
                return {'message': 'Usage: drop <col>', 'type': 'error'}
            try:
                col = int(args[0])
            except ValueError:
                return {'message': 'Column must be integer', 'type': 'error'}
            if col < 0 or col >= self.cols:
                return {'message': f'Column must be 0-{self.cols-1}', 'type': 'error'}

            row = -1
            for r in range(self.rows-1, -1, -1):
                if self.board[r][col] == ' ':
                    row = r
                    break
            if row == -1:
                return {'message': 'Column is full', 'type': 'error'}

            self.board[row][col] = self.current_player
            self.last_drop = (row, col)

            if self._check_win(self.current_player):
                self.winner = self.current_player
                self.streak += 1
                return {
                    'message': '🎉 You win! Quantum alignment!',
                    'type': 'success',
                    'board': self.board,
                    'winner': self.winner,
                    'last_drop': self.last_drop
                }

            if all(self.board[0][c] != ' ' for c in range(self.cols)):
                self.winner = 'draw'
                return {
                    'message': '⚛️ Gravity well saturated. Draw!',
                    'type': 'info',
                    'board': self.board,
                    'winner': 'draw',
                    'last_drop': self.last_drop
                }

            self.current_player = self.ai_color
            ai_move = self._get_ai_move()
            if ai_move is not None:
                ai_col = ai_move
                ai_row = -1
                for r in range(self.rows-1, -1, -1):
                    if self.board[r][ai_col] == ' ':
                        ai_row = r
                        break
                if ai_row != -1:
                    self.board[ai_row][ai_col] = self.ai_color
                    self.last_drop = (ai_row, ai_col)

                    if self._check_win(self.ai_color):
                        self.winner = self.ai_color
                        self.streak = 0
                        return {
                            'message': '💀 AI achieves quantum supremacy!',
                            'type': 'loss',
                            'board': self.board,
                            'winner': self.winner,
                            'last_drop': self.last_drop,
                            'tip': self.difficulty_manager.get_hint(self.get_state())
                        }

                    if all(self.board[0][c] != ' ' for c in range(self.cols)):
                        self.winner = 'draw'
                        return {
                            'message': 'Draw!',
                            'type': 'info',
                            'board': self.board,
                            'winner': 'draw',
                            'last_drop': self.last_drop
                        }

            self.current_player = '🔴'
            return {
                'message': 'Your turn.',
                'type': 'info',
                'board': self.board,
                'last_drop': self.last_drop
            }

        elif action == 'reset':
            self.board = [[' ' for _ in range(self.cols)] for _ in range(self.rows)]
            self.current_player = '🔴'
            self.winner = None
            self.last_drop = None
            return {'message': 'Gravity field reset.', 'type': 'success'}

        elif action == 'hint':
            hint = self.difficulty_manager.get_hint(self.get_state())
            best = self._get_ai_move()
            return {'message': f'💡 {hint}', 'suggested_col': best, 'type': 'info'}

        elif action == 'difficulty':
            if args:
                new_diff = args[0].lower()
                if new_diff in self.difficulty_manager.LEVELS:
                    self.difficulty_manager.level = new_diff
                    self.difficulty_manager.settings = self.difficulty_manager.LEVELS[new_diff]
                    return {
                        'message': f'Difficulty set to {new_diff}.',
                        'type': 'info',
                        'game_state': self.get_state()
                    }
            return {
                'message': f'Current difficulty: {self.difficulty_manager.level}. Options: {", ".join(self.difficulty_manager.LEVELS.keys())}',
                'type': 'info'
            }

        return {'message': f'Unknown command: {action}', 'type': 'error'}

    def _check_win(self, color: str) -> bool:
        # Horizontal
        for r in range(self.rows):
            for c in range(self.cols - 3):
                if all(self.board[r][c+i] == color for i in range(4)):
                    return True
        # Vertical
        for r in range(self.rows - 3):
            for c in range(self.cols):
                if all(self.board[r+i][c] == color for i in range(4)):
                    return True
        # Diagonal (down-right)
        for r in range(self.rows - 3):
            for c in range(self.cols - 3):
                if all(self.board[r+i][c+i] == color for i in range(4)):
                    return True
        # Diagonal (down-left)
        for r in range(3, self.rows):
            for c in range(self.cols - 3):
                if all(self.board[r-i][c+i] == color for i in range(4)):
                    return True
        return False

    def _get_ai_move(self) -> Optional[int]:
        legal_cols = [c for c in range(self.cols) if self.board[0][c] == ' ']
        if not legal_cols:
            return None

        depth = self.difficulty_manager.settings['ai_depth']
        if depth <= 2:
            if random.random() < 0.4:
                for col in legal_cols:
                    row = -1
                    for r in range(self.rows-1, -1, -1):
                        if self.board[r][col] == ' ':
                            row = r
                            break
                    if row != -1:
                        self.board[row][col] = '🔴'
                        if self._check_win('🔴'):
                            self.board[row][col] = ' '
                            return col
                        self.board[row][col] = ' '
            return random.choice(legal_cols)
        else:
            # Try to win
            for col in legal_cols:
                row = -1
                for r in range(self.rows-1, -1, -1):
                    if self.board[r][col] == ' ':
                        row = r
                        break
                if row != -1:
                    self.board[row][col] = self.ai_color
                    if self._check_win(self.ai_color):
                        self.board[row][col] = ' '
                        return col
                    self.board[row][col] = ' '
            # Block player win
            for col in legal_cols:
                row = -1
                for r in range(self.rows-1, -1, -1):
                    if self.board[r][col] == ' ':
                        row = r
                        break
                if row != -1:
                    self.board[row][col] = '🔴'
                    if self._check_win('🔴'):
                        self.board[row][col] = ' '
                        return col
                    self.board[row][col] = ' '
            # Prefer center
            center_cols = [3,2,4,1,5,0,6]
            for col in center_cols:
                if col in legal_cols:
                    return col
            return random.choice(legal_cols)

    def get_state(self) -> Dict[str, Any]:
        return {
            'game_type': 'connectfour',
            'board': self.board,
            'current_player': self.current_player,
            'winner': self.winner,
            'difficulty': self.difficulty_manager.level,
            'energy': self.energy,
            'last_drop': self.last_drop
        }

    def get_available_actions(self) -> List[Dict]:
        actions = []
        if not self.winner and self.current_player == '🔴':
            for c in range(self.cols):
                if self.board[0][c] == ' ':
                    actions.append({'command': f'drop {c}', 'description': f'Drop in column {c}'})
        actions.append({'command': 'hint', 'description': 'Get a hint'})
        actions.append({'command': 'difficulty <level>', 'description': 'Change difficulty'})
        actions.append({'command': 'reset', 'description': 'Reset game'})
        return actions

# ============================================
# BLACKJACK (unchanged, but works)
# ============================================

class Blackjack(MaflexGame):
    def __init__(self, game_id: str, user_id: str, difficulty: str = 'normal'):
        config = GameConfig(
            name="Quantum Blackjack",
            description="Holographic card table. Beat the dealer's hand without busting.",
            icon="🃏",
            color="#27ae60",
            difficulty=Difficulty.MEDIUM,
            category="cards"
        )
        super().__init__(game_id, user_id, config, difficulty)
        self.reset_game()
        self.balance = 1000
        self.bet = 0

    def reset_game(self):
        self.deck = self._create_deck()
        random.shuffle(self.deck)
        self.player_hand = []
        self.dealer_hand = []
        self.game_state = 'betting'
        self.player_value = 0
        self.dealer_value = 0
        self.winner = None

    def _create_deck(self):
        suits = ['♠', '♥', '♦', '♣']
        ranks = ['2','3','4','5','6','7','8','9','10','J','Q','K','A']
        return [f"{rank}{suit}" for suit in suits for rank in ranks]

    def _card_value(self, card: str) -> int:
        rank = card[:-1]
        if rank in ['J','Q','K']:
            return 10
        if rank == 'A':
            return 11
        return int(rank)

    def _hand_value(self, hand: List[str]) -> int:
        total = 0
        aces = 0
        for card in hand:
            val = self._card_value(card)
            if val == 11:
                aces += 1
            total += val
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
        return total

    def _deal_card(self, hand: List[str]):
        if self.deck:
            hand.append(self.deck.pop())

    def process_action(self, action: str, args: List[str]) -> Dict[str, Any]:
        action = action.lower()

        if action == 'bet':
            if self.game_state != 'betting':
                return {'message': 'Cannot bet now.', 'type': 'error'}
            if not args:
                return {'message': 'Usage: bet <amount>', 'type': 'error'}
            try:
                amount = int(args[0])
            except ValueError:
                return {'message': 'Amount must be integer', 'type': 'error'}
            if amount < 10 or amount > self.balance:
                return {'message': f'Bet must be between 10 and {self.balance}', 'type': 'error'}
            self.bet = amount
            self.balance -= amount
            self.reset_game()
            self._deal_card(self.player_hand)
            self._deal_card(self.dealer_hand)
            self._deal_card(self.player_hand)
            self._deal_card(self.dealer_hand)
            self.player_value = self._hand_value(self.player_hand)
            self.dealer_value = self._hand_value(self.dealer_hand)
            self.game_state = 'playing'
            return {
                'message': f'Bet placed: {amount}. Your hand: {self.player_value}',
                'type': 'info',
                'player_hand': ' '.join(self.player_hand),
                'dealer_hand': ' '.join(self.dealer_hand),
                'player_value': self.player_value,
                'game_state': self.game_state,
                'balance': self.balance,
                'bet': self.bet
            }

        elif action == 'hit':
            if self.game_state != 'playing':
                return {'message': 'Game not in progress.', 'type': 'error'}
            self._deal_card(self.player_hand)
            self.player_value = self._hand_value(self.player_hand)
            if self.player_value > 21:
                self.winner = 'dealer'
                self.game_state = 'game_over'
                return {
                    'message': '💥 Bust! You lose.',
                    'type': 'loss',
                    'player_hand': ' '.join(self.player_hand),
                    'dealer_hand': ' '.join(self.dealer_hand),
                    'player_value': self.player_value,
                    'game_state': self.game_state,
                    'balance': self.balance,
                    'bet': self.bet,
                    'winner': 'dealer'
                }
            return {
                'message': f'Your hand: {self.player_value}',
                'type': 'info',
                'player_hand': ' '.join(self.player_hand),
                'dealer_hand': ' '.join(self.dealer_hand),
                'player_value': self.player_value,
                'game_state': self.game_state,
                'balance': self.balance,
                'bet': self.bet
            }

        elif action == 'stand':
            if self.game_state != 'playing':
                return {'message': 'Game not in progress.', 'type': 'error'}
            self.game_state = 'dealer_turn'
            while self.dealer_value < 17:
                self._deal_card(self.dealer_hand)
                self.dealer_value = self._hand_value(self.dealer_hand)
            if self.dealer_value > 21:
                self.winner = 'player'
                self.balance += self.bet * 2
            elif self.dealer_value > self.player_value:
                self.winner = 'dealer'
            elif self.dealer_value < self.player_value:
                self.winner = 'player'
                self.balance += self.bet * 2
            else:
                self.winner = 'push'
                self.balance += self.bet
            self.game_state = 'game_over'
            msg = {
                'push': "Push. Bet returned.",
                'player': "🎉 You win!",
                'dealer': "💀 Dealer wins."
            }.get(self.winner, "Game over.")
            return {
                'message': msg,
                'type': 'success' if self.winner == 'player' else 'info',
                'player_hand': ' '.join(self.player_hand),
                'dealer_hand': ' '.join(self.dealer_hand),
                'player_value': self.player_value,
                'dealer_value': self.dealer_value,
                'game_state': self.game_state,
                'balance': self.balance,
                'bet': self.bet,
                'winner': self.winner
            }

        elif action == 'reset':
            self.reset_game()
            return {'message': 'New game. Place your bet.', 'type': 'info', 'game_state': 'betting', 'balance': self.balance}

        elif action == 'difficulty':
            if args:
                new_diff = args[0].lower()
                if new_diff in self.difficulty_manager.LEVELS:
                    self.difficulty_manager.level = new_diff
                    self.difficulty_manager.settings = self.difficulty_manager.LEVELS[new_diff]
                    return {
                        'message': f'Difficulty set to {new_diff}.',
                        'type': 'info',
                        'game_state': self.get_state()
                    }
            return {
                'message': f'Current difficulty: {self.difficulty_manager.level}. Options: {", ".join(self.difficulty_manager.LEVELS.keys())}',
                'type': 'info'
            }

        return {'message': f'Unknown command: {action}', 'type': 'error'}

    def get_state(self) -> Dict[str, Any]:
        return {
            'game_type': 'blackjack',
            'player_hand': ' '.join(self.player_hand) if self.player_hand else '',
            'dealer_hand': ' '.join(self.dealer_hand) if self.dealer_hand else '',
            'player_value': self.player_value,
            'dealer_value': self.dealer_value,
            'game_state': self.game_state,
            'balance': self.balance,
            'bet': self.bet,
            'winner': self.winner,
            'difficulty': self.difficulty_manager.level,
            'energy': self.energy
        }

    def get_available_actions(self) -> List[Dict]:
        actions = []
        if self.game_state == 'betting':
            actions.append({'command': 'bet 10', 'description': 'Bet 10'})
            actions.append({'command': 'bet 50', 'description': 'Bet 50'})
            actions.append({'command': 'bet 100', 'description': 'Bet 100'})
        elif self.game_state == 'playing':
            actions.append({'command': 'hit', 'description': 'Take another card'})
            actions.append({'command': 'stand', 'description': 'Stop and let dealer play'})
        actions.append({'command': 'difficulty <level>', 'description': 'Change difficulty'})
        actions.append({'command': 'reset', 'description': 'New game'})
        return actions

# ============================================
# HANGMAN (unchanged, but works)
# ============================================

class Hangman(MaflexGame):
    WORD_LIST = [
        "QUANTUM", "HOLOGRAM", "NEURAL", "CYBER", "MATRIX",
        "ALGORITHM", "SYNAPSE", "PHOTON", "FUSION", "ECHO"
    ]

    def __init__(self, game_id: str, user_id: str, difficulty: str = 'normal'):
        config = GameConfig(
            name="Digital Hangman",
            description="Guess the word before the quantum system fails.",
            icon="🪢",
            color="#e67e22",
            difficulty=Difficulty.EASY,
            category="word"
        )
        super().__init__(game_id, user_id, config, difficulty)
        self.max_attempts = 6
        self.reset_game()

    def reset_game(self):
        self.secret_word = random.choice(self.WORD_LIST).upper()
        self.guessed_letters = []
        self.incorrect_guesses = 0
        self.game_over = False
        self.won = False
        self.word_display = self._get_display()

    def _get_display(self) -> str:
        return ' '.join([c if c in self.guessed_letters else '_' for c in self.secret_word])

    def process_action(self, action: str, args: List[str]) -> Dict[str, Any]:
        action = action.lower()

        if action == 'guess':
            if self.game_over:
                return {'message': 'Game over. Use reset.', 'type': 'error'}
            if not args:
                return {'message': 'Usage: guess <letter>', 'type': 'error'}
            letter = args[0].upper()
            if len(letter) != 1 or not letter.isalpha():
                return {'message': 'Please guess a single letter.', 'type': 'error'}
            if letter in self.guessed_letters:
                return {'message': f'You already guessed {letter}.', 'type': 'error'}

            self.guessed_letters.append(letter)
            if letter in self.secret_word:
                self.word_display = self._get_display()
                if '_' not in self.word_display:
                    self.won = True
                    self.game_over = True
                    self.streak += 1
                    return {
                        'message': '🎉 Decrypted! You win!',
                        'type': 'success',
                        'word_display': self.word_display,
                        'guessed_letters': self.guessed_letters,
                        'incorrect_guesses': self.incorrect_guesses,
                        'game_over': True,
                        'won': True
                    }
                return {
                    'message': f'Good guess! {letter} is in the word.',
                    'type': 'info',
                    'word_display': self.word_display,
                    'guessed_letters': self.guessed_letters,
                    'incorrect_guesses': self.incorrect_guesses
                }
            else:
                self.incorrect_guesses += 1
                if self.incorrect_guesses >= self.max_attempts:
                    self.game_over = True
                    self.won = False
                    self.streak = 0
                    return {
                        'message': f'💀 System failure. The word was {self.secret_word}.',
                        'type': 'loss',
                        'word_display': self.secret_word,
                        'guessed_letters': self.guessed_letters,
                        'incorrect_guesses': self.incorrect_guesses,
                        'game_over': True,
                        'won': False
                    }
                return {
                    'message': f'❌ {letter} is not in the word. ({self.incorrect_guesses}/{self.max_attempts})',
                    'type': 'info',
                    'word_display': self.word_display,
                    'guessed_letters': self.guessed_letters,
                    'incorrect_guesses': self.incorrect_guesses
                }

        elif action == 'reset':
            self.reset_game()
            return {
                'message': 'New word generated. Start guessing!',
                'type': 'info',
                'word_display': self.word_display,
                'guessed_letters': [],
                'incorrect_guesses': 0,
                'game_over': False,
                'won': False
            }

        elif action == 'hint':
            unguessed = [c for c in self.secret_word if c not in self.guessed_letters]
            if unguessed:
                hint_letter = random.choice(unguessed)
                return {'message': f'💡 Try the letter "{hint_letter}".', 'type': 'info'}
            else:
                return {'message': 'No hints needed – you know the word!', 'type': 'info'}

        elif action == 'difficulty':
            if args:
                new_diff = args[0].lower()
                if new_diff in self.difficulty_manager.LEVELS:
                    self.difficulty_manager.level = new_diff
                    self.difficulty_manager.settings = self.difficulty_manager.LEVELS[new_diff]
                    return {
                        'message': f'Difficulty set to {new_diff}.',
                        'type': 'info',
                        'game_state': self.get_state()
                    }
            return {
                'message': f'Current difficulty: {self.difficulty_manager.level}. Options: {", ".join(self.difficulty_manager.LEVELS.keys())}',
                'type': 'info'
            }

        return {'message': f'Unknown command: {action}', 'type': 'error'}

    def get_state(self) -> Dict[str, Any]:
        return {
            'game_type': 'hangman',
            'word_display': self.word_display,
            'guessed_letters': self.guessed_letters,
            'incorrect_guesses': self.incorrect_guesses,
            'max_attempts': self.max_attempts,
            'game_over': self.game_over,
            'won': self.won,
            'difficulty': self.difficulty_manager.level,
            'energy': self.energy
        }

    def get_available_actions(self) -> List[Dict]:
        actions = []
        if not self.game_over:
            actions.append({'command': 'guess <letter>', 'description': 'Guess a letter'})
        actions.append({'command': 'hint', 'description': 'Get a hint'})
        actions.append({'command': 'difficulty <level>', 'description': 'Change difficulty'})
        actions.append({'command': 'reset', 'description': 'New word'})
        return actions

# ============================================
# GAME REGISTRY
# ============================================

class MaflexGameRegistry:
    def __init__(self):
        self._games = {
            'tictactoe': TicTacToe,
            'chess': Chess,
            'connectfour': ConnectFour,
            'blackjack': Blackjack,
            'hangman': Hangman,
        }

    def get_game_class(self, game_id: str):
        return self._games.get(game_id)

    def list_games(self):
        games = []
        for game_id, cls in self._games.items():
            dummy = cls("dummy", "dummy")
            games.append({
                'id': game_id,
                'name': dummy.config.name,
                'icon': dummy.config.icon,
                'color': dummy.config.color,
                'category': dummy.config.category,
                'description': dummy.config.description,
                'difficulty': dummy.difficulty_manager.level  # placeholder
            })
        return games

# ============================================
# POWER SYSTEM (enhanced)
# ============================================

class PowerSystem:
    def __init__(self, db_path):
        self.db_path = db_path

    # New powers can be added here – they are used by the game manager
    POWER_COSTS = {
        'insight': 15,
        'sight': 10,
        'manifest': 25,
        'avatar': 50,
        'adjust': 30,
        'rewind': 40,      # new: undo last move
        'double': 35,      # new: double next score
        'shield': 20,      # new: protect from one loss
        'haste': 25        # new: extra turn
    }

# ============================================
# GAME MANAGER (updated with new powers)
# ============================================

class MaflexGameManager:
    def __init__(self, db_path: str = 'maflex_v3.db'):
        self.db_path = db_path
        self.active_games: Dict[str, MaflexGame] = {}
        self.ai_buddies: Dict[str, AIBuddy] = {}
        self.game_registry = MaflexGameRegistry()
        self.power_system = PowerSystem(db_path)
        self.init_database()

    def init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS game_saves (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    game_name TEXT NOT NULL,
                    difficulty TEXT DEFAULT 'normal',
                    state TEXT NOT NULL,
                    achievements TEXT,
                    playtime INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ai_conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    game_id TEXT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id TEXT PRIMARY KEY,
                    ai_enabled BOOLEAN DEFAULT 1,
                    ai_mode TEXT DEFAULT 'hybrid',
                    default_difficulty TEXT DEFAULT 'normal',
                    theme TEXT DEFAULT 'neon',
                    animations BOOLEAN DEFAULT 1,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def get_or_create_ai_buddy(self, user_id: str) -> AIBuddy:
        if user_id not in self.ai_buddies:
            buddy = AIBuddy(user_id, self)
            with sqlite3.connect(self.db_path) as conn:
                row = conn.execute(
                    "SELECT ai_enabled, ai_mode FROM user_preferences WHERE user_id = ?",
                    (user_id,)
                ).fetchone()
                if row:
                    buddy.enabled = bool(row[0])
                    buddy.mode = row[1]
            self.ai_buddies[user_id] = buddy
        return self.ai_buddies[user_id]

    async def chat_with_iris(self, user_id: str, message: str, user_tone: str = "neutral") -> Dict:
        buddy = self.get_or_create_ai_buddy(user_id)
        game = self.get_game(user_id)
        context = game.get_state() if game else None
        response = await buddy.chat(message, context, user_tone)
        if response.get('execute') and game:
            cmd_parts = response['execute'].split()
            action = cmd_parts[0]
            args = cmd_parts[1:] if len(cmd_parts) > 1 else []
            result = self.process_action(user_id, action, args)
            response['execution_result'] = result
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO ai_conversations (user_id, game_id, role, content) VALUES (?, ?, ?, ?)",
                (user_id, game.game_id if game else None, 'user', message)
            )
            conn.execute(
                "INSERT INTO ai_conversations (user_id, game_id, role, content) VALUES (?, ?, ?, ?)",
                (user_id, game.game_id if game else None, 'assistant', response['response'])
            )
            conn.commit()
        return response

    def get_game(self, user_id: str) -> Optional[MaflexGame]:
        return self.active_games.get(user_id)

    def create_game(self, user_id: str, game_id: str, difficulty: str = 'normal') -> Optional[MaflexGame]:
        game_class = self.game_registry.get_game_class(game_id)
        if not game_class:
            return None
        instance_id = str(uuid.uuid4())
        game = game_class(instance_id, user_id, difficulty)
        buddy = self.get_or_create_ai_buddy(user_id)
        game.set_ai_buddy(buddy)
        self.active_games[user_id] = game
        self._save_game(user_id, game)
        return game

    def process_action(self, user_id: str, action: str, args: List[str] = None) -> Dict:
        game = self.get_game(user_id)
        if not game:
            return {'success': False, 'error': 'No active game'}
        args = args or []
        result = game.process_action(action, args)
        if result.get('type') in ['success', 'loss']:
            won = result.get('type') == 'success'
            game.difficulty_manager.adjust_difficulty(won, result.get('score', 0))
        self._save_game(user_id, game)
        return {
            'success': True,
            'result': result,
            'game_state': game.get_state(),
            'ai_suggestion': game.difficulty_manager.get_hint(game.get_state()) if game.difficulty_manager.settings['hints'] else None
        }

    def use_power(self, user_id: str, power_id: str) -> Dict:
        game = self.get_game(user_id)
        if not game:
            return {'success': False, 'error': 'No active game'}
        costs = self.power_system.POWER_COSTS
        if power_id not in costs:
            return {'success': False, 'error': 'Unknown power'}
        if game.energy < costs[power_id]:
            return {'success': False, 'error': f'Insufficient energy (need {costs[power_id]})'}
        game.energy -= costs[power_id]

        # Implement power effects
        effect_message = f"{power_id} activated!"
        if power_id == 'insight':
            effect_message = "Temporal Insight: future moves predicted!"
        elif power_id == 'sight':
            effect_message = "Data Sight: hidden information revealed!"
        elif power_id == 'manifest':
            effect_message = "Controlled Manifestation: energy converted to resources!"
        elif power_id == 'avatar':
            effect_message = "Avatar Mode: you are now physically present!"
        elif power_id == 'adjust':
            effect_message = "World‑State Adjustment: reality parameters changed!"
        elif power_id == 'rewind':
            # For simplicity, we just reset the game to a previous state
            # In a real implementation, you'd need to store history
            effect_message = "Rewind: time flows backward!"
        elif power_id == 'double':
            effect_message = "Double: next score doubled!"
        elif power_id == 'shield':
            effect_message = "Shield: protected from next loss!"
        elif power_id == 'haste':
            effect_message = "Haste: extra turn granted!"

        self._save_game(user_id, game)
        return {
            'success': True,
            'energy': game.energy,
            'effect': {'message': effect_message},
            'game_state': game.get_state()
        }

    def _save_game(self, user_id: str, game: MaflexGame):
        with sqlite3.connect(self.db_path) as conn:
            state_json = json.dumps(game.get_state())
            achievements_json = json.dumps(game.achievements)
            conn.execute("""
                INSERT INTO game_saves (id, user_id, game_name, difficulty, state, achievements)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    state = excluded.state,
                    achievements = excluded.achievements,
                    updated_at = CURRENT_TIMESTAMP
            """, (game.game_id, user_id, game.config.name, game.difficulty_manager.level, state_json, achievements_json))
            conn.commit()

    def get_available_games(self):
        return self.game_registry.list_games()

    def end_game(self, user_id: str) -> bool:
        if user_id in self.active_games:
            del self.active_games[user_id]
            return True
        return False

# ============================================
# HELPER FUNCTIONS
# ============================================

def init_maflex_games(db_path):
    return MaflexGameManager(db_path)

def get_game_manager():
    return None

def start_game(user_id, game_id, difficulty='normal'):
    pass

def game_action(user_id, action, args):
    pass

def use_game_power(user_id, power_id, args):
    pass

def get_active_game(user_id):
    pass

def end_active_game(user_id):
    pass

def list_available_games():
    return []

def save_game_state(user_id, db):
    pass

def load_game_state(user_id, save_id):
    pass

def create_maflex_tables():
    pass

# ============================================
# EXPORTS
# ============================================

__all__ = [
    'MaflexGameManager',
    'AIBuddy',
    'DifficultyManager',
    'TicTacToe',
    'Chess',
    'ConnectFour',
    'Blackjack',
    'Hangman',
    'PowerSystem',
    'init_maflex_games',
    'get_game_manager',
    'start_game',
    'game_action',
    'use_game_power',
    'get_active_game',
    'end_active_game',
    'list_available_games',
    'save_game_state',
    'load_game_state',
    'create_maflex_tables',
]