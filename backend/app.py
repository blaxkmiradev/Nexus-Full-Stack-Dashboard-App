import os
import json
import bcrypt
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
)
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "nexus-super-secret-change-in-prod")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 3600          # 1 hour
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = 86400 * 7   # 7 days

CORS(app, resources={r"/api/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173"]}})
jwt = JWTManager(app)

# ── In-memory "database" ──────────────────────────────────────────────────────
# Passwords are bcrypt-hashed. Plain-text equivalents are in comments.
USERS_DB = {
    "admin": {
        "id": 1,
        "username": "admin",
        "email": "admin@nexus.dev",
        "full_name": "Admin User",
        "role": "Administrator",
        "password_hash": bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode(),
        "avatar_initials": "AU",
        "joined": "2024-01-15",
        "department": "Engineering",
    },
    "john": {
        "id": 2,
        "username": "john",
        "email": "john@nexus.dev",
        "full_name": "John Doe",
        "role": "Developer",
        "password_hash": bcrypt.hashpw(b"john123", bcrypt.gensalt()).decode(),
        "avatar_initials": "JD",
        "joined": "2024-03-10",
        "department": "Product",
    },
    "sarah": {
        "id": 3,
        "username": "sarah",
        "email": "sarah@nexus.dev",
        "full_name": "Sarah Kim",
        "role": "Designer",
        "password_hash": bcrypt.hashpw(b"sarah123", bcrypt.gensalt()).decode(),
        "avatar_initials": "SK",
        "joined": "2024-05-22",
        "department": "Design",
    },
}

# token blocklist (for logout)
TOKEN_BLOCKLIST = set()

# ── JWT callbacks ─────────────────────────────────────────────────────────────
@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    return jwt_payload["jti"] in TOKEN_BLOCKLIST

@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    return jsonify({"error": "Token has been revoked. Please log in again."}), 401

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({"error": "Token has expired. Please log in again."}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({"error": "Invalid token."}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({"error": "Authorization token is missing."}), 401

# ── Helpers ───────────────────────────────────────────────────────────────────
def user_public(user: dict) -> dict:
    """Return user dict without the password hash."""
    return {k: v for k, v in user.items() if k != "password_hash"}

def ts_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

# ── Auth routes ───────────────────────────────────────────────────────────────
@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip().lower()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "Username and password are required."}), 400

    user = USERS_DB.get(username)
    if not user:
        return jsonify({"error": "Invalid username or password."}), 401

    if not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        return jsonify({"error": "Invalid username or password."}), 401

    access_token = create_access_token(identity=username)
    refresh_token = create_refresh_token(identity=username)

    return jsonify({
        "message": "Login successful.",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": user_public(user),
    }), 200


