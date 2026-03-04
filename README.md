# Nexus — Full-Stack Dashboard App

A modern, professional full-stack web application built with **React + Vite** on the frontend and **Python Flask** on the backend. Features JWT authentication, a fully functional dashboard with 6 pages, real API integration, and a clean, responsive UI.

---

## Screenshots

> **Login Page** — Split-screen layout with feature highlights and demo credentials hint.

> **Dashboard Overview** — Stats cards, recent activity feed, and performance metrics all fetched live from the Flask API.

> **Projects** — Table view with status badges, progress bars, and a create project modal.

> **Tasks** — Kanban board with three columns (To Do / In Progress / Done) and live drag-between-columns via arrow buttons.

> **Messages** — Two-panel inbox with unread indicators and mark-as-read functionality.

> **Analytics** — Bar chart, project distribution bars, and team performance scores.

> **Settings** — Toggle switches, theme selector, language picker — all saved to the API.

> **Profile** — Editable personal info, password change form with strength meter.

---

## Tech Stack

| Layer     | Technology                                      |
|-----------|-------------------------------------------------|
| Frontend  | React 19, Vite 8, React Router v6, Axios        |
| Backend   | Python 3.13, Flask 3, Flask-JWT-Extended, bcrypt|
| Auth      | JWT (access + refresh tokens), token blocklist  |
| Styling   | Pure CSS (no frameworks), Inter font            |
| State     | React Context API + localStorage persistence    |

---

## Project Structure

```
nexus/
├── backend/                  # Flask API
│   ├── app.py                # All routes and in-memory data
│   ├── .env                  # Environment variables (JWT secret)
│   └── requirements.txt      # Python dependencies
│
├── src/                      # React frontend
│   ├── api/
│   │   └── client.js         # Axios instance + all API functions
│   ├── components/
│   │   ├── Icons.jsx          # All SVG icons as a single object
│   │   ├── Layout.jsx         # Sidebar + topbar shell
│   │   ├── Sidebar.jsx        # Navigation sidebar
│   │   ├── Toast.jsx          # Toast notification system
│   │   └── *.css
│   ├── context/
│   │   └── AuthContext.jsx    # JWT auth state + login/logout
│   ├── hooks/
│   │   └── useToast.js        # Toast notification hook
│   ├── pages/
│   │   ├── OverviewPage.jsx   # Dashboard home
│   │   ├── ProjectsPage.jsx   # Projects table + create modal
│   │   ├── TasksPage.jsx      # Kanban board
│   │   ├── MessagesPage.jsx   # Inbox + message viewer
│   │   ├── AnalyticsPage.jsx  # Charts and team scores
│   │   ├── SettingsPage.jsx   # Preferences + toggles
│   │   ├── ProfilePage.jsx    # Edit profile + change password
│   │   └── *.css
│   ├── LoginPage.jsx          # Split-screen login page
│   ├── App.jsx                # Router + protected routes
│   └── main.jsx               # React entry point
│
├── vite.config.js             # Vite + /api proxy to Flask
├── package.json
└── README.md
```

---

## Getting Started

### Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.10+

---

### 1. Clone the repository

```bash
git clone https://github.com/your-username/nexus.git
cd nexus
```

---

### 2. Start the Flask Backend

```bash
cd backend

# Create and activate a virtual environment (recommended)
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the server
python app.py
```

The backend will start at **http://localhost:5000**

> To verify it is running, open http://localhost:5000/api/health — you should see `{"status": "ok"}`.

---

### 3. Start the React Frontend

Open a new terminal from the project root:

```bash
# Install dependencies
npm install

# Start the dev server
npm run dev
```

The frontend will start at **http://localhost:5173**

---

### 4. Log in

Use one of the built-in demo accounts:

| Username | Password   | Role          |
|----------|------------|---------------|
| admin    | admin123   | Administrator |
| john     | john123    | Developer     |
| sarah    | sarah123   | Designer      |

---

## Environment Variables

Create or edit `backend/.env`:

```env
JWT_SECRET_KEY=your-super-secret-key-change-this-in-production
FLASK_ENV=development
FLASK_DEBUG=1
```

> **Important:** Always change `JWT_SECRET_KEY` before deploying to production. Never commit your `.env` file.

---

## API Reference

All endpoints (except `/api/health`) require a JWT Bearer token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

### Auth

| Method | Endpoint                     | Auth | Description                        |
|--------|------------------------------|------|------------------------------------|
| POST   | `/api/auth/login`            | No   | Login with username + password     |
| POST   | `/api/auth/logout`           | Yes  | Revoke current access token        |
| POST   | `/api/auth/refresh`          | Yes* | Get new access token via refresh   |
| GET    | `/api/auth/me`               | Yes  | Get current user info              |

*Uses the refresh token instead of the access token.

