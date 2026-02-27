from .task_keywords import ANDROID_KEYWORDS, BACKEND_KEYWORDS, FRONTEND_KEYWORDS, QA_KEYWORDS


def _get_skills_text(work):
    """Extract skills from task and convert to lowercase"""
    skills = work.get('skills', [])
    return [skill.lower() for skill in skills]


def _get_full_task_text(work):
    """Extract searchable text from entire task (title, description, skills)"""
    return f"{work.get('title', '')} {work.get('description', '')} {' '.join(work.get('skills', []))}".lower()


def _has_keywords_in_skills(skills, keywords):
    """Check if skills contain any of the keywords"""
    return any(kw.lower() in skills for kw in keywords)


def _has_keywords_in_text(text, keywords):
    """Check if text contains any of the keywords"""
    return any(kw.lower() in text for kw in keywords)


def get_task_stack_type(work):
    """Classify task into frontend, backend, android, or qa stack based on skills"""
    skills = _get_skills_text(work)
    has_frontend = _has_keywords_in_skills(skills, FRONTEND_KEYWORDS)
    has_backend = _has_keywords_in_skills(skills, BACKEND_KEYWORDS)
    has_android = _has_keywords_in_skills(skills, ANDROID_KEYWORDS)
    has_qa = _has_keywords_in_skills(skills, QA_KEYWORDS)
    
    if has_android:
        return "android"
    
    if has_backend:
        return "backend"
    
    if has_frontend:
        return "frontend"
    
    if has_qa and not has_backend and not has_frontend:
        return "qa"
    
    if has_qa:
        full_text = _get_full_task_text(work)
        has_frontend_in_text = _has_keywords_in_text(full_text, FRONTEND_KEYWORDS)
        has_backend_in_text = _has_keywords_in_text(full_text, BACKEND_KEYWORDS)
        
        if has_backend_in_text:
            return "backend"
        
        if has_frontend_in_text:
            return "frontend"
        
        return "qa"
    
    return "frontend"


def get_tags_for_task(work):
    """Determine who to tag for a task based on skills, with fallback to full text only for pure QA tasks"""
    skills = _get_skills_text(work)
    has_frontend = _has_keywords_in_skills(skills, FRONTEND_KEYWORDS)
    has_backend = _has_keywords_in_skills(skills, BACKEND_KEYWORDS)
    has_android = _has_keywords_in_skills(skills, ANDROID_KEYWORDS)
    has_qa = _has_keywords_in_skills(skills, QA_KEYWORDS)
    
    if has_android:
        return "⚠️ **IGNORED: Android/React Native Task**"
    
    if has_backend:
        return "@abdullahnaeemgill1724"
    
    if has_frontend:
        return "@sohaib54975"
    
    if has_qa and not has_backend and not has_frontend:
        full_text = _get_full_task_text(work)
        has_frontend_in_text = _has_keywords_in_text(full_text, FRONTEND_KEYWORDS)
        has_backend_in_text = _has_keywords_in_text(full_text, BACKEND_KEYWORDS)
        
        if has_backend_in_text:
            return "@abdullahnaeemgill1724"
        
        if has_frontend_in_text:
            return "@sohaib54975"
    
    return "@abdullahnaeemgill1724 @sohaib54975"
