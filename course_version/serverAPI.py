# Student Name: Abdelrahman Conber


from bottle import Bottle, request, response
import json
import main.store as qpersist
from main.user import User
from main.app_logic import BoardLogic

app = Bottle()

@app.route('/new_game', method='GET')
def new_game():
    """
    Initialize a new game and return the board.

    Returns:
        str: JSON response containing the message and the newly created board.
    """
    board_logic = BoardLogic("tic_tac_toe")
    board = board_logic.new_game()
    qpersist.store(board, "tic_tac_toe")
    return json.dumps({"message": "New game created", "board": board})

@app.route('/load_game', method='GET')
def load_game():
    """
    Load the game from storage and return the board.

    Returns:
        str: JSON response containing the message and the loaded board.
    """
    game_id = request.query.id
    board = qpersist.load(game_id)
    return json.dumps({"message": "Game loaded", "board": board})

@app.route('/make_move', method='POST')
def make_move():
    """
    Extract move and player info from the request and update the board with the player's move.

    Returns:
        str: JSON response indicating the success or failure of the move and the updated board.
    """
    move = json.loads(request.body.read())
    player = User("username", "password")  # Placeholder user info, replace with actual user info
    
    # Update the board with the player's move
    game_id = request.query.id
    board_logic = BoardLogic("tic_tac_toe")
    try:
        updated_board = board_logic.update_board(move["move"], move["player_symbol"])
        qpersist.store(updated_board, game_id)
        return json.dumps({"message": "Move successful", "board": updated_board})
    except ValueError as e:
        response.status = 400
        return json.dumps({"error": str(e)})

@app.route('/load_game_status', method='GET')
def load_game_status():
    """
    Load the game status from storage and return.

    Returns:
        str: JSON response containing the message and the loaded game ID.
    """
    game_id = request.query.id
    return json.dumps({"message": "Game status loaded", "game_id": game_id})

@app.route('/save_game_status', method='POST')
def save_game_status():
    """
    Save the game status to storage.

    Returns:
        str: JSON response containing the message and the saved game ID.
    """
    game_id = request.query.id
    return json.dumps({"message": "Game status saved", "game_id": game_id})

@app.route('/user_info', method='GET')
def user_info():
    """
    Retrieve user information.

    Returns:
        str: JSON response containing the user's username, wins, and losses.
    """
    user = User("username", "password")  # Placeholder user info, replace with actual user info
    return json.dumps({"username": user.username, "wins": user.wins, "losses": user.losses})

if __name__ == '__main__':
    app.run(host='localhost', port=8080)
