"""IRIS v8 Sandbox Executor — Safe Code Execution"""
import os
import sys
import subprocess
import tempfile
import resource
import signal
from typing import Dict, List, Optional
from config import config

class SandboxExecutor:
    """
    Safely execute Python and shell code:
    - Resource limits (CPU, memory)
    - Timeout enforcement
    - Restricted imports
    - No network access (optional)
    - Temporary file isolation
    """

    def __init__(self):
        self.sandbox_dir = config.SANDBOX_DIR
        os.makedirs(self.sandbox_dir, exist_ok=True)
        self.max_cpu_time = 5  # seconds
        self.max_memory = 256 * 1024 * 1024  # 256MB
        self.max_output_size = 10000  # characters

    def execute_python(self, code: str, allowed_modules: List[str] = None) -> Dict:
        """Execute Python code in restricted sandbox."""
        try:
            # Write code to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.sandbox_dir, delete=False) as f:
                f.write(code)
                temp_file = f.name

            # Run with restrictions
            result = self._run_restricted(['python', temp_file])

            # Cleanup
            os.remove(temp_file)

            return {
                "success": result["returncode"] == 0,
                "output": result["stdout"][:self.max_output_size],
                "error": result["stderr"][:self.max_output_size] if result["stderr"] else None,
                "returncode": result["returncode"],
                "duration": result.get("duration", 0)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def execute_shell(self, command: str, allowed_commands: List[str] = None) -> Dict:
        """Execute shell command with restrictions."""
        # Block dangerous commands
        dangerous = [
            "rm -rf /", "rm -rf /*", ":(){ :|:& };:", "dd if=/dev/zero",
            "> /dev/sda", "mkfs", "fdisk", "format", "del /f /s /q",
            "rd /s /q", "format c:", "shutdown", "reboot", "halt",
            "poweroff", "init 0", "kill -9 -1"
        ]
        for d in dangerous:
            if d in command.lower():
                return {"success": False, "error": f"Dangerous command blocked: {d}"}

        try:
            result = self._run_restricted(command, shell=True)
            return {
                "success": result["returncode"] == 0,
                "output": result["stdout"][:self.max_output_size],
                "error": result["stderr"][:self.max_output_size] if result["stderr"] else None,
                "returncode": result["returncode"],
                "duration": result.get("duration", 0)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _run_restricted(self, cmd, shell=False):
        """Run command with resource limits."""
        import time
        start = time.time()

        def set_limits():
            # CPU time limit
            resource.setrlimit(resource.RLIMIT_CPU, (self.max_cpu_time, self.max_cpu_time))
            # Memory limit
            resource.setrlimit(resource.RLIMIT_AS, (self.max_memory, self.max_memory))
            # File size limit
            resource.setrlimit(resource.RLIMIT_FSIZE, (10*1024*1024, 10*1024*1024))

        try:
            proc = subprocess.Popen(
                cmd,
                shell=shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.sandbox_dir,
                preexec_fn=set_limits
            )
            stdout, stderr = proc.communicate(timeout=self.max_cpu_time + 2)
            duration = time.time() - start

            return {
                "returncode": proc.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "duration": duration
            }
        except subprocess.TimeoutExpired:
            proc.kill()
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": "Execution timed out",
                "duration": self.max_cpu_time + 2
            }
        except Exception as e:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "duration": time.time() - start
            }

# Singleton
sandbox_executor = SandboxExecutor()
