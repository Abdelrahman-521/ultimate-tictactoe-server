import unittest
from bottle import request
from main import server_api

class TestServerApi(unittest.TestCase):
    
    def test_new_game(self):
        """
        Test the new_game route.
        """
        # Simulate a GET request to /new_game
        request.query['game_id'] = 'test_game'
        response = server_api.new_game()
        
        # Check if the response contains the expected keys
        expected_keys = ['message', 'board', 'game_id']
        for key in expected_keys:
            self.assertIn(key, response)
        
        # Check if the message is correct
        self.assertEqual(response['message'], 'New game created')
        
        # Check if the board is not empty
        self.assertTrue(response['board'])
        
        # Check if the game ID is correct
        self.assertEqual(response['game_id'], 'test_game')
    
    def test_load_game(self):
        """
        Test the load_game route.
        """
        # Simulate a GET request to /load_game
        request.query['game_id'] = 'test_game'
        response = server_api.load_game()
        
        # Check if the response contains the expected keys
        expected_keys = ['message', 'board']
        for key in expected_keys:
            self.assertIn(key, response)
        
        # Check if the message is correct
        self.assertEqual(response['message'], 'Game loaded')
        
        # Check if the board is not empty
        self.assertTrue(response['board'])

if __name__ == '__main__':
    unittest.main()
