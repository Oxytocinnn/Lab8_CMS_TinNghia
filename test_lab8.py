import sys

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from app import app
from models import CafeComment

app.config["WTF_CSRF_ENABLED"] = False
client = app.test_client()

res = client.get('/')
assert res.status_code == 200, f'Home failed: {res.status_code}'
print('[Pass] GET /: OK')

res = client.get('/login')
assert res.status_code == 200, f'Login page failed: {res.status_code}'
assert 'Đăng nhập'.encode('utf-8') in res.data, 'Login text missing'
print('[Pass] GET /login: OK')

res = client.post('/login', data={'username': 'tam_blogger', 'password': 'pass123', 'remember': True}, follow_redirects=True)
assert res.status_code == 200, f'Login POST failed: {res.status_code}'
assert b'tam_blogger' in res.data, 'tam_blogger not logged in'
assert 'Đăng xuất'.encode('utf-8') in res.data, 'Logout link missing after login'
print('[Pass] POST /login (standard password login): OK')

res = client.get('/logout', follow_redirects=True)
assert res.status_code == 200, f'Logout failed: {res.status_code}'
assert 'Đăng nhập'.encode('utf-8') in res.data, 'Login link missing after logout'
print('[Pass] GET /logout: OK')

res = client.get('/quick-login/an_foodie', follow_redirects=True)
assert res.status_code == 200, f'Quick login failed: {res.status_code}'
assert b'an_foodie' in res.data, 'Username not found in response'
print('[Pass] GET /quick-login/an_foodie: OK')

res = client.get('/?show=followed')
assert res.status_code == 200
cookie_val = res.headers.get('Set-Cookie', '')
assert 'show_followed=1' in cookie_val, f'Cookie not set properly: {cookie_val}'
print('[Pass] Cookie show_followed=1: OK')

res = client.get('/users/tam_blogger')
assert res.status_code == 200
assert b'gravatar.com/avatar' in res.data, 'Gravatar avatar missing'
print('[Pass] GET /users/tam_blogger with Gravatar: OK')

res = client.get('/reviews')
assert res.status_code == 200
print('[Pass] GET /reviews (CMS Pagination): OK')

res = client.get('/reviews/1')
assert res.status_code == 200
print('[Pass] GET /reviews/1 (Markdown Detail): OK')

res = client.get('/cafes')
assert res.status_code == 200
print('[Pass] GET /cafes: OK')

res = client.get('/cafes/1')
assert res.status_code == 200
print('[Pass] GET /cafes/1: OK')

res = client.post('/cafes/1/comments', data={
    'rating': '5',
    'body_md': "Quan ngon qua! <script>alert('XSS')</script> **Uong rat dam da**"
}, follow_redirects=True)
assert res.status_code == 200
assert b'<script>' not in res.data, 'XSS vulnerability: <script> was not stripped!'
assert b'<strong>Uong rat dam da</strong>' in res.data or b'<b>Uong rat dam da</b>' in res.data, 'Markdown formatting missing'
print('[Pass] XSS sanitization with Bleach: PASSED (script stripped, bold rendered)!')

res = client.get('/ai-log')
assert res.status_code == 200
assert b'AI Tool' in res.data or b'XSS' in res.data
print('[Pass] GET /ai-log: OK')

print('\n===> TOAN BO CAC TEST CASE (BAO GOM DANG NHAP / DANG XUAT) DA PASS 100%! <===')
