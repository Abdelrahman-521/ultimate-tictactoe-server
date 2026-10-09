import pytest
from webtest import TestApp

from uttt.server import create_app
from uttt.store import Store


@pytest.fixture
def app():
    return TestApp(create_app(Store(), ai_time_limit=0.3))


def test_health_and_home_page(app):
    assert app.get("/api/health").json == {"status": "ok"}
    page = app.get("/")
    assert "Ultimate Tic-Tac-Toe" in page.text


def test_local_game_flow(app):
    game = app.post_json("/api/games", {"mode": "local"}, status=201).json
    assert len(game["legal_moves"]) == 81 and game["to_move"] == "X"
    game = app.post_json(f"/api/games/{game['id']}/moves", {"board": 4, "cell": 2}).json
    assert game["active_board"] == 2 and game["to_move"] == "O"
    assert app.get(f"/api/games/{game['id']}").json["history"] == [["X", 4, 2]]


def test_illegal_and_malformed_moves_are_400(app):
    gid = app.post_json("/api/games", {"mode": "local"}).json["id"]
    app.post_json(f"/api/games/{gid}/moves", {"board": 4, "cell": 2})
    bad = app.post_json(f"/api/games/{gid}/moves", {"board": 5, "cell": 0}, status=400).json
    assert "board 2" in bad["error"]
    app.post_json(f"/api/games/{gid}/moves", {"board": "x"}, status=400)
    app.post(f"/api/games/{gid}/moves", "not json", content_type="application/json", status=400)


def test_unknown_game_is_404(app):
    app.get("/api/games/doesnotexist", status=404)
    app.post_json("/api/games/doesnotexist/moves", {"board": 0, "cell": 0}, status=404)


def test_ai_replies_in_the_same_request(app):
    game = app.post_json("/api/games", {"mode": "ai", "level": "easy"}, status=201).json
    game = app.post_json(f"/api/games/{game['id']}/moves", {"board": 4, "cell": 4}).json
    assert len(game["history"]) == 2
    assert game["computer_move"][0] == 4          # sent to board 4 by our move
    assert game["to_move"] == "X"


def test_ai_opens_when_human_plays_o(app):
    game = app.post_json("/api/games", {"mode": "ai", "level": "easy", "human": "O"}, status=201).json
    assert len(game["history"]) == 1 and game["to_move"] == "O"


def test_bad_game_options_are_400(app):
    app.post_json("/api/games", {"mode": "online"}, status=400)
    app.post_json("/api/games", {"mode": "ai", "level": "godlike"}, status=400)


def test_accounts_and_scoring(app):
    app.post_json("/api/users", {"username": "abdel", "password": "correct horse"}, status=201)
    app.post_json("/api/users", {"username": "abdel", "password": "correct horse"}, status=400)
    app.post_json("/api/sessions", {"username": "abdel", "password": "nope nope"}, status=401)
    token = app.post_json("/api/sessions", {"username": "abdel", "password": "correct horse"}).json["token"]
    assert app.get("/api/users/abdel").json == {"username": "abdel", "wins": 0, "losses": 0, "draws": 0}
    app.get("/api/users/ghost", status=404)
    gid = app.post_json("/api/games", {"mode": "ai", "level": "easy"},
                        headers={"Authorization": f"Bearer {token}"}).json["id"]
    assert gid
