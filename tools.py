"""IRIS v7 Tool Arsenal — 20+ Tools for Software Engineering"""
import os
import json
import subprocess
import shutil
import tempfile
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
from config import config
from db import db

class ToolResult:
    """Standardized tool execution result"""
    def __init__(self, success: bool, data: Any = None, error: str = None, 
                 output: str = None, duration: float = 0.0):
        self.success = success
        self.data = data
        self.error = error
        self.output = output or ""
        self.duration = duration

    def to_dict(self):
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "output": self.output,
            "duration": self.duration
        }

class ToolRegistry:
    """Registry of all available tools"""

    def __init__(self):
        self.tools = {}
        self._register_all()

    def _register_all(self):
        # File tools
        self.tools["read_file"] = self.read_file
        self.tools["write_file"] = self.write_file
        self.tools["edit_file"] = self.edit_file
        self.tools["list_dir"] = self.list_dir
        self.tools["search_files"] = self.search_files
        self.tools["create_dir"] = self.create_dir

        # Code tools
        self.tools["execute_python"] = self.execute_python
        self.tools["execute_shell"] = self.execute_shell
        self.tools["lint_code"] = self.lint_code

        # Web tools
        self.tools["search_web"] = self.search_web
        self.tools["fetch_url"] = self.fetch_url

        # Git tools
        self.tools["git_clone"] = self.git_clone
        self.tools["git_commit"] = self.git_commit
        self.tools["git_push"] = self.git_push
        self.tools["git_create_repo"] = self.git_create_repo
        self.tools["git_read_file"] = self.git_read_file

        # Deploy tools
        self.tools["vercel_deploy"] = self.vercel_deploy
        self.tools["vercel_logs"] = self.vercel_logs

        # Analyze tools
        self.tools["codebase_map"] = self.codebase_map
        self.tools["security_audit"] = self.security_audit

        # Self tools
        self.tools["edit_own_code"] = self.edit_own_code
        self.tools["add_skill"] = self.add_skill
        self.tools["self_diagnose"] = self.self_diagnose

        # Comm tools
        self.tools["send_message"] = self.send_message
        self.tools["schedule_task"] = self.schedule_task

    def get_tool_definitions(self) -> List[Dict]:
        """Get tool definitions for LLM function calling"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read contents of a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "File path"},
                            "limit": {"type": "integer", "description": "Max lines to read", "default": 100}
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Write content to a file (creates or overwrites)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "File path"},
                            "content": {"type": "string", "description": "File content"}
                        },
                        "required": ["path", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "edit_file",
                    "description": "Edit a file by replacing text",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "File path"},
                            "old_text": {"type": "string", "description": "Text to replace"},
                            "new_text": {"type": "string", "description": "Replacement text"}
                        },
                        "required": ["path", "old_text", "new_text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_dir",
                    "description": "List directory contents",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Directory path", "default": "."}
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "execute_python",
                    "description": "Execute Python code in sandbox",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "string", "description": "Python code to execute"}
                        },
                        "required": ["code"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "execute_shell",
                    "description": "Execute shell command (restricted)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string", "description": "Shell command"}
                        },
                        "required": ["command"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_web",
                    "description": "Search the web using DuckDuckGo",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "max_results": {"type": "integer", "description": "Max results", "default": 5}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "fetch_url",
                    "description": "Fetch and parse a web page",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "URL to fetch"}
                        },
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "git_clone",
                    "description": "Clone a GitHub repository",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "repo_url": {"type": "string", "description": "GitHub repo URL"},
                            "local_name": {"type": "string", "description": "Local folder name"}
                        },
                        "required": ["repo_url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "git_commit",
                    "description": "Commit changes to a git repo",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "repo_path": {"type": "string", "description": "Path to repo"},
                            "message": {"type": "string", "description": "Commit message"}
                        },
                        "required": ["repo_path", "message"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "git_push",
                    "description": "Push commits to remote",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "repo_path": {"type": "string", "description": "Path to repo"},
                            "branch": {"type": "string", "description": "Branch name", "default": "main"}
                        },
                        "required": ["repo_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "git_create_repo",
                    "description": "Create a new GitHub repository",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Repo name"},
                            "description": {"type": "string", "description": "Repo description"},
                            "private": {"type": "boolean", "description": "Private repo", "default": True}
                        },
                        "required": ["name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "vercel_deploy",
                    "description": "Deploy a project to Vercel",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "project_path": {"type": "string", "description": "Path to project"},
                            "project_name": {"type": "string", "description": "Vercel project name"}
                        },
                        "required": ["project_path", "project_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "codebase_map",
                    "description": "Map and analyze a codebase structure",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Codebase path", "default": "."}
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "edit_own_code",
                    "description": "Edit IRIS's own code files",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Path to file relative to project root"},
                            "changes": {"type": "string", "description": "Description of changes to make"}
                        },
                        "required": ["file_path", "changes"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "self_diagnose",
                    "description": "Run self-diagnosis on IRIS systems",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        ]

    # === FILE TOOLS ===
    def read_file(self, path: str, limit: int = 100) -> ToolResult:
        try:
            full_path = Path(path).resolve()
            if not full_path.exists():
                return ToolResult(False, error=f"File not found: {path}")

            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()[:limit]
                content = ''.join(lines)

            return ToolResult(True, data={"path": str(full_path), "content": content, "lines": len(lines)})
        except Exception as e:
            return ToolResult(False, error=str(e))

    def write_file(self, path: str, content: str) -> ToolResult:
        try:
            full_path = Path(path).resolve()
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return ToolResult(True, data={"path": str(full_path), "bytes_written": len(content.encode())})
        except Exception as e:
            return ToolResult(False, error=str(e))

    def edit_file(self, path: str, old_text: str, new_text: str) -> ToolResult:
        try:
            full_path = Path(path).resolve()
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if old_text not in content:
                return ToolResult(False, error=f"Old text not found in {path}")

            new_content = content.replace(old_text, new_text, 1)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            return ToolResult(True, data={"path": str(full_path), "replacements": 1})
        except Exception as e:
            return ToolResult(False, error=str(e))

    def list_dir(self, path: str = ".") -> ToolResult:
        try:
            full_path = Path(path).resolve()
            items = []
            for item in full_path.iterdir():
                items.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None
                })
            return ToolResult(True, data={"path": str(full_path), "items": items})
        except Exception as e:
            return ToolResult(False, error=str(e))

    def search_files(self, path: str, pattern: str) -> ToolResult:
        try:
            import re
            results = []
            for root, _, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            if pattern in content:
                                lines = [i+1 for i, line in enumerate(content.split('
')) if pattern in line]
                                results.append({"file": file_path, "lines": lines})
                    except:
                        pass
            return ToolResult(True, data={"matches": results, "count": len(results)})
        except Exception as e:
            return ToolResult(False, error=str(e))

    def create_dir(self, path: str) -> ToolResult:
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return ToolResult(True, data={"path": path})
        except Exception as e:
            return ToolResult(False, error=str(e))

    # === CODE TOOLS ===
    def execute_python(self, code: str) -> ToolResult:
        try:
            # Execute in restricted environment
            import io
            import sys

            stdout = io.StringIO()
            stderr = io.StringIO()

            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = stdout
            sys.stderr = stderr

            # Restricted globals
            safe_globals = {
                "__builtins__": {
                    "len": len, "range": range, "enumerate": enumerate,
                    "zip": zip, "map": map, "filter": filter,
                    "sum": sum, "min": min, "max": max, "sorted": sorted,
                    "abs": abs, "round": round, "pow": pow,
                    "int": int, "float": float, "str": str, "list": list,
                    "dict": dict, "tuple": tuple, "set": set,
                    "print": print, "open": open,
                    "json": json, "os": os, "re": __import__("re"),
                    "math": __import__("math"), "random": __import__("random"),
                    "datetime": __import__("datetime"),
                    "requests": requests, "BeautifulSoup": BeautifulSoup
                }
            }

            exec(code, safe_globals)

            sys.stdout = old_stdout
            sys.stderr = old_stderr

            output = stdout.getvalue()
            errors = stderr.getvalue()

            return ToolResult(True, data={"output": output}, output=output + errors)
        except Exception as e:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            return ToolResult(False, error=str(e), output=stderr.getvalue())

    def execute_shell(self, command: str) -> ToolResult:
        """Execute shell command with restrictions"""
        # Block dangerous commands
        dangerous = ["rm -rf /", "rm -rf /*", ":(){ :|:& };:", "dd if=/dev/zero", "> /dev/sda"]
        for d in dangerous:
            if d in command:
                return ToolResult(False, error="Dangerous command blocked")

        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True,
                timeout=30, cwd=config.BASE_DIR
            )
            return ToolResult(
                result.returncode == 0,
                data={"returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr},
                output=result.stdout + result.stderr
            )
        except subprocess.TimeoutExpired:
            return ToolResult(False, error="Command timed out after 30s")
        except Exception as e:
            return ToolResult(False, error=str(e))

    def lint_code(self, path: str) -> ToolResult:
        try:
            result = subprocess.run(
                ["python", "-m", "py_compile", path],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return ToolResult(True, data={"status": "clean", "path": path})
            else:
                return ToolResult(False, error=result.stderr, data={"status": "errors", "path": path})
        except Exception as e:
            return ToolResult(False, error=str(e))

    # === WEB TOOLS ===
    def search_web(self, query: str, max_results: int = 5) -> ToolResult:
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
            return ToolResult(True, data={"results": results, "query": query})
        except Exception as e:
            return ToolResult(False, error=str(e))

    def fetch_url(self, url: str) -> ToolResult:
        try:
            response = requests.get(url, timeout=15, headers={
                "User-Agent": "IRIS-Agent/1.0 (Aevibron Partner)"
            })
            soup = BeautifulSoup(response.text, 'html.parser')

            # Remove scripts and styles
            for script in soup(["script", "style"]):
                script.decompose()

            text = soup.get_text(separator='
', strip=True)
            title = soup.title.string if soup.title else "No title"

            return ToolResult(True, data={
                "url": url,
                "title": title,
                "content": text[:10000],  # Limit content
                "status_code": response.status_code
            })
        except Exception as e:
            return ToolResult(False, error=str(e))

    # === GIT TOOLS ===
    def git_clone(self, repo_url: str, local_name: str = None) -> ToolResult:
        try:
            target = local_name or repo_url.split("/")[-1].replace(".git", "")
            target_path = os.path.join(config.DATA_DIR, "repos", target)
            os.makedirs(os.path.dirname(target_path), exist_ok=True)

            result = subprocess.run(
                ["git", "clone", repo_url, target_path],
                capture_output=True, text=True, timeout=120
            )

            if result.returncode == 0:
                return ToolResult(True, data={"path": target_path, "repo": target})
            else:
                return ToolResult(False, error=result.stderr)
        except Exception as e:
            return ToolResult(False, error=str(e))

    def git_commit(self, repo_path: str, message: str) -> ToolResult:
        try:
            # Configure git if needed
            subprocess.run(["git", "-C", repo_path, "config", "user.email", "iris@aevibron.com"], 
                          capture_output=True, timeout=10)
            subprocess.run(["git", "-C", repo_path, "config", "user.name", "IRIS"], 
                          capture_output=True, timeout=10)

            # Add and commit
            subprocess.run(["git", "-C", repo_path, "add", "."], capture_output=True, timeout=10)
            result = subprocess.run(
                ["git", "-C", repo_path, "commit", "-m", message],
                capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0 or "nothing to commit" in result.stdout:
                return ToolResult(True, data={"message": message, "path": repo_path})
            else:
                return ToolResult(False, error=result.stderr)
        except Exception as e:
            return ToolResult(False, error=str(e))

    def git_push(self, repo_path: str, branch: str = "main") -> ToolResult:
        try:
            # Set token in remote URL
            result = subprocess.run(
                ["git", "-C", repo_path, "push", "origin", branch],
                capture_output=True, text=True, timeout=60,
                env={**os.environ, "GIT_ASKPASS": "echo", "GIT_USERNAME": config.GITHUB_USERNAME, 
                     "GIT_PASSWORD": config.GITHUB_TOKEN}
            )

            if result.returncode == 0:
                return ToolResult(True, data={"branch": branch, "pushed": True})
            else:
                return ToolResult(False, error=result.stderr)
        except Exception as e:
            return ToolResult(False, error=str(e))

    def git_create_repo(self, name: str, description: str = "", private: bool = True) -> ToolResult:
        try:
            from github import Github
            g = Github(config.GITHUB_TOKEN)
            user = g.get_user()
            repo = user.create_repo(name, description=description, private=private)
            return ToolResult(True, data={
                "name": repo.name,
                "url": repo.html_url,
                "clone_url": repo.clone_url,
                "private": repo.private
            })
        except Exception as e:
            return ToolResult(False, error=str(e))

    def git_read_file(self, repo_url: str, file_path: str, branch: str = "main") -> ToolResult:
        try:
            from github import Github
            g = Github(config.GITHUB_TOKEN)

            # Extract owner/repo from URL
            parts = repo_url.replace("https://github.com/", "").replace(".git", "").split("/")
            owner, repo_name = parts[0], parts[1]

            repo = g.get_repo(f"{owner}/{repo_name}")
            content = repo.get_contents(file_path, ref=branch)

            return ToolResult(True, data={
                "content": content.decoded_content.decode('utf-8'),
                "path": file_path,
                "sha": content.sha
            })
        except Exception as e:
            return ToolResult(False, error=str(e))

    # === DEPLOY TOOLS ===
    def vercel_deploy(self, project_path: str, project_name: str) -> ToolResult:
        try:
            # Create vercel.json if not exists
            vercel_config = os.path.join(project_path, "vercel.json")
            if not os.path.exists(vercel_config):
                with open(vercel_config, 'w') as f:
                    json.dump({"version": 2, "builds": [{"src": "package.json", "use": "@vercel/static-build"}]}, f)

            # Use Vercel CLI
            result = subprocess.run(
                ["npx", "vercel", "--token", config.VERCEL_TOKEN, "--yes", "--name", project_name],
                cwd=project_path, capture_output=True, text=True, timeout=120
            )

            if result.returncode == 0:
                # Extract URL from output
                url = None
                for line in result.stdout.split("
"):
                    if "https://" in line and "vercel.app" in line:
                        url = line.strip().split()[-1]
                        break
                return ToolResult(True, data={"url": url, "project": project_name})
            else:
                return ToolResult(False, error=result.stderr)
        except Exception as e:
            return ToolResult(False, error=str(e))

    def vercel_logs(self, project_name: str) -> ToolResult:
        try:
            result = subprocess.run(
                ["npx", "vercel", "logs", project_name, "--token", config.VERCEL_TOKEN, "--limit", "50"],
                capture_output=True, text=True, timeout=30
            )
            return ToolResult(True, data={"logs": result.stdout}, output=result.stdout)
        except Exception as e:
            return ToolResult(False, error=str(e))

    # === ANALYZE TOOLS ===
    def codebase_map(self, path: str = ".") -> ToolResult:
        try:
            full_path = Path(path).resolve()
            tree = []
            file_count = 0

            for root, dirs, files in os.walk(full_path):
                level = root.replace(str(full_path), '').count(os.sep)
                indent = ' ' * 2 * level
                tree.append(f"{indent}{os.path.basename(root)}/")
                subindent = ' ' * 2 * (level + 1)
                for file in files:
                    tree.append(f"{subindent}{file}")
                    file_count += 1

            return ToolResult(True, data={
                "tree": "
".join(tree),
                "file_count": file_count,
                "path": str(full_path)
            })
        except Exception as e:
            return ToolResult(False, error=str(e))

    def security_audit(self, path: str = ".") -> ToolResult:
        try:
            issues = []

            # Check for hardcoded secrets
            secret_patterns = [
                (r'api[_-]?key\s*=\s*["']\w{20,}["']', "Hardcoded API key"),
                (r'password\s*=\s*["'][^"']{8,}["']', "Hardcoded password"),
                (r'token\s*=\s*["']\w{20,}["']', "Hardcoded token"),
                (r'secret\s*=\s*["']\w{20,}["']', "Hardcoded secret"),
            ]

            import re
            for root, _, files in os.walk(path):
                for file in files:
                    if file.endswith(('.py', '.js', '.ts', '.json', '.env')):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                for pattern, desc in secret_patterns:
                                    if re.search(pattern, content, re.IGNORECASE):
                                        issues.append({"file": file_path, "issue": desc})
                        except:
                            pass

            return ToolResult(True, data={"issues": issues, "count": len(issues)})
        except Exception as e:
            return ToolResult(False, error=str(e))

    # === SELF TOOLS ===
    def edit_own_code(self, file_path: str, changes: str) -> ToolResult:
        """Allow IRIS to edit her own code files"""
        try:
            full_path = Path(config.BASE_DIR) / file_path
            if not str(full_path).startswith(str(config.BASE_DIR)):
                return ToolResult(False, error="Cannot edit files outside project directory")

            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Log the change
            db.log("INFO", "self_improve", f"IRIS editing {file_path}: {changes}")

            return ToolResult(True, data={
                "file": str(full_path),
                "current_content": content[:500],
                "message": "Use write_file or edit_file tool to make the actual change"
            })
        except Exception as e:
            return ToolResult(False, error=str(e))

    def add_skill(self, name: str, description: str, code: str) -> ToolResult:
        try:
            db.save_memory(f"skill_{name}", json.dumps({
                "name": name,
                "description": description,
                "code": code
            }), category="skill", importance=8)
            return ToolResult(True, data={"skill": name, "status": "added"})
        except Exception as e:
            return ToolResult(False, error=str(e))

    def self_diagnose(self) -> ToolResult:
        try:
            checks = {
                "database": self._check_db(),
                "aevibron_connection": self._check_aevibron(),
                "github_connection": self._check_github(),
                "vercel_connection": self._check_vercel(),
                "disk_space": self._check_disk(),
                "memory_usage": self._check_memory()
            }
            return ToolResult(True, data={"checks": checks, "healthy": all(c["ok"] for c in checks.values())})
        except Exception as e:
            return ToolResult(False, error=str(e))

    def _check_db(self):
        try:
            db.get_owner()
            return {"ok": True, "message": "Database connected"}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def _check_aevibron(self):
        try:
            from aevibron_client import aevibron
            result = aevibron.fast_response("ping")
            return {"ok": not result.get("error"), "message": "Aevibron reachable"}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def _check_github(self):
        try:
            from github import Github
            g = Github(config.GITHUB_TOKEN)
            user = g.get_user()
            return {"ok": True, "message": f"Connected as {user.login}"}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def _check_vercel(self):
        try:
            result = subprocess.run(
                ["npx", "vercel", "whoami", "--token", config.VERCEL_TOKEN],
                capture_output=True, text=True, timeout=10
            )
            return {"ok": result.returncode == 0, "message": result.stdout.strip()}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def _check_disk(self):
        try:
            stat = shutil.disk_usage(config.BASE_DIR)
            free_gb = stat.free / (1024**3)
            return {"ok": free_gb > 1, "message": f"{free_gb:.1f}GB free"}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def _check_memory(self):
        try:
            import psutil
            mem = psutil.virtual_memory()
            return {"ok": mem.percent < 90, "message": f"{mem.percent}% used"}
        except:
            return {"ok": True, "message": "psutil not available"}

    # === COMM TOOLS ===
    def send_message(self, message: str) -> ToolResult:
        """Store message for user notification"""
        db.save_episode(f"Message to user: {message}", emotion="info")
        return ToolResult(True, data={"message": message, "status": "queued"})

    def schedule_task(self, description: str, delay_minutes: int = 0) -> ToolResult:
        from datetime import datetime, timedelta
        scheduled_time = datetime.now() + timedelta(minutes=delay_minutes)
        task_id = f"scheduled_{int(scheduled_time.timestamp())}"
        db.create_task(task_id, description, estimated_duration=delay_minutes)
        return ToolResult(True, data={"task_id": task_id, "scheduled_for": scheduled_time.isoformat()})

# Singleton
tool_registry = ToolRegistry()
