import random

import pytest

from uttt import ai
from uttt.engine import Game, O, X
from uttt.store import Store, UserError


def test_ai_always_returns_a_legal_move():
    rng = random.Random(3)
    g = Game()
    for _ in range(12):
        g.play(*rng.choice(g.legal_moves()))
    move = ai.choose_move(g, "easy", seed=1)
    assert move in g.legal_moves()


def test_ai_takes_an_immediate_game_win():
    g = Game()
    for b in (0, 1):
        for c in (0, 1, 2):
            g.cells[b * 9 + c] = X
        g.boards[b] = X
    g.cells[2 * 9 + 0] = X
    g.cells[2 * 9 + 1] = X
    g.to_move, g.active = X, None
    assert ai.choose_move(g, "easy", seed=0) == (2, 2)


def test_normal_ai_beats_a_random_player_most_of_the_time():
    wins = 0
    for seed in range(6):
        rng = random.Random(seed)
        g = Game()
        while not g.over:
            if g.to_move == X:
                g.play(*ai.choose_move(g, "normal", seed=seed, time_limit=1.0))
            else:
                g.play(*rng.choice(g.legal_moves()))
        wins += g.winner == X
    assert wins >= 5


def test_register_login_and_password_rules():
    s = Store()
    s.register("abdel", "correct horse")
    token = s.login("abdel", "correct horse")
    assert s.user_for_token(token) == "abdel"
    with pytest.raises(UserError):
        s.login("abdel", "wrong password")
    with pytest.raises(UserError, match="taken"):
        s.register("abdel", "another password")
    with pytest.raises(UserError):
        s.register("ab", "longenough")
    with pytest.raises(UserError):
        s.register("validname", "short")


def test_passwords_are_hashed_not_stored():
    s = Store()
    s.register("abdel", "correct horse")
    row = s.db.execute("SELECT * FROM users").fetchone()
    assert b"correct horse" not in bytes(row["pw_hash"]) and len(row["pw_hash"]) == 32


def test_games_round_trip_and_score_once():
    s = Store()
    s.register("abdel", "correct horse")
    gid = s.create_game("ai", "easy", "abdel", human=X)
    g, meta = s.load_game(gid)
    g.play(4, 4)
    s.save_game(gid, g)
    again, _ = s.load_game(gid)
    assert again.history == g.history
    g.winner = X
    s.score_game(gid, g)
    s.score_game(gid, g)
    assert s.stats("abdel")["wins"] == 1
    assert s.load_game("nope") == (None, None)
