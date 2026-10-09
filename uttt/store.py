"""SQLite storage for users, login sessions and games.

Passwords are stored as salted PBKDF2-SHA256 hashes, never as plain text.
A game is stored as its move list; the board is rebuilt by replaying it, so
the database can never hold a position the rules don't allow.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import threading
import time

from .engine import Game

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    salt BLOB NOT NULL,
    pw_hash BLOB NOT NULL,
    wins INTEGER NOT NULL DEFAULT 0,
    losses INTEGER NOT NULL DEFAULT 0,
    draws INTEGER NOT NULL DEFAULT 0,
    created REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    username TEXT NOT NULL REFERENCES users(username),
    created REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS games (
    id TEXT PRIMARY KEY,
    mode TEXT NOT NULL,            -- 'local' (two people, one screen) or 'ai'
    level TEXT,
    owner TEXT REFERENCES users(username),
    human TEXT NOT NULL DEFAULT 'X',
    history TEXT NOT NULL,         -- JSON list of [player, board, cell]
    scored INTEGER NOT NULL DEFAULT 0,
    created REAL NOT NULL,
    updated REAL NOT NULL
);
"""

ITERATIONS = 200_000


class UserError(ValueError):
    pass


def _hash(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)


class Store:
    def __init__(self, path: str = ":memory:"):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.lock = threading.Lock()
        with self.lock:
            self.db.executescript(SCHEMA)

    # ---------- users ----------

    def register(self, username: str, password: str) -> None:
        username = (username or "").strip()
        if not (3 <= len(username) <= 20) or not username.replace("_", "").isalnum():
            raise UserError("username must be 3-20 letters, numbers or underscores")
        if len(password or "") < 8:
            raise UserError("password must be at least 8 characters")
        salt = os.urandom(16)
        try:
            with self.lock, self.db:
                self.db.execute("INSERT INTO users (username, salt, pw_hash, created) VALUES (?, ?, ?, ?)",
                                (username, salt, _hash(password, salt), time.time()))
        except sqlite3.IntegrityError:
            raise UserError("that username is taken") from None

    def login(self, username: str, password: str) -> str:
        row = self.db.execute("SELECT salt, pw_hash FROM users WHERE username = ?", (username,)).fetchone()
        # Compare in constant time, and hash even for unknown users so the
        # response time doesn't reveal which usernames exist.
        salt = row["salt"] if row else b"\0" * 16
        ok = hmac.compare_digest(_hash(password or "", salt), row["pw_hash"] if row else b"")
        if not (row and ok):
            raise UserError("wrong username or password")
        token = secrets.token_urlsafe(24)
        with self.lock, self.db:
            self.db.execute("INSERT INTO sessions VALUES (?, ?, ?)", (token, username, time.time()))
        return token

    def user_for_token(self, token: str | None) -> str | None:
        if not token:
            return None
        row = self.db.execute("SELECT username FROM sessions WHERE token = ?", (token,)).fetchone()
        return row["username"] if row else None

    def stats(self, username: str) -> dict | None:
        row = self.db.execute("SELECT username, wins, losses, draws FROM users WHERE username = ?",
                              (username,)).fetchone()
        return dict(row) if row else None

    # ---------- games ----------

    def create_game(self, mode: str, level: str | None, owner: str | None, human: str = "X") -> str:
        game_id = secrets.token_hex(6)
        now = time.time()
        with self.lock, self.db:
            self.db.execute("INSERT INTO games (id, mode, level, owner, human, history, created, updated) "
                            "VALUES (?, ?, ?, ?, ?, '[]', ?, ?)", (game_id, mode, level, owner, human, now, now))
        return game_id

    def load_game(self, game_id: str):
        row = self.db.execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()
        if row is None:
            return None, None
        meta = dict(row)
        return Game.from_history(json.loads(meta.pop("history"))), meta

    def save_game(self, game_id: str, game: Game) -> None:
        with self.lock, self.db:
            self.db.execute("UPDATE games SET history = ?, updated = ? WHERE id = ?",
                            (json.dumps(game.history), time.time(), game_id))

    def score_game(self, game_id: str, game: Game) -> None:
        """Credit a finished vs-computer game to its owner, once."""
        _, meta = self.load_game(game_id)
        if not meta or meta["scored"] or not game.over or meta["mode"] != "ai" or not meta["owner"]:
            return
        column = "draws" if game.winner == "D" else ("wins" if game.winner == meta["human"] else "losses")
        with self.lock, self.db:
            self.db.execute(f"UPDATE users SET {column} = {column} + 1 WHERE username = ?", (meta["owner"],))
            self.db.execute("UPDATE games SET scored = 1 WHERE id = ?", (game_id,))
