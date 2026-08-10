"""SQLite persistence for FastSurvey."""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DB_PATH = Path(os.getenv("FASTSURVEY_DB", "data/fastsurvey.sqlite"))


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA busy_timeout=5000")
    return connection


@contextmanager
def transaction():
    connection = connect()
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    password_hash TEXT,
    google_linked INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS surveys (
    id INTEGER PRIMARY KEY,
    admin_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    slug TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    goals TEXT NOT NULL DEFAULT '',
    guide_json TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','live','closed')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY,
    token TEXT NOT NULL UNIQUE,
    survey_id INTEGER NOT NULL REFERENCES surveys(id) ON DELETE CASCADE,
    respondent_meta TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','complete','screened_out','abandoned')),
    progress INTEGER NOT NULL DEFAULT 0,
    quality_score REAL NOT NULL DEFAULT 1.0,
    started_at TEXT NOT NULL,
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
    survey_id INTEGER REFERENCES surveys(id) ON DELETE CASCADE,
    channel TEXT NOT NULL CHECK(channel IN ('designer','interview','insights')),
    role TEXT NOT NULL CHECK(role IN ('system','user','assistant')),
    content TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS extracted_answers (
    id INTEGER PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    objective_key TEXT NOT NULL,
    value_json TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 0,
    raw_quote TEXT NOT NULL DEFAULT '',
    sentiment TEXT NOT NULL DEFAULT 'neutral',
    UNIQUE(conversation_id, objective_key)
);

CREATE TABLE IF NOT EXISTS insights (
    id INTEGER PRIMARY KEY,
    survey_id INTEGER NOT NULL REFERENCES surveys(id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    content_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_surveys_admin ON surveys(admin_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversations_survey ON conversations(survey_id, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id, id);
CREATE INDEX IF NOT EXISTS idx_messages_survey_channel ON messages(survey_id, channel, id);
"""


def init() -> None:
    with transaction() as connection:
        connection.executescript(SCHEMA)


def row(sql: str, params: tuple = ()) -> dict | None:
    with transaction() as connection:
        result = connection.execute(sql, params).fetchone()
        return dict(result) if result else None


def rows(sql: str, params: tuple = ()) -> list[dict]:
    with transaction() as connection:
        return [dict(item) for item in connection.execute(sql, params).fetchall()]


def execute(sql: str, params: tuple = ()) -> int:
    with transaction() as connection:
        cursor = connection.execute(sql, params)
        return int(cursor.lastrowid)


def create_user(email: str, name: str, password_hash: str | None = None, *, google: bool = False) -> dict:
    email = email.strip().lower()
    with transaction() as connection:
        existing = connection.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if existing:
            if google:
                connection.execute("UPDATE users SET google_linked=1, name=COALESCE(NULLIF(?,''),name) WHERE id=?", (name, existing["id"]))
            return dict(connection.execute("SELECT * FROM users WHERE id=?", (existing["id"],)).fetchone())
        cursor = connection.execute(
            "INSERT INTO users(email,name,password_hash,google_linked,created_at) VALUES(?,?,?,?,?)",
            (email, name.strip() or email.split("@", 1)[0], password_hash, int(google), now()),
        )
        return dict(connection.execute("SELECT * FROM users WHERE id=?", (cursor.lastrowid,)).fetchone())


def create_survey(admin_id: int, goals: str, title: str, guide: dict) -> dict:
    slug = secrets.token_urlsafe(7).replace("_", "").replace("-", "").lower()
    timestamp = now()
    survey_id = execute(
        "INSERT INTO surveys(admin_id,slug,title,goals,guide_json,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
        (admin_id, slug, title[:160], goals, _json(guide), timestamp, timestamp),
    )
    return get_survey(survey_id)


def get_survey(survey_id: int, admin_id: int | None = None) -> dict | None:
    query = "SELECT * FROM surveys WHERE id=?"
    params: tuple = (survey_id,)
    if admin_id is not None:
        query += " AND admin_id=?"
        params += (admin_id,)
    item = row(query, params)
    if item:
        item["guide"] = json.loads(item.pop("guide_json") or "{}")
    return item


def get_survey_by_slug(slug: str) -> dict | None:
    item = row("SELECT * FROM surveys WHERE slug=?", (slug,))
    if item:
        item["guide"] = json.loads(item.pop("guide_json") or "{}")
    return item


def save_guide(survey_id: int, guide: dict, title: str | None = None) -> None:
    if title:
        execute("UPDATE surveys SET guide_json=?,title=?,updated_at=? WHERE id=?", (_json(guide), title[:160], now(), survey_id))
    else:
        execute("UPDATE surveys SET guide_json=?,updated_at=? WHERE id=?", (_json(guide), now(), survey_id))


def set_survey_status(survey_id: int, status: str) -> None:
    execute("UPDATE surveys SET status=?,updated_at=? WHERE id=?", (status, now(), survey_id))


def list_surveys(admin_id: int) -> list[dict]:
    return rows(
        """SELECT s.*, COUNT(c.id) response_count,
                  SUM(CASE WHEN c.status='complete' THEN 1 ELSE 0 END) complete_count
           FROM surveys s LEFT JOIN conversations c ON c.survey_id=s.id
           WHERE s.admin_id=? GROUP BY s.id ORDER BY s.updated_at DESC""",
        (admin_id,),
    )


def add_message(*, role: str, content: str, channel: str, survey_id: int | None = None,
                conversation_id: int | None = None, metadata: dict | None = None) -> int:
    return execute(
        "INSERT INTO messages(conversation_id,survey_id,channel,role,content,metadata_json,created_at) VALUES(?,?,?,?,?,?,?)",
        (conversation_id, survey_id, channel, role, content, _json(metadata or {}), now()),
    )


def messages(*, survey_id: int | None = None, conversation_id: int | None = None,
             channel: str) -> list[dict]:
    if conversation_id is not None:
        result = rows("SELECT * FROM messages WHERE conversation_id=? AND channel=? ORDER BY id", (conversation_id, channel))
    else:
        result = rows("SELECT * FROM messages WHERE survey_id=? AND conversation_id IS NULL AND channel=? ORDER BY id", (survey_id, channel))
    for item in result:
        item["metadata"] = json.loads(item.pop("metadata_json") or "{}")
    return result


def create_conversation(survey_id: int, meta: dict) -> dict:
    token = secrets.token_urlsafe(24)
    conversation_id = execute(
        "INSERT INTO conversations(token,survey_id,respondent_meta,started_at) VALUES(?,?,?,?)",
        (token, survey_id, _json(meta), now()),
    )
    return get_conversation(token)


def get_conversation(token: str) -> dict | None:
    item = row("SELECT * FROM conversations WHERE token=?", (token,))
    if item:
        item["respondent_meta"] = json.loads(item["respondent_meta"] or "{}")
    return item


def update_conversation(conversation_id: int, *, progress: int, status: str = "active", quality_score: float | None = None) -> None:
    completed = now() if status in {"complete", "screened_out"} else None
    if quality_score is None:
        execute("UPDATE conversations SET progress=?,status=?,completed_at=? WHERE id=?", (progress, status, completed, conversation_id))
    else:
        execute("UPDATE conversations SET progress=?,status=?,quality_score=?,completed_at=? WHERE id=?", (progress, status, quality_score, completed, conversation_id))


def survey_conversations(survey_id: int) -> list[dict]:
    return rows(
        """SELECT c.*, COUNT(m.id) message_count
           FROM conversations c LEFT JOIN messages m ON m.conversation_id=c.id
           WHERE c.survey_id=? GROUP BY c.id ORDER BY c.started_at DESC""",
        (survey_id,),
    )


def save_answers(conversation_id: int, answers: list[dict]) -> None:
    with transaction() as connection:
        for answer in answers:
            connection.execute(
                """INSERT INTO extracted_answers(conversation_id,objective_key,value_json,confidence,raw_quote,sentiment)
                   VALUES(?,?,?,?,?,?) ON CONFLICT(conversation_id,objective_key) DO UPDATE SET
                   value_json=excluded.value_json,confidence=excluded.confidence,
                   raw_quote=excluded.raw_quote,sentiment=excluded.sentiment""",
                (conversation_id, str(answer.get("objective_key", "unknown")), _json(answer.get("value")),
                 float(answer.get("confidence", 0)), str(answer.get("raw_quote", ""))[:1000],
                 str(answer.get("sentiment", "neutral"))[:24]),
            )


def answers_for_conversation(conversation_id: int) -> list[dict]:
    result = rows("SELECT * FROM extracted_answers WHERE conversation_id=? ORDER BY id", (conversation_id,))
    for item in result:
        item["value"] = json.loads(item.pop("value_json") or "null")
    return result


def all_answers(survey_id: int) -> list[dict]:
    result = rows(
        """SELECT a.*,c.token,c.started_at FROM extracted_answers a
           JOIN conversations c ON c.id=a.conversation_id WHERE c.survey_id=? ORDER BY a.id""",
        (survey_id,),
    )
    for item in result:
        item["value"] = json.loads(item.pop("value_json") or "null")
    return result


def conversation_for_admin(conversation_id: int, admin_id: int) -> dict | None:
    return row(
        """SELECT c.*,s.title survey_title,s.id survey_id FROM conversations c
           JOIN surveys s ON s.id=c.survey_id WHERE c.id=? AND s.admin_id=?""",
        (conversation_id, admin_id),
    )


def quality_score(conversation_id: int) -> float:
    user_messages = rows(
        "SELECT content,created_at FROM messages WHERE conversation_id=? AND role='user' ORDER BY id",
        (conversation_id,),
    )
    if not user_messages:
        return 1.0
    score = 1.0
    normalized = [item["content"].strip().lower() for item in user_messages]
    if len(normalized) >= 3 and len(set(normalized)) <= len(normalized) / 2:
        score -= 0.35
    short = sum(len(text.split()) < 2 for text in normalized)
    if short / len(normalized) > 0.6:
        score -= 0.25
    return max(0.1, round(score, 2))


init()
