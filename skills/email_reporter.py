"""
IRIS Email Reporter – sends daily, weekly, monthly reports.
"""

import os
import smtplib
import json
import logging
from email.message import EmailMessage
from email.utils import formatdate
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
import platform
from typing import Dict, List, Optional
import subprocess

# Import IRIS modules (they will be injected later to avoid circular imports)
# We'll use dependency injection: the main app passes the needed managers.

logger = logging.getLogger(__name__)

class EmailReporter:
    def __init__(self, db_path: str, doc_manager=None, memory=None, exports_dir="exports"):
        self.db_path = db_path
        self.doc_manager = doc_manager
        self.memory = memory
        self.exports_dir = Path(exports_dir)
        self.smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', 587))
        self.smtp_user = os.environ.get('SMTP_USER', '')
        self.smtp_password = os.environ.get('SMTP_PASSWORD', '')
        self.recipient = os.environ.get('REPORT_RECIPIENT', 'iris.with.vybeflix@gmail.com')
        self.sender = os.environ.get('REPORT_SENDER', self.smtp_user)

    def _get_db_connection(self):
        return sqlite3.connect(self.db_path)

    def send_creator_message(self, subject, body):
        """Send a simple email from creator."""
        return self.send_report('creator_message', f"Subject: {subject}\n\n{body}")

    def send_user_message(self, subject, body):
        """Send a simple email from any user."""
        return self.send_report('user_message', f"Subject: {subject}\n\n{body}")

    # ========== Data Collection ==========

    def get_system_stats(self) -> Dict:
        """Collect system performance data."""
        try:
            import psutil
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "ram_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent,
                "uptime": str(uptime).split('.')[0],
                "boot_time": boot_time.isoformat()
            }
        except ImportError:
            return {"error": "psutil not available"}
        except Exception as e:
            return {"error": str(e)}

    def send_report_with_attachment(self, subject, body, file_path, filename=None, mime_type='application/octet-stream'):
        """Send an email with a file attachment."""
        if not self.smtp_user or not self.smtp_password:
            logger.error("SMTP credentials not set")
            return False

        if not filename:
            filename = os.path.basename(file_path)

        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = self.sender
        msg['To'] = self.recipient
        msg['Date'] = formatdate(localtime=True)
        msg.set_content(body)

        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
            msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=filename)
        except Exception as e:
            logger.error(f"Failed to attach file: {e}")
            return False

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            logger.info(f"Email with attachment sent to {self.recipient}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def get_security_logs(self, days: int = 1) -> List[Dict]:
        """Retrieve activity logs from the last `days` days."""
        with self._get_db_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            since = (datetime.now() - timedelta(days=days)).isoformat()
            cursor.execute("""
                SELECT * FROM activity_log
                WHERE timestamp > ?
                ORDER BY timestamp DESC
            """, (since,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_document_stats(self) -> Dict:
        """Get statistics about stored documents."""
        if not self.doc_manager:
            return {"error": "doc_manager not available"}
        return self.doc_manager.get_document_stats()

    def get_memory_stats(self) -> Dict:
        """Get memory (facts) statistics."""
        if not self.memory:
            return {"error": "memory not available"}
        return self.memory.get_stats()

    def get_chat_activity(self, days: int = 7) -> Dict:
        """Count messages and chats in the last N days."""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            since = (datetime.now() - timedelta(days=days)).isoformat()
            cursor.execute("""
                SELECT COUNT(*) FROM messages
                WHERE timestamp > ?
            """, (since,))
            message_count = cursor.fetchone()[0]
            cursor.execute("""
                SELECT COUNT(*) FROM chats
                WHERE updated_at > ?
            """, (since,))
            chat_count = cursor.fetchone()[0]
            return {
                "messages": message_count,
                "chats": chat_count,
                "period_days": days
            }

    # ========== Report Generation ==========

    def generate_daily_report(self) -> str:
        stats = self.get_system_stats()
        logs = self.get_security_logs(days=1)
        doc_stats = self.get_document_stats()
        chat_activity = self.get_chat_activity(days=1)

        # Placeholder for trading data – you can extend this
        trading_data = "No trading data available."

        report = f"""IRIS Daily Report – {datetime.now().strftime('%Y-%m-%d')}

=== System Status ===
CPU: {stats.get('cpu_percent', 'N/A')}%
RAM: {stats.get('ram_percent', 'N/A')}%
Disk: {stats.get('disk_usage', 'N/A')}%
Uptime: {stats.get('uptime', 'N/A')}

=== Document Stats ===
Total documents: {doc_stats.get('total', 0)}
Total size: {self._format_bytes(doc_stats.get('total_size', 0))}
By type: {doc_stats.get('by_type', {})}

=== Chat Activity (last 24h) ===
New chats: {chat_activity.get('chats', 0)}
Messages: {chat_activity.get('messages', 0)}

=== Security Logs (last 24h) ===
Total events: {len(logs)}
{self._format_logs(logs[:10])}  # show top 10

=== Trading Summary ===
{trading_data}
"""
        return report

    def generate_weekly_report(self) -> str:
        stats = self.get_system_stats()
        doc_stats = self.get_document_stats()
        memory_stats = self.get_memory_stats()
        chat_activity = self.get_chat_activity(days=7)

        report = f"""IRIS Weekly Report – Week of {datetime.now().strftime('%Y-%m-%d')}

=== System Health ===
Average CPU: {stats.get('cpu_percent', 'N/A')}%
Average RAM: {stats.get('ram_percent', 'N/A')}%
Disk usage: {stats.get('disk_usage', 'N/A')}%
Uptime: {stats.get('uptime', 'N/A')}

=== Document Analytics ===
Total documents: {doc_stats.get('total', 0)}
Total size: {self._format_bytes(doc_stats.get('total_size', 0))}
New documents this week: {doc_stats.get('new_this_week', 0)}  (if you add this field)

=== Memory & Facts ===
Facts stored: {memory_stats.get('facts', 0)}
Memories: {memory_stats.get('memories', 0)}
Concept links: {memory_stats.get('concept_links', 0)}

=== Chat Activity (last 7 days) ===
New chats: {chat_activity.get('chats', 0)}
Messages: {chat_activity.get('messages', 0)}

=== Performance Insights ===
(Placeholder – you can add AI response times, etc.)
"""
        return report

    def generate_monthly_report(self) -> str:
        stats = self.get_system_stats()
        doc_stats = self.get_document_stats()
        memory_stats = self.get_memory_stats()
        chat_activity = self.get_chat_activity(days=30)

        report = f"""IRIS Monthly Report – {datetime.now().strftime('%B %Y')}

=== System Overview ===
CPU: {stats.get('cpu_percent', 'N/A')}%
RAM: {stats.get('ram_percent', 'N/A')}%
Disk: {stats.get('disk_usage', 'N/A')}%
Uptime: {stats.get('uptime', 'N/A')}

=== Document Archive ===
Total documents: {doc_stats.get('total', 0)}
Total size: {self._format_bytes(doc_stats.get('total_size', 0))}
By type: {doc_stats.get('by_type', {})}

=== Memory Growth ===
Facts: {memory_stats.get('facts', 0)} (+{memory_stats.get('facts_last_month', 0)})
Memories: {memory_stats.get('memories', 0)} (+{memory_stats.get('memories_last_month', 0)})

=== Chat Statistics (30 days) ===
Chats created: {chat_activity.get('chats', 0)}
Messages exchanged: {chat_activity.get('messages', 0)}

=== Backups ===
- Database backup attached.
- Exports folder archived.
"""
        return report

    # ========== Backup Creation ==========

    def create_backup_archive(self) -> Path:
        """Create a zip archive of databases and exports."""
        import zipfile
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        archive_name = self.exports_dir / f"backup_{timestamp}.zip"
        with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add main database
            if os.path.exists(self.db_path):
                zipf.write(self.db_path, arcname=os.path.basename(self.db_path))
            # Add docs database if exists
            docs_db = self.db_path.replace('iris_secure', 'iris_docs')
            if os.path.exists(docs_db):
                zipf.write(docs_db, arcname=os.path.basename(docs_db))
            # Add exports folder contents
            for file in self.exports_dir.glob('*'):
                if file.name != archive_name.name:
                    zipf.write(file, arcname=f"exports/{file.name}")
        return archive_name

    # ========== Email Sending ==========

    def send_report(self, report_type: str, body: str, attachments: List[Path] = None):
        if not self.smtp_user or not self.smtp_password:
            logger.error("SMTP credentials not set")
            return False

        msg = EmailMessage()
        msg['Subject'] = f"IRIS {report_type.capitalize()} Report – {datetime.now().strftime('%Y-%m-%d')}"
        msg['From'] = self.sender
        msg['To'] = self.recipient
        msg['Date'] = formatdate(localtime=True)
        msg.set_content(body)

        if attachments:
            for att in attachments:
                with open(att, 'rb') as f:
                    data = f.read()
                msg.add_attachment(data, maintype='application', subtype='octet-stream',
                                   filename=att.name)

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            logger.info(f"{report_type} report sent to {self.recipient}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    # ========== Helpers ==========

    def _format_bytes(self, bytes_val):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_val < 1024:
                return f"{bytes_val:.2f} {unit}"
            bytes_val /= 1024
        return f"{bytes_val:.2f} TB"

    def _format_logs(self, logs):
        if not logs:
            return "No logs."
        lines = []
        for log in logs:
            lines.append(f"{log['timestamp']} - {log['action']} - {log.get('details', '')}")
        return "\n".join(lines)

    # ========== Public API ==========

    def send_daily_report(self):
        body = self.generate_daily_report()
        return self.send_report('daily', body)

    def send_weekly_report(self):
        body = self.generate_weekly_report()
        return self.send_report('weekly', body)

    def send_monthly_report(self):
        body = self.generate_monthly_report()
        # For monthly, include backup archive
        archive = self.create_backup_archive()
        return self.send_report('monthly', body, attachments=[archive])