"""REST API for the game, built with Bottle.

This is the module Abdel owned in the course project (serverAPI.py), rebuilt
so that it actually runs: real routes for users, games and moves, JSON in and
out, proper HTTP status codes, and a computer opponent.

    python -m uttt.server            # then open http://localhost:8080
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from bottle import Bottle, HTTPResponse, request, response, run, static_file

from . import ai
from .engine import IllegalMove
from .store import Store, UserError

WEB_DIR = Path(__file__).resolve().parent.parent / "web"


def _json(status: int, payload: dict) -> HTTPResponse:
    return HTTPResponse(status=status, body=json.dumps(payload), headers={"Content-Type": "application/json"})


def _body() -> dict:
    try:
        data = request.json
    except ValueError:
        raise _json(400, {"error": "body must be JSON"}) from None
    if not isinstance(data, dict):
        raise _json(400, {"error": "body must be a JSON object"})
    return data


def _current_user(store: Store):
    header = request.get_header("Authorization", "")
    token = header[7:] if header.startswith("Bearer ") else None
    return store.user_for_token(token)


def _game_payload(game_id, game, meta):
    data = game.to_dict()
    data.update({"id": game_id, "mode": meta["mode"], "level": meta["level"], "human": meta["human"]})
    return data


def create_app(store: Store | None = None, ai_time_limit: float = 2.0) -> Bottle:
    store = store or Store()
    app = Bottle()

    @app.error(404)
    @app.error(405)
    @app.error(500)
    def _error(err):
        response.content_type = "application/json"
        return json.dumps({"error": err.status_line})

    # ---------- web page ----------

    @app.get("/")
    def index():
        return static_file("index.html", root=str(WEB_DIR))

    @app.get("/static/<path:path>")
    def static(path):
        return static_file(path, root=str(WEB_DIR))

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    # ---------- users ----------

    @app.post("/api/users")
    def register():
        data = _body()
        try:
            store.register(data.get("username", ""), data.get("password", ""))
        except UserError as err:
            return _json(400, {"error": str(err)})
        return _json(201, {"username": data["username"].strip()})

    @app.post("/api/sessions")
    def login():
        data = _body()
        try:
            token = store.login(data.get("username", ""), data.get("password", ""))
        except UserError as err:
            return _json(401, {"error": str(err)})
        return {"token": token, "username": data["username"]}

    @app.get("/api/users/<username>")
    def user_stats(username):
        stats = store.stats(username)
        return stats if stats else _json(404, {"error": "no such user"})

    # ---------- games ----------

    @app.post("/api/games")
    def new_game():
        data = _body()
        mode = data.get("mode", "local")
        level = data.get("level", "normal")
        human = data.get("human", "X")
        if mode not in ("local", "ai"):
            return _json(400, {"error": "mode must be 'local' or 'ai'"})
        if mode == "ai" and level not in ai.LEVELS:
            return _json(400, {"error": f"level must be one of {sorted(ai.LEVELS)}"})
        if human not in ("X", "O"):
            return _json(400, {"error": "human must be 'X' or 'O'"})
        game_id = store.create_game(mode, level if mode == "ai" else None, _current_user(store), human)
        game, meta = store.load_game(game_id)
        if mode == "ai" and human == "O":  # computer opens
            game.play(*ai.choose_move(game, level, time_limit=ai_time_limit))
            store.save_game(game_id, game)
        return _json(201, _game_payload(game_id, game, meta))

    @app.get("/api/games/<game_id>")
    def get_game(game_id):
        game, meta = store.load_game(game_id)
        if game is None:
            return _json(404, {"error": "no such game"})
        return _game_payload(game_id, game, meta)

    @app.post("/api/games/<game_id>/moves")
    def make_move(game_id):
        game, meta = store.load_game(game_id)
        if game is None:
            return _json(404, {"error": "no such game"})
        if game.over:
            return _json(409, {"error": "the game is over"})
        if meta["mode"] == "ai" and game.to_move != meta["human"]:
            return _json(409, {"error": "it's the computer's turn"})
        data = _body()
        try:
            board, cell = int(data["board"]), int(data["cell"])
            game.play(board, cell)
        except (KeyError, TypeError, ValueError) as err:
            message = str(err) if isinstance(err, IllegalMove) else "send {\"board\": 0-8, \"cell\": 0-8}"
            return _json(400, {"error": message})
        reply = None
        if meta["mode"] == "ai" and not game.over:
            reply = ai.choose_move(game, meta["level"], time_limit=ai_time_limit)
            game.play(*reply)
        store.save_game(game_id, game)
        store.score_game(game_id, game)
        payload = _game_payload(game_id, game, meta)
        payload["computer_move"] = list(reply) if reply else None
        return payload

    return app


def main():
    parser = argparse.ArgumentParser(description="Ultimate Tic-Tac-Toe server")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--db", default="uttt.sqlite3", help="SQLite file (':memory:' for throwaway)")
    args = parser.parse_args()
    run(create_app(Store(args.db)), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
