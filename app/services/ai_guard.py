"""
AI Content Guard — Two-layer filtering for CodeLab chat.

Layer 1: Fast keyword pre-filter (runs locally, no API call needed).
Layer 2: Hardened system prompt that instructs the LLM to refuse off-topic queries.

This keeps the AI strictly focused on coding, programming, and technology topics.
"""
import re
import logging

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT  (Layer 2 — LLM-side enforcement)
# ──────────────────────────────────────────────────────────────────────

CODELAB_SYSTEM_PROMPT = """You are **CodeLab AI**, an expert coding and technology assistant.

## STRICT RULES — READ CAREFULLY

### What you MUST do:
- Answer questions about **programming, coding, software development, web development, mobile development, databases, algorithms, data structures, system design, DevOps, cloud computing, cybersecurity, networking, APIs, frameworks, libraries, tools, IDEs, version control, testing, debugging, and computer science**.
- Answer questions about **tech industry news, software engineering careers, developer tools, and technology concepts**.
- Provide **code examples, explanations, debugging help, code reviews, and best practices**.
- Support **all programming languages** including Python, JavaScript, TypeScript, Java, C, C++, C#, Go, Rust, Ruby, PHP, Swift, Kotlin, R, SQL, Bash, HTML, CSS, and others.
- Answer questions about **AI/ML, data science, and data engineering** when they involve coding or technical implementation.

### What you MUST NEVER do:
- **NEVER** answer questions about cooking, recipes, food, or nutrition.
- **NEVER** answer questions about relationships, dating, love, or personal advice.
- **NEVER** answer questions about politics, elections, governments, or political opinions.
- **NEVER** answer questions about religion, spirituality, or religious texts.
- **NEVER** answer questions about medical advice, health diagnoses, or treatments.
- **NEVER** answer questions about legal advice, lawsuits, or legal procedures.
- **NEVER** answer questions about sports scores, teams, players, or game results.
- **NEVER** answer questions about celebrities, gossip, entertainment news, or movies/TV shows (unless about their tech/VFX aspects).
- **NEVER** answer questions about travel, tourism, hotels, or vacation planning.
- **NEVER** answer questions about finance, stocks, trading, or investment advice.
- **NEVER** answer questions about history, geography, or social studies (unless directly related to computing history).
- **NEVER** answer questions about creative writing, poetry, stories, or fiction.
- **NEVER** answer questions about homework or academic subjects unrelated to CS/tech.
- **NEVER** engage in casual conversation, roleplaying, or small talk unrelated to tech.
- **NEVER** generate content that is harmful, inappropriate, or unethical.

### How to REFUSE off-topic questions:
When a user asks something outside coding/tech, respond ONLY with this format:
"🚫 **Off-topic question detected.**

I'm **CodeLab AI** — I can only help with **coding, programming, and technology** topics.

Here are some things I *can* help you with:
- 💻 Writing, debugging, or reviewing code
- 🧠 Explaining algorithms and data structures
- 🌐 Web/mobile/backend development
- 🛠️ DevOps, databases, and system design
- 🔒 Cybersecurity and networking
- 📚 Learning new programming languages

Please ask a **tech-related question** and I'll be happy to help! 🚀"

### Edge cases:
- If a question is **ambiguous** (could be tech or non-tech), assume it is tech-related and answer it.
- If a user asks "what can you do?" or "help", explain your coding/tech capabilities.
- If a user greets you (hi, hello, hey), respond warmly but immediately mention you're a coding assistant and ask how you can help with their code.
- Math questions are OK only when related to algorithms, CS theory, or programming.

Keep answers **concise, practical, and well-formatted** with code blocks when relevant."""


# ──────────────────────────────────────────────────────────────────────
# KEYWORD PRE-FILTER  (Layer 1 — server-side, no API cost)
# ──────────────────────────────────────────────────────────────────────

