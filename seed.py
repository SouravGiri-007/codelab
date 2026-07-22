"""Seed CodeLab with example snippets and news. Run from codelab/ directory."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set a dev secret key if not already configured
if 'SECRET_KEY' not in os.environ:
    os.environ['SECRET_KEY'] = 'dev-secret-key-change-in-production'

from app import create_app, db
from app.models import (User, Snippet, Tag, NewsArticle,
                        NewsletterSubscription, AdminSetting)
from app.auth import register_user
from app.utils import slugify
from datetime import datetime, timezone

app = create_app()

SNIPPETS = [
    {
        "title": "Flask REST API Boilerplate",
        "language": "python",
        "description": "A clean Flask API skeleton with error handling, JSON responses, and request validation. Perfect as a starting point for any Flask API project.",
        "tags": ["flask", "api", "python", "boilerplate"],
        "body": '''from flask import Flask, request, jsonify
from werkzeug.exceptions import HTTPException

app = Flask(__name__)
app.config['ERROR_INCLUDE_MESSAGE'] = False

# In-memory store (replace with a real DB)
items = []
next_id = 1

def error_response(message, status=400):
    return jsonify({"error": message}), status

@app.errorhandler(HTTPException)
def handle_exception(e):
    return jsonify({"error": e.name, "detail": e.description}), e.code

@app.get("/api/items")
def list_items():
    """List all items with optional search."""
    q = request.args.get("q", "").lower()
    result = [i for i in items if q in i["name"].lower()] if q else items
    return jsonify({"items": result, "count": len(result)})

@app.post("/api/items")
def create_item():
    """Create a new item."""
    global next_id
    data = request.get_json(silent=True)
    if not data or "name" not in data:
        return error_response("'name' is required")
    
    item = {"id": next_id, "name": data["name"], "done": False}
    items.append(item)
    next_id += 1
    return jsonify(item), 201

@app.patch("/api/items/<int:item_id>")
def update_item(item_id):
    """Toggle item completion status."""
    item = next((i for i in items if i["id"] == item_id), None)
    if not item:
        return error_response("Item not found", 404)
    item["done"] = not item["done"]
    return jsonify(item)

@app.delete("/api/items/<int:item_id>")
def delete_item(item_id):
    """Delete an item by ID."""
    global items
    original_len = len(items)
    items = [i for i in items if i["id"] != item_id]
    if len(items) == original_len:
        return error_response("Item not found", 404)
    return "", 204

if __name__ == "__main__":
    app.run(debug=True)'''
    },
    {
        "title": "Debounce Function in JavaScript",
        "language": "javascript",
        "description": "A reusable debounce utility that delays function execution until after a pause in calls. Essential for search inputs, window resize handlers, and scroll events.",
        "tags": ["javascript", "utility", "performance", "debounce"],
        "body": '''/**
 * Creates a debounced version of a function.
 * @param {Function} fn - The function to debounce
 * @param {number} delay - Delay in milliseconds
 * @returns {Function} Debounced function with .cancel() method
 */
function debounce(fn, delay = 300) {
    let timer = null;

    const debounced = function (...args) {
        clearTimeout(timer);
        timer = setTimeout(() => {
            fn.apply(this, args);
        }, delay);
    };

    debounced.cancel = function () {
        clearTimeout(timer);
        timer = null;
    };

    return debounced;
}

// --- Usage Examples ---

// 1. Search input
const searchInput = document.querySelector("#search");
const handleSearch = debounce((e) => {
    console.log("Searching for:", e.target.value);
    fetchResults(e.target.value);
}, 500);

searchInput.addEventListener("input", handleSearch);

// 2. Window resize
const handleResize = debounce(() => {
    console.log("Window size:", window.innerWidth, "x", window.innerHeight);
}, 250);

window.addEventListener("resize", handleResize);'''
    },
    {
        "title": "CSS Glassmorphism Card Component",
        "language": "css",
        "description": "A modern glassmorphism card with frosted glass effect, animated gradient border, and hover states. Works great for dashboards, portfolios, and landing pages.",
        "tags": ["css", "design", "glassmorphism", "ui"],
        "body": '''/* Glassmorphism Card */
.glass-card {
    position: relative;
    max-width: 380px;
    padding: 2rem;
    border-radius: 20px;
    background: rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.15);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
    color: #fff;
    transition: transform 0.3s ease;
    overflow: hidden;
}

.glass-card:hover {
    transform: translateY(-6px);
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.glass-card h3 { font-size: 1.4rem; font-weight: 700; margin-bottom: 0.75rem; }
.glass-card p { font-size: 0.95rem; line-height: 1.6; opacity: 0.85; }

body {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    font-family: "Inter", system-ui, sans-serif;
}'''
    },
    {
        "title": "Binary Search with Bisect Module",
        "language": "python",
        "description": "Python's bisect module for efficient binary search operations on sorted lists. Includes insertion, finding, and counting duplicates in O(log n) time.",
        "tags": ["python", "algorithm", "search", "bisect"],
        "body": '''import bisect

# --- Setup ---
data = [2, 5, 7, 10, 15, 20, 25, 30]

# bisect_right: find insertion point (after existing entries)
idx = bisect.bisect_right(data, 15)  # returns 5
bisect.insort(data, 12)              # insert 12 maintaining sort

def find_closest(sorted_list, target):
    """Find the element closest to target in a sorted list."""
    pos = bisect.bisect_left(sorted_list, target)
    if pos == 0:
        return sorted_list[0]
    if pos == len(sorted_list):
        return sorted_list[-1]
    before = sorted_list[pos - 1]
    after = sorted_list[pos]
    return before if target - before <= after - target else after

def count_in_range(sorted_list, low, high):
    """Count elements in [low, high] using binary search."""
    left = bisect.bisect_left(sorted_list, low)
    right = bisect.bisect_right(sorted_list, high)
    return right - left

# --- Demo ---
if __name__ == "__main__":
    nums = [1, 3, 3, 3, 5, 7, 9, 9, 12, 15]
    print("List:", nums)
    print("Closest to 8:", find_closest(nums, 8))
    print("Count in [3, 9]:", count_in_range(nums, 3, 9))'''
    },
    {
        "title": "Async File I/O with Error Handling",
        "language": "typescript",
        "description": "TypeScript utility for reading/writing files asynchronously with proper error handling, retry logic, and type safety.",
        "tags": ["typescript", "async", "nodejs", "filesystem"],
        "body": '''import { readFile, writeFile, mkdir } from "fs/promises";
import { dirname } from "path";

interface ReadResult { success: true; data: string; path: string; }
interface ErrorResult { success: false; error: string; path: string; }
type FileResult = ReadResult | ErrorResult;

async function safeRead(filePath: string): Promise<FileResult> {
    try {
        const data = await readFile(filePath, "utf-8");
        return { success: true, data, path: filePath };
    } catch (err: any) {
        return {
            success: false,
            error: err.code === "ENOENT" ? "File not found" : err.message,
            path: filePath,
        };
    }
}

async function safeWrite(filePath: string, content: string): Promise<FileResult> {
    try {
        await mkdir(dirname(filePath), { recursive: true });
        await writeFile(filePath, content, "utf-8");
        return { success: true, data: content, path: filePath };
    } catch (err: any) {
        return { success: false, error: err.message, path: filePath };
    }
}

async function readJSON<T>(filePath: string): Promise<T | null> {
    const result = await safeRead(filePath);
    if (!result.success) return null;
    try { return JSON.parse(result.data) as T; } catch { return null; }
}

async function main() {
    const result = await safeRead("./config.json");
    if (result.success) {
        console.log(`Read ${result.path}: ${result.data.length} chars`);
    } else {
        console.error(`Failed: ${result.error}`);
    }
}

main();'''
    },
    {
        "title": "SQL Window Functions for Analytics",
        "language": "sql",
        "description": "Essential SQL window function patterns: running totals, ranking, row numbering, and period-over-period comparisons.",
        "tags": ["sql", "analytics", "window-functions", "database"],
        "body": '''-- 1. Running total per category
SELECT
    sale_date, category, amount,
    SUM(amount) OVER (
        PARTITION BY category ORDER BY sale_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_total
FROM sales ORDER BY category, sale_date;

-- 2. Rank products by total sales
SELECT
    product, category, SUM(amount) AS total_sales,
    DENSE_RANK() OVER (
        PARTITION BY category ORDER BY SUM(amount) DESC
    ) AS rank_in_category
FROM sales GROUP BY product, category;

-- 3. Month-over-month growth
WITH monthly AS (
    SELECT DATE_TRUNC('month', sale_date) AS month,
           SUM(amount) AS revenue
    FROM sales GROUP BY 1
)
SELECT month, revenue,
    LAG(revenue) OVER (ORDER BY month) AS prev_month,
    ROUND((revenue - LAG(revenue) OVER (ORDER BY month))
        / NULLIF(LAG(revenue) OVER (ORDER BY month), 0) * 100, 2)
    AS growth_pct
FROM monthly;

-- 4. Top 3 products per category
SELECT * FROM (
    SELECT category, product, SUM(amount) AS total,
        ROW_NUMBER() OVER (
            PARTITION BY category ORDER BY SUM(amount) DESC
        ) AS rn
    FROM sales GROUP BY category, product
) ranked WHERE rn <= 3;'''
    },
]

# Sample news articles (these will be static seed data)
SAMPLE_NEWS = [
    {
        'title': 'Python 3.13 Released with Free-Threaded Mode and JIT',
        'source': 'hackernews',
        'source_url': 'https://news.ycombinator.com/item?id=python313',
        'external_id': 'python313',
        'summary': 'Python 3.13 introduces experimental free-threaded mode (no GIL) and a just-in-time compiler. These are major performance improvements that let Python run truly parallel threads without the global interpreter lock bottleneck.',
        'upvotes': 1247,
        'comment_count': 389,
    },
    {
        'title': 'Rust Foundation Announces New Corporate Members and Roadmap',
        'source': 'hackernews',
        'source_url': 'https://news.ycombinator.com/item?id=rust-foundation',
        'external_id': 'rust-foundation',
        'summary': 'The Rust Foundation has added several new corporate sponsors and published a detailed roadmap for 2025, focusing on improving the Rust compiler, expanding the ecosystem, and making Rust more accessible to enterprise developers.',
        'upvotes': 892,
        'comment_count': 214,
    },
    {
        'title': 'Building a Real-Time Collaboration Engine with CRDTs',
        'source': 'devto',
        'source_url': 'https://dev.to/user/crdt-collab',
        'external_id': 'crdt-article',
        'summary': 'A comprehensive guide to implementing Conflict-Free Replicated Data Types (CRDTs) for building real-time collaborative applications like Google Docs. Covers practical examples in JavaScript with Yjs library.',
        'upvotes': 456,
        'comment_count': 87,
    },
    {
        'title': 'PostgreSQL 17 Performance: 20% Faster Queries Without Changes',
        'source': 'reddit',
        'source_url': 'https://reddit.com/r/programming/comments/pg17perf',
        'external_id': 'reddit-pg17',
        'summary': 'PostgreSQL 17 delivers significant performance improvements out of the box, with sequential scans up to 20% faster and improved query planning. No application changes required to benefit from the speed boost.',
        'upvotes': 2341,
        'comment_count': 456,
    },
    {
        'title': 'Why TypeScript 5.5 Makes Your Code Safer Automatically',
        'source': 'devto',
        'source_url': 'https://dev.to/user/ts55-safer',
        'external_id': 'ts55-article',
        'summary': 'TypeScript 5.5 introduces inferred type predicates in .filter() calls, meaning type narrowing works automatically without manual type guards. This catches entire categories of bugs at compile time that were previously missed.',
        'upvotes': 678,
        'comment_count': 123,
    },
]


with app.app_context():
    db.create_all()

    # Create demo users (first user is admin)
    if not User.query.filter_by(username='alex').first():
        u = register_user('alex', 'alex@dev.io', 'demo123')
        u.is_admin = True
        db.session.add(u)
    if not User.query.filter_by(username='sarah').first():
        register_user('sarah', 'sarah@dev.io', 'demo123')

    alex = User.query.filter_by(username='alex').first()
    sarah = User.query.filter_by(username='sarah').first()

    # Seed snippets
    authors = [alex, sarah, alex, sarah, alex, sarah]
    count = 0
    for i, data in enumerate(SNIPPETS):
        if Snippet.query.filter_by(title=data['title']).first():
            continue

        tags = []
        for tag_name in data['tags']:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name, slug=slugify(tag_name))
                db.session.add(tag)
            tags.append(tag)

        snippet = Snippet(
            title=data['title'],
            body=data['body'],
            language=data['language'],
            description=data['description'],
            is_public=True,
            user_id=authors[i].id,
            created_at=datetime.now(timezone.utc),
        )
        snippet.tags = tags
        db.session.add(snippet)
        count += 1

    # Seed news articles
    news_count = 0
    for data in SAMPLE_NEWS:
        if NewsArticle.query.filter_by(source_url=data['source_url']).first():
            continue
        article = NewsArticle(
            title=data['title'],
            source=data['source'],
            source_url=data['source_url'],
            external_id=data.get('external_id', ''),
            summary=data['summary'],
            upvotes=data['upvotes'],
            comment_count=data['comment_count'],
            is_published=True,
        )
        db.session.add(article)
        news_count += 1

    # Default admin settings
    defaults = {
        'ai_chat_enabled': 'true',
        'news_enabled': 'true',
        'email_enabled': 'true',
        'news_fetch_interval': '4',
    }
    for key, value in defaults.items():
        if not AdminSetting.query.get(key):
            db.session.add(AdminSetting(key=key, value=value))

    db.session.commit()
    print(f"Seeded {count} snippets, {news_count} news articles")
    print(f"Users: {User.query.count()} (alex is admin: {alex.is_admin})")
    print(f"Tags: {Tag.query.count()}, News: {NewsArticle.query.count()}")