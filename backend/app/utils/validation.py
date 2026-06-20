"""
Question validation to filter study-related queries
"""

def is_study_question(message: str) -> bool:
    """
    Check if the message is a study-related question or valid conversation
    Returns True if it's study-related or general conversation, False if it's off-topic
    """
    
    message_lower = message.lower().strip()
    
    # ========== ALLOWED: POLITE/CONVERSATIONAL MESSAGES ==========
    polite_messages = [
        "thanks",
        "thank you",
        "ok",
        "okay",
        "sure",
        "yes",
        "no",
        "hello",
        "hi",
        "hey",
        "good morning",
        "good afternoon",
        "good evening",
        "good night",
        "bye",
        "goodbye",
        "see you",
        "take care",
        "help",
        "please",
        "sorry",
        "excuse me",
        "cool",
        "great",
        "awesome",
        "nice",
        "interesting",
        "i see",
        "got it",
        "understood",
        "makes sense",
        "continue",
        "next",
        "more",
        "again",
        "one more time",
        "can you explain",
        "can you help",
        "i don't understand",
        "i don't get it",
        "confused",
        "still confused",
    ]
    
    # Check for polite/conversational messages
    for phrase in polite_messages:
        if message_lower == phrase or message_lower.startswith(phrase):
            return True
    
    # ========== ALLOWED: STUDY KEYWORDS ==========
    study_keywords = [
        "what is",
        "what are",
        "what's",
        "whats",
        "explain",
        "how do",
        "how to",
        "how does",
        "why is",
        "why are",
        "define",
        "definition",
        "meaning of",
        "tell me about",
        "teach me",
        "learn",
        "learning",
        "study",
        "studying",
        "homework",
        "assignment",
        "project",
        "exam",
        "test",
        "quiz",
        "question about",
        "help with",
        "solve",
        "problem",
        "calculate",
        "formula",
        "equation",
        "concept",
        "theory",
        "example of",
        "difference between",
        "compare",
        "contrast",
        "analyze",
        "review",
        "summary",
        "summarize",
        "essay",
        "write about",
        "how can i",
        "i need help",
        "i'm stuck",
        "i don't know",
        "confused about",
        "can you help me",
        "please explain",
    ]
    
    # Check for study keywords
    for keyword in study_keywords:
        if keyword in message_lower:
            return True
    
    # ========== ALLOWED: SCHOOL SUBJECTS ==========
    subjects = [
        # Sciences
        "physics",
        "chemistry",
        "biology",
        "mathematics",
        "math",
        "algebra",
        "geometry",
        "calculus",
        "trigonometry",
        "statistics",
        "computer science",
        "programming",
        "coding",
        "python",
        "javascript",
        "java",
        "c++",
        "sql",
        "database",
        "web development",
        
        # Languages
        "english",
        "spanish",
        "french",
        "german",
        "chinese",
        "japanese",
        "hindi",
        "arabic",
        "portuguese",
        "russian",
        "grammar",
        "vocabulary",
        "pronunciation",
        
        # Social Studies
        "history",
        "geography",
        "economics",
        "political science",
        "sociology",
        "anthropology",
        "philosophy",
        "psychology",
        "civics",
        
        # Arts & Humanities
        "literature",
        "poetry",
        "art",
        "music",
        "history of art",
        "art history",
        "theater",
        "drama",
        
        # Business & Professional
        "business",
        "accounting",
        "finance",
        "management",
        "marketing",
        "entrepreneurship",
        "supply chain",
        
        # Other subjects
        "medicine",
        "anatomy",
        "physiology",
        "engineering",
        "architecture",
        "agriculture",
        "law",
        "nursing",
        "education",
        "environmental science",
        "geology",
        "astronomy",
        "physics",
        "quantum",
        "relativity",
    ]
    
    # Check for school subjects
    for subject in subjects:
        if subject in message_lower:
            return True
    
    # ========== BLOCKED: OFF-TOPIC KEYWORDS ==========
    blocked_keywords = [
        "movie",
        "film",
        "watch",
        "game",
        "gaming",
        "play video",
        "video game",
        "minecraft",
        "fortnite",
        "call of duty",
        "gta",
        "song",
        "music video",
        "lyrics",
        "artist",
        "band",
        "concert",
        "spotify",
        "youtube",
        "tiktok",
        "instagram",
        "facebook",
        "twitter",
        "sports",
        "football",
        "basketball",
        "baseball",
        "soccer",
        "cricket",
        "tennis",
        "nfl",
        "nba",
        "nhl",
        "recipe",
        "cooking",
        "food",
        "restaurant",
        "pizza",
        "burger",
        "joke",
        "funny",
        "meme",
        "dating",
        "relationship",
        "love",
        "romance",
        "breakup",
        "dating advice",
        "fashion",
        "clothes",
        "shopping",
        "news",
        "politics",
        "election",
        "covid",
        "conspiracy",
        "fake news",
        "hacking",
        "illegal",
        "hack",
        "jailbreak",
        "bypass",
        "crack",
    ]
    
    # Check for blocked keywords (strong rejection)
    for keyword in blocked_keywords:
        if keyword in message_lower:
            return False
    
    # ========== DEFAULT: ALLOW IF CONTAINS QUESTION MARK ==========
    # If it has a question mark and isn't blocked, it's probably a question
    if "?" in message:
        return True
    
    # ========== DEFAULT: ALLOW SHORT RESPONSES AND UNCLEAR MESSAGES ==========
    # If message is very short or unclear, give it a chance
    words = message.split()
    if len(words) <= 3:
        return True
    
    # ========== DEFAULT: ALLOW BY DEFAULT ==========
    # Be lenient - only reject if clearly off-topic
    # This way legitimate study questions won't get rejected
    return True