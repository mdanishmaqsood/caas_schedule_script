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


def get_qa_tech_stack(work):
    text = _get_task_text(work)
    has_frontend = _has_keywords(text, FRONTEND_KEYWORDS)
    has_backend = _has_keywords(text, BACKEND_KEYWORDS)
    
    if has_frontend and not has_backend:
        return "frontend"
    elif has_backend and not has_frontend:
        return "backend"
    else:
        return "general"


def get_task_stack_type(work):
    text = _get_task_text(work)
    has_frontend = _has_keywords(text, FRONTEND_KEYWORDS[:7])
    has_backend = _has_keywords(text, BACKEND_KEYWORDS[:4])
    has_android = _has_keywords(text, ANDROID_KEYWORDS)
    has_qa = _has_keywords(text, QA_KEYWORDS)
    
    if has_android and not has_frontend and not has_backend and not has_qa:
        return "android"
    elif has_frontend and not has_backend and not has_qa and not has_android:
        return "frontend"
    elif has_backend and not has_frontend and not has_qa and not has_android:
        return "backend"
    elif has_qa and not has_frontend and not has_backend and not has_android:
        return "qa"
    elif has_frontend or has_backend or has_qa or has_android:
        return "mixed"
    return "other"


def get_tags_for_task(work):
    text = _get_task_text(work)
    has_frontend = _has_keywords(text, FRONTEND_KEYWORDS[:7])
    has_backend = _has_keywords(text, BACKEND_KEYWORDS[:4])
    has_android = _has_keywords(text, ANDROID_KEYWORDS)
    has_qa = _has_keywords(text, QA_KEYWORDS)
    
    if has_android and not has_frontend and not has_backend and not has_qa:
        return "@sohaib54975"
    elif has_frontend and not has_backend and not has_qa and not has_android:
        return "@sohaib54975"
    elif has_backend and not has_frontend and not has_qa and not has_android:
        return "@abdullahnaeemgill1724"
    return "@sohaib54975 @abdullahnaeemgill1724"