**Login request body:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Login response:**
```json
{
  "message": "Login successful.",
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@nexus.dev",
    "full_name": "Admin User",
    "role": "Administrator",
    "department": "Engineering",
    "joined": "2024-01-15"
  }
}
```

---

### Dashboard

| Method | Endpoint                       | Description              |
|--------|--------------------------------|--------------------------|
| GET    | `/api/dashboard/stats`         | Summary stat cards       |
| GET    | `/api/dashboard/activity`      | Recent activity feed     |
| GET    | `/api/dashboard/performance`   | Performance percentages  |

---

### Projects

| Method | Endpoint               | Description              |
|--------|------------------------|--------------------------|
| GET    | `/api/projects`        | List all projects        |
| GET    | `/api/projects/:id`    | Get a single project     |
| POST   | `/api/projects`        | Create a new project     |

**Create project body:**
```json
{
  "name": "Project Nova",
  "description": "Next-gen platform rebuild.",
  "due": "2025-12-01"
}
```

---

### Tasks

| Method | Endpoint           | Description                           |
|--------|--------------------|---------------------------------------|
| GET    | `/api/tasks`       | List all tasks (optional `?status=`)  |
| POST   | `/api/tasks`       | Create a new task                     |
| PUT    | `/api/tasks/:id`   | Update a task (status, priority, etc) |

**Update task body:**
```json
{
  "status": "in_progress"
}
```

---

### Messages

| Method | Endpoint                     | Description           |
|--------|------------------------------|-----------------------|
| GET    | `/api/messages`              | List all messages     |
| PUT    | `/api/messages/:id/read`     | Mark message as read  |

---

### Analytics

| Method | Endpoint          | Description                              |
|--------|-------------------|------------------------------------------|
| GET    | `/api/analytics`  | Monthly tasks, distribution, team scores |

---

### Profile

| Method | Endpoint                         | Description              |
|--------|----------------------------------|--------------------------|
| GET    | `/api/profile`                   | Get own profile          |
| PUT    | `/api/profile`                   | Update name/email/dept   |
| POST   | `/api/profile/change-password`   | Change password          |

**Change password body:**
```json
{
  "current_password": "admin123",
  "new_password": "newSecurePass!"
}
```

---

### Settings

| Method | Endpoint        | Description              |
|--------|-----------------|--------------------------|
| GET    | `/api/settings` | Get notification/UI prefs|
| PUT    | `/api/settings` | Save preferences         |

**Update settings body:**
```json
{
  "notifications": {
    "email_alerts": true,
    "weekly_digest": false
  },
  "appearance": {
    "theme": "dark",
    "language": "en"
  }
}
```

---

### Health Check

| Method | Endpoint       | Auth | Description        |
|--------|----------------|------|--------------------|
| GET    | `/api/health`  | No   | Server health check|

---

## Features

### Authentication
- JWT access tokens (1 hour expiry) + refresh tokens (7 days)
- Token blocklist for secure logout
- Auto-refresh on 401 via Axios response interceptor
- Session persistence in `localStorage`
- Protected routes redirect unauthenticated users to `/login`
- Public routes redirect authenticated users to `/dashboard`

### Frontend Pages
- **Overview** — Live stats, activity feed, and performance bars fetched from API
- **Projects** — Sortable table with status filter tabs, progress bars, and a create modal
- **Tasks** — Kanban board with To Do / In Progress / Done columns; move tasks left/right via API
- **Messages** — Split-panel inbox; clicking a message marks it as read and updates the sidebar badge
- **Analytics** — Custom CSS bar chart, project distribution, team performance scores
- **Settings** — Toggle switches, theme switcher, language select; all persist to the API
- **Profile** — Edit name/email/department, change password with live strength meter

### UX Details
- Skeleton loaders on every data-fetching page
- Toast notifications for success and error states
- Responsive layout — sidebar collapses behind a hamburger on mobile
- Smooth page transition animations
- Custom scrollbar styling
- All icons are inline SVG (no icon library dependency)

---

## Build for Production

```bash
# Build the frontend
npm run build

# The output is in /dist — serve it with any static file server
# e.g. with Python:
python -m http.server --directory dist 8080
```

For production deployment, set a strong `JWT_SECRET_KEY` in your environment and configure CORS origins in `backend/app.py` to match your domain.

---

## Notes

- The backend uses an **in-memory "database"** — data resets when the server restarts. To persist data, swap the `USERS_DB`, `PROJECTS_DB`, etc. dicts for a real database (SQLite, PostgreSQL, etc.) with SQLAlchemy.
- Passwords are **bcrypt-hashed** even in the demo — never stored in plain text.
- The `vite.config.js` includes a proxy so all `/api/*` requests from the frontend are forwarded to `http://localhost:5000` during development.

---

## License

MIT — free to use and modify.
```

Now let me save this README and build to verify everything compiles: