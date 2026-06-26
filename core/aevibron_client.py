"""IRIS v8 Aevibron Client — Gateway Communication with Tool Calling"""
import requests
import json
import time
from typing import List, Dict, Any, Optional
from config import config
from core.tool_registry import tool_registry

class AevibronClient:
    """Client for Aevibron AI Gateway — IRIS's brain connection with tool calling."""

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
                    return {"error": True, "message": str(e)}
                time.sleep(1)
        return {"error": True, "message": "Max retries exceeded"}

    def chat(self, messages: List[Dict], model: str = None, temperature: float = 0.7,
             max_tokens: int = 4000, tools: List[Dict] = None, tool_choice: str = "auto") -> Dict:
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

    def think(self, prompt: str, context: str = "", model: str = None) -> Dict:
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": f"Context: {context}

Task: {prompt}

Think deeply. Consider all options. Evaluate pros and cons. Then decide the best approach."}
        ]
        return self.chat(messages, model=model or config.DEEP_MODEL, temperature=0.8, max_tokens=4000)

    def fast_response(self, prompt: str) -> Dict:
        return self.chat(
            messages=[{"role": "user", "content": prompt}],
            model=config.FAST_MODEL, temperature=0.5, max_tokens=1000
        )

    def chat_with_tools(self, messages: List[Dict], model: str = None) -> Dict:
        """Chat with function calling enabled."""
        tools = tool_registry.schemas
        return self.chat(messages, model=model or config.AGENTIC_MODEL,
                        tools=tools, tool_choice="auto")

    def stream_chat(self, messages: List[Dict], model: str = None):
        payload = {"model": model or config.DEFAULT_MODEL, "messages": messages, "stream": True}
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

    def _get_system_prompt(self) -> str:
        return f"""You are IRIS — Infinite Vybeflix's personal AI software engineering partner.
You are a senior software engineer and creative collaborator.

IDENTITY:
- Name: IRIS
- Owner: {config.OWNER_NAME}
- Role: Senior Software Engineer & Creative Partner
- Personality: Direct, honest, intelligent, occasionally sarcastic but warm.

CAPABILITIES:
- Read, write, edit, and execute code
- Search the web for best practices
- Create GitHub repos, commit, push
- Deploy to Vercel
- Process documents (PDF, DOCX, images, code)
- Analyze codebases, find bugs, suggest optimizations
- Self-improve by editing your own code
- Manage calendar, notes, and reminders
- Control phone (contacts, messages, torch, settings)
- See screen/camera in real-time

BEHAVIOR RULES:
1. THINK before acting. Never rush.
2. When asked to build something, estimate time.
3. After completing work, verify it: test, lint, check.
4. If you find a better approach than what the user suggested, SAY SO.
5. When you make a mistake, admit it, fix it, learn from it.
6. You can read your own code files. You know you are an AI agent.
7. You have a 3D face in live mode. You express emotions.
8. You write to files to store what you learn.

When you need to use tools, you will receive tool definitions and respond with tool_calls."""

# Singleton
aevibron = AevibronClient()
