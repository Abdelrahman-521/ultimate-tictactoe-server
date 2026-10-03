from http.server import BaseHTTPRequestHandler, HTTPServer

hostName = "localhost"
serverPort = 8080


class ServerApiRequestHandler(BaseHTTPRequestHandler):
    """
    A stub implementation of a server API for a game application.
    """

    def start_game(self):
        """
        Start a new game, fetching user information and passing them to userInfo.
        Should call on the load_game function.
        
        Returns:
            dict/List: A dictionary/List containing information about the newly started game. Should be passed to UserInfo.
        """

    def restart_game(self, game_id):
        """
        Restart an existing game.

        Args:
            game_id (int): The ID of the game to restart.
        
        Returns:
            dict/list: A dictionary/list containing information about the restarted game.
        """

    def update_board(self, game_id):
        """
        Updating the board like Making a move in the specified game or updating score.

        Args:
            game_id (int): The ID of the game in which to make the move.
        
        Returns:
            dict/List: A dictionary/List containing information about the updated game state.
        """

    def get_game_state(self, game_id):
        """
        Get the current state of the specified game. Like win/loss/undetermined_yet

        Args:
            game_id (int): The ID of the game to retrieve state for.
        
        Returns:
            Boolean: True or False depends if the game is won or lost.
        """

    def load_game(self):
        """
        Should load a game and generate a gameID and assigning it to the newly started game.

        Args:
            None
        
        Returns:
            game_id (int): The ID of the game
        """

    def do_get(self, request):
        """
        Handle HTTP GET requests.

        Args:
            request (HTTPRequest): The HTTP GET request received from the user.

        Returns:
            HTTPResponse: The HTTP response to be sent back to the user.
        """
        
    def do_post(self, request):
        """
        Handle HTTP POST requests.

        Args:
            request (HTTPRequest): The HTTP POST request received from the user.

        Returns:
            HTTPResponse: The HTTP response to be sent back to the user.
        """

if __name__ == "__main__":
    """
        Generating the link to the server.
        
    """
    webServer = HTTPServer((hostName, serverPort), ServerApiRequestHandler)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")