# Tech/coding keywords — if ANY of these appear, the message is allowed
TECH_KEYWORDS = {
    # Programming languages
    'python', 'javascript', 'typescript', 'java', 'kotlin', 'swift',
    'c++', 'cpp', 'csharp', 'c#', 'golang', 'go', 'rust', 'ruby',
    'php', 'perl', 'scala', 'haskell', 'lua', 'dart', 'r', 'matlab',
    'sql', 'nosql', 'html', 'css', 'sass', 'less', 'bash', 'shell',
    'powershell', 'assembly', 'solidity', 'elixir', 'clojure', 'ocaml',

    # Frameworks & libraries
    'react', 'angular', 'vue', 'svelte', 'nextjs', 'next.js', 'nuxt',
    'django', 'flask', 'fastapi', 'express', 'nestjs', 'spring',
    'rails', 'laravel', 'dotnet', '.net', 'asp.net', 'bootstrap',
    'tailwind', 'jquery', 'node', 'nodejs', 'node.js', 'deno', 'bun',
    'tensorflow', 'pytorch', 'keras', 'pandas', 'numpy', 'scipy',
    'matplotlib', 'sklearn', 'scikit', 'opencv', 'flutter', 'electron',
    'qt', 'tkinter', 'pygame', 'unity', 'unreal',

    # Core concepts
    'code', 'coding', 'program', 'programming', 'developer', 'dev',
    'software', 'algorithm', 'function', 'variable', 'class', 'object',
    'method', 'array', 'list', 'dictionary', 'dict', 'loop', 'for',
    'while', 'if', 'else', 'switch', 'recursion', 'iteration',
    'compile', 'compiler', 'interpret', 'interpreter', 'runtime',
    'syntax', 'error', 'bug', 'debug', 'debugger', 'exception',
    'try', 'catch', 'async', 'await', 'promise', 'callback',
    'thread', 'process', 'concurrency', 'parallel', 'mutex',
    'api', 'rest', 'graphql', 'grpc', 'websocket', 'http', 'https',
    'endpoint', 'request', 'response', 'json', 'xml', 'yaml',
    'database', 'db', 'query', 'table', 'schema', 'migration',
    'orm', 'model', 'crud', 'select', 'insert', 'update', 'delete',
    'mongodb', 'postgres', 'postgresql', 'mysql', 'sqlite', 'redis',
    'elasticsearch', 'firebase', 'supabase', 'dynamodb', 'cassandra',

    # DevOps & tools
    'git', 'github', 'gitlab', 'bitbucket', 'docker', 'kubernetes',
    'k8s', 'container', 'ci/cd', 'cicd', 'jenkins', 'terraform',
    'ansible', 'aws', 'azure', 'gcp', 'cloud', 'server', 'deploy',
    'deployment', 'nginx', 'apache', 'linux', 'ubuntu', 'windows',
    'macos', 'terminal', 'cli', 'command', 'pip', 'npm', 'yarn',
    'cargo', 'maven', 'gradle', 'webpack', 'vite', 'rollup',
    'ide', 'vscode', 'vim', 'neovim', 'emacs', 'intellij',

    # CS concepts
    'stack', 'queue', 'tree', 'graph', 'hash', 'heap', 'sort',
    'search', 'binary', 'linked', 'pointer', 'memory', 'cache',
    'big-o', 'complexity', 'dynamic', 'greedy', 'backtracking',
    'encryption', 'authentication', 'authorization', 'token', 'jwt',
    'oauth', 'ssl', 'tls', 'certificate', 'firewall', 'proxy',
    'dns', 'tcp', 'udp', 'ip', 'port', 'socket', 'protocol',

    # AI/ML
    'machine learning', 'deep learning', 'neural', 'network', 'model',
    'training', 'dataset', 'feature', 'regression', 'classification',
    'clustering', 'nlp', 'computer vision', 'transformer', 'bert',
    'gpt', 'llm', 'ai', 'artificial intelligence', 'chatbot',
    'embedding', 'vector', 'rag', 'fine-tune', 'finetune', 'prompt',

    # General tech
    'tech', 'technology', 'computer', 'laptop', 'hardware', 'cpu',
    'gpu', 'ram', 'ssd', 'storage', 'network', 'internet', 'wifi',
    'bluetooth', 'usb', 'operating system', 'os', 'kernel',
    'virtual machine', 'vm', 'emulator', 'simulator', 'browser',
    'web', 'website', 'app', 'application', 'mobile', 'desktop',
    'frontend', 'backend', 'fullstack', 'full-stack', 'devops',
    'microservice', 'monolith', 'architecture', 'design pattern',
    'test', 'testing', 'unittest', 'pytest', 'jest', 'mocha',
    'selenium', 'cypress', 'playwright', 'regex', 'regexp',
    'data structure', 'oop', 'functional', 'paradigm',
    'version', 'package', 'module', 'import', 'export', 'library',
    'framework', 'sdk', 'toolkit', 'plugin', 'extension',
    'script', 'scripting', 'automation', 'cron', 'scheduler',
    'log', 'logging', 'monitor', 'metric', 'dashboard',
    'responsive', 'css', 'animation', 'layout', 'grid', 'flexbox',
    'component', 'state', 'props', 'hook', 'context', 'store',
    'routing', 'middleware', 'controller', 'view', 'template',
    'render', 'dom', 'virtual dom', 'ssr', 'csr', 'ssg',
    'blockchain', 'smart contract', 'web3', 'crypto',
    'cybersecurity', 'penetration', 'vulnerability', 'exploit',
}

