import pytest

from uttt.engine import DRAW, Game, IllegalMove, O, X, line_winner


def test_first_move_can_go_anywhere():
    assert len(Game().legal_moves()) == 81


def test_your_cell_sends_the_opponent_to_that_board():
    g = Game().play(4, 2)
    assert g.active == 2
    assert g.to_move == O
    assert all(b == 2 for b, _ in g.legal_moves())
    with pytest.raises(IllegalMove, match="must play in board 2"):
        g.play(5, 0)


def test_taken_square_and_bad_coordinates_are_rejected():
    g = Game().play(0, 0)
    with pytest.raises(IllegalMove):
        g.play(0, 0)  # O is sent to board 0, square 0 is taken
    with pytest.raises(IllegalMove):
        Game().play(9, 0)


def test_winning_a_small_board_and_free_move_when_sent_to_it():
    g = Game.from_history([(X, 0, 0), (O, 0, 4), (X, 4, 0), (O, 0, 8), (X, 8, 0), (O, 0, 1),
                           (X, 1, 0), (O, 0, 7)])
    assert g.boards[0] == O                      # O took 4, 1, 7 in board 0: middle column
    g.play(7, 0)                                 # X sends O to board 0, which is decided
    assert g.active is None
    assert {b for b, _ in g.legal_moves()} == {1, 2, 3, 4, 5, 6, 7, 8}
    with pytest.raises(IllegalMove, match="already decided"):
        g.play(0, 2)


def _give(game, board, player, cells=(0, 1, 2)):
    """Test helper: hand a small board to `player` directly."""
    for c in cells:
        game.cells[board * 9 + c] = player
    game.boards[board] = player


def test_three_small_boards_in_a_row_wins_the_game():
    g = Game()
    _give(g, 0, X)
    _give(g, 1, X)
    g.cells[2 * 9 + 0] = X
    g.cells[2 * 9 + 1] = X
    g.to_move, g.active = X, 2
    g.play(2, 2)
    assert g.boards[2] == X
    assert g.winner == X
    assert g.legal_moves() == []
    with pytest.raises(IllegalMove, match="over"):
        g.play(3, 3)


def test_full_small_board_without_a_line_is_a_draw():
    g = Game()
    for c, mark in zip(range(8), [X, O, X, X, O, O, O, X]):
        g.cells[3 * 9 + c] = mark
    g.to_move, g.active = X, 3
    g.play(3, 8)
    assert g.boards[3] == DRAW


def test_whole_game_draw_when_all_boards_decided_without_a_line():
    g = Game()
    owners = [X, O, X, X, O, O, O, X, None]
    for b, owner in enumerate(owners[:8]):
        _give(g, b, owner)
    # Last board: fill it without a line; the final move makes it a drawn board.
    for c, mark in zip(range(8), [X, O, X, X, O, O, O, X]):
        g.cells[8 * 9 + c] = mark
    g.to_move, g.active = X, 8
    g.play(8, 8)
    assert g.winner == DRAW


def test_line_winner():
    assert line_winner([X, X, X, "", "", "", "", "", ""]) == X
    assert line_winner([O, "", "", "", O, "", "", "", O]) == O
    assert line_winner([DRAW, DRAW, DRAW, "", "", "", "", "", ""]) == ""


def test_replaying_history_rebuilds_the_same_position():
    g = Game()
    for move in [(4, 4), (4, 0), (0, 4), (4, 8), (8, 4)]:
        g.play(*move)
    again = Game.from_history(g.history)
    assert again.to_dict() == g.to_dict()
