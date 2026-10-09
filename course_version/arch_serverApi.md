## ServerApi Description:
The provided code serves as a stub implementation of the server API for the game "Ultimate Tic Tac Toe". It introduces a custom request handler class named `ServerApiRequestHandler`, which inherits from `BaseHTTPRequestHandler`. This class encapsulates functionalities such as initiating a new game, restarting an ongoing game, updating the game board, fetching the current game state, and loading a game from storage. Moreover, it incorporates methods `do_get` and `do_post` to manage HTTP GET and POST requests correspondingly.

## Server Features:
The following list is not definite and is subject to change. 

    - Game basics (start and restart game, updating board/ board status checking)
    - Defines methods for various game-related operations such as starting, restarting, and updating the game.
    - Provides methods for handling HTTP GET and POST requests, allowing clients to interact with the server API.
    - Includes a main block to initialize and start the HTTP server on a specified host and port.



![alt text](<UMLserverApi.png>)