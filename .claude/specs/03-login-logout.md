# Spec: Login and Logout

## Overview
The Login and Logout feature allows users to securely access their personal account on Spendly. Users can authenticate using their registered email and password, which establishes a session that allows them to access protected routes (like their profile and expense management). Logging out terminates this session, ensuring that account access is restricted when the user is finished.

## Depends on
- Step 02: Registration

## Routes
- `GET /login` — Renders the login form — public
- `POST /login` — Authenticates user credentials and sets `session["user_id"]` — public
- `GET /logout` — Clears the user session and redirects to login — logged-in

## Database changes
No database changes.

## Templates
- **Modify:** `templates/login.html` — Update to use Flask flash messages for error reporting instead of a passed-in `error` variable.

## Files to change
- `app.py`

## Files to create
No new files.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Use `session.clear()` to ensure all session data is removed during logout.
- Use `flash()` for authentication errors (e.g., "Invalid email or password").
- Ensure `login_required` decorator is correctly applied to the `/logout` route.

## Definition of done
- [ ] User can see the login page at `/login`.
- [ ] Entering valid credentials redirects the user to the `/profile` page.
- [ ] Entering invalid credentials displays a flash error message and keeps the user on the login page.
- [ ] An unauthenticated user attempting to access `/profile` is redirected to `/login`.
- [ ] A logged-in user clicking "Logout" (or visiting `/logout`) is cleared from the session and redirected to `/login`.
- [ ] After logout, attempting to access `/profile` redirects the user back to `/login`.
