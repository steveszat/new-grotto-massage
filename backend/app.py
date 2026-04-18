from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS

DB_PATH = Path("/var/lib/feedback/feedback.db")

app = Flask(__name__)
CORS(app)


ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Feedback Submissions</title>
  <style>
    :root {
      --bg: #f6f3ee;
      --card: #ffffff;
      --text: #1f2937;
      --muted: #6b7280;
      --border: #ddd6cf;
      --accent: #8b1e2d;
      --accent-dark: #721927;
      --success-bg: #eef8ee;
      --success-border: #b7d9b7;
      --success-text: #245b24;
      --warning-bg: #fff4e5;
      --warning-border: #f0c36d;
      --warning-text: #8a5a00;
      --shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
      --radius: 14px;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
    }

    .page {
      max-width: 1100px;
      margin: 0 auto;
      padding: 32px 18px 48px;
    }

    .header {
      margin-bottom: 24px;
    }

    .header h1 {
      margin: 0 0 8px;
      color: var(--accent);
      font-size: 2rem;
    }

    .header p {
      margin: 0;
      color: var(--muted);
    }

    .stats {
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 14px;
      margin: 22px 0 28px;
    }

    .stat-card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      padding: 16px 18px;
    }

    .stat-label {
      font-size: 0.9rem;
      color: var(--muted);
      margin-bottom: 6px;
    }

    .stat-value {
      font-size: 1.6rem;
      font-weight: 700;
      color: var(--accent);
    }

    .submission-list {
      display: grid;
      gap: 16px;
    }

    .submission-card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      padding: 18px 20px;
    }

    .submission-top {
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: flex-start;
      margin-bottom: 12px;
    }

    .submission-title {
      margin: 0;
      font-size: 1.15rem;
      color: var(--accent);
    }

    .submission-meta {
      font-size: 0.95rem;
      color: var(--muted);
      margin-top: 4px;
    }

    .badges {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      justify-content: flex-end;
    }

    .badge {
      display: inline-block;
      padding: 6px 10px;
      border-radius: 999px;
      font-size: 0.82rem;
      font-weight: 700;
      border: 1px solid var(--border);
      background: #f8f6f3;
      color: var(--text);
      white-space: nowrap;
    }

    .badge.status-new {
      background: var(--warning-bg);
      border-color: var(--warning-border);
      color: var(--warning-text);
    }

    .badge.status-published {
      background: var(--success-bg);
      border-color: var(--success-border);
      color: var(--success-text);
    }

    .badge.permission-private {
      background: #f3f4f6;
      border-color: #d1d5db;
      color: #374151;
    }

    .badge.permission-public {
      background: var(--success-bg);
      border-color: var(--success-border);
      color: var(--success-text);
    }

    .message-box {
      background: #faf8f5;
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 14px 16px;
      white-space: pre-wrap;
    }

    .message-label {
      font-size: 0.85rem;
      font-weight: 700;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.04em;
      margin-bottom: 8px;
    }

    .detail-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 14px;
      margin-top: 14px;
    }

    .detail {
      background: #fcfbf9;
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 12px 14px;
    }

    .detail-label {
      font-size: 0.82rem;
      font-weight: 700;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.04em;
      margin-bottom: 4px;
    }

    .detail-value {
      font-size: 0.97rem;
      color: var(--text);
      word-break: break-word;
    }

    .editor {
      margin-top: 14px;
      padding: 14px;
      border: 1px solid var(--border);
      border-radius: 12px;
      background: #fcfbf9;
    }

    .editor label {
      display: block;
      font-size: 0.9rem;
      font-weight: 700;
      margin-bottom: 8px;
      color: var(--muted);
    }

    .editor textarea {
      width: 100%;
      min-height: 120px;
      resize: vertical;
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 12px;
      font: inherit;
      color: var(--text);
      background: #fff;
    }

    .editor-actions {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      align-items: center;
      margin-top: 12px;
    }

    .button {
      appearance: none;
      border: 0;
      border-radius: 10px;
      padding: 10px 14px;
      font: inherit;
      font-weight: 700;
      cursor: pointer;
    }

    .button-save {
      background: var(--accent);
      color: #fff;
    }

    .button-save:hover {
      background: var(--accent-dark);
    }

    .button-publish {
      background: #1f7a3d;
      color: #fff;
    }

    .button-unpublish {
      background: #6b7280;
      color: #fff;
    }

    .editor-status {
      font-size: 0.9rem;
      color: var(--muted);
    }

    .empty-state {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      padding: 28px;
      text-align: center;
      color: var(--muted);
    }

    @media (max-width: 900px) {
      .stats,
      .detail-grid {
        grid-template-columns: 1fr 1fr;
      }
    }

    @media (max-width: 640px) {
      .stats,
      .detail-grid {
        grid-template-columns: 1fr;
      }

      .submission-top {
        flex-direction: column;
      }

      .badges {
        justify-content: flex-start;
      }
    }
  </style>
