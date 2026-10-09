"""Rules of Ultimate Tic-Tac-Toe.

The board is nine small tic-tac-toe boards in a 3x3 grid. Where you play
inside a small board decides which small board your opponent must play in
next. Win a small board by getting three in a row inside it; win the game by
winning three small boards in a row. If you are sent to a board that is
already won or full, you may play anywhere that is still open.

Squares are addressed as (board, cell), both 0-8, numbered left to right,
top to bottom.
"""

from __future__ import annotations

from dataclasses import dataclass, field

LINES = ((0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6))
X, O, DRAW, EMPTY = "X", "O", "D", ""


class IllegalMove(ValueError):
    pass


def line_winner(cells) -> str:
    """'X' or 'O' if they own a full line, else ''."""
    for a, b, c in LINES:
        if cells[a] and cells[a] in (X, O) and cells[a] == cells[b] == cells[c]:
            return cells[a]
    return EMPTY


@dataclass
class Game:
    cells: list = field(default_factory=lambda: [EMPTY] * 81)      # index = board * 9 + cell
    boards: list = field(default_factory=lambda: [EMPTY] * 9)      # small-board results: '', X, O, D
    to_move: str = X
    active: int | None = None                                      # board you must play in (None = any open board)
    winner: str = EMPTY                                            # '', X, O or D (draw)
    history: list = field(default_factory=list)                    # [(player, board, cell), ...]

    # ---------- queries ----------

    @property
    def over(self) -> bool:
        return self.winner != EMPTY

    def open_board(self, b: int) -> bool:
        return self.boards[b] == EMPTY

    def legal_moves(self) -> list[tuple[int, int]]:
        if self.over:
            return []
        targets = [self.active] if self.active is not None else [b for b in range(9) if self.open_board(b)]
        return [(b, c) for b in targets for c in range(9) if self.cells[b * 9 + c] == EMPTY]

    # ---------- moves ----------

    def play(self, board: int, cell: int) -> "Game":
        if self.over:
            raise IllegalMove("the game is over")
        if not (0 <= board <= 8 and 0 <= cell <= 8):
            raise IllegalMove("board and cell must be 0-8")
        if not self.open_board(board):
            raise IllegalMove(f"board {board} is already decided")
        if self.active is not None and board != self.active:
            raise IllegalMove(f"you must play in board {self.active}")
        if self.cells[board * 9 + cell] != EMPTY:
            raise IllegalMove("that square is taken")

        player = self.to_move
        self.cells[board * 9 + cell] = player
        self.history.append((player, board, cell))

        small = self.cells[board * 9 : board * 9 + 9]
        won = line_winner(small)
        if won:
            self.boards[board] = won
        elif all(small):
            self.boards[board] = DRAW

        overall = line_winner(self.boards)
        if overall:
            self.winner = overall
        elif all(self.boards):
            self.winner = DRAW

        self.active = cell if self.open_board(cell) else None
        self.to_move = O if player == X else X
        if not self.over and not self.legal_moves():
            self.winner = DRAW
        return self

    # ---------- (de)serialisation ----------

    def copy(self) -> "Game":
        return Game(self.cells[:], self.boards[:], self.to_move, self.active, self.winner, self.history[:])

    def to_dict(self) -> dict:
        return {
            "cells": [self.cells[b * 9 : b * 9 + 9] for b in range(9)],
            "boards": self.boards,
            "to_move": self.to_move,
            "active_board": self.active,
            "winner": self.winner or None,
            "legal_moves": [list(m) for m in self.legal_moves()],
            "history": [list(h) for h in self.history],
        }

    @classmethod
    def from_history(cls, history) -> "Game":
        game = cls()
        for _, board, cell in history:
            game.play(board, cell)
        return game
