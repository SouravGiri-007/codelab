#!/usr/bin/env python
"""CodeLab Integration Tests"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set a dev secret key if not already configured
if 'SECRET_KEY' not in os.environ:
    os.environ['SECRET_KEY'] = 'dev-secret-key-change-in-production'

from app import create_app, db
from app.models import User, Snippet

app = create_app()
app.config['WTF_CSRF_ENABLED'] = False
client = app.test_client()

with app.app_context():
    db.drop_all()
    db.create_all()

    # 1. Register
    r = client.post('/auth/register', data={
        'username': 'devuser', 'email': 'dev@test.com',
        'password': 'testpass123', 'confirm_password': 'testpass123'
    }, follow_redirects=True)
    ok1 = r.status_code == 200 and User.query.first() is not None
    print(f'1. Register  -> {"PASS" if ok1 else "FAIL"} (status={r.status_code})')

    # 2. Login
    r = client.post('/auth/login', data={
        'email': 'dev@test.com', 'password': 'testpass123'
    }, follow_redirects=True)
    ok2 = r.status_code == 200 and b'Welcome' in r.data
    print(f'2. Login     -> {"PASS" if ok2 else "FAIL"} (welcome={b"Welcome" in r.data})')

    # 3. Create Snippet
    r = client.post('/snippet/new', data={
        'title': 'Quick Sort',
        'body': 'def quicksort(arr):\n    if len(arr) <= 1:\n        return arr\n    pivot = arr[len(arr) // 2]\n    left = [x for x in arr if x < pivot]\n    mid = [x for x in arr if x == pivot]\n    right = [x for x in arr if x > pivot]\n    return quicksort(left) + mid + quicksort(right)',
        'language': 'python',
        'description': 'Classic divide and conquer sort',
        'tags': 'sorting, algorithm',
        'is_public': 'y'
    }, follow_redirects=True)
    s = Snippet.query.first()
    ok3 = s is not None and s.title == 'Quick Sort'
    print(f'3. Create    -> {"PASS" if ok3 else "FAIL"} (snippet={"YES" if s else "NO"})')

    if not s:
        print('\nFATAL: Snippet not created, stopping.')
        sys.exit(1)

    # 4. View Snippet
    r = client.get(f'/snippet/{s.id}')
    ok4 = r.status_code == 200 and b'Quick Sort' in r.data
    print(f'4. View      -> {"PASS" if ok4 else "FAIL"} (status={r.status_code})')

    # 5. Like
    client.post(f'/snippet/{s.id}/like')
    db.session.refresh(s)
    ok5 = s.like_count == 1
    print(f'5. Like      -> {"PASS" if ok5 else "FAIL"} (count={s.like_count})')

    # 6. Save
    r = client.post(f'/snippet/{s.id}/save', follow_redirects=True)
    ok6 = b'Saved' in r.data
    print(f'6. Save      -> {"PASS" if ok6 else "FAIL"}')

    # 7. Comment
    r = client.post(f'/snippet/{s.id}/comment', data={'body': 'Clean code!'})
    db.session.refresh(s)
    ok7 = s.comment_count == 1
    print(f'7. Comment   -> {"PASS" if ok7 else "FAIL"} (count={s.comment_count})')

    # 8. Profile
    r = client.get('/auth/profile/devuser')
    ok8 = r.status_code == 200 and b'devuser' in r.data
    print(f'8. Profile   -> {"PASS" if ok8 else "FAIL"} (status={r.status_code})')

    # 9. API GET
    r = client.get(f'/api/v1/snippets/{s.id}')
    d = json.loads(r.data)
    ok9 = d['success'] and d['data']['title'] == 'Quick Sort' and 'sorting' in d['data']['tags']
    print(f'9. API GET   -> {"PASS" if ok9 else "FAIL"} (title={d["data"]["title"]})')

    # 10. API Search
    r = client.get('/api/v1/snippets?q=sort')
    d = json.loads(r.data)
    ok10 = d['success'] and d['data']['total'] >= 1
    print(f'10. API Src  -> {"PASS" if ok10 else "FAIL"} (found={d["data"]["total"]})')

    # 11. Edit
    client.post(f'/snippet/{s.id}/edit', data={
        'title': 'Updated Title', 'body': s.body,
        'language': 'python', 'tags': 'updated', 'is_public': 'y'
    }, follow_redirects=True)
    db.session.refresh(s)
    ok11 = s.title == 'Updated Title'
    print(f'11. Edit     -> {"PASS" if ok11 else "FAIL"} (title={s.title})')

    # 12. Unlike
    client.post(f'/snippet/{s.id}/like')
    db.session.refresh(s)
    ok12 = s.like_count == 0
    print(f'12. Unlike   -> {"PASS" if ok12 else "FAIL"} (count={s.like_count})')

    # 13. Delete
    client.post(f'/snippet/{s.id}/delete')
    db.session.rollback()  # Clear any pending session state after cascade delete
    ok13 = Snippet.query.first() is None
    print(f'13. Delete   -> {"PASS" if ok13 else "FAIL"}')

    # 14. Smoke test pages
    pages = [
        ('/', 200), ('/explore', 200), ('/playground', 200),
        ('/tags', 200), ('/my-snippets', 200), ('/saved', 200),
        ('/api/v1/tags', 200),
    ]
    all_pages_ok = True
    for url, expected in pages:
        r = client.get(url)
        if r.status_code != expected:
            print(f'   PAGE {url} -> expected {expected}, got {r.status_code}')
            all_pages_ok = False
    print(f'14. Pages    -> {"PASS" if all_pages_ok else "FAIL"} (7 pages checked)')

    # Summary
    results = [ok1, ok2, ok3, ok4, ok5, ok6, ok7, ok8, ok9, ok10, ok11, ok12, ok13, all_pages_ok]
    passed = sum(results)
    total = len(results)

    print(f'\n{"=" * 50}')
    print(f'  Results: {passed}/{total} tests passed')
    if passed == total:
        print(f'  ALL TESTS PASSED!')
    print(f'{"=" * 50}')
    sys.exit(0 if passed == total else 1)