</head>
<body>
  <main class="page">
    <div class="header">
      <h1>Feedback Submissions</h1>
      <p>Newest first. Private feedback, suggestions, complaints, and testimonial candidates.</p>
    </div>

    <section class="stats">
      <div class="stat-card">
        <div class="stat-label">Total</div>
        <div class="stat-value">{{ stats.total }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">New</div>
        <div class="stat-value">{{ stats.new_count }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Public Allowed</div>
        <div class="stat-value">{{ stats.public_count }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Private</div>
        <div class="stat-value">{{ stats.private_count }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Published</div>
        <div class="stat-value">{{ stats.published_count }}</div>
      </div>
    </section>

    {% if submissions %}
      <section class="submission-list">
        {% for s in submissions %}
          <article class="submission-card">
            <div class="submission-top">
              <div>
                <h2 class="submission-title">{{ s.display_name }}</h2>
                <div class="submission-meta">
                  Submitted {{ s.created_at_display }}
                </div>
              </div>

              <div class="badges">
                <span class="badge">{{ s.category_display }}</span>
                <span class="badge {{ 'status-published' if s.is_published else 'status-new' }}">
                  {{ s.status_badge }}
                </span>
                <span class="badge {{ 'permission-private' if s.permission == 'private' else 'permission-public' }}">
                  {{ s.permission_display }}
                </span>
              </div>
            </div>

            <div class="message-box">
              <div class="message-label">Original Submission</div>
              <div>{{ s.original_message }}</div>
            </div>

            <div class="editor">
              <label for="public_message_{{ s.id }}">Public Version</label>
              <textarea id="public_message_{{ s.id }}">{{ s.public_message }}</textarea>

              <div class="editor-actions">
                <button class="button button-save" onclick="saveSubmission({{ s.id }})">
                  Save
                </button>

                {% if s.is_published %}
                  <button class="button button-unpublish" onclick="setPublished({{ s.id }}, false)">
                    Unpublish
                  </button>
                {% else %}
                  <button class="button button-publish" onclick="setPublished({{ s.id }}, true)">
                    Publish
                  </button>
                {% endif %}

                <span class="editor-status" id="status_{{ s.id }}"></span>
              </div>
            </div>

            <div class="detail-grid">
              <div class="detail">
                <div class="detail-label">First Name</div>
                <div class="detail-value">{{ s.first_name or '—' }}</div>
              </div>

              <div class="detail">
                <div class="detail-label">Last Name</div>
                <div class="detail-value">{{ s.last_name or '—' }}</div>
              </div>

              <div class="detail">
                <div class="detail-label">Email</div>
                <div class="detail-value">{{ s.email or '—' }}</div>
              </div>

              <div class="detail">
                <div class="detail-label">Phone</div>
                <div class="detail-value">{{ s.phone or '—' }}</div>
              </div>
            </div>
          </article>
        {% endfor %}
      </section>
    {% else %}
      <div class="empty-state">
        No submissions yet.
      </div>
    {% endif %}
  </main>

  <script>
    async function saveSubmission(submissionId) {
      const textarea = document.getElementById(`public_message_${submissionId}`);
      const statusEl = document.getElementById(`status_${submissionId}`);

      statusEl.textContent = 'Saving...';

      try {
        const response = await fetch(`/api/submissions/${submissionId}/update`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            public_message: textarea.value
          })
        });

        if (!response.ok) {
          throw new Error('Save failed');
        }

        statusEl.textContent = 'Saved';
      } catch (error) {
        statusEl.textContent = 'Save failed';
      }
    }

    async function setPublished(submissionId, isPublished) {
      const textarea = document.getElementById(`public_message_${submissionId}`);
      const statusEl = document.getElementById(`status_${submissionId}`);

      statusEl.textContent = isPublished ? 'Publishing...' : 'Unpublishing...';

      try {
        const response = await fetch(`/api/submissions/${submissionId}/update`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            public_message: textarea.value,
            is_published: isPublished
          })
        });

        if (!response.ok) {
          throw new Error('Publish update failed');
        }

        window.location.reload();
      } catch (error) {
        statusEl.textContent = isPublished ? 'Publish failed' : 'Unpublish failed';
      }
    }
  </script>
