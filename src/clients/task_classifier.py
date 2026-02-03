FRONTEND_KEYWORDS = [
    "react", "next", "next.js", "figma", "frontend", 
    "design", "ui", "ux", "css", "html", "javascript", "typescript", 
    "vue", "angular"
]

BACKEND_KEYWORDS = [
    "django", "python", "fastapi", "backend", "api", "database", 
    "sql", "postgres", "mongodb", "flask", "node", "express"
]

ANDROID_KEYWORDS = [
    "react_native", "react native", "mobile", "android", "ios", "flutter", "kotlin", "swift"
]

QA_KEYWORDS = [
    "qa", "qa_tasks", "quality assurance", "testing", "test", "qa tasks"
]


def _get_task_text(work):
    """Extract searchable text from task"""
    return f"{work.get('title', '')} {work.get('description', '')} {' '.join(work.get('skills', []))}".lower()


def _has_keywords(text, keywords):
    """Check if text contains any of the keywords"""
    return any(kw.lower() in text for kw in keywords)


def get_task_stack_type(work):
    """Classify task as frontend or backend only"""
    text = _get_task_text(work)
    has_frontend = _has_keywords(text, FRONTEND_KEYWORDS)
    has_backend = _has_keywords(text, BACKEND_KEYWORDS)
    has_android = _has_keywords(text, ANDROID_KEYWORDS)
    
    # Android/React Native tasks should be filtered out already, but if they appear, classify as frontend
    if has_android:
        return "frontend"
    
    # If task has both frontend and backend keywords, determine dominant stack
    if has_frontend and has_backend:
        # Count keyword matches to determine which is dominant
        frontend_count = sum(1 for kw in FRONTEND_KEYWORDS if kw.lower() in text)
        backend_count = sum(1 for kw in BACKEND_KEYWORDS if kw.lower() in text)
        return "backend" if backend_count > frontend_count else "frontend"
    
    # Backend tasks (including backend QA)
    if has_backend:
        return "backend"
    
    # Frontend tasks (including frontend QA and general QA)
    if has_frontend:
        return "frontend"
    
    # Default: if no clear match, classify as frontend (most QA tasks are frontend)
    return "frontend"


def get_tags_for_task(work):
    """Determine who to tag for a task"""
    text = _get_task_text(work)
    has_frontend = _has_keywords(text, FRONTEND_KEYWORDS)
    has_backend = _has_keywords(text, BACKEND_KEYWORDS)
    has_android = _has_keywords(text, ANDROID_KEYWORDS)
    
    # Android/React Native tasks - mark as ignored
    if has_android:
        return "⚠️ **IGNORED: Android/React Native Task**"
    
    # Backend tasks → Abdullah only
    if has_backend and not has_frontend:
        return "@abdullahnaeemgill1724"
    
    # Frontend tasks (includes QA, design, etc.) → Sohaib only
    if has_frontend:
        return "@sohaib54975"
    
    # If both or neither, count keyword matches to determine dominant stack
    if has_backend:
        frontend_count = sum(1 for kw in FRONTEND_KEYWORDS if kw.lower() in text)
        backend_count = sum(1 for kw in BACKEND_KEYWORDS if kw.lower() in text)
        return "@abdullahnaeemgill1724" if backend_count > frontend_count else "@sohaib54975"
    
    # Default to Sohaib for unclear tasks
    return "@sohaib54975"
