"""A computer opponent: Monte Carlo tree search (UCT).

From the current position it repeatedly picks a promising move sequence,
plays the rest of the game out at random, and records who won. Moves that
lead to more wins get explored more. After the budget runs out it plays the
move it explored most.

It also never misses a game-winning move and never ignores an opponent's
immediate game-winning threat.
"""

from __future__ import annotations

import math
import random
import time

from .engine import DRAW, Game, O, X

LEVELS = {"easy": 60, "normal": 600, "hard": 2500}


class Node:
    __slots__ = ("move", "parent", "children", "untried", "wins", "visits", "player")

    def __init__(self, game: Game, move=None, parent=None):
        self.move = move
        self.parent = parent
        self.children: list[Node] = []
        self.untried = game.legal_moves()
        self.wins = 0.0
        self.visits = 0
        self.player = O if game.to_move == X else X   # who made `move`

    def best_child(self, c=1.4):
        log_n = math.log(self.visits)
        return max(self.children, key=lambda ch: ch.wins / ch.visits + c * math.sqrt(log_n / ch.visits))


def _rollout(game: Game, rng: random.Random) -> str:
    while not game.over:
        game.play(*rng.choice(game.legal_moves()))
    return game.winner


def _winning_move(game: Game, player: str):
    """A move that wins the whole game for `player` right now, if any."""
    probe = game.copy()
    probe.to_move = player
    for move in probe.legal_moves():
        trial = probe.copy()
        trial.play(*move)
        if trial.winner == player:
            return move
    return None


def choose_move(game: Game, level: str = "normal", seed=None, time_limit: float = 2.0):
    if game.over:
        raise ValueError("the game is over")
    moves = game.legal_moves()
    if len(moves) == 1:
        return moves[0]
    me = game.to_move
    them = O if me == X else X
    win = _winning_move(game, me)
    if win:
        return win
    rng = random.Random(seed)

    root = Node(game)
    budget = LEVELS.get(level, LEVELS["normal"])
    deadline = time.monotonic() + time_limit
    for _ in range(budget):
        node, state = root, game.copy()
        # Selection
        while not node.untried and node.children:
            node = node.best_child()
            state.play(*node.move)
        # Expansion
        if node.untried:
            move = node.untried.pop(rng.randrange(len(node.untried)))
            state.play(*move)
            child = Node(state, move, node)
            node.children.append(child)
            node = child
        # Simulation
        result = _rollout(state, rng)
        # Backpropagation
        while node is not None:
            node.visits += 1
            if result == node.player:
                node.wins += 1
            elif result == DRAW:
                node.wins += 0.5
            node = node.parent
        if time.monotonic() > deadline:
            break

    ranked = sorted(root.children, key=lambda ch: ch.visits, reverse=True)
    # Don't hand the opponent an immediate game win if a safer move exists.
    for child in ranked:
        after = game.copy()
        after.play(*child.move)
        if after.over or _winning_move(after, them) is None:
            return child.move
    return ranked[0].move