</body>
</html>
"""


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_slug TEXT NOT NULL,
                first_name TEXT,
                last_name TEXT,
                category TEXT NOT NULL,
                original_message TEXT NOT NULL,
                public_message TEXT,
                permission TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                contact_ok INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'new',
                is_published INTEGER NOT NULL DEFAULT 0,
                source TEXT NOT NULL DEFAULT 'web',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                spam_flag INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.commit()


def is_valid_email(email: str) -> bool:
    if not email:
        return False
    if "@" not in email:
        return False
    local, _, domain = email.partition("@")
    return bool(local and domain and "." in domain)


def normalize_phone(value: str) -> str:
    digits = "".join(ch for ch in value if ch.isdigit())
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    return value.strip()


def is_valid_phone(value: str) -> bool:
    digits = "".join(ch for ch in value if ch.isdigit())
    return len(digits) == 10


def clean_text(value: Any) -> str:
    return str(value or "").strip()


def is_honeypot_triggered(payload: dict[str, Any]) -> bool:
    return bool(clean_text(payload.get("company")))


def format_permission(permission: str) -> str:
    mapping = {
        "public_first_last_initial": "Public: First Name + Last Initial",
        "public_first": "Public: First Name Only",
        "public_anonymous": "Public: Anonymous",
        "private": "Private Only",
    }
    return mapping.get(permission, permission.title())


def format_category(category: str) -> str:
    return category.replace("_", " ").title()


def display_name_for_submission(row: sqlite3.Row) -> str:
    first_name = clean_text(row["first_name"])
    last_name = clean_text(row["last_name"])
    permission = clean_text(row["permission"])

    if permission == "private":
        if first_name or last_name:
            return f"{first_name} {last_name}".strip()
        return "Private Submission"

    if permission == "public_anonymous":
        return "Anonymous"

    if permission == "public_first":
        return first_name or "Anonymous"

    if permission == "public_first_last_initial":
        if first_name and last_name:
            return f"{first_name} {last_name[0]}."
        if first_name:
            return first_name
        return "Anonymous"

    return f"{first_name} {last_name}".strip() or "Unknown"


def display_name_for_public(first_name: str, last_name: str, permission: str) -> str:
    first_name = clean_text(first_name)
    last_name = clean_text(last_name)
    permission = clean_text(permission)

    if permission == "public_anonymous":
        return "Anonymous"

    if permission == "public_first":
        return first_name or "Anonymous"

    if permission == "public_first_last_initial":
        if first_name and last_name:
            return f"{first_name} {last_name[0]}."
        if first_name:
            return first_name
        return "Anonymous"

    return "Anonymous"


def format_timestamp(value: str) -> str:
    try:
        dt = datetime.fromisoformat(value)
        return dt.astimezone().strftime("%Y-%m-%d %I:%M %p")
    except Exception:
        return value


@app.route("/api/submit-feedback", methods=["POST"])
def submit_feedback():
    if not request.is_json:
        return jsonify({"success": False, "error": "Expected JSON payload."}), 400

    payload = request.get_json(silent=True) or {}

    business_slug = clean_text(payload.get("business_slug"))
    first_name = clean_text(payload.get("first_name"))
    last_name = clean_text(payload.get("last_name"))
    category = clean_text(payload.get("category")).lower()
    original_message = clean_text(payload.get("original_message"))
    permission = clean_text(payload.get("permission")).lower()
    email = clean_text(payload.get("email"))
    phone = clean_text(payload.get("phone"))
    contact_ok = bool(payload.get("contact_ok"))

    allowed_categories = {"feedback", "suggestion", "complaint", "testimonial", "other"}
    allowed_permissions = {
        "public_first_last_initial",
        "public_first",
        "public_anonymous",
        "private",
    }

    if not business_slug:
        return jsonify({"success": False, "error": "Missing business slug."}), 400

    if category not in allowed_categories:
        return jsonify({"success": False, "error": "Invalid category."}), 400

    if permission not in allowed_permissions:
        return jsonify({"success": False, "error": "Invalid permission."}), 400

    if not original_message:
        return jsonify({"success": False, "error": "Feedback message is required."}), 400

    spam_flag = 1 if is_honeypot_triggered(payload) else 0

    if email and not is_valid_email(email):
        return jsonify({"success": False, "error": "Invalid email address."}), 400

    if phone and not is_valid_phone(phone):
        return jsonify({"success": False, "error": "Invalid phone number."}), 400

    if contact_ok and not (is_valid_email(email) or is_valid_phone(phone)):
        return jsonify(
            {"success": False, "error": "Contact permission requires a valid email or phone."}
        ), 400

    if permission in {"public_first_last_initial", "public_first"} and not first_name:
        permission = "public_anonymous"

    normalized_phone = normalize_phone(phone) if phone else ""
    now = datetime.now(timezone.utc).isoformat()

    with get_db_connection() as conn:
        conn.execute(
            """
            INSERT INTO submissions (
                business_slug,
                first_name,
                last_name,
                category,
                original_message,
                public_message,
                permission,
                email,
                phone,
                contact_ok,
                status,
                is_published,
                source,
                created_at,
                updated_at,
                ip_address,
                user_agent,
                spam_flag
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                business_slug,
                first_name,
                last_name,
                category,
                original_message,
                original_message,
                permission,
                email,
                normalized_phone,
                1 if contact_ok else 0,
                "new",
                0,
                "web",
                now,
                now,
                request.headers.get("X-Forwarded-For", request.remote_addr),
                request.headers.get("User-Agent", ""),
                spam_flag,
            ),
        )
        conn.commit()

    return jsonify({"success": True}), 200


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"success": True, "status": "ok"}), 200


