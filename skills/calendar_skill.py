"""IRIS v8 Aevibron Calendar Skill — Custom Calendar with Notifications"""
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from config import config
from core.db import db

class CalendarSkill:
    """
    Aevibron Calendar — IRIS's own calendar system:
    - Create events with title, description, time, location
    - Recurring events (daily, weekly, monthly)
    - Priority levels
    - Automatic notifications
    - Category-based organization
    - Natural language parsing ("meeting tomorrow at 3pm")
    """

    def __init__(self):
        self.data_dir = config.CALENDAR_DIR
        os.makedirs(self.data_dir, exist_ok=True)

    def parse_natural_date(self, text: str) -> Dict:
        """Parse natural language date/time."""
        from datetime import datetime, timedelta
        now = datetime.now()
        text_lower = text.lower()

        # Simple keyword parsing
        if "tomorrow" in text_lower:
            date = now + timedelta(days=1)
        elif "today" in text_lower:
            date = now
        elif "next week" in text_lower:
            date = now + timedelta(weeks=1)
        elif "in an hour" in text_lower:
            date = now + timedelta(hours=1)
        elif "in 30 minutes" in text_lower or "in half an hour" in text_lower:
            date = now + timedelta(minutes=30)
        else:
            date = now

        # Time extraction
        import re
        time_match = re.search(r'(\d{1,2}):?(\d{2})?\s*(am|pm)?', text_lower)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2)) if time_match.group(2) else 0
            period = time_match.group(3)
            if period == "pm" and hour != 12:
                hour += 12
            elif period == "am" and hour == 12:
                hour = 0
            date = date.replace(hour=hour, minute=minute, second=0)

        return {"success": True, "parsed_date": date.isoformat(), "original": text}

    def add_event(self, title: str, start_time: str, end_time: str = None,
                  description: str = None, location: str = None,
                  category: str = "general", priority: int = 5,
                  recurring: str = None) -> Dict:
        """Add a new calendar event."""
        try:
            event_id = db.add_calendar_event(
                title=title, start_time=start_time, end_time=end_time,
                description=description, location=location,
                category=category, priority=priority, recurring=recurring
            )
            return {
                "success": True,
                "event_id": event_id,
                "title": title,
                "start_time": start_time,
                "message": f"Event '{title}' added to calendar."
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_events(self, start: str = None, end: str = None, category: str = None) -> Dict:
        """Get calendar events in a date range."""
        events = db.get_calendar_events(start=start, end=end, category=category)
        return {"success": True, "events": events, "count": len(events)}

    def get_upcoming(self, hours: int = 24) -> Dict:
        """Get upcoming events within N hours."""
        events = db.get_upcoming_events(hours=hours)
        return {"success": True, "events": events, "count": len(events)}

    def get_today(self) -> Dict:
        """Get today's events."""
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        start = f"{today}T00:00:00"
        end = f"{today}T23:59:59"
        return self.get_events(start=start, end=end)

    def delete_event(self, event_id: int) -> Dict:
        """Delete an event by ID."""
        try:
            conn = db._get_conn()
            conn.execute("DELETE FROM calendar_events WHERE id = ?", (event_id,))
            conn.commit()
            conn.close()
            return {"success": True, "message": f"Event {event_id} deleted."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def check_notifications(self) -> List[Dict]:
        """Check for events that need notification."""
        upcoming = db.get_upcoming_events(hours=1)
        notifications = []
        for event in upcoming:
            if not event.get("notified"):
                notifications.append({
                    "event_id": event["id"],
                    "title": event["title"],
                    "start_time": event["start_time"],
                    "message": f"Upcoming: {event['title']} at {event['start_time']}"
                })
                db.mark_notified(event["id"])
        return notifications

    def export_to_ics(self, events: List[Dict] = None) -> str:
        """Export events to ICS format."""
        if events is None:
            events = db.get_calendar_events()
        ics_lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Aevibron//IRIS Calendar//EN"]
        for event in events:
            ics_lines.extend([
                "BEGIN:VEVENT",
                f"SUMMARY:{event.get('title', '')}",
                f"DTSTART:{event.get('start_time', '').replace('-', '').replace(':', '').replace('T', 'T')}",
                f"DESCRIPTION:{event.get('description', '')}",
                f"LOCATION:{event.get('location', '')}",
                "END:VEVENT"
            ])
        ics_lines.append("END:VCALENDAR")
        return "
".join(ics_lines)

    def get_categories(self) -> List[str]:
        """Get all event categories."""
        conn = db._get_conn()
        cursor = conn.execute("SELECT DISTINCT category FROM calendar_events")
        categories = [row[0] for row in cursor.fetchall()]
        conn.close()
        return categories

# Singleton
calendar_skill = CalendarSkill()
