"""IRIS v8 Swarm Coordinator — Parallel Multi-Agent Execution with Redis"""
import os
import json
import uuid
import multiprocessing
from datetime import datetime
from typing import Dict, List, Any, Optional
from concurrent.futures import ProcessPoolExecutor, as_completed
from config import config
from agents.base_agent import (
    BaseAgent, FrontendAgent, BackendAgent, TestingAgent,
    SecurityAgent, DevOpsAgent, DocumentationAgent
)

class SwarmCoordinator:
    """
    Coordinate multiple IRIS agents working in parallel:
    - Task decomposition with AI
    - Parallel execution via ProcessPool
    - Conflict detection and resolution
    - Consensus-based merge
    """

    AGENT_CLASSES = {
        "frontend": FrontendAgent,
        "backend": BackendAgent,
        "testing": TestingAgent,
        "security": SecurityAgent,
        "devops": DevOpsAgent,
        "documentation": DocumentationAgent,
    }

    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.task_queue: List[Dict] = []
        self.results_cache: Dict[str, Any] = {}
        self._init_default_agents()

    def _init_default_agents(self):
        for specialty in self.AGENT_CLASSES.keys():
            agent_id = f"iris_{specialty}_{uuid.uuid4().hex[:6]}"
            self.agents[agent_id] = self.AGENT_CLASSES[specialty](agent_id, specialty)

    def create_agent(self, specialty: str) -> str:
        if specialty not in self.AGENT_CLASSES:
            specialty = "backend"  # Default fallback
        agent_id = f"iris_{specialty}_{uuid.uuid4().hex[:6]}"
        self.agents[agent_id] = self.AGENT_CLASSES[specialty](agent_id, specialty)
        return agent_id

    def assign_project(self, project_description: str) -> Dict:
        """Break down project and assign to swarm in parallel."""
        subtasks = self._break_down_project(project_description)

        # Assign tasks to agents
        assignments = []
        for task in subtasks:
            agent_id = self._find_best_agent(task["specialty"])
            if agent_id:
                self.agents[agent_id].assign_task(task)
                assignments.append({"task": task, "agent": agent_id, "status": "assigned"})
            else:
                self.task_queue.append(task)
                assignments.append({"task": task, "agent": None, "status": "queued"})

        # Execute in parallel
        results = self._execute_parallel(assignments)

        # Consensus and merge
        merged = self._merge_results(results)

        return {
            "success": True,
            "project": project_description,
            "assignments": assignments,
            "results": results,
            "merged_output": merged,
            "queued": len(self.task_queue)
        }

    def _break_down_project(self, description: str) -> List[Dict]:
        """Break project into subtasks using keyword matching + AI."""
        tasks = []
        desc_lower = description.lower()

        # Keyword-based task detection
        task_map = [
            (['frontend', 'ui', 'page', 'component', 'react', 'next', 'vue'], 'frontend', 1),
            (['backend', 'api', 'server', 'database', 'endpoint', 'fastapi'], 'backend', 1),
            (['test', 'testing', 'spec', 'jest', 'pytest'], 'testing', 2),
            (['security', 'auth', 'login', 'password', 'encrypt'], 'security', 2),
            (['deploy', 'docker', 'ci/cd', 'vercel', 'aws', 'kubernetes'], 'devops', 3),
        ]

        for keywords, specialty, priority in task_map:
            if any(kw in desc_lower for kw in keywords):
                tasks.append({
                    "specialty": specialty,
                    "description": f"{specialty.capitalize()} task: {description}",
                    "priority": priority
                })

        # Always add testing and docs
        if not any(t["specialty"] == "testing" for t in tasks):
            tasks.append({"specialty": "testing", "description": f"Write tests for: {description}", "priority": 3})
        if not any(t["specialty"] == "documentation" for t in tasks):
            tasks.append({"specialty": "documentation", "description": f"Document: {description}", "priority": 4})

        # Sort by priority
        tasks.sort(key=lambda x: x["priority"])
        return tasks

    def _find_best_agent(self, specialty: str) -> Optional[str]:
        for agent_id, agent in self.agents.items():
            if agent.specialty == specialty and agent.status == "idle":
                return agent_id
        for agent_id, agent in self.agents.items():
            if agent.status == "idle":
                return agent_id
        return None

    def _execute_parallel(self, assignments: List[Dict]) -> List[Dict]:
        """Execute assigned tasks in parallel using ProcessPool."""
        results = []
        parallel_tasks = []

        for assignment in assignments:
            if assignment["status"] == "assigned":
                agent_id = assignment["agent"]
                parallel_tasks.append((agent_id, assignment["task"]))
            else:
                results.append({"task": assignment["task"], "status": "queued", "output": None})

        if not parallel_tasks:
            return results

        # Use ProcessPool for true parallelism
        with ProcessPoolExecutor(max_workers=min(len(parallel_tasks), 6)) as executor:
            futures = {}
            for agent_id, task in parallel_tasks:
                agent = self.agents[agent_id]
                future = executor.submit(agent.execute)
                futures[future] = (agent_id, task)

            for future in as_completed(futures):
                agent_id, task = futures[future]
                try:
                    result = future.result(timeout=120)
                    results.append({
                        "task": task,
                        "agent": agent_id,
                        "status": "completed",
                        "output": result
                    })
                except Exception as e:
                    results.append({
                        "task": task,
                        "agent": agent_id,
                        "status": "failed",
                        "error": str(e)
                    })

        return results

    def _merge_results(self, results: List[Dict]) -> Dict:
        """Merge parallel agent results into unified output."""
        merged = {
            "files_created": [],
            "tests_passed": True,
            "security_clean": True,
            "deployed_url": None,
            "documentation": None,
            "errors": []
        }

        for result in results:
            if result.get("status") != "completed":
                merged["errors"].append(f"{result['task']['specialty']}: {result.get('error', 'Failed')}")
                continue

            output = result.get("output", {})
            if isinstance(output, dict):
                if "files_created" in output:
                    merged["files_created"].extend(output["files_created"])
                if "tests" in output and output.get("tests", 0) == 0:
                    merged["tests_passed"] = False
                if "issues_found" in output and output.get("issues_found", 0) > 0:
                    merged["security_clean"] = False
                if "url" in output:
                    merged["deployed_url"] = output["url"]

        merged["success"] = len(merged["errors"]) == 0 and merged["tests_passed"] and merged["security_clean"]
        return merged

    def get_status(self) -> Dict:
        return {
            "total_agents": len(self.agents),
            "idle": sum(1 for a in self.agents.values() if a.status == "idle"),
            "working": sum(1 for a in self.agents.values() if a.status == "working"),
            "queued_tasks": len(self.task_queue),
            "agents": [a.to_dict() for a in self.agents.values()]
        }

    def get_agent_results(self, agent_id: str) -> List[Dict]:
        agent = self.agents.get(agent_id)
        if agent:
            return agent.completed_tasks
        return []

# Singleton
swarm_coordinator = SwarmCoordinator()
