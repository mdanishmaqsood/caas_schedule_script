from datetime import datetime, timezone
from .task_classifier import get_tags_for_task

def format_task_message(work, task_id, is_accepted=False):
    tags = get_tags_for_task(work)
    title = "✅ **Task Auto-Accepted!**" if is_accepted else "🎯 **New Task Available!**"
    time_note = "\n\n🤖 This task was automatically accepted during business hours (11:00-17:00)" if is_accepted else ""
    
    return (
        f"{tags}\n\n{title}\n\n"
        f"**Title:** {work.get('title', 'N/A')}\n"
        f"**Task ID:** {task_id}\n"
        f"**Priority:** {work.get('priority', 'N/A')}\n"
        f"**Skills Required:** {', '.join(work.get('skills', ['N/A']))}\n\n"
        f"**Description:**\n{work.get('description', 'No description available')}\n\n"
        f"**Repository:** {work.get('repoUrl', 'N/A')}\n"
        f"**Branch:** {work.get('branchName', 'N/A')}{time_note}"
    )


def format_daily_summary(summary):

    total_tasks = sum(len(tasks) for tasks in summary.values())
    
    message = f"📊 **Daily Task Summary (Last 24 Hours)**\n\n**Total Tasks:** {total_tasks}\n\n"
    
    for stack_type, tasks in summary.items():
        if tasks:
            message += f"**{stack_type.upper()} ({len(tasks)} tasks)**\n"
            for task in tasks:
                task_time = datetime.fromisoformat(task['timestamp']).strftime('%I:%M %p')
                task_title = task['title'][:50]
                qa_info = f" [*{task.get('qa_tech_stack', '').upper()} related*]" if stack_type == "qa" and task.get('qa_tech_stack') else ""
                message += f"  • [{task_time}] Task #{task['task_id']}: {task_title}...{qa_info}\n"
            message += "\n"
    
    message += f"_Generated on {datetime.now(timezone.utc).strftime('%Y-%m-%d at %I:%M %p')} UTC_"
    
    return message
