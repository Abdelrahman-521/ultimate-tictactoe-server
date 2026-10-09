// Front end for the Ultimate Tic-Tac-Toe API. Plain JavaScript, no build step.

const $ = (id) => document.getElementById(id);
const state = { game: null, token: null, username: null, busy: false };

async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json" };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  const res = await fetch(path, { ...options, headers });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || res.statusText);
  return data;
}

function statusText(g) {
  if (g.winner === "D") return "It's a draw.";
  if (g.winner) {
    if (g.mode === "ai") return g.winner === g.human ? "You win!" : "The computer wins.";
    return `${g.winner} wins!`;
  }
  const where = g.active_board === null ? "anywhere open" : `in the highlighted board`;
  if (g.mode === "ai") return g.to_move === g.human ? `Your move (${g.human}), ${where}.` : "Computer is thinking…";
  return `${g.to_move} to move, ${where}.`;
}

function render() {
  const g = state.game;
  const board = $("board");
  board.innerHTML = "";
  if (!g) return;
  const legal = new Set(g.legal_moves.map(([b, c]) => `${b}-${c}`));
  const myTurn = g.mode === "local" || g.to_move === g.human;
  const last = g.history.length ? g.history[g.history.length - 1] : null;

  for (let b = 0; b < 9; b++) {
    const small = document.createElement("div");
    small.className = "small";
    if (!g.winner && myTurn && g.legal_moves.some(([mb]) => mb === b)) small.classList.add("playable");
    for (let c = 0; c < 9; c++) {
      const cell = document.createElement("button");
      const mark = g.cells[b][c];
      cell.className = `cell ${mark}`;
      cell.textContent = mark;
      cell.setAttribute("aria-label", `board ${b + 1}, square ${c + 1}${mark ? ", " + mark : ""}`);
      if (last && last[1] === b && last[2] === c) cell.classList.add("last");
      if (myTurn && !state.busy && legal.has(`${b}-${c}`)) {
        cell.classList.add("legal");
        cell.addEventListener("click", () => play(b, c));
      } else {
        cell.disabled = true;
      }
      small.appendChild(cell);
    }
    if (g.boards[b]) {
      const claimed = document.createElement("div");
      claimed.className = `claimed ${g.boards[b]}`;
      claimed.textContent = g.boards[b] === "D" ? "–" : g.boards[b];
      small.appendChild(claimed);
    }
    board.appendChild(small);
  }
  $("status").textContent = state.busy ? "Computer is thinking…" : statusText(g);
}

async function play(b, c) {
  state.busy = true;
  render();
  try {
    state.game = await api(`/api/games/${state.game.id}/moves`, {
      method: "POST", body: JSON.stringify({ board: b, cell: c }),
    });
    if (state.game.winner) refreshRecord();
  } catch (err) {
    $("status").textContent = err.message;
  } finally {
    state.busy = false;
    render();
  }
}

async function newGame() {
  const mode = $("mode").value;
  state.busy = true;
  $("status").textContent = "Setting up…";
  try {
    state.game = await api("/api/games", {
      method: "POST",
      body: JSON.stringify({ mode, level: $("level").value, human: mode === "ai" ? $("human").value : "X" }),
    });
    try { localStorage.setItem("uttt-game", state.game.id); } catch (_) {}
  } catch (err) {
    $("status").textContent = err.message;
  } finally {
    state.busy = false;
    render();
  }
}

async function refreshRecord() {
  if (!state.username) return;
  const s = await api(`/api/users/${encodeURIComponent(state.username)}`);
  $("record").textContent = `vs computer: ${s.wins} wins, ${s.losses} losses, ${s.draws} draws`;
}

function showAccount() {
  $("logged-in").hidden = !state.username;
  $("logged-out").hidden = !!state.username;
  $("who").textContent = state.username ? `Logged in as ${state.username}` : "";
  refreshRecord().catch(() => {});
}

async function login(register) {
  const username = $("username").value.trim();
  const password = $("password").value;
  $("account-msg").textContent = "";
  try {
    if (register) await api("/api/users", { method: "POST", body: JSON.stringify({ username, password }) });
    const s = await api("/api/sessions", { method: "POST", body: JSON.stringify({ username, password }) });
    state.token = s.token;
    state.username = s.username;
    try { localStorage.setItem("uttt-session", JSON.stringify(s)); } catch (_) {}
    $("password").value = "";
    showAccount();
  } catch (err) {
    $("account-msg").textContent = err.message;
  }
}

function logout() {
  state.token = state.username = null;
  try { localStorage.removeItem("uttt-session"); } catch (_) {}
  showAccount();
}

function syncControls() {
  const ai = $("mode").value === "ai";
  $("level-wrap").hidden = !ai;
  $("side-wrap").hidden = !ai;
}

async function start() {
  $("new-game").addEventListener("click", newGame);
  $("mode").addEventListener("change", syncControls);
  $("login").addEventListener("click", () => login(false));
  $("register").addEventListener("click", () => login(true));
  $("logout").addEventListener("click", logout);
  syncControls();
  try {
    const saved = JSON.parse(localStorage.getItem("uttt-session") || "null");
    if (saved) Object.assign(state, { token: saved.token, username: saved.username });
  } catch (_) {}
  showAccount();
  const savedGame = (() => { try { return localStorage.getItem("uttt-game"); } catch (_) { return null; } })();
  if (savedGame) {
    try { state.game = await api(`/api/games/${savedGame}`); render(); return; } catch (_) {}
  }
  newGame();
}

start();
