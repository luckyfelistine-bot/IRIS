"""IRIS v8 Self-Improvement — AST-Based Safe Code Editing"""
import os
import json
import shutil
import subprocess
import ast
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from config import config
from core.models import ToolResult

class SelfImprovementEngine:
    """IRIS reads her own code, finds bugs, fixes them safely using AST."""

    def __init__(self):
        self.backup_dir = config.BACKUPS_DIR
        self.sandbox_dir = config.SANDBOX_DIR
        self.change_log = []
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(self.sandbox_dir, exist_ok=True)

    def analyze_self(self) -> Dict:
        """Analyze IRIS codebase for issues using AST."""
        issues = []
        py_files = list(Path(config.BASE_DIR).rglob("*.py"))

        for file_path in py_files:
            if "__pycache__" in str(file_path):
                continue
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    source = f.read()

                # AST parse
                try:
                    tree = ast.parse(source)
                except SyntaxError as e:
                    issues.append({"type": "syntax", "file": str(file_path), "line": e.lineno,
                                   "description": str(e), "severity": "critical"})
                    continue

                # Check for bare except
                for node in ast.walk(tree):
                    if isinstance(node, ast.ExceptHandler):
                        if node.type is None:
                            issues.append({"type": "code_quality", "file": str(file_path),
                                           "line": node.lineno, "description": "Bare except clause",
                                           "severity": "high"})

                # Check for TODO/FIXME
                for i, line in enumerate(source.split("
"), 1):
                    if any(marker in line for marker in ["TODO", "FIXME", "HACK", "BUG", "XXX"]):
                        issues.append({"type": "todo", "file": str(file_path), "line": i,
                                       "description": line.strip(), "severity": "medium"})

                # Check for hardcoded secrets
                for i, line in enumerate(source.split("
"), 1):
                    low = line.lower()
                    if any(p in low for p in ["api_key = ", "password = ", "token = ", "secret = "]):
                        if "os.getenv" not in low:
                            issues.append({"type": "security", "file": str(file_path), "line": i,
                                           "description": "Potential hardcoded secret", "severity": "critical"})

                # Check for unused imports
                imported = []
                used = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imported.append(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        imported.append(node.module)
                    elif isinstance(node, ast.Name):
                        used.add(node.id)

                for imp in imported:
                    base = imp.split(".")[0]
                    if base not in ["os", "sys", "json", "re", "typing", "datetime", "time", "pathlib"]:
                        if base not in used and source.count(base + ".") < 2:
                            issues.append({"type": "code_quality", "file": str(file_path), "line": 1,
                                           "description": f"Potentially unused import: {imp}", "severity": "low"})

            except Exception as e:
                issues.append({"type": "error", "file": str(file_path),
                               "description": f"Failed to analyze: {e}", "severity": "low"})

        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        issues.sort(key=lambda x: severity_order.get(x["severity"], 4))

        return {
            "total_files": len(py_files), "total_issues": len(issues),
            "critical": len([i for i in issues if i["severity"] == "critical"]),
            "high": len([i for i in issues if i["severity"] == "high"]),
            "medium": len([i for i in issues if i["severity"] == "medium"]),
            "low": len([i for i in issues if i["severity"] == "low"]),
            "issues": issues[:50]
        }

    def create_backup(self, file_path: str) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{Path(file_path).stem}_{timestamp}{Path(file_path).suffix}"
        backup_path = os.path.join(self.backup_dir, backup_name)
        shutil.copy2(file_path, backup_path)
        return backup_path

    def apply_fix(self, file_path: str, old_text: str, new_text: str) -> ToolResult:
        """Apply a fix with AST validation."""
        try:
            full_path = Path(file_path).resolve()
            if not str(full_path).startswith(str(config.BASE_DIR)):
                return ToolResult(success=False, error="Cannot edit files outside project")

            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()

            if old_text not in content:
                return ToolResult(success=False, error="Old text not found in file")

            new_content = content.replace(old_text, new_text, 1)

            # AST validate
            try:
                ast.parse(new_content)
            except SyntaxError as e:
                return ToolResult(success=False, error=f"AST validation failed: {e}")

            # Test in sandbox
            sandbox_file = os.path.join(self.sandbox_dir, Path(file_path).name)
            with open(sandbox_file, "w", encoding="utf-8") as f:
                f.write(new_content)

            test_result = subprocess.run(["python", "-m", "py_compile", sandbox_file],
                                         capture_output=True, text=True, timeout=10)
            if test_result.returncode != 0:
                return ToolResult(success=False, error=f"Syntax check failed: {test_result.stderr}")

            # Backup and apply
            backup = self.create_backup(str(full_path))
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(new_content)

            self._log_change(str(full_path), old_text[:200], new_text[:200], backup, "success")
            return ToolResult(success=True, data={"file": str(full_path), "backup": backup, "tested": True})

        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def _log_change(self, file_path: str, old_text: str, new_text: str, backup: str, status: str):
        change = {
            "timestamp": datetime.now().isoformat(), "file": file_path,
            "old": old_text[:200], "new": new_text[:200], "backup": backup, "status": status
        }
        self.change_log.append(change)
        log_file = os.path.join(config.SELF_DIR, "improvements.md")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"
## {change['timestamp']}
**File:** `{file_path}`
**Status:** {status}

")

    def get_change_history(self) -> List[Dict]:
        return self.change_log

    def get_own_codebase_map(self) -> Dict:
        py_files = []
        total_lines = 0
        for file_path in Path(config.BASE_DIR).rglob("*.py"):
            if "__pycache__" in str(file_path):
                continue
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                line_count = len(lines)
                total_lines += line_count
                classes = []
                functions = []
                for i, line in enumerate(lines):
                    stripped = line.strip()
                    if stripped.startswith("class "):
                        classes.append({"name": stripped.split("(")[0].replace("class ", ""), "line": i+1})
                    elif stripped.startswith("def ") and not stripped.startswith("def __"):
                        functions.append({"name": stripped.split("(")[0].replace("def ", ""), "line": i+1})
                py_files.append({"path": str(file_path.relative_to(config.BASE_DIR)),
                                 "lines": line_count, "classes": classes, "functions": functions})
            except: pass
        return {"total_files": len(py_files), "total_lines": total_lines, "files": py_files}

# Singleton
self_improvement = SelfImprovementEngine()
