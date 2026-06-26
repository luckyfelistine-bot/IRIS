"""IRIS v8 Aevibron Notes Skill — Smart Note Taking & Organization"""
import os
import json
from datetime import datetime
from typing import Dict, List, Optional
from config import config
from core.db import db

class NotesSkill:
    """
    Aevibron Notes — IRIS's note management:
    - Create, edit, delete notes
    - Categories and tags
    - Pin important notes
    - Search across all notes
    - Markdown support
    - Auto-summarize long notes
    """

    def __init__(self):
        self.data_dir = config.NOTES_DIR
        os.makedirs(self.data_dir, exist_ok=True)

    def create_note(self, title: str, content: str = "", category: str = "general", tags: List[str] = None) -> Dict:
        """Create a new note."""
        try:
            note_id = db.add_note(title=title, content=content, category=category, tags=tags or [])
            return {
                "success": True,
                "note_id": note_id,
                "title": title,
                "message": f"Note '{title}' created."
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_notes(self, category: str = None, search: str = None) -> Dict:
        """Get notes with optional filtering."""
        notes = db.get_notes(category=category, search=search)
        return {"success": True, "notes": notes, "count": len(notes)}

    def get_note(self, note_id: int) -> Dict:
        """Get a single note by ID."""
        notes = db.get_notes()
        for note in notes:
            if note["id"] == note_id:
                return {"success": True, "note": note}
        return {"success": False, "error": "Note not found"}

    def update_note(self, note_id: int, title: str = None, content: str = None, category: str = None, tags: List[str] = None) -> Dict:
        """Update a note."""
        try:
            kwargs = {}
            if title: kwargs["title"] = title
            if content: kwargs["content"] = content
            if category: kwargs["category"] = category
            if tags: kwargs["tags"] = json.dumps(tags)
            db.update_note(note_id, **kwargs)
            return {"success": True, "message": f"Note {note_id} updated."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_note(self, note_id: int) -> Dict:
        """Delete a note."""
        try:
            conn = db._get_conn()
            conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
            conn.commit()
            conn.close()
            return {"success": True, "message": f"Note {note_id} deleted."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def pin_note(self, note_id: int, pinned: bool = True) -> Dict:
        """Pin or unpin a note."""
        try:
            db.update_note(note_id, pinned=1 if pinned else 0)
            return {"success": True, "message": f"Note {note_id} {'pinned' if pinned else 'unpinned'}."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def search_notes(self, query: str) -> Dict:
        """Search notes by title or content."""
        return self.get_notes(search=query)

    def get_categories(self) -> List[str]:
        """Get all note categories."""
        conn = db._get_conn()
        cursor = conn.execute("SELECT DISTINCT category FROM notes")
        categories = [row[0] for row in cursor.fetchall()]
        conn.close()
        return categories

    def export_note(self, note_id: int, format: str = "markdown") -> Dict:
        """Export a note to markdown or text."""
        result = self.get_note(note_id)
        if not result["success"]:
            return result
        note = result["note"]
        if format == "markdown":
            md = f"# {note['title']}

**Category:** {note['category']}
**Tags:** {note.get('tags', '[]')}
**Created:** {note['created_at']}

{note['content']}
"
            return {"success": True, "content": md, "format": "markdown"}
        return {"success": True, "content": note["content"], "format": "text"}

    def quick_note(self, text: str) -> Dict:
        """Create a quick note with auto-generated title."""
        title = text[:50] + ("..." if len(text) > 50 else "")
        return self.create_note(title=title, content=text, category="quick")

# Singleton
notes_skill = NotesSkill()