@app.route("/api/auth/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify({"access_token": access_token}), 200


@app.route("/api/auth/logout", methods=["POST"])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    TOKEN_BLOCKLIST.add(jti)
    return jsonify({"message": "Successfully logged out."}), 200


@app.route("/api/auth/me", methods=["GET"])
@jwt_required()
def me():
    identity = get_jwt_identity()
    user = USERS_DB.get(identity)
    if not user:
        return jsonify({"error": "User not found."}), 404
    return jsonify({"user": user_public(user)}), 200

# ── Profile routes ────────────────────────────────────────────────────────────
@app.route("/api/profile", methods=["GET"])
@jwt_required()
def get_profile():
    identity = get_jwt_identity()
    user = USERS_DB.get(identity)
    if not user:
        return jsonify({"error": "User not found."}), 404
    return jsonify({"profile": user_public(user)}), 200


@app.route("/api/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    identity = get_jwt_identity()
    user = USERS_DB.get(identity)
    if not user:
        return jsonify({"error": "User not found."}), 404

    data = request.get_json(silent=True) or {}
    allowed = {"full_name", "email", "department"}

    for field in allowed:
        if field in data and str(data[field]).strip():
            user[field] = str(data[field]).strip()

    USERS_DB[identity] = user
    return jsonify({"message": "Profile updated.", "profile": user_public(user)}), 200


@app.route("/api/profile/change-password", methods=["POST"])
@jwt_required()
def change_password():
    identity = get_jwt_identity()
    user = USERS_DB.get(identity)
    if not user:
        return jsonify({"error": "User not found."}), 404

    data = request.get_json(silent=True) or {}
    current = data.get("current_password", "")
    new_pw = data.get("new_password", "")

    if not current or not new_pw:
        return jsonify({"error": "Both current and new password are required."}), 400

    if not bcrypt.checkpw(current.encode(), user["password_hash"].encode()):
        return jsonify({"error": "Current password is incorrect."}), 401

    if len(new_pw) < 6:
        return jsonify({"error": "New password must be at least 6 characters."}), 400

    user["password_hash"] = bcrypt.hashpw(new_pw.encode(), bcrypt.gensalt()).decode()
    USERS_DB[identity] = user
    return jsonify({"message": "Password changed successfully."}), 200

# ── Dashboard routes ──────────────────────────────────────────────────────────
@app.route("/api/dashboard/stats", methods=["GET"])
@jwt_required()
def dashboard_stats():
    return jsonify({
        "stats": [
            {"label": "Total Projects", "value": 12, "change": "+2 this month", "up": True,  "color": "#6366f1"},
            {"label": "Open Tasks",     "value": 48, "change": "+5 this week",  "up": True,  "color": "#0ea5e9"},
            {"label": "Messages",       "value": 7,  "change": "3 unread",      "up": False, "color": "#f59e0b"},
            {"label": "Reports",        "value": 3,  "change": "1 pending",     "up": False, "color": "#10b981"},
        ]
    }), 200


@app.route("/api/dashboard/activity", methods=["GET"])
@jwt_required()
def dashboard_activity():
    return jsonify({
        "activity": [
            {"id": 1, "title": "Project Alpha milestone completed", "time": "Just now",    "type": "project"},
            {"id": 2, "title": "New message from Sarah K.",         "time": "12 min ago",  "type": "message"},
            {"id": 3, "title": "Q3 report generated",              "time": "1 hour ago",  "type": "report"},
            {"id": 4, "title": "Task #34 marked as done",          "time": "3 hours ago", "type": "task"},
            {"id": 5, "title": "Project Beta kickoff scheduled",   "time": "Yesterday",   "type": "project"},
            {"id": 6, "title": "Analytics export ready",           "time": "Yesterday",   "type": "report"},
        ]
    }), 200


@app.route("/api/dashboard/performance", methods=["GET"])
@jwt_required()
def dashboard_performance():
    return jsonify({
        "performance": [
            {"label": "Tasks Completed",    "value": 72, "color": "#6366f1"},
            {"label": "Projects on Track",  "value": 85, "color": "#10b981"},
            {"label": "Team Response Rate", "value": 61, "color": "#f59e0b"},
            {"label": "Report Accuracy",    "value": 94, "color": "#0ea5e9"},
        ]
    }), 200

# ── Projects routes ───────────────────────────────────────────────────────────
PROJECTS_DB = [
    {"id": 1, "name": "Project Alpha",   "status": "active",    "progress": 72, "team": 4, "due": "2025-08-30", "description": "Main product redesign initiative."},
    {"id": 2, "name": "Project Beta",    "status": "active",    "progress": 35, "team": 3, "due": "2025-09-15", "description": "New API integration layer."},
    {"id": 3, "name": "Project Gamma",   "status": "completed", "progress": 100,"team": 2, "due": "2025-06-01", "description": "Infrastructure migration completed."},
    {"id": 4, "name": "Project Delta",   "status": "paused",    "progress": 20, "team": 5, "due": "2025-10-20", "description": "Mobile app v2 on hold."},
    {"id": 5, "name": "Project Epsilon", "status": "active",    "progress": 58, "team": 3, "due": "2025-08-01", "description": "Analytics dashboard upgrade."},
]

@app.route("/api/projects", methods=["GET"])
@jwt_required()
def get_projects():
    return jsonify({"projects": PROJECTS_DB}), 200


@app.route("/api/projects/<int:project_id>", methods=["GET"])
@jwt_required()
def get_project(project_id):
    project = next((p for p in PROJECTS_DB if p["id"] == project_id), None)
    if not project:
        return jsonify({"error": "Project not found."}), 404
    return jsonify({"project": project}), 200


@app.route("/api/projects", methods=["POST"])
@jwt_required()
def create_project():
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    description = data.get("description", "").strip()

    if not name:
        return jsonify({"error": "Project name is required."}), 400

    new_id = max(p["id"] for p in PROJECTS_DB) + 1
    new_project = {
        "id": new_id,
        "name": name,
        "status": "active",
        "progress": 0,
        "team": 1,
        "due": data.get("due", "TBD"),
        "description": description,
    }
    PROJECTS_DB.append(new_project)
    return jsonify({"message": "Project created.", "project": new_project}), 201

# ── Tasks routes ──────────────────────────────────────────────────────────────
TASKS_DB = [
    {"id": 1, "title": "Design system audit",         "status": "done",        "priority": "high",   "due": "2025-07-10", "project": "Project Alpha"},
    {"id": 2, "title": "API endpoint documentation",  "status": "in_progress", "priority": "medium", "due": "2025-07-20", "project": "Project Beta"},
    {"id": 3, "title": "Unit test coverage to 80%",   "status": "in_progress", "priority": "high",   "due": "2025-07-25", "project": "Project Alpha"},
    {"id": 4, "title": "Onboarding flow redesign",    "status": "todo",        "priority": "low",    "due": "2025-08-05", "project": "Project Beta"},
    {"id": 5, "title": "Performance benchmarking",    "status": "todo",        "priority": "medium", "due": "2025-08-10", "project": "Project Epsilon"},
    {"id": 6, "title": "Security audit Q3",           "status": "todo",        "priority": "high",   "due": "2025-08-15", "project": "Project Delta"},
    {"id": 7, "title": "Database index optimisation", "status": "done",        "priority": "medium", "due": "2025-06-30", "project": "Project Gamma"},
]

@app.route("/api/tasks", methods=["GET"])
@jwt_required()
def get_tasks():
    status_filter = request.args.get("status")
    tasks = TASKS_DB
    if status_filter:
        tasks = [t for t in tasks if t["status"] == status_filter]
    return jsonify({"tasks": tasks}), 200


@app.route("/api/tasks/<int:task_id>", methods=["PUT"])
@jwt_required()
def update_task(task_id):
    task = next((t for t in TASKS_DB if t["id"] == task_id), None)
    if not task:
        return jsonify({"error": "Task not found."}), 404

    data = request.get_json(silent=True) or {}
    allowed = {"title", "status", "priority", "due"}
    for field in allowed:
        if field in data:
            task[field] = data[field]

    return jsonify({"message": "Task updated.", "task": task}), 200


@app.route("/api/tasks", methods=["POST"])
@jwt_required()
def create_task():
    data = request.get_json(silent=True) or {}
    title = data.get("title", "").strip()

    if not title:
        return jsonify({"error": "Task title is required."}), 400

    new_id = max(t["id"] for t in TASKS_DB) + 1
    new_task = {
        "id": new_id,
        "title": title,
        "status": "todo",
        "priority": data.get("priority", "medium"),
        "due": data.get("due", "TBD"),
        "project": data.get("project", "General"),
    }
    TASKS_DB.append(new_task)
    return jsonify({"message": "Task created.", "task": new_task}), 201

# ── Messages routes ───────────────────────────────────────────────────────────
MESSAGES_DB = [
    {"id": 1, "from": "Sarah Kim",   "from_initials": "SK", "subject": "Design review tomorrow",      "preview": "Hey, just confirming the design review is still on for tomorrow at 2pm...", "time": "10 min ago",  "read": False, "color": "#6366f1"},
    {"id": 2, "from": "John Doe",    "from_initials": "JD", "subject": "API docs updated",             "preview": "I have pushed the latest API documentation. Please review when you get...",  "time": "1 hour ago",  "read": False, "color": "#0ea5e9"},
    {"id": 3, "from": "Mike Ross",   "from_initials": "MR", "subject": "Sprint planning next week",    "preview": "Can we sync on the sprint planning session? I have a few items to add...",   "time": "3 hours ago", "read": True,  "color": "#10b981"},
    {"id": 4, "from": "Lisa Park",   "from_initials": "LP", "subject": "Budget approval needed",       "preview": "The Q3 budget report is ready for your approval. Please review at...",       "time": "Yesterday",   "read": True,  "color": "#f59e0b"},
    {"id": 5, "from": "Tom Clark",   "from_initials": "TC", "subject": "New team member joining",      "preview": "Excited to share that Rachel Lee is joining the team on Monday...",           "time": "2 days ago",  "read": True,  "color": "#ec4899"},
    {"id": 6, "from": "Emma Wilson", "from_initials": "EW", "subject": "Client feedback received",     "preview": "Just received feedback from the client on the latest build. Overall...",      "time": "3 days ago",  "read": True,  "color": "#8b5cf6"},
    {"id": 7, "from": "Admin",       "from_initials": "AU", "subject": "System maintenance on Friday", "preview": "Scheduled maintenance window: Friday 23:00 - 01:00 UTC. Services may...",    "time": "1 week ago",  "read": True,  "color": "#64748b"},
]

@app.route("/api/messages", methods=["GET"])
@jwt_required()
def get_messages():
    return jsonify({
        "messages": MESSAGES_DB,
        "unread_count": sum(1 for m in MESSAGES_DB if not m["read"]),
    }), 200


@app.route("/api/messages/<int:msg_id>/read", methods=["PUT"])
@jwt_required()
def mark_message_read(msg_id):
    msg = next((m for m in MESSAGES_DB if m["id"] == msg_id), None)
    if not msg:
        return jsonify({"error": "Message not found."}), 404
    msg["read"] = True
    return jsonify({"message": "Marked as read.", "unread_count": sum(1 for m in MESSAGES_DB if not m["read"])}), 200

# ── Analytics routes ──────────────────────────────────────────────────────────
@app.route("/api/analytics", methods=["GET"])
@jwt_required()
def get_analytics():
    return jsonify({
        "monthly_tasks": [
            {"month": "Jan", "completed": 28, "created": 35},
            {"month": "Feb", "completed": 32, "created": 30},
            {"month": "Mar", "completed": 27, "created": 40},
            {"month": "Apr", "completed": 45, "created": 42},
            {"month": "May", "completed": 38, "created": 36},
            {"month": "Jun", "completed": 52, "created": 48},
            {"month": "Jul", "completed": 41, "created": 55},
        ],
        "project_distribution": [
            {"name": "Active",    "value": 3, "color": "#6366f1"},
            {"name": "Completed", "value": 1, "color": "#10b981"},
            {"name": "Paused",    "value": 1, "color": "#f59e0b"},
        ],
        "team_performance": [
            {"name": "Engineering", "score": 87},
            {"name": "Design",      "score": 92},
            {"name": "Product",     "score": 78},
            {"name": "QA",          "score": 84},
        ],
        "summary": {
            "total_tasks_this_month": 55,
            "completed_this_month": 41,
            "completion_rate": 74.5,
            "avg_task_duration_days": 4.2,
        },
    }), 200

# ── Settings routes ───────────────────────────────────────────────────────────
SETTINGS_DB = {
    "admin": {
        "notifications": {
            "email_alerts": True,
            "push_alerts": True,
            "weekly_digest": False,
            "task_reminders": True,
        },
        "appearance": {
            "theme": "light",
            "compact_mode": False,
            "language": "en",
        },
        "privacy": {
            "profile_visible": True,
            "activity_visible": True,
        },
    }
}

@app.route("/api/settings", methods=["GET"])
@jwt_required()
def get_settings():
    identity = get_jwt_identity()
    settings = SETTINGS_DB.get(identity, {
        "notifications": {"email_alerts": True, "push_alerts": True, "weekly_digest": False, "task_reminders": True},
        "appearance": {"theme": "light", "compact_mode": False, "language": "en"},
        "privacy": {"profile_visible": True, "activity_visible": True},
    })
    return jsonify({"settings": settings}), 200


@app.route("/api/settings", methods=["PUT"])
@jwt_required()
def update_settings():
    identity = get_jwt_identity()
    data = request.get_json(silent=True) or {}

    current = SETTINGS_DB.get(identity, {})
    for section in ("notifications", "appearance", "privacy"):
        if section in data and isinstance(data[section], dict):
            current.setdefault(section, {}).update(data[section])

    SETTINGS_DB[identity] = current
    return jsonify({"message": "Settings saved.", "settings": current}), 200

# ── Health check ──────────────────────────────────────────────────────────────
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "timestamp": ts_now()}), 200

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
