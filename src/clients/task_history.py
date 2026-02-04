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
            
            summary = {"frontend": [], "backend": [], "android": [], "qa": []}
            for task in recent_tasks:
                stack_type = task.get('stack_type', 'frontend')
                
                if stack_type in ['other']:
                    stack_type = self._reclassify_task_by_skills(task)
                
                if stack_type in summary:
                    summary[stack_type].append(task)
            
            return summary
        except Exception as e:
            logger.error(f"Error getting 24-hour summary: {str(e)}")
            return None
    
    def _reclassify_task_by_skills(self, task):
        """Re-classify a task into frontend, backend, android, or qa stacks"""
        FRONTEND_KEYWORDS = ["react", "next", "nextjs", "figma", "frontend", "design", "ui", "ux", "javascript", "typescript", "vue", "angular"]
        BACKEND_KEYWORDS = ["django", "python", "fastapi", "backend","flask",]
        ANDROID_KEYWORDS = ["react_native", "react native", "mobile", "android", "ios", "flutter", "kotlin", "swift"]
        QA_KEYWORDS = ["qa", "qa_tasks", "quality assurance", "testing", "test", "qa tasks"]
        
        skills = [s.lower() for s in task.get('skills', [])]
        
        has_backend = any(kw in skills for kw in BACKEND_KEYWORDS)
        has_frontend = any(kw in skills for kw in FRONTEND_KEYWORDS)
        has_android = any(kw in skills for kw in ANDROID_KEYWORDS)
        has_qa = any(kw in skills for kw in QA_KEYWORDS)
        
        if has_android:
            return "android"
        
        if has_backend:
            return "backend"
        
        if has_frontend:
            return "frontend"
        
        if has_qa and not has_backend and not has_frontend:
            return "qa"
        
        if has_qa:
            full_text = (task.get('title', '') + ' ' + task.get('description', '')).lower()
            
            has_backend_in_text = any(kw in full_text for kw in BACKEND_KEYWORDS)
            has_frontend_in_text = any(kw in full_text for kw in FRONTEND_KEYWORDS)
            
            if has_backend_in_text:
                return "backend"
            
            if has_frontend_in_text:
                return "frontend"
            
            return "qa"
        
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
