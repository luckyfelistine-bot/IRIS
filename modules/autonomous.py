"""IRIS v8 Autonomous Worker — Background Task Scheduler & Executor"""
import os
import json
import threading
import time
import queue
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from config import config
from core.db import db

class AutonomousEngine:
    """
    IRIS autonomous background worker:
    - Schedule tasks for future execution
    - Recurring tasks (cron-like)
    - Priority queue
    - Background thread execution
    - Self-improvement tasks
    - Notification checks
    """

    def __init__(self):
        self.running = False
        self.worker_thread = None
        self.task_queue = queue.PriorityQueue()
        self.scheduled_tasks = []
        self.completed_tasks = []
        self.failed_tasks = []
        self.callbacks = {}
        self._lock = threading.Lock()

    def start(self) -> Dict:
        """Start the autonomous worker."""
        if self.running:
            return {"success": False, "message": "Already running"}
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        return {"success": True, "message": "Autonomous worker started"}

    def stop(self) -> Dict:
        """Stop the autonomous worker."""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=2)
        return {"success": True, "message": "Autonomous worker stopped"}

    def get_status(self) -> Dict:
        return {
            "running": self.running,
            "queue_size": self.task_queue.qsize(),
            "scheduled": len(self.scheduled_tasks),
            "completed": len(self.completed_tasks),
            "failed": len(self.failed_tasks)
        }

    def queue_task(self, description: str, priority: int = 5, estimated_minutes: int = 10,
                   task_type: str = "general", callback: Callable = None) -> str:
        """Queue a task for immediate execution."""
        task_id = f"task_{int(time.time())}_{os.urandom(4).hex()}"
        task = {
            "id": task_id,
            "description": description,
            "priority": priority,
            "estimated_minutes": estimated_minutes,
            "type": task_type,
            "created_at": datetime.now().isoformat(),
            "status": "queued"
        }
        db.create_task(task_id, description, priority, estimated_minutes)
        self.task_queue.put((priority, task_id, task))
        if callback:
            self.callbacks[task_id] = callback
        return task_id

    def schedule_task(self, description: str, run_at: datetime, recurring: bool = False,
                      interval_hours: int = 24, task_type: str = "general") -> str:
        """Schedule a task for future execution."""
        task_id = f"scheduled_{int(run_at.timestamp())}_{os.urandom(4).hex()}"
        task = {
            "id": task_id,
            "description": description,
            "run_at": run_at.isoformat(),
            "recurring": recurring,
            "interval_hours": interval_hours,
            "type": task_type,
            "created_at": datetime.now().isoformat(),
            "status": "scheduled"
        }
        self.scheduled_tasks.append(task)
        db.create_task(task_id, description, priority=5, estimated_duration=10)
        return task_id

    def _worker_loop(self):
        """Main worker loop."""
        while self.running:
            try:
                # Check scheduled tasks
                now = datetime.now()
                for task in list(self.scheduled_tasks):
                    run_at = datetime.fromisoformat(task["run_at"])
                    if now >= run_at:
                        self._execute_task(task)
                        self.scheduled_tasks.remove(task)
                        if task.get("recurring"):
                            next_run = run_at + timedelta(hours=task["interval_hours"])
                            self.schedule_task(
                                task["description"], next_run,
                                recurring=True, interval_hours=task["interval_hours"],
                                task_type=task["type"]
                            )

                # Process queued tasks
                if not self.task_queue.empty():
                    priority, task_id, task = self.task_queue.get(timeout=1)
                    self._execute_task(task)

                # Check for calendar notifications
                self._check_calendar_notifications()

                # Self-improvement check (every hour)
                if int(time.time()) % 3600 < 5:
                    self._self_improvement_check()

                time.sleep(5)
            except Exception as e:
                print(f"Autonomous worker error: {e}")
                time.sleep(10)

    def _execute_task(self, task: Dict):
        """Execute a single task."""
        task["status"] = "running"
        task["started_at"] = datetime.now().isoformat()
        db.update_task(task["id"], status="running")

        try:
            # Route to appropriate handler
            if task["type"] == "self_improve":
                result = self._run_self_improvement(task)
            elif task["type"] == "calendar_notify":
                result = self._run_calendar_notification(task)
            elif task["type"] == "backup":
                result = self._run_backup(task)
            elif task["type"] == "health_check":
                result = self._run_health_check(task)
            else:
                result = self._run_generic_task(task)

            task["status"] = "completed"
            task["result"] = result
            task["completed_at"] = datetime.now().isoformat()
            self.completed_tasks.append(task)
            db.update_task(task["id"], status="completed", result=json.dumps(result))

            if task["id"] in self.callbacks:
                self.callbacks[task["id"]](result)

        except Exception as e:
            task["status"] = "failed"
            task["error"] = str(e)
            self.failed_tasks.append(task)
            db.update_task(task["id"], status="failed", result=str(e))

    def _run_self_improvement(self, task: Dict) -> Dict:
        """Run self-analysis and propose fixes."""
        from modules.self_improve import self_improvement
        analysis = self_improvement.analyze_self()
        return {"analysis": analysis, "action": "Self-improvement check complete"}

    def _run_calendar_notification(self, task: Dict) -> Dict:
        """Check and send calendar notifications."""
        from skills.calendar_skill import calendar_skill
        notifications = calendar_skill.check_notifications()
        return {"notifications": notifications, "count": len(notifications)}

    def _run_backup(self, task: Dict) -> Dict:
        """Backup IRIS data."""
        import shutil
        backup_dir = os.path.join(config.DATA_DIR, f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        shutil.copytree(config.DATA_DIR, backup_dir, ignore=shutil.ignore_patterns("backup_*"))
        return {"backup_path": backup_dir, "status": "completed"}

    def _run_health_check(self, task: Dict) -> Dict:
        """Run system health check."""
        from core.tool_registry import tool_registry
        result = tool_registry.tools["self_diagnose"]()
        return result.data if result.success else {"error": result.error}

    def _run_generic_task(self, task: Dict) -> Dict:
        """Run a generic task."""
        return {"message": f"Completed: {task['description']}", "type": task["type"]}

    def _check_calendar_notifications(self):
        """Check for upcoming calendar events."""
        from skills.calendar_skill import calendar_skill
        notifications = calendar_skill.check_notifications()
        if notifications:
            for notif in notifications:
                db.log("INFO", "calendar", f"Notification: {notif['message']}")

    def _self_improvement_check(self):
        """Periodic self-improvement check."""
        from modules.self_improve import self_improvement
        analysis = self_improvement.analyze_self()
        if analysis["critical"] > 0:
            db.log("WARNING", "self_improve", f"Found {analysis['critical']} critical issues")

# Singleton
autonomous_engine = AutonomousEngine()
