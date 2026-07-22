<div align="center">

# &lt;/&gt; CodeLab

**Code Snippet Sharing, AI Chat, and Tech News Aggregation**

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-LLM-F55036?style=for-the-badge&logo=groq&logoColor=white)

[✨ Features](#-features) •
[🚀 Quick Start](#-quick-start) •
[🔧 Configuration](#-configuration) •
[📖 API](#-api) •
[🧪 Tests](#-tests) •
[📦 Deployment](#-deployment)

---

</div>

## ✨ Features

### 📝 Code Snippet Sharing
- **Create, edit, delete** code snippets in 20+ programming languages
- **Syntax highlighting** powered by Pygments with line numbers
- **Tag system** for easy discovery and filtering
- **Public/private** visibility control per snippet
- **Like and save** snippets to your personal collection
- **Comments** for discussion on each snippet

### 🤖 AI Coding Assistant
- Chat with **Llama 3.1, Gemma 2, and Mixtral** models via Groq
- Streaming responses for real-time interaction
- **Two-layer content guard** — keyword pre-filter + hardened system prompt
- Off-topic question detection (coding/tech only)
- Conversation history preserved per user

### 📰 Tech News Aggregation
- Automatically fetches news from **Hacker News, Dev.to, and Reddit r/programming**
- **AI-powered summarization** using Groq LLMs
- Scheduled background fetching every 4 hours (configurable)
- Source filtering and popular sort
- Email newsletter delivery to subscribers

### 🎮 Code Playground
- Write and preview code with syntax highlighting
- Experiment with different languages in-browser
- No login required for basic exploration

### 👤 User Management
- **Email/password** authentication with secure hashing
- **Google OAuth** sign-in integration
- User profiles with bio, social links, and snippet stats
- Admin panel with user management, feature toggles, and stats

### 🛡️ Security
- CSRF protection on all forms
- Rate limiting on authentication endpoints (Flask-Limiter)
- Open redirect validation on login
- Session cookies with HttpOnly and Secure flags
- Consistent JSON API envelope (`{success, data, error}`)

---

## 🚀 Quick Start

### Prerequisites
- Python **3.11+**
- pip (Python package manager)

### 1. Clone & Enter
```bash
git clone https://github.com/yourusername/codelab.git
cd codelab
```

### 2. Set Up Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the project root:

```env
# Required
SECRET_KEY=your-secret-key-here-change-this

# Optional — AI Chat (get a free key at https://console.groq.com)
GROQ_API_KEY=gsk_your_groq_api_key

# Optional — Google OAuth (https://console.cloud.google.com)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Optional — Email (SMTP)
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
MAIL_FROM=your-email@gmail.com

# Optional — Environment (set to 'production' for Secure cookies)
ENV=development
```

> **Note:** The app runs in development mode without any optional keys. AI chat and Google login simply won't work until you add the respective keys.

### 5. Seed the Database
```bash
python seed.py
```
This creates:
- **3 users** — `alex` (admin) and `sarah` (regular user) — both with password `demo123`
- **6 sample snippets** spanning Python, JavaScript, TypeScript, CSS, and SQL
- **5 sample news articles**
- **25 tags**
- **Default admin settings**

### 6. Run the Server
```bash
python run.py
```

Open **http://127.0.0.1:5000** in your browser.

### Demo Credentials
| Role | Email | Password |
|------|-------|----------|
| Admin | `alex@dev.io` | `demo123` |
| User | `sarah@dev.io` | `demo123` |

---

## 🔧 Configuration

### Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | ✅ Yes | — | Flask session signing key (generate a random 32+ char string) |
| `GROQ_API_KEY` | No | `''` | API key for AI chat and news summarization |
| `GOOGLE_CLIENT_ID` | No | `''` | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | No | `''` | Google OAuth client secret |
| `DEFAULT_CHAT_MODEL` | No | `llama-3.1-8b-instant` | Default Groq model for chat |
| `NEWS_MODEL` | No | `llama-3.1-8b-instant` | Groq model for news summarization |
| `SMTP_SERVER` | No | `smtp.gmail.com` | SMTP server for email |
| `SMTP_PORT` | No | `587` | SMTP port |
| `SMTP_USERNAME` | No | `''` | SMTP username |
| `SMTP_PASSWORD` | No | `''` | SMTP password |
| `MAIL_FROM` | No | `''` | From address for emails |
| `MAIL_FROM_NAME` | No | `CodeLab` | From name for emails |
| `ENV` | No | — | Set to `production` to enable Secure session cookies |
| `RATELIMIT_ENABLED` | No | `true` | Enable/disable rate limiting |
| `RATELIMIT_STORAGE_URI` | No | `memory://` | Rate limit storage backend (use `redis://` for multi-worker) |
| `CODELAB_DATABASE_URL` | No | `sqlite:///app/codelab.db` | Database connection string |

### Rate Limiting Defaults
| Endpoint | Limit |
|---|---|
| Global | 200/hour, 20/minute |
| `/auth/register` | 5/hour, 2/10 minutes |
| `/auth/login` | 10/hour, 5/15 minutes |
| `/auth/google/login` | 10/hour, 5/15 minutes |
| `/auth/google/callback` | 20/hour, 10/30 minutes |

---

## 📖 API

All API endpoints return a consistent JSON envelope:

```json
// Success
{ "success": true, "data": { ... } }

// Error
{ "success": false, "error": "Description of what went wrong" }

// Paginated list
{ "success": true, "data": { "snippets": [...], "total": 10, "page": 1, "per_page": 20, "pages": 1 } }
```

### Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/api/v1/snippets` | No | List public snippets (paginated) |
| `GET` | `/api/v1/snippets/:id` | No | Get single snippet |
| `POST` | `/api/v1/snippets` | Yes | Create a new snippet |
| `PUT` | `/api/v1/snippets/:id` | Yes | Update your snippet |
| `DELETE` | `/api/v1/snippets/:id` | Yes | Delete your snippet |
| `POST` | `/api/v1/snippets/:id/like` | Yes | Toggle like |
| `GET` | `/api/v1/tags` | No | List all tags |
| `GET` | `/api/v1/users/:username` | No | Get user profile |

**Query parameters for `GET /api/v1/snippets`:**
- `q` — search text (title, body, description, tags)
- `lang` — filter by language (e.g., `python`)
- `tag` — filter by tag slug
- `author` — filter by username
- `sort` — `newest` (default), `oldest`, `popular`
- `page` — page number (default 1)
- `per_page` — items per page (default 20, max 50)

---

## 🧪 Tests

```bash
# Run core test suite
python tests.py

# Run extended feature tests (requires seeded database)
python seed.py
python test_new_features.py
```

The test suite covers:
- User registration and login
- Snippet CRUD operations
- Likes, saves, and comments
- Profile pages
- API endpoints (GET, search)
- Admin panel access control
- Error page rendering

---

## 📁 Project Structure

```
codelab/
├── app/
│   ├── __init__.py          # Flask app factory & extensions
│   ├── auth.py              # Authentication logic (local + Google)
│   ├── config.py            # Configuration & environment variables
│   ├── errors.py            # Error handlers (403, 404, 500, 413)
│   ├── forms.py             # WTForms form definitions
│   ├── models.py            # SQLAlchemy database models
│   ├── utils.py             # Utility functions (slugify, time_ago, etc.)
│   ├── routes/
│   │   ├── admin.py         # Admin dashboard & management
│   │   ├── api.py           # REST API v1 endpoints
│   │   ├── auth.py          # Login, register, profiles
│   │   ├── chat.py          # AI chat interface
│   │   ├── main.py          # Snippets, explore, playground
│   │   ├── news.py          # News listing & detail
│   │   └── subscription.py  # Newsletter subscribe/unsubscribe
│   ├── services/
│   │   ├── ai_guard.py      # Content moderation (keyword + prompt)
│   │   ├── ai_service.py    # Groq API integration
│   │   ├── email_service.py # SMTP email sending
│   │   └── news_service.py  # HN/Dev.to/Reddit fetching
│   ├── static/
│   │   ├── css/style.css    # Complete stylesheet (dark mode support)
│   │   └── js/main.js       # Frontend interactions
│   └── templates/           # Jinja2 templates (25 files)
├── run.py                   # Application entry point
├── seed.py                  # Database seeder
├── tests.py                 # Core test suite
├── test_new_features.py     # Extended feature tests
└── requirements.txt         # Python dependencies
```

---

## 📦 Deployment

### Traditional VPS / Docker

**Production Checklist:**
1. **Set a strong `SECRET_KEY`** — generate one with `python -c "import secrets; print(secrets.token_hex(32))"`
2. **Set `ENV=production`** — enables Secure session cookies (requires HTTPS)
3. **Disable debug mode** — set `FLASK_DEBUG=0`
4. **Use a production WSGI server** — Gunicorn is already in `requirements.txt`:
   ```bash
   gunicorn wsgi:app -w 4 -b 0.0.0.0:8000
   ```
5. **Set up rate limit storage** — for multi-worker deployments, use Redis:
   ```env
   RATELIMIT_STORAGE_URI=redis://localhost:6379/0
   ```
6. **Use a production database** — switch from SQLite to PostgreSQL:
   ```env
   CODELAB_DATABASE_URL=postgresql://user:pass@localhost/codelab
   ```
7. **Set up HTTPS** — use Nginx/Caddy as a reverse proxy with Let's Encrypt

---

### Deploy to Render (Recommended)

Render runs your app as a **long-running web service**, so **all features work** — APScheduler, background news fetching, rate limiting, and PostgreSQL — with no special config files.

#### ✅ What Works Out of the Box
- All web routes, API, AI Chat, Playground, Admin Panel
- Google OAuth login
- **APScheduler** (background news fetching every 4 hours)
- **PostgreSQL via Neon** (set the `CODELAB_DATABASE_URL` env var)
- Rate limiting (uses in-memory storage — fine for a single instance)
- File uploads (persistent disk on Render)

#### Quick Deploy (Manual)

**1. Push your code to GitHub**
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/codelab.git
git push -u origin main
```

**2. On Render Dashboard**
- Go to [render.com](https://render.com) and click **New + → Web Service**
- Connect your GitHub repository
- Fill in the form:

| Field | Value |
|---|---|
| **Name** | `codelab` (or your choice) |
| **Runtime** | `Python` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn wsgi:app --worker-class sync --timeout 120 --access-logfile -` |
| **Plan** | Free (or paid for more power) |

**3. Add Environment Variables**
Add these in the **Environment Variables** section:

| Variable | Value |
|---|---|
| `SECRET_KEY` | Run `python -c "import secrets; print(secrets.token_hex(32))"` and paste the output |
| `CODELAB_DATABASE_URL` | Your Neon PostgreSQL connection string |
| `ENV` | `production` |
| `FLASK_DEBUG` | `0` |
| `GROQ_API_KEY` | *(optional)* Your Groq API key |
| `GOOGLE_CLIENT_ID` | *(optional)* Your Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | *(optional)* Your Google OAuth client secret |

**4. Deploy!**
Click **Create Web Service**. Render will:
- Clone your repo
- Install dependencies
- Start the app with Gunicorn
- Automatically initialize the database and start the news scheduler

Your app will be at `https://codelab.onrender.com` (or your custom domain).

#### Deploy via Render Blueprint (Infrastructure as Code)

This project includes a `render.yaml` file that lets you deploy with a single click:

- Fork/clone the repo to GitHub
- Go to [render.com](https://render.com) → **New + → Blueprint**
- Connect your repo
- Render will read `render.yaml`, create the web service, and set up env vars
- Secrets (`CODELAB_DATABASE_URL`, `GROQ_API_KEY`, etc.) need to be filled in manually after creation

#### Files for Render
| File | Purpose |
|---|---|
| `wsgi.py` | Production entry point — creates app, inits DB, starts scheduler, exports `app` for Gunicorn |
| `Procfile` | Declares the Gunicorn start command (auto-detected by Render) |
| `render.yaml` | Render Blueprint config for infrastructure-as-code deployment |

---

### Deploy to Vercel (Alternative)

Vercel runs your app as **serverless functions**, which means some features won't work. Only use this if you specifically want serverless. This project includes Vercel-specific files (`api/index.py`, `vercel.json`) for this option.

#### ❌ Limitations on Vercel
| Feature | Why | Alternative |
|---|---|---|
| **APScheduler** | Serverless functions die after each request — no background threads | Use **Vercel Cron Jobs** (Pro tier) |
| **SQLite** | Vercel's filesystem is ephemeral | Use **PostgreSQL** (Neon, Supabase) |
| **Rate limiting** | In-memory storage resets on each cold start | Use Redis via `RATELIMIT_STORAGE_URI` |

#### Quick Deploy to Vercel
1. Push to GitHub
2. Go to [vercel.com](https://vercel.com) → **Add New → Project**
3. Import your repo and add the same env vars as above
4. Click Deploy — Vercel auto-detects `api/index.py` as the entry point

> ⚠️ **Vercel Pro required for Cron Jobs** — on the free tier, the scheduler won't run, so news won't auto-fetch

---

### Deploy to Railway / Fly.io

These platforms also run long-lived containers, so everything works like Render:

```bash
# Example: Railway
railway login
railway init
railway up
```

Make sure to set all required environment variables in your hosting dashboard.

---

## 🖼️ Screenshots

*(Add screenshots here after deployment)*

| Page | Description |
|---|---|
| **Explore** | Browse public snippets with search, language, and tag filters |
| **Snippet Detail** | View code with syntax highlighting, like/save/comment |
| **AI Chat** | Conversational coding assistant powered by Groq |
| **Playground** | Write and preview code in-browser |
| **News** | Tech news aggregated from HN, Dev.to, and Reddit |
| **Admin Dashboard** | Stats, user management, feature toggles |
| **Login / Register** | Email/password and Google OAuth sign-in |

---

## 🛠️ Tech Stack

| Category | Technology |
|---|---|
| **Backend** | Flask 3.0, SQLAlchemy 2.0, Flask-Login |
| **Database** | SQLite (dev) / PostgreSQL (prod) |
| **AI** | Groq API (Llama 3.1, Gemma 2, Mixtral) |
| **Auth** | Flask-Login, Authlib (Google OAuth) |
| **Templating** | Jinja2 with Pygments syntax highlighting |
| **CSS** | Custom stylesheet with dark mode support |
| **Rate Limiting** | Flask-Limiter |
| **Scheduling** | APScheduler (news fetching) |
| **Email** | SMTP (Gmail) |
| **HTTP** | httpx (async news scraping) |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -am 'Add my feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Open a Pull Request

---

<div align="center">

Built with ❤️ using Flask

</div>