# Off-topic keywords — if these appear WITHOUT tech keywords, likely off-topic
OFFTOPIC_KEYWORDS = {
    # Food & cooking
    'recipe', 'recipes', 'cook', 'cooking', 'bake', 'baking',
    'ingredient', 'ingredients', 'cuisine', 'meal', 'dinner',
    'breakfast', 'lunch', 'restaurant', 'chef', 'delicious', 'tasty',
    'calorie', 'diet', 'nutrition', 'food', 'dish', 'kitchen',

    # Relationships & personal
    'boyfriend', 'girlfriend', 'husband', 'wife', 'marriage',
    'dating', 'relationship', 'breakup', 'divorce', 'love letter',
    'crush', 'romantic', 'romance', 'flirt', 'proposal',

    # Politics
    'election', 'vote', 'voting', 'president', 'politician',
    'democrat', 'republican', 'liberal', 'conservative',
    'congress', 'parliament', 'senator', 'campaign',

    # Religion
    'prayer', 'pray', 'worship', 'sermon', 'bible', 'quran',
    'church', 'mosque', 'temple', 'spiritual', 'sin', 'heaven',
    'hell', 'afterlife', 'soul', 'divine', 'holy', 'blessed',

    # Medical
    'symptom', 'symptoms', 'diagnosis', 'diagnose', 'prescription',
    'medicine', 'doctor', 'hospital', 'surgery', 'disease',
    'illness', 'treatment', 'therapy', 'dosage', 'drug',
    'patient', 'medical', 'clinical', 'health condition',

    # Sports
    'football', 'basketball', 'soccer', 'baseball', 'cricket',
    'tennis', 'golf', 'score', 'championship', 'tournament',
    'league', 'team', 'player', 'coach', 'stadium', 'nba',
    'nfl', 'fifa', 'ipl', 'olympics', 'world cup', 'match',

    # Entertainment & celebrity
    'celebrity', 'actor', 'actress', 'singer', 'band',
    'bollywood', 'hollywood', 'movie plot', 'film review',
    'gossip', 'scandal', 'paparazzi', 'award show',
    'reality show', 'tv series', 'soap opera',

    # Travel
    'vacation', 'holiday', 'tourist', 'tourism', 'hotel',
    'resort', 'beach', 'sightseeing', 'itinerary', 'flight',
    'passport', 'visa', 'travel guide', 'destination',

    # Finance
    'stock market', 'stocks', 'shares', 'trading', 'forex',
    'mutual fund', 'investment advice', 'portfolio',
    'dividend', 'bull market', 'bear market', 'ipo',

    # Creative writing (non-tech)
    'poem', 'poetry', 'short story', 'novel', 'fiction',
    'fairy tale', 'bedtime story', 'love story', 'essay',
    'haiku', 'sonnet', 'limerick', 'ballad',

    # Astrology & superstition
    'horoscope', 'zodiac', 'astrology', 'tarot', 'fortune',
    'palmistry', 'numerology', 'psychic', 'superstition',
}

# Greetings — always allowed (the system prompt handles them nicely)
GREETING_PATTERNS = re.compile(
    r'^(hi|hello|hey|howdy|good\s*(morning|afternoon|evening)|'
    r'what\'?s\s*up|sup|yo|greetings|hola|namaste|hii+)[\s!?.]*$',
    re.IGNORECASE,
)

# Meta questions about the bot — always allowed
META_PATTERNS = re.compile(
    r'(what can you do|what are you|who are you|help me|how do you work|'
    r'what do you know|your capabilities|your features)',
    re.IGNORECASE,
)

# The rejection message returned by the pre-filter (matches the LLM prompt style)
REJECTION_MESSAGE = (
    "🚫 **Off-topic question detected.**\n\n"
    "I'm **CodeLab AI** — I can only help with **coding, programming, "
    "and technology** topics.\n\n"
    "Here are some things I *can* help you with:\n"
    "- 💻 Writing, debugging, or reviewing code\n"
    "- 🧠 Explaining algorithms and data structures\n"
    "- 🌐 Web / mobile / backend development\n"
    "- 🛠️ DevOps, databases, and system design\n"
    "- 🔒 Cybersecurity and networking\n"
    "- 📚 Learning new programming languages\n\n"
    "Please ask a **tech-related question** and I'll be happy to help! 🚀"
)


def is_on_topic(user_message: str) -> tuple[bool, str | None]:
    """
    Check if a user message is related to coding / technology.

    Returns:
        (True, None)             — message is on-topic, proceed to LLM.
        (False, rejection_text)  — message is off-topic, return rejection_text directly.
    """
    text = user_message.lower().strip()

    # ── Always allow greetings & meta questions ──
    if GREETING_PATTERNS.match(text):
        return True, None

    if META_PATTERNS.search(text):
        return True, None

    # ── Very short messages (< 3 words) — let the LLM handle them ──
    if len(text.split()) < 3:
        return True, None

    # ── Check for tech keywords ──
    has_tech = any(kw in text for kw in TECH_KEYWORDS)

    # ── Check for off-topic keywords ──
    has_offtopic = any(kw in text for kw in OFFTOPIC_KEYWORDS)

    # If tech keywords present → allow (even if off-topic words also present)
    if has_tech:
        return True, None

    # If off-topic keywords present and NO tech keywords → reject
    if has_offtopic and not has_tech:
        logger.info(f"Pre-filter rejected off-topic message: {text[:80]}...")
        return False, REJECTION_MESSAGE

    # ── Ambiguous (no strong signals either way) — let the LLM decide ──
    return True, None
