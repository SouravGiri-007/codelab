"""Quick smoke test for CodeLab with new AI features."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set a dev secret key if not already configured
if 'SECRET_KEY' not in os.environ:
    os.environ['SECRET_KEY'] = 'dev-secret-key-change-in-production'

from app import create_app, db
from app.models import User, Snippet, NewsArticle, NewsletterSubscription, ChatMessage, AdminSetting, Tag

app = create_app()
app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for tests

client = app.test_client()

errors = []
passed = 0

def check(name, response, status=200):
    global passed
    if response.status_code == status:
        passed += 1
        print(f"  PASS: {name} ({status})")
    else:
        errors.append(f"{name}: got {response.status_code}, expected {status}")
        print(f"  FAIL: {name} (got {response.status_code})")

with app.app_context():
    db.create_all()

    # 1. Public pages
    print("\n--- Public Pages ---")
    check("GET /", client.get('/'))
    check("GET /explore", client.get('/explore'))
    check("GET /tags", client.get('/tags'))
    check("GET /playground", client.get('/playground'))
    check("GET /auth/login", client.get('/auth/login'))
    check("GET /auth/register", client.get('/auth/register'))

    # 2. News pages
    print("\n--- News Pages ---")
    check("GET /news", client.get('/news'))
    r = client.get('/news')
    assert b'Tech News' in r.data or b'news' in r.data.lower()
    check("News page has content", r)
    check("GET /news/1", client.get('/news/1'))
    check("News filter source", client.get('/news?source=hackernews'))
    check("News sort popular", client.get('/news?sort=popular'))

    # 3. Subscribe page
    print("\n--- Newsletter ---")
    check("GET /subscribe", client.get('/subscribe'))

    # 4. Login
    print("\n--- Auth ---")
    r = client.post('/auth/login', data={
        'email': 'alex@dev.io', 'password': 'demo123', 'remember_me': 'y'
    }, follow_redirects=False)
    check("POST /auth/login", r, 302)

    # 5. Logged-in pages
    print("\n--- Logged In ---")
    check("GET /chat", client.get('/chat'))
    check("GET /my-snippets", client.get('/my-snippets'))
    check("GET /saved", client.get('/saved'))

    # 6. Admin pages (alex is admin)
    print("\n--- Admin (alex=admin) ---")
    check("GET /admin/", client.get('/admin/'))
    r = client.get('/admin/')
    assert b'Dashboard' in r.data
    check("Admin dashboard content", r)
    check("GET /admin/news", client.get('/admin/news'))
    check("GET /admin/subscriptions", client.get('/admin/subscriptions'))
    check("GET /admin/users", client.get('/admin/users'))
    check("GET /admin/settings", client.get('/admin/settings'))

    # 7. News detail
    print("\n--- News Detail ---")
    r = client.get('/news/1')
    assert b'Python 3.13' in r.data
    check("News detail has article content", r)

    # 8. Non-admin can't access admin
    print("\n--- Permissions ---")
    client.get('/auth/logout')
    r = client.post('/auth/login', data={
        'email': 'sarah@dev.io', 'password': 'demo123'
    }, follow_redirects=False)
    check("Login sarah", r, 302)
    check("Sarah denied admin", client.get('/admin/'), 403)
    check("Sarah can access chat", client.get('/chat'))

    # 9. DB counts
    print("\n--- DB Counts ---")
    print(f"  Users: {User.query.count()}")
    print(f"  Snippets: {Snippet.query.count()}")
    print(f"  News: {NewsArticle.query.count()}")
    print(f"  Tags: {Tag.query.count()}")
    print(f"  Admin Settings: {AdminSetting.query.count()}")
    assert User.query.count() == 2
    assert NewsArticle.query.count() == 5
    assert AdminSetting.query.count() == 4

    # Summary
    print(f"\n{'='*40}")
    print(f"PASSED: {passed}")
    if errors:
        print(f"FAILED: {len(errors)}")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("ALL TESTS PASSED!")
    print(f"{'='*40}")