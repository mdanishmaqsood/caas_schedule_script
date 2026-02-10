FRONTEND_KEYWORDS = [
    "react", "next", "next.js", "nextjs", "figma", "frontend", 
    "design", "ui", "ux", "javascript", "typescript", 
    "vue", "angular", "svelte", "tailwind", "css", "html",
    "webpack", "vite", "remix", "gatsby", "nuxt", "astro",
    "web", "spa", "pwa", "responsive", "bootstrap", "material ui",
    "storybook", "jest", "vitest", "rollup", "parcel", "turbopack",
    "emotion", "styled components", "sass", "scss", "less",
    "accessibility", "a11y", "wcag", "aria", "component library"
]

BACKEND_KEYWORDS = [
    "django", "python", "fastapi", "backend", "flask",
    "node", "node.js", "nodejs", "express", "nestjs", "nest",
    "go", "golang", "rust", "java", "spring", "spring boot",
    "dotnet", ".net", "c#", "csharp", "php", "laravel",
    "sql", "postgres", "postgresql", "mongodb", "mysql", "redis",
    "api", "rest", "graphql", "grpc", "microservices", "docker", "kubernetes",
    "aws", "gcp", "azure", "firebase", "supabase", "serverless",
    "rabbitmq", "kafka", "elasticsearch", "ratelimit", "caching",
    "jwt", "oauth", "authentication", "authorization", "security",
    "websocket", "socket.io", "real-time", "sse", "crud", "orm", "prisma",
    "typeorm", "sequelize", "entity framework", "hibernate", "deployment"
]

ANDROID_KEYWORDS = [
    "react_native", "react native", "mobile", "android", "ios", "flutter", "kotlin", "swift",
    "xcode", "gradle", "android studio", "app dev", "native", "hybrid",
    "dart", "objective-c", "expo", "rn", "swiftui", "jetpack compose",
    "firebase", "push notification", "geolocation", "camera", "permissions",
    "cordova", "ionic", "nativescript", "xamarin", "macos", "watchos",
    "ipa", "apk", "app store", "google play", "testflight"
]

QA_KEYWORDS = [
    "qa", "qa_tasks", "quality assurance", "testing", "test", "qa tasks",
    "e2e", "end to end", "automation", "manual", "ui test", "unit test",
    "integration test", "regression", "test case", "selenium", "cypress",
    "jest", "pytest", "mocha", "vitest", "playwright", "puppeteer",
    "appium", "detox", "xctest", "espresso", "performance test",
    "load test", "stress test", "api test", "postman", "insomnia",
    "smoke test", "sanity test", "bug report", "bug fix", "defect"
]


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
