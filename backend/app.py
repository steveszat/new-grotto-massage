from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request
from flask_cors import CORS

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "feedback.db"

app = Flask(__name__)
CORS(app)


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


@app.route("/api/submit-feedback", methods=["POST"])
def submit_feedback():
    if not request.is_json:
        return jsonify({"success": False, "error": "Expected JSON payload."}), 400

    payload = request.get_json(silent=True) or {}

    business_slug = clean_text(payload.get("business_slug"))
    first_name = clean_text(payload.get("first_name"))
    last_name = clean_text(payload.get("last_name"))
    category = clean_text(payload.get("category")).lower()
    original_message = clean_text(payload.get("message"))
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


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)