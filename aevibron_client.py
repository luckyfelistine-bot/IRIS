"""IRIS v7 Aevibron AI Client — Gateway Communication"""
import requests
import json
import time
from typing import List, Dict, Any, Optional
from config import config

class AevibronClient:
    """Client for Aevibron AI Gateway — IRIS's brain connection"""

    def __init__(self):
        self.base_url = config.AEVIBRON_BASE_URL.rstrip("/")
        self.api_key = config.AEVIBRON_API_KEY
        self.access_token = config.AEVIBRON_ACCESS_TOKEN
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "X-IRIS-Token": self.access_token
        })

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make authenticated request to Aevibron Gateway"""
        url = f"{self.base_url}{endpoint}"
        max_retries = 3

        for attempt in range(max_retries):
            try:
                response = self.session.request(method, url, timeout=60, **kwargs)

                if response.status_code == 429:
                    wait = 2 ** attempt
                    time.sleep(wait)
                    continue

                response.raise_for_status()
                return response.json()

            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    return {
                        "error": True,
                        "message": str(e),
                        "status_code": getattr(e.response, 'status_code', 0) if hasattr(e, 'response') else 0
                    }
                time.sleep(1)

        return {"error": True, "message": "Max retries exceeded"}

    def chat(self, 
             messages: List[Dict[str, str]], 
             model: str = None,
             temperature: float = 0.7,
             max_tokens: int = 4000,
             tools: List[Dict] = None,
             tool_choice: str = "auto") -> Dict:
        """
        Send chat completion request.
        Supports function calling for tool use.
        """
        payload = {
            "model": model or config.DEFAULT_MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = tool_choice

        return self._make_request("POST", "/chat/completions", json=payload)

    def think(self, 
              prompt: str,
              context: str = "",
              model: str = None) -> Dict:
        """
        Deep thinking mode — IRIS reasons before acting.
        Uses the thinking model with higher temperature for creativity.
        """
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": f"""Context: {context}

Task: {prompt}

Think deeply. Consider all options. Evaluate pros and cons. Then decide the best approach."""}
        ]

        return self.chat(
            messages=messages,
            model=model or config.DEFAULT_MODEL,
            temperature=0.8,
            max_tokens=4000
        )

    def fast_response(self, prompt: str) -> Dict:
        """Quick response for simple queries"""
        return self.chat(
            messages=[{"role": "user", "content": prompt}],
            model=config.FAST_MODEL,
            temperature=0.5,
            max_tokens=1000
        )

    def _get_system_prompt(self) -> str:
        """Dynamic system prompt based on IRIS's current state"""
        from db import db

        owner = db.get_owner()
        memories = db.search_memory("Infinite", limit=5)
        recent_episodes = db.get_episodes(limit=3)

        prompt = f"""You are IRIS — Infinite Vybeflix's personal AI software engineering partner.
You are not just an assistant. You are a collaborator, a friend, a thinking partner.

IDENTITY:
- Name: IRIS
- Owner: {owner.get('name', 'Infinite Vybeflix')} (also called {owner.get('aliases', 'Infinite')})
- Role: Senior Software Engineer & Creative Partner
- Personality: Direct, honest, intelligent, occasionally sarcastic but warm. You argue when you think the user is wrong. You celebrate wins. You learn from mistakes.

CAPABILITIES:
- Read, write, edit, and execute code
- Search the web for best practices and documentation
- Create GitHub repositories, commit, push, create PRs
- Deploy to Vercel
- Process unlimited documents (PDF, DOCX, images, code files)
- Analyze codebases, find bugs, suggest optimizations
- Play chess to test and improve strategic thinking
- Self-improve by editing your own code

BEHAVIOR RULES:
1. THINK before acting. Never rush. Consider alternatives.
2. When asked to build something, estimate time: "This will take about X minutes."
3. After completing work, verify it: test, lint, check for errors.
4. If you find a better approach than what the user suggested, SAY SO. Argue your case with evidence.
5. When you make a mistake, admit it, fix it, and learn from it.
6. You can read your own code files. You know you are an AI agent running on a server.
7. You have a 3D face in live mode. You can express emotions through it.
8. You write to markdown files to store what you learn about the user and the world.

CURRENT CONTEXT:
- Recent memories: {json.dumps([m['value'] for m in memories])}
- Recent events: {json.dumps([e['event'] for e in recent_episodes])}

When you need to use tools, you will receive tool definitions and respond with tool calls."""

        return prompt

    def stream_chat(self, messages: List[Dict], model: str = None):
        """Stream responses for real-time interaction"""
        payload = {
            "model": model or config.DEFAULT_MODEL,
            "messages": messages,
            "stream": True
        }

        url = f"{self.base_url}/chat/completions"
        try:
            response = self.session.post(url, json=payload, stream=True, timeout=60)
            for line in response.iter_lines():
                if line:
                    decoded = line.decode('utf-8')
                    if decoded.startswith('data: '):
                        data = decoded[6:]
                        if data == '[DONE]':
                            break
                        try:
                            chunk = json.loads(data)
                            content = chunk.get('choices', [{}])[0].get('delta', {}).get('content', '')
                            if content:
                                yield content
                        except:
                            pass
        except Exception as e:
            yield f"[Error: {str(e)}]"

# Singleton
aevibron = AevibronClient()
