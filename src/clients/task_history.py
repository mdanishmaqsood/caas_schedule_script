import json
import logging
import os
from datetime import datetime, timedelta
from .task_classifier import get_task_stack_type, get_qa_tech_stack

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
                "timestamp": datetime.now().isoformat(),
                "priority": work.get('priority', 'N/A'),
                "skills": work.get('skills', []),
                "qa_tech_stack": get_qa_tech_stack(work) if stack_type == "qa" else None
            }
            
            history = []
            if os.path.exists(self.history_file):
                with open(self.history_file, "r") as f:
                    history = json.load(f)
            
            if not any(t.get('task_id') == task_id for t in history):
                history.append(task_data)
                os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
                with open(self.history_file, "w") as f:
                    json.dump(history, f, indent=2)
                logger.info(f"Task {task_id} logged as {stack_type} stack")
            else:
                logger.info(f"Task {task_id} already in history")
        except Exception as e:
            logger.error(f"Error logging task: {str(e)}")
    
    def get_last_24_hours_summary(self):
        try:
            if not os.path.exists(self.history_file):
                return None
            
            with open(self.history_file, "r") as f:
                history = json.load(f)
            
            cutoff_time = datetime.now() - timedelta(hours=24)
            recent_tasks = [t for t in history if datetime.fromisoformat(t['timestamp']) >= cutoff_time]
            
            summary = {"frontend": [], "backend": [], "android": [], "qa": [], "mixed": [], "other": []}
            for task in recent_tasks:
                summary[task.get('stack_type', 'other')].append(task)
            
            return summary
        except Exception as e:
            logger.error(f"Error getting 24-hour summary: {str(e)}")
            return None
    
    def cleanup_old_tasks(self):
        """Delete tasks older than 24 hours from history"""
        try:
            if not os.path.exists(self.history_file):
                return
            
            with open(self.history_file, "r") as f:
                history = json.load(f)
            
            cutoff_time = datetime.now() - timedelta(hours=24)
            recent_tasks = [t for t in history if datetime.fromisoformat(t['timestamp']) >= cutoff_time]
            deleted_count = len(history) - len(recent_tasks)
            
            with open(self.history_file, "w") as f:
                json.dump(recent_tasks, f, indent=2)
            
            logger.info(f"Cleaned up {deleted_count} tasks" if deleted_count > 0 else "No old tasks to clean up")
        except Exception as e:
            logger.error(f"Error cleaning up old tasks: {str(e)}")
