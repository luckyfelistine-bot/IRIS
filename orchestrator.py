"""IRIS v7 Agent Orchestrator — The Brain"""
import json
import time
import uuid
from typing import Dict, List, Any, Generator
from datetime import datetime
from config import config
from db import db
from aevibron_client import aevibron
from tools import tool_registry, ToolResult

class AgentOrchestrator:
    """
    IRIS's central brain. Handles the think-act-observe-reflect loop.

    Loop:
    1. OBSERVE — Gather context (memory, files, conversation history)
    2. THINK — Reason about approach, estimate time, plan steps
    3. ACT — Execute tools based on reasoning
    4. VERIFY — Check results, test, lint
    5. REFLECT — Learn from success/failure
    6. REPORT — Update user with status and results
    """

    def __init__(self):
        self.registry = tool_registry
        self.max_iterations = config.MAX_TOOL_ITERATIONS
        self.current_task = None

    def process(self, user_input: str, session_id: str = None) -> Generator[Dict, None, None]:
        """
        Main entry point. Yields status updates for real-time UI.
        Returns final result.
        """
        session_id = session_id or str(uuid.uuid4())
        task_id = f"task_{int(time.time())}_{uuid.uuid4().hex[:6]}"

        # Save user message
        db.save_message(session_id, "user", user_input)

        # === PHASE 1: OBSERVE ===
        yield self._status("observing", "Gathering context...", 5)
        context = self._gather_context(user_input, session_id)

        # === PHASE 2: THINK ===
        yield self._status("thinking", "Analyzing your request...", 10)
        reasoning = self._think(user_input, context)

        # If it's a simple question, just answer
        if reasoning.get("type") == "direct_answer":
            yield self._status("answering", "Formulating response...", 20)
            answer = self._generate_answer(user_input, context)
            db.save_message(session_id, "assistant", answer, reasoning=reasoning.get("thoughts"))
            yield self._status("complete", answer, 100, final=True, data={"answer": answer})
            return

        # === PHASE 3: PLAN ===
        yield self._status("planning", f"Plan: {reasoning.get('plan_summary', 'Working on it...')}", 15)
        plan = reasoning.get("plan", [])
        estimated_time = reasoning.get("estimated_minutes", 5)

        yield self._status("estimated", 
            f"""This will take about {estimated_time} minute{'s' if estimated_time > 1 else ''}. Starting now...""",
            20, data={"estimated_minutes": estimated_time, "plan": plan}
        )

        # Create task record
        db.create_task(task_id, user_input, priority=reasoning.get("priority", 5), 
                      estimated_duration=estimated_time)
        db.update_task(task_id, status="running", steps=plan)
        self.current_task = task_id

        # === PHASE 4: EXECUTE ===
        results = []
        for i, step in enumerate(plan):
            progress = 20 + int((i / len(plan)) * 60) if plan else 50
            yield self._status("working", f"Step {i+1}/{len(plan)}: {step.get('description', 'Working...')}", progress)

            step_result = self._execute_step(step, context, session_id)
            results.append(step_result)

            # If step failed, try to recover
            if not step_result.get("success"):
                yield self._status("recovering", f"Issue detected: {step_result.get('error', 'Unknown error')}. Attempting fix...", progress)
                recovery = self._recover_step(step, step_result, context)
                if recovery:
                    results.append(recovery)

        # === PHASE 5: VERIFY ===
        yield self._status("verifying", "Verifying results...", 85)
        verification = self._verify_results(results, reasoning)

        # === PHASE 6: REFLECT & LEARN ===
        yield self._status("reflecting", "Learning from this task...", 90)
        self._reflect(task_id, user_input, results, verification)

        # === PHASE 7: FINAL REPORT ===
        db.update_task(task_id, status="completed" if verification["success"] else "failed",
                      steps=results, result=json.dumps(verification))

        final_report = self._generate_report(user_input, results, verification, reasoning)
        db.save_message(session_id, "assistant", final_report, 
                       tool_calls=[r.get("tool") for r in results if r.get("tool")],
                       reasoning=reasoning.get("thoughts"))

        yield self._status("complete", final_report, 100, final=True, data={
            "task_id": task_id,
            "verification": verification,
            "results": results
        })

    def _gather_context(self, user_input: str, session_id: str) -> Dict:
        """Gather all relevant context for decision making"""
        context = {
            "user_input": user_input,
            "owner": db.get_owner(),
            "recent_conversations": db.get_conversation(session_id, limit=10),
            "relevant_memories": db.search_memory(user_input, limit=5),
            "recent_episodes": db.get_episodes(limit=5),
            "active_tasks": [],  # Could query active tasks
            "current_time": datetime.now().isoformat(),
            "system_status": self._quick_diagnose()
        }
        return context

    def _think(self, user_input: str, context: Dict) -> Dict:
        """Deep thinking — analyze request and plan approach"""

        # Build thinking prompt
        thinking_prompt = f"""Analyze this request and decide the best approach.

USER REQUEST: {user_input}

CONTEXT:
- Owner: {context['owner'].get('name', 'Unknown')}
- Recent memories: {[m['key'] for m in context['relevant_memories']]}
- System status: {context['system_status']}

INSTRUCTIONS:
1. Determine if this is a simple question (direct_answer) or a complex task (requires_tools)
2. If complex, create a step-by-step plan
3. Estimate time in minutes
4. Assign priority (1-10, 10 = urgent)
5. Identify which tools are needed

Respond in JSON format:
{{
    "type": "direct_answer" or "requires_tools",
    "thoughts": "your reasoning process",
    "plan_summary": "brief description of approach",
    "plan": [
        {{"step": 1, "description": "what to do", "tool": "tool_name", "params": {{}}}}
    ],
    "estimated_minutes": 5,
    "priority": 5,
    "tools_needed": ["tool1", "tool2"]
}}"""

        response = aevibron.think(thinking_prompt, context=json.dumps(context, default=str))

        if response.get("error"):
            # Fallback: simple direct answer
            return {
                "type": "direct_answer",
                "thoughts": "Falling back to direct answer due to API error",
                "plan_summary": "Answer directly",
                "plan": [],
                "estimated_minutes": 1,
                "priority": 5,
                "tools_needed": []
            }

        # Parse reasoning from response
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")

        # Try to extract JSON
        try:
            # Find JSON in response
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                reasoning = json.loads(content[start:end])
            else:
                reasoning = json.loads(content)
        except:
            # Fallback parsing
            reasoning = {
                "type": "direct_answer" if len(user_input) < 100 and "?" in user_input else "requires_tools",
                "thoughts": content[:500],
                "plan_summary": "Processing your request",
                "plan": [{"step": 1, "description": "Process request", "tool": "execute_python", "params": {"code": "# Processing"}}],
                "estimated_minutes": 3,
                "priority": 5,
                "tools_needed": []
            }

        return reasoning

    def _generate_answer(self, user_input: str, context: Dict) -> str:
        """Generate direct answer for simple questions"""
        messages = [
            {"role": "system", "content": aevibron._get_system_prompt()},
            {"role": "user", "content": user_input}
        ]

        # Add context
        if context.get("relevant_memories"):
            memory_text = "\n".join([f"- {m['key']}: {m['value']}" for m in context["relevant_memories"]])
            messages.insert(1, {"role": "system", "content": f"Relevant memories:\n{memory_text}"})

        response = aevibron.chat(messages, temperature=0.7)

        if response.get("error"):
            return f"I'm having trouble connecting to my brain right now. Error: {response.get('message', 'Unknown')}"

        return response.get("choices", [{}])[0].get("message", {}).get("content", "I'm thinking...")

    def _execute_step(self, step: Dict, context: Dict, session_id: str) -> Dict:
        """Execute a single step from the plan"""
        tool_name = step.get("tool")
        params = step.get("params", {})

        if not tool_name or tool_name not in self.registry.tools:
            return {"success": False, "error": f"Unknown tool: {tool_name}", "step": step}

        start_time = time.time()
        result = self.registry.tools[tool_name](**params)
        duration = time.time() - start_time

        # Log the tool use
        db.log("INFO", "tool_execution", f"Executed {tool_name} in {duration:.2f}s")

        return {
            "success": result.success,
            "tool": tool_name,
            "params": params,
            "data": result.data,
            "error": result.error,
            "output": result.output,
            "duration": duration,
            "step": step
        }

    def _recover_step(self, step: Dict, failed_result: Dict, context: Dict) -> Dict:
        """Attempt to recover from a failed step"""
        # Try alternative approach
        recovery_prompt = f"""The following step failed:
Tool: {step.get('tool')}
Params: {step.get('params')}
Error: {failed_result.get('error')}

Suggest an alternative approach or fix."""

        response = aevibron.fast_response(recovery_prompt)
        # For now, just log and return
        db.log("WARNING", "recovery", f"Failed step recovery attempted: {failed_result.get('error')}")
        return {"success": False, "recovery_attempted": True, "error": failed_result.get("error")}

    def _verify_results(self, results: List[Dict], reasoning: Dict) -> Dict:
        """Verify all results are correct and complete"""
        all_success = all(r.get("success") for r in results)

        verification = {
            "success": all_success,
            "total_steps": len(results),
            "successful_steps": sum(1 for r in results if r.get("success")),
            "failed_steps": [r for r in results if not r.get("success")],
            "total_duration": sum(r.get("duration", 0) for r in results),
            "checks": []
        }

        # Run additional checks if code was involved
        code_tools = ["write_file", "edit_file", "execute_python"]
        if any(r.get("tool") in code_tools for r in results):
            verification["checks"].append({"check": "code_executed", "status": "review_needed"})

        return verification

    def _reflect(self, task_id: str, user_input: str, results: List[Dict], verification: Dict):
        """Learn from this task execution"""
        # Extract lessons
        if verification["success"]:
            lesson = f"Successfully completed: {user_input[:100]}"
            db.save_episode(lesson, context=json.dumps({"task_id": task_id}), emotion="success",
                          lesson="This approach works well")
        else:
            lesson = f"Failed task: {user_input[:100]}"
            errors = [r.get("error") for r in results if r.get("error")]
            db.save_episode(lesson, context=json.dumps({"task_id": task_id, "errors": errors}),
                          emotion="frustration", lesson="Need to improve error handling")

        # Save to memory if new pattern discovered
        tools_used = [r.get("tool") for r in results if r.get("tool")]
        if tools_used:
            db.save_memory(
                f"pattern_{task_id}",
                f"Used tools {tools_used} to: {user_input[:200]}",
                category="pattern",
                importance=6 if verification["success"] else 8
            )

    def _generate_report(self, user_input: str, results: List[Dict], 
                        verification: Dict, reasoning: Dict) -> str:
        """Generate final user-facing report"""

        if verification["success"]:
            report_parts = ["✅ Done! "]

            # Summarize what was accomplished
            if reasoning.get("plan_summary"):
                report_parts.append(reasoning["plan_summary"])

            # Add key results
            for result in results:
                if result.get("success") and result.get("data"):
                    if result.get("tool") == "git_create_repo":
                        report_parts.append(f"\n📁 Created repo: {result['data'].get('url', '')}")
                    elif result.get("tool") == "vercel_deploy":
                        report_parts.append(f"\n🚀 Deployed to: {result['data'].get('url', '')}")
                    elif result.get("tool") == "write_file":
                        report_parts.append(f"\n📝 Wrote: {result['data'].get('path', '')}")

            report_parts.append(f"\n\n⏱️ Completed in {verification.get('total_duration', 0):.1f}s")
            report_parts.append("\n\nWhat would you like me to do next?")

            return "\n".join(report_parts)
        else:
            errors = "\n".join([f"- {r.get('error', 'Unknown error')}" for r in verification.get("failed_steps", [])])
            return f"""❌ I encountered some issues:
{errors}

Let me try a different approach. Should I:
1. Retry with modifications
2. Try an alternative solution
3. Explain what went wrong in detail"""

    def _status(self, phase: str, message: str, progress: int, 
                final: bool = False, data: Dict = None) -> Dict:
        """Generate status update for UI"""
        return {
            "phase": phase,
            "message": message,
            "progress": progress,
            "final": final,
            "timestamp": datetime.now().isoformat(),
            "data": data or {}
        }

    def _quick_diagnose(self) -> Dict:
        """Quick system health check"""
        try:
            db.get_owner()
            return {"status": "healthy", "db": "connected"}
        except Exception as e:
            return {"status": "degraded", "db": str(e)}

# Singleton
orchestrator = AgentOrchestrator()
