import json
import logging
import os
from datetime import datetime, timedelta, timezone
from .task_classifier import get_task_stack_type

logger = logging.getLogger()


class TaskHistory:
    def __init__(self, history_file="src/data/task_history.json"):
        self.history_file = history_file
    
    def log_task(self, work):

        try:
            task_id = work.get('id')
            stack_type = get_task_stack_type(work)
            
            task_data = {
                "task_id": task_id,
                "title": work.get('title', 'N/A'),
                "stack_type": stack_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "priority": work.get('priority', 'N/A'),
                "skills": work.get('skills', [])
            }
            
            history = []
            if os.path.exists(self.history_file):
                try:
                    with open(self.history_file, "r") as f:
                        content = f.read().strip()
                        if content:
                            history = json.loads(content)
                except (json.JSONDecodeError, ValueError):
                    logger.warning("Task history file corrupted, starting fresh")
                    history = []
            
            if not any(t.get('task_id') == task_id for t in history):
                history.append(task_data)
                os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
                # Write to temporary file first, then rename for atomic operation
                temp_file = self.history_file + ".tmp"
                with open(temp_file, "w") as f:
                    json.dump(history, f, indent=2)
                if os.path.exists(self.history_file):
                    os.remove(self.history_file)
                os.rename(temp_file, self.history_file)
                logger.info(f"Task {task_id} logged as {stack_type} stack")
            else:
                logger.info(f"Task {task_id} already in history")
        except Exception as e:
            logger.error(f"Error logging task: {str(e)}")

    def has_task(self, task_id):
        """Check if a task ID already exists in history"""
        try:
            if not os.path.exists(self.history_file):
                return False

            with open(self.history_file, "r") as f:
                content = f.read().strip()
                if not content:
                    return False
                history = json.loads(content)

            return any(t.get('task_id') == task_id for t in history)
        except (json.JSONDecodeError, ValueError):
            logger.warning("Task history file corrupted while checking task, treating as empty")
            return False
        except Exception as e:
            logger.error(f"Error checking task history: {str(e)}")
            return False
    
    def get_last_24_hours_summary(self):
        try:
            if not os.path.exists(self.history_file):
                return None
            
            with open(self.history_file, "r") as f:
                content = f.read().strip()
                if not content:
                    return None
                history = json.loads(content)
            
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
            recent_tasks = [t for t in history if datetime.fromisoformat(t['timestamp']) >= cutoff_time]
            
            summary = {"frontend": [], "backend": []}
            for task in recent_tasks:
                stack_type = task.get('stack_type', 'frontend')
                
                # For 'mixed' or 'qa' tasks, re-classify based on skills
                if stack_type in ['qa', 'mixed', 'android', 'other']:
                    stack_type = self._reclassify_task_by_skills(task)
                
                if stack_type in summary:
                    summary[stack_type].append(task)
            
            return summary
        except Exception as e:
            logger.error(f"Error getting 24-hour summary: {str(e)}")
            return None
    
    def _reclassify_task_by_skills(self, task):
        """Re-classify a task based on its skills when stack_type is ambiguous"""
        FRONTEND_KEYWORDS = ["react", "next", "nextjs", "figma", "frontend", "design", "ui", "ux", "css", "html", "javascript", "typescript", "vue", "angular"]
        BACKEND_KEYWORDS = ["django", "python", "fastapi", "backend", "api", "database", "sql", "postgres", "mongodb", "flask", "node", "express"]
        
        skills = [s.lower() for s in task.get('skills', [])]
        title_desc = (task.get('title', '') + ' ' + task.get('description', '')).lower()
        
        # Check for backend keywords in skills and title
        has_backend = any(kw in skills or kw in title_desc for kw in BACKEND_KEYWORDS)
        has_frontend = any(kw in skills or kw in title_desc for kw in FRONTEND_KEYWORDS)
        
        # If both or neither found, count matches to determine dominant
        if has_backend and has_frontend:
            backend_count = sum(1 for kw in BACKEND_KEYWORDS if any(kw in s for s in skills) or kw in title_desc)
            frontend_count = sum(1 for kw in FRONTEND_KEYWORDS if any(kw in s for s in skills) or kw in title_desc)
            return "backend" if backend_count >= frontend_count else "frontend"
        
        # If only backend keywords found, it's backend
        if has_backend:
            return "backend"
        
        # Default to frontend (includes QA and other tasks without clear indicators)
        return "frontend"
    
    def cleanup_old_tasks(self):
        """Delete tasks older than 24 hours from history"""
        try:
            if not os.path.exists(self.history_file):
                return
            
            with open(self.history_file, "r") as f:
                content = f.read().strip()
                if not content:
                    return
                history = json.loads(content)
            
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
            recent_tasks = [t for t in history if datetime.fromisoformat(t['timestamp']) >= cutoff_time]
            deleted_count = len(history) - len(recent_tasks)
            
            with open(self.history_file, "w") as f:
                json.dump(recent_tasks, f, indent=2)
            
            logger.info(f"Cleaned up {deleted_count} tasks" if deleted_count > 0 else "No old tasks to clean up")
        except Exception as e:
            logger.error(f"Error cleaning up old tasks: {str(e)}")

    def clear_history(self):
        """Clear all task history"""
        try:
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            with open(self.history_file, "w") as f:
                json.dump([], f, indent=2)
            logger.info("Task history cleared")
        except Exception as e:
            logger.error(f"Error clearing task history: {str(e)}")
