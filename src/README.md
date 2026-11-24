# Daily Query – frontend

## Run it
```bash
pip install flask
python dq_app.py       # then open http://localhost:5050
```
Demo admin login: `admin` / `admin123`. Or sign up a normal user.

## Files
```
dq_app.py                 page routes + /api/health (run this one)
dq_api.py                 stand-in REST API (replace with the real backend later)
templates/base.html       shared page skeleton
templates/login.html      log in
templates/signup.html     sign up
templates/app_dashboard.html  search, library, account, users (admin)
static/css/app.css        all styles
static/js/api.js          session token + fetch helper
static/js/auth.js         login/signup forms
static/js/app.js          dashboard behaviour
```
None of these files share a name with the team's existing files (app.py, mock_api.py,
dashboard.html/.css/.js, form.html), so adding them changes nothing that already exists.

## API contract (what the backend must provide)
| Diagram step | Method & URL | Who |
|---|---|---|
| Signup | `POST /api/signup` {username, email, password} → 201 {token, user} | anyone |
| Login | `POST /api/login` {username, password} → {token, user} | anyone |
| Logout | `POST /api/logout` → 204 | logged in |
| Search | `GET /api/search?q=` → {items, total} (Semantic Scholar shape) | logged in |
| Add favourite | `PUT /api/favorites` {paperId, title, ...} | logged in |
| Get favourites | `GET /api/favorites` → {items} | logged in |
| Remove favourite | `DELETE /api/favorites/<paperId>` → 204 | logged in |
| List users | `GET /api/users` | admin |
| Get / update user | `GET` / `PUT /api/users/<id>` | admin, or the user themselves |
| Delete user | `DELETE /api/users/<id>` → 204 | admin |

Every request after login sends `Authorization: Bearer <token>`.
