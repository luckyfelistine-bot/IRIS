import json
import os
import hashlib
import re
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, asdict

@dataclass
class MemoryEntry:
    id: str
    timestamp: str
    user_msg: str
    iris_response: str
    mood: str
    importance: float = 1.0
    tags: List[str] = None
    memory_type: str = "episodic"
    concepts: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.concepts is None:
            self.concepts = []

@dataclass
class MemoryFact:
    id: str
    subject: str
    fact: str
    category: str
    confidence: float
    created_at: str
    updated_at: str
    access_count: int
    is_auto: bool
    persistent: bool = True
    confirmed: bool = True
    tags: List[str] = None
    user_id: str = None
    shared: bool = False

    def __post_init__(self):
        if self.tags is None:
            self.tags = []

    def to_dict(self):
        return {
            "id": self.id,
            "subject": self.subject,
            "fact": self.fact,
            "category": self.category,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "access_count": self.access_count,
            "is_auto": self.is_auto,
            "persistent": self.persistent,
            "confirmed": self.confirmed,
            "tags": self.tags,
            "user_id": self.user_id,
            "shared": self.shared
        }

class SmartMemory:
    def __init__(self, db_path: str = "iris_secure_v7.db"):
        self.db_path = db_path
        self.init_db()
        self._init_self_awareness()   # now enabled
        print("🧠 Smart Memory System v9.0 Ready")

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS smart_memories (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_msg TEXT,
                    iris_response TEXT,
                    mood TEXT DEFAULT 'neutral',
                    importance REAL DEFAULT 1.0,
                    tags TEXT,
                    concepts TEXT,
                    memory_type TEXT DEFAULT 'episodic',
                    category TEXT DEFAULT 'general'
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS concept_links (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    concept_a TEXT NOT NULL,
                    concept_b TEXT NOT NULL,
                    strength REAL DEFAULT 1.0,
                    memory_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memory_facts (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    fact TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    confidence REAL DEFAULT 1.0,
                    is_auto INTEGER DEFAULT 0,
                    persistent INTEGER DEFAULT 1,
                    confirmed INTEGER DEFAULT 1,
                    tags TEXT DEFAULT '[]',
                    shared INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 0
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memory_preferences (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    item TEXT NOT NULL,
                    value TEXT NOT NULL,
                    set_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def _init_self_awareness(self):
        self_facts = [
            ("iris", "My name is IRIS.", "identity", 1.0, False, True, ["identity", "self"], 'system', True),
            ("iris", "I was created by Infinite vybeflix.", "identity", 1.0, False, True, ["identity", "creator"], 'system', True),
            ("iris", "I am an AI assistant designed to help with various tasks.", "identity", 1.0, False, True, ["identity", "capability"], 'system', True),
            ("iris", "I have persistent memory and can remember information about you.", "capability", 1.0, False, True, ["capability"], 'system', True),
            ("iris", "I can process documents, answer questions, and help with coding.", "capability", 1.0, False, True, ["capability"], 'system', True),
            ("iris", "I support voice input and output if the required libraries are installed.", "capability", 1.0, False, True, ["capability"], 'system', True),
            ("iris", "I can generate charts and visualizations.", "capability", 1.0, False, True, ["capability"], 'system', True),
            ("iris", "I have a memory graph that shows connections between concepts.", "capability", 1.0, False, True, ["capability"], 'system', True),
        ]
        for subject, fact, category, confidence, is_auto, persistent, tags, user_id, shared in self_facts:
            self.learn_fact(subject, fact, category, confidence, is_auto, persistent, tags, user_id, shared)

    def _generate_id(self, text: str) -> str:
        return hashlib.md5(f"{text}{datetime.now().isoformat()}".encode()).hexdigest()[:12]

    def _extract_keywords(self, text: str) -> List[str]:
        words = re.findall(r'\b[A-Za-z]{4,}\b', text.lower())
        stop_words = {'what', 'when', 'where', 'which', 'while', 'about', 'would', 'could',
                      'should', 'this', 'that', 'with', 'from', 'have', 'been', 'were', 'they'}
        return list(set([w for w in words if w not in stop_words]))[:8]

    def _extract_concepts(self, text: str) -> List[str]:
        words = re.findall(r'\b[A-Z][a-z]{3,}\b', text)
        words += re.findall(r'\b(?:project|task|meeting|file|code|bug|feature|design|plan)\s+(?:\w+)', text.lower())
        return list(set(words))[:5]

    def _calculate_importance(self, user_msg: str, iris_response: str, mood: str) -> float:
        importance = 1.0
        importance += min(len(user_msg) / 100, 2.0)
        if mood in ['excited', 'concerned', 'grateful', 'frustrated', 'stressed']:
            importance += 1.5
        if '?' in user_msg:
            importance += 0.5
        personal_indicators = ['i am', 'my name', 'i like', 'i love', 'i hate', 'i need', 'i want',
                              'my birthday', 'i prefer', 'my project', 'my work', 'i work at',
                              'i live in', 'my favorite']
        if any(ind in user_msg.lower() for ind in personal_indicators):
            importance += 2.0
        return min(importance, 5.0)

    def add_conversation(self, user_msg: str, iris_response: str, mood: str = "neutral",
                        category: str = "general") -> Tuple[str, List[str]]:
        mem_id = self._generate_id(user_msg)
        importance = self._calculate_importance(user_msg, iris_response, mood)
        tags = self._extract_keywords(user_msg + " " + iris_response)
        concepts = self._extract_concepts(user_msg + " " + iris_response)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO smart_memories 
                (id, user_msg, iris_response, mood, importance, tags, concepts, memory_type, category)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (mem_id, user_msg, iris_response, mood, importance,
                  json.dumps(tags), json.dumps(concepts), 'episodic', category))

            for i, concept_a in enumerate(concepts):
                for concept_b in concepts[i+1:]:
                    link_id = self._generate_id(f"{concept_a}{concept_b}{mem_id}")
                    cursor.execute("""
                        INSERT OR REPLACE INTO concept_links (id, concept_a, concept_b, strength, memory_id)
                        VALUES (?, ?, ?, ?, ?)
                    """, (link_id, concept_a, concept_b, importance * 0.5, mem_id))
            conn.commit()

        new_fact_ids = self._auto_extract_facts(user_msg, iris_response)
        return mem_id, new_fact_ids

    def _auto_extract_facts(self, user_msg: str, iris_response: str) -> List[str]:
        new_ids = []
        patterns = [
            (r'i am (\w+)', 'identity', 'user', 0.9),
            (r'my name is (\w+)', 'identity', 'user', 1.0),
            (r'call me (\w+)', 'identity', 'user', 0.9),
            (r'i\'m (\w+)', 'identity', 'user', 0.8),
            (r'i like (\w+)', 'like', 'user', 0.9),
            (r'i love (\w+)', 'like', 'user', 1.0),
            (r'i enjoy (\w+)', 'like', 'user', 0.9),
            (r'my favorite (\w+) is (\w+)', 'favorite', 'user', 1.0),
            (r'i hate (\w+)', 'dislike', 'user', 0.9),
            (r'i don\'t like (\w+)', 'dislike', 'user', 0.8),
            (r'i dislike (\w+)', 'dislike', 'user', 0.8),
            (r'i work at (\w+)', 'work', 'user', 1.0),
            (r'i work on (\w+)', 'project', 'user', 0.9),
            (r'my project is (\w+)', 'project', 'user', 1.0),
            (r'i\'m working on (\w+)', 'project', 'user', 0.9),
            (r'i live in (\w+)', 'location', 'user', 1.0),
            (r'i\'m from (\w+)', 'location', 'user', 0.9),
            (r'my birthday is (.*)', 'birthday', 'user', 1.0),
            (r'i am (\d+) years old', 'age', 'user', 1.0),
            (r'i was born in (\w+)', 'birthplace', 'user', 0.9),
            (r'my (girlfriend|boyfriend|partner|spouse|wife|husband|fiancée|fiancé) is (\w+)', 'relationship', 'user', 1.0),
            (r'i have a (girlfriend|boyfriend|partner|spouse|wife|husband|fiancée|fiancé) (called|named) (\w+)', 'relationship', 'user', 1.0),
            (r'i have a (\w+) (called|named) (\w+)', 'has', 'user', 0.9),
            (r'my (\w+)\'s name is (\w+)', 'relationship', 'user', 0.9),
            (r'i am married to (\w+)', 'relationship', 'user', 1.0),
            (r'i am in a relationship with (\w+)', 'relationship', 'user', 0.9),
        ]
        for pattern, category, subject, confidence in patterns:
            match = re.search(pattern, user_msg.lower())
            if match:
                groups = match.groups()
                if len(groups) == 1:
                    fact_text = groups[0]
                elif len(groups) == 2:
                    fact_text = f"{groups[0]}: {groups[1]}"
                elif len(groups) == 3:
                    fact_text = f"{groups[0]}: {groups[2]}"
                else:
                    fact_text = " ".join(groups)
                fact = f"{category}: {fact_text}"
                existing = self.get_facts_by_subject(subject, category, fact_text)
                if not existing:
                    fact_id = self.learn_fact(subject, fact, category, confidence, is_auto=True, persistent=False, tags=[category])
                    new_ids.append(fact_id)
                    print(f"[Auto Memory] Learned: {fact}")
        return new_ids

    def learn_fact(self, subject: str, fact: str, category: str = "general", confidence: float = 1.0,
                   is_auto: bool = False, persistent: bool = True, tags: List[str] = None,
                   user_id: str = None, shared: bool = False) -> str:
        if user_id is None:
            raise ValueError("user_id is required")
        fact_id = self._generate_id(f"{subject}{fact}{user_id}")
        now = datetime.now().isoformat()
        tags_json = json.dumps(tags or [])
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO memory_facts 
                (id, user_id, subject, fact, category, confidence, is_auto, persistent, tags, shared, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (fact_id, user_id, subject, fact, category, confidence, 1 if is_auto else 0, 1 if persistent else 0,
                  tags_json, 1 if shared else 0, now, now))
            conn.commit()
        return fact_id

    def get_fact(self, fact_id: str) -> Optional[MemoryFact]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM memory_facts WHERE id = ?", (fact_id,))
            row = cursor.fetchone()
            if row:
                return MemoryFact(
                    id=row['id'],
                    subject=row['subject'],
                    fact=row['fact'],
                    category=row['category'],
                    confidence=row['confidence'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    access_count=row['access_count'],
                    is_auto=bool(row['is_auto']),
                    persistent=bool(row['persistent']),
                    confirmed=bool(row['confirmed']),
                    tags=json.loads(row['tags']) if row['tags'] else [],
                    user_id=row['user_id'],
                    shared=bool(row['shared'])
                )
            return None

    def get_facts_by_subject(self, subject: str, category: str = None, fact_contains: str = None) -> List[MemoryFact]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            query = "SELECT * FROM memory_facts WHERE subject = ?"
            params = [subject]
            if category:
                query += " AND category = ?"
                params.append(category)
            if fact_contains:
                query += " AND fact LIKE ?"
                params.append(f"%{fact_contains}%")
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [self._row_to_fact(row) for row in rows]

    def get_all_facts(self, limit: int = 100, pending_only: bool = False, category: str = None,
                      tag: str = None, search: str = None, user_id: str = None,
                      include_shared: bool = False) -> List[MemoryFact]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            query = "SELECT * FROM memory_facts"
            conditions = []
            params = []

            if pending_only:
                conditions.append("confirmed = 0")
            if category:
                conditions.append("category = ?")
                params.append(category)
            if tag:
                conditions.append("tags LIKE ?")
                params.append(f'%"{tag}"%')
            if search:
                conditions.append("(fact LIKE ? OR category LIKE ?)")
                params.append(f'%{search}%')
                params.append(f'%{search}%')

            if user_id:
                if include_shared:
                    conditions.append("(user_id = ? OR shared = 1)")
                else:
                    conditions.append("user_id = ?")
                params.append(user_id)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += " ORDER BY confidence DESC, updated_at DESC LIMIT ?"
            params.append(limit)
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [self._row_to_fact(row) for row in rows]

    def _row_to_fact(self, row) -> MemoryFact:
        return MemoryFact(
            id=row['id'],
            subject=row['subject'],
            fact=row['fact'],
            category=row['category'],
            confidence=row['confidence'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            access_count=row['access_count'],
            is_auto=bool(row['is_auto']),
            persistent=bool(row['persistent']),
            confirmed=bool(row['confirmed']),
            tags=json.loads(row['tags']) if row['tags'] else [],
            user_id=row['user_id'],
            shared=bool(row['shared'])
        )

    def update_fact(self, fact_id: str, new_fact: str = None, new_confidence: float = None,
                    new_category: str = None, new_tags: List[str] = None) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            updates = []
            params = []
            if new_fact:
                updates.append("fact = ?")
                params.append(new_fact)
            if new_confidence is not None:
                updates.append("confidence = ?")
                params.append(new_confidence)
            if new_category:
                updates.append("category = ?")
                params.append(new_category)
            if new_tags is not None:
                updates.append("tags = ?")
                params.append(json.dumps(new_tags))
            if not updates:
                return False
            updates.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            params.append(fact_id)
            cursor.execute(f"UPDATE memory_facts SET {', '.join(updates)} WHERE id = ?", params)
            conn.commit()
            return cursor.rowcount > 0

    def delete_fact(self, fact_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM memory_facts WHERE id = ?", (fact_id,))
            conn.commit()
            return cursor.rowcount > 0

    def confirm_fact(self, fact_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE memory_facts SET confirmed = 1 WHERE id = ?", (fact_id,))
            conn.commit()
            return cursor.rowcount > 0

    def confirm_all_pending(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE memory_facts SET confirmed = 1 WHERE confirmed = 0")
            conn.commit()
            return cursor.rowcount

    def get_all_tags(self) -> List[str]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT tags FROM memory_facts")
            rows = cursor.fetchall()
            tags_set = set()
            for row in rows:
                if row[0]:
                    tags_set.update(json.loads(row[0]))
            return sorted(list(tags_set))

    def export_facts(self) -> List[dict]:
        facts = self.get_all_facts(limit=10000)
        return [f.to_dict() for f in facts]

    def import_facts(self, facts_data: List[dict]) -> int:
        count = 0
        for f in facts_data:
            try:
                self.learn_fact(
                    subject=f.get('subject', 'user'),
                    fact=f['fact'],
                    category=f.get('category', 'general'),
                    confidence=f.get('confidence', 1.0),
                    is_auto=f.get('is_auto', False),
                    persistent=f.get('persistent', True),
                    tags=f.get('tags', [])
                )
                count += 1
            except Exception as e:
                print(f"Import error for fact {f.get('id', 'unknown')}: {e}")
        return count

    def get_relevant_facts_for_prompt(self, user_msg: str, max_facts: int = 10, user_id: str = None) -> str:
        if not user_id:
            return ""
        keywords = self._extract_keywords(user_msg)
        if not keywords:
            return ""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            like_clauses = " OR ".join(["fact LIKE ?"] * len(keywords))
            params = [f"%{kw}%" for kw in keywords]
            cursor.execute(f"""
                SELECT * FROM memory_facts 
                WHERE (user_id = ? OR shared = 1) AND confirmed = 1 AND ({like_clauses})
                ORDER BY confidence DESC, access_count DESC
                LIMIT ?
            """, [user_id] + params + [max_facts])
            rows = cursor.fetchall()
            if not rows:
                return ""
            facts_list = [f"- {row['fact']} (confidence: {row['confidence']})" for row in rows]
            return "Relevant memories:\n" + "\n".join(facts_list)

    def get_formatted_memory_summary(self) -> str:
        facts = self.get_all_facts(limit=50, pending_only=False)
        if not facts:
            return ""
        lines = ["I remember the following information:"]
        for f in facts:
            lines.append(f"- {f.fact} (confidence: {f.confidence})")
        return "\n".join(lines)

    def search_memories(self, query: str, limit: int = 5) -> List[MemoryEntry]:
        query_lower = query.lower()
        query_tags = self._extract_keywords(query)
        results = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM smart_memories 
                WHERE user_msg LIKE ? OR iris_response LIKE ? OR tags LIKE ? OR concepts LIKE ?
                ORDER BY importance DESC, timestamp DESC
                LIMIT ?
            """, (f'%{query_lower}%', f'%{query_lower}%',
                  f'%{json.dumps(query_tags)}%', f'%{query_lower}%', limit))
            for row in cursor.fetchall():
                entry = MemoryEntry(
                    id=row['id'],
                    timestamp=row['timestamp'],
                    user_msg=row['user_msg'],
                    iris_response=row['iris_response'],
                    mood=row['mood'],
                    importance=row['importance'],
                    tags=json.loads(row['tags']) if row['tags'] else [],
                    concepts=json.loads(row['concepts']) if row['concepts'] else []
                )
                results.append(entry)
        return results

    def get_memory_graph(self) -> Dict:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT concept_a as concept FROM concept_links
                UNION
                SELECT DISTINCT concept_b as concept FROM concept_links
            """)
            concepts = [row['concept'] for row in cursor.fetchall()]
            cursor.execute("""
                SELECT concept_a, concept_b, strength FROM concept_links
                ORDER BY strength DESC
                LIMIT 100
            """)
            links = [{"source": row['concept_a'], "target": row['concept_b'], "value": row['strength']}
                     for row in cursor.fetchall()]
            cursor.execute("""
                SELECT id, user_msg, concepts FROM smart_memories
                ORDER BY timestamp DESC
                LIMIT 20
            """)
            memories = [{
                "id": row['id'],
                "preview": row['user_msg'][:50] + "...",
                "concepts": json.loads(row['concepts']) if row['concepts'] else []
            } for row in cursor.fetchall()]
            return {"nodes": [{"id": c, "group": 1} for c in concepts], "links": links, "memories": memories}

    def get_recent_context(self, limit: int = 5) -> str:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM smart_memories 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            if not rows:
                return ""
            context = []
            for row in reversed(rows):
                time_str = datetime.fromisoformat(row['timestamp']).strftime("%b %d, %I:%M %p")
                context.append(f"[{time_str}] User: {row['user_msg']}")
                context.append(f"[{time_str}] IRIS: {row['iris_response'][:100]}...")
            return "\n".join(context)

    def get_memory_summary(self) -> str:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM smart_memories")
            mem_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM memory_facts")
            fact_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(DISTINCT concept_a) FROM concept_links")
            concept_count = cursor.fetchone()[0]
            return f"🧠 {mem_count} conversations • {fact_count} facts • {concept_count} concepts"

    def get_stats(self) -> Dict:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM smart_memories")
            memories = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM memory_facts")
            facts = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM concept_links")
            concept_links = cursor.fetchone()[0]
            cursor.execute("SELECT AVG(importance) FROM smart_memories")
            avg_importance = cursor.fetchone()[0] or 0
            cursor.execute("SELECT AVG(confidence) FROM memory_facts")
            avg_confidence = cursor.fetchone()[0] or 0
            return {
                "memories": memories,
                "facts": facts,
                "concept_links": concept_links,
                "avg_importance": round(avg_importance, 2),
                "avg_confidence": round(avg_confidence, 2)
            }