"""IRIS v7 Predictive Engine - Anticipates What You Need"""
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import Counter
from config import config
from db import db

class PredictiveEngine:
    """
    IRIS anticipates what you need:
    - Pattern recognition from your behavior
    - Time-based suggestions (morning standup, evening review)
    - Project context awareness
    - Proactive bug detection
    - Code completion before you ask
    """

    def __init__(self):
        self.pattern_window = 30
        self.confidence_threshold = 0.7

    def analyze_patterns(self) -> Dict:
        """Analyze user behavior patterns"""
        conn = db.get_connection()

        cursor = conn.execute("SELECT strftime('%H', created_at) as hour, COUNT(*) as count FROM conversations WHERE role = 'user' AND created_at > datetime('now', '-30 days') GROUP BY hour ORDER BY count DESC")
        hour_patterns = {r['hour']: r['count'] for r in cursor.fetchall()}

        cursor = conn.execute("SELECT strftime('%w', created_at) as day, COUNT(*) as count FROM conversations WHERE role = 'user' AND created_at > datetime('now', '-30 days') GROUP BY day ORDER BY count DESC")
        day_patterns = {r['day']: r['count'] for r in cursor.fetchall()}

        cursor = conn.execute("SELECT content FROM conversations WHERE role = 'user' AND created_at > datetime('now', '-7 days') ORDER BY created_at DESC LIMIT 100")
        topics = []
        for row in cursor.fetchall():
            content = row['content'].lower()
            if 'build' in content or 'create' in content:
                topics.append('building')
            elif 'fix' in content or 'bug' in content:
                topics.append('debugging')
            elif 'deploy' in content:
                topics.append('deployment')
            elif 'design' in content or 'ui' in content or 'css' in content:
                topics.append('design')
            elif 'api' in content or 'backend' in content:
                topics.append('backend')
            elif 'test' in content:
                topics.append('testing')

        conn.close()

        topic_counts = Counter(topics)

        return {
            "peak_hours": hour_patterns,
            "active_days": day_patterns,
            "top_topics": dict(topic_counts.most_common(5)),
            "total_interactions": sum(hour_patterns.values()),
            "analysis_period": "30 days"
        }

    def predict_next_action(self) -> Dict:
        """Predict what the user will do next"""
        patterns = self.analyze_patterns()
        now = datetime.now()

        suggestions = []

        if 8 <= now.hour <= 10:
            suggestions.append({"action": "morning_standup", "message": "Good morning Infinite! Ready for today's standup? Want me to review yesterday's progress?", "confidence": 0.8})
        elif 12 <= now.hour <= 14:
            suggestions.append({"action": "lunch_learning", "message": "Lunch time? I found some interesting articles about Python optimization. Want to read?", "confidence": 0.6})
        elif 17 <= now.hour <= 19:
            suggestions.append({"action": "evening_review", "message": "Evening review time! Shall I summarize what we accomplished today?", "confidence": 0.75})

        top_topics = patterns.get("top_topics", {})
        if top_topics:
            top_topic = list(top_topics.keys())[0]
            if top_topic == "building":
                suggestions.append({"action": "continue_building", "message": "You've been building a lot lately. Want to continue on the current project?", "confidence": 0.7})
            elif top_topic == "debugging":
                suggestions.append({"action": "bug_hunt", "message": "I noticed you've been debugging. Shall I run a full codebase analysis for issues?", "confidence": 0.72})

        conn = db.get_connection()
        cursor = conn.execute("SELECT * FROM code_projects WHERE updated_at < datetime('now', '-3 days') ORDER BY updated_at DESC LIMIT 3")
        stale_projects = [dict(r) for r in cursor.fetchall()]
        conn.close()

        if stale_projects:
            suggestions.append({"action": "stale_project", "message": f"It's been a while since we worked on {stale_projects[0]['name']}. Want to revisit?", "confidence": 0.65})

        suggestions.sort(key=lambda x: x["confidence"], reverse=True)

        return {
            "predictions": suggestions[:3],
            "best_guess": suggestions[0] if suggestions else None,
            "patterns": patterns
        }

    def proactive_suggestion(self) -> Optional[str]:
        """Generate a proactive suggestion message"""
        prediction = self.predict_next_action()
        best = prediction.get("best_guess")

        if best and best["confidence"] > self.confidence_threshold:
            return best["message"]

        return None

    def learn_from_correction(self, predicted: str, actual: str) -> bool:
        """Learn when predictions are wrong"""
        db.save_memory(f"prediction_correction_{datetime.now().timestamp()}", f"Predicted: {predicted}, Actual: {actual}", category="prediction_learning", importance=6)
        return True

predictive_engine = PredictiveEngine()