@app.route("/api/submissions/<int:submission_id>/update", methods=["POST"])
def update_submission(submission_id: int):
    if not request.is_json:
        return jsonify({"success": False, "error": "Expected JSON payload."}), 400

    data = request.get_json(silent=True) or {}

    public_message = clean_text(data.get("public_message"))
    is_published_raw = data.get("is_published")

    with get_db_connection() as conn:
        existing = conn.execute(
            """
            SELECT id, public_message, is_published
            FROM submissions
            WHERE id = ?
            """,
            (submission_id,),
        ).fetchone()

        if existing is None:
            return jsonify({"success": False, "error": "Submission not found."}), 404

        new_public_message = public_message or existing["public_message"] or ""
        new_is_published = existing["is_published"]

        if is_published_raw is not None:
            new_is_published = 1 if bool(is_published_raw) else 0

        new_status = "published" if new_is_published else "approved"

        conn.execute(
            """
            UPDATE submissions
            SET public_message = ?, is_published = ?, status = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                new_public_message,
                new_is_published,
                new_status,
                datetime.now(timezone.utc).isoformat(),
                submission_id,
            ),
        )
        conn.commit()

    return jsonify({"success": True}), 200


@app.route("/api/testimonials", methods=["GET"])
def get_testimonials():
    with get_db_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                id,
                first_name,
                last_name,
                public_message,
                permission
            FROM submissions
            WHERE is_published = 1
              AND spam_flag = 0
              AND TRIM(COALESCE(public_message, '')) <> ''
            ORDER BY datetime(created_at) DESC, id DESC
            """
        ).fetchall()

    results = []
    for row in rows:
        results.append(
            {
                "id": row["id"],
                "name": display_name_for_public(
                    row["first_name"],
                    row["last_name"],
                    row["permission"],
                ),
                "message": row["public_message"],
            }
        )

    return jsonify({"success": True, "testimonials": results}), 200


@app.route("/admin/submissions", methods=["GET"])
def admin_submissions():
    with get_db_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                id,
                business_slug,
                first_name,
                last_name,
                category,
                original_message,
                public_message,
                permission,
                email,
                phone,
                contact_ok,
                status,
                is_published,
                source,
                created_at,
                updated_at,
                ip_address,
                user_agent,
                spam_flag
            FROM submissions
            WHERE spam_flag = 0
            ORDER BY datetime(created_at) DESC, id DESC
            """
        ).fetchall()

    submissions = []
    for row in rows:
        submissions.append(
            {
                "id": row["id"],
                "display_name": display_name_for_submission(row),
                "first_name": row["first_name"],
                "last_name": row["last_name"],
                "category": row["category"],
                "category_display": format_category(row["category"]),
                "original_message": row["original_message"],
                "public_message": row["public_message"] or row["original_message"],
                "permission": row["permission"],
                "permission_display": format_permission(row["permission"]),
                "status": row["status"],
                "status_badge": "Published" if row["is_published"] else "New",
                "is_published": bool(row["is_published"]),
                "email": row["email"],
                "phone": row["phone"],
                "created_at_display": format_timestamp(row["created_at"]),
            }
        )

    stats = {
        "total": len(submissions),
        "new_count": sum(1 for s in submissions if s["status"] == "new"),
        "public_count": sum(1 for s in submissions if s["permission"] != "private"),
        "private_count": sum(1 for s in submissions if s["permission"] == "private"),
        "published_count": sum(1 for s in submissions if s["is_published"]),
    }

    return render_template_string(
        ADMIN_TEMPLATE,
        submissions=submissions,
        stats=stats,
    )


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
