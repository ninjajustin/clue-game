import eventlet
eventlet.monkey_patch()
import random
import json
import os
import uuid
from flask_cors import CORS
from flask import Flask, request, jsonify, Response
from flask_socketio import SocketIO, send, emit
from game_system.game_system import GameSystem
from game_system.turn_manager import TurnManager
from game_system.solution import Solution
from game_system.card import Card
from game_system.suggestion import Suggestion
from game_system.accusation import Accusation
from game_system.BoardManager import BoardManager

app = Flask(__name__)
CORS(app, origins=["https://peppy-empanada-ec068d.netlify.app"])
socketio = SocketIO(app, cors_allowed_origins="https://peppy-empanada-ec068d.netlify.app")
# CORS(app, origins=["http://192.168.1.22:3001"])
# socketio = SocketIO(app, cors_allowed_origins="http://192.168.1.22:3001")
# CORS(app, origin=["http://localhost:3000"])
# socketio = SocketIO(app, cors_allowed_origins="http://localhost:3000")

game_system = GameSystem()
turn_manager = TurnManager(game_system.players)
board_manager = BoardManager()

# Store mapping from socket ID to player ID
socket_player_map = {}

cards = [[
        Card("Colonel Mustard", "suspect"),
        Card("Professor Plum", "suspect"),
        Card("Reverend Green", "suspect"),
        Card("Mrs. Peacock", "suspect"),
        Card("Miss Scarlett", "suspect"),
        Card("Mrs. White", "suspect")
    ],
    [
        Card("Dagger", "weapon"),
        Card("Candlestick", "weapon"),
        Card("Revolver", "weapon"),
        Card("Rope", "weapon"),
        Card("Lead Pipe", "weapon"),
        Card("Wrench", "weapon")
    ],
    [
        Card("Hall", "room"),
        Card("Lounge", "room"),
        Card("Library", "room"),
        Card("Kitchen", "room"),
        Card("Billiard Room", "room"),
        Card("Study", "room"),
        Card("Ballroom", "room"),
        Card("Dining Room", "room"),
        Card("Conservatory", "room")    
    ]]

option_table = """  
========================================================================
||......Characters.......||......Weapons......||........Rooms........||
||  1.) Colonel Mustard  ||  1.) Dagger       ||  1.) Hall           ||
||  2.) Professor Plum   ||  2.) Candlestick  ||  2.) Lounge         ||
||  3.) Reverend Green   ||  3.) Revolver     ||  3.) Library        ||
||  4.) Mrs. Peacock     ||  4.) Rope         ||  4.) Kitchen        ||
||  5.) Miss Scarlett    ||  5.) Lead Pipe    ||  5.) Billiard Room  ||
||  6.) Mrs. White       ||  6.) Wrench       ||  6.) Study          ||
||                       ||                   ||  7.) Ballroom       ||
||                       ||                   ||  8.) Dining Room    ||
||                       ||                   ||  9.) Conservatory   ||
========================================================================
"""

def createSolution():
    # Create Solution for game
    c_index = random.randint(0, 5)
    w_index = 6 + random.randint(0, 5)
    r_index = 12 + random.randint(0, 8)
    character = game_system.cards[c_index]
    weapon = game_system.cards[w_index]
    room = game_system.cards[r_index]
    print(f"Solution:  Character: {c_index + 1} {character}  Weapon: {w_index - 5} {weapon}  Room: {r_index - 11} {room}")
    game_system.cards.remove(character)
    game_system.cards.remove(weapon)
    game_system.cards.remove(room)
    return Solution(character, weapon, room)

solution = createSolution()

@app.route("/")  # Define the root route
def home():
    return "Your Flask app is live!"

# --------------------------------------------------------------------
@app.before_request 
def basic_authentication():
    if request.method.lower() == 'options':
        return Response()
# --------------------------------------------------------------------

@socketio.on('connect')
def handle_connect():
    print("Client connected")
    send("Welcome to the WebSocket server!")  # Sends a welcome message to the client upon connection

@socketio.on('disconnect')
def handle_disconnect():
    """
    Handle player disconnection. Remove the disconnected player from the game and notify all clients.
    """
    socket_id = request.sid  # Get the socket ID of the disconnected client
    player_id = socket_player_map.pop(socket_id, None)  # Remove the mapping for this socket

    if player_id:
        # Find the player in the game system
        player = next((p for p in game_system.players if p.id == player_id), None)
        if player:
            print(f"{player.name} ({player_id}) disconnected and will be removed from the game.")
            # Remove player from the active game
            game_system.players.remove(player)
            if player in game_system.active_players:
                game_system.active_players.remove(player)
            
            # Adjust the turn counter if necessary
            if len(game_system.active_players) > 0:
                game_system.counter %= len(game_system.active_players)
            else:
                game_system.counter = 0  # Reset if no active players
            
            # Notify all clients about the updated game state
            emit('player_disconnected', {
                "message": f"{player.name} has disconnected.",
                "remaining_players": [p.name for p in game_system.active_players]
            }, broadcast=True)

            # Check if the game should end (e.g., only one player remains)
            if len(game_system.active_players) == 1:
                winner = game_system.active_players[0]
                emit('game_over', {
                    "message": f"{winner.name} wins by default as the only remaining player.",
                    "winner": winner.name
                }, broadcast=True)

    else:
        print("Disconnected client was not associated with any player.")


@socketio.on('detailed_board')
def detailed_board(data=None):
    try:
        board_state = board_manager.draw_detailed_board()
        emit('board_response', board_state, broadcast=True)
    except Exception as e:
        emit('board_response', {"error": str(e)}, broadcast=True)
    
# --------------------------------------------------------------------
@app.route('/api/optionTable', methods=['GET'])
def get_option_table():
    return jsonify({"optionTable" : option_table})
# --------------------------------------------------------------------

@socketio.on('add_player')
def add_player(data):
    # Debugging: log received data
    print(f"Received data: {data}")

    # Parse data as JSON if it is a string
    if isinstance(data, str):
        data = json.loads(data)

    player_name = data.get("playerName")

    if len(game_system.available_characters) == 0:
        emit('player_added', {"error": "Max number of players have already joined."})
        return

    c_index = random.randint(0, len(game_system.available_characters) - 1)
    character = game_system.available_characters[c_index]
    game_system.available_characters.pop(c_index)

    # Check if player name and character are provided
    if not player_name:
        emit('player_added', {"error": "Player name is required."})
        return

    # Check if the player already exists by name
    if player_name in [player.name for player in game_system.players]:
        emit('player_added', {"error": f"{player_name} already exists"})
        return
    
    # Generate a unique player ID
    player_id = str(uuid.uuid4())

    # Associate the player's unique ID with the socket ID (the client's connection)
    socket_player_map[request.sid] = player_id

    # Add player with name and character
    location = board_manager.character_locations[character]
    message = game_system.add_player(player_name, character, player_id, location)
    print(f"{player_name} added to the game as {character}.")
    emit('player_added', {"message": message, "player_id": player_id})

@socketio.on('get_players')
def get_players():
    """
    WebSocket event to return player information and their assigned cards.
    """
    players = []
    for player in game_system.players:
        # Prepare player's card data
        player_cards = [card.to_dict() for card in player.cards]
        player_info = {
            "id": player.id,
            "name": player.name,
            "character": player.character,
            "location": player.position,
            "cards": player_cards
        }
        players.append(player_info)
    # Emit only to the requesting client
    emit('return_players', {"players": players}, broadcast=True)

@socketio.on('get_current_player')
def get_current_player(data=None):  # Add 'data' as a default argument
    """
    WebSocket event to return current player information.
    """
    try:
        name = game_system.players[game_system.counter].name
        emit('get_current_player_response', {"current_player": name})
    except IndexError:
        emit('get_current_player_response', {"error": "No current player found"})

@socketio.on('start_game')
def start_game(data=None):  # Add 'data' as a placeholder argument
    try:
        # Attempt to start the game
        game_system.start_game()
        game_system.active_players = game_system.players.copy()
        # Emit a success response
        emit('game_started', {
            'current_player': game_system.active_players[game_system.counter].name, 
            'character': game_system.active_players[game_system.counter].character,
            'message': 'Game started successfully. Cards have been distributed and shown to players.'
            }, broadcast=True)
    except Exception as e:
        # Emit an error response if an exception occurs
        emit('game_started', {
            'status': 'error',
            'message': str(e)
        }, broadcast=True)

@socketio.on('player_turn')
def player_turn(data):
    # Parse data as JSON if it is a string
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError as e:
            print("JSONDecodeError:", e)
            emit('player_turn_response', {"error": "Invalid JSON format"})
            return

    action = data.get("action")  # Either "start" or "end"
    player_id = game_system.active_players[game_system.counter].name
    gameOver = False

    if not action or not player_id:
        emit('player_turn_response', {"error": "Missing action or playerId"})
        return

    print(f"{player_id} is trying to {action} their turn.")

    if action == "start":
        message = game_system.start_turn(player_id)
        if len(game_system.active_players) == 1:
            message = f"{player_id} wins by default."
            gameOver = True
        print(f"Turn started for {player_id}.")
        emit('player_turn_response', {"message": message, "gameOver": gameOver}, broadcast=True)
    elif action == "end":
        if len(game_system.active_players) == 0:
            emit('player_turn_response', {"error": "No active players in the game.", "gameOver": True}, broadcast=True)
            return

        game_system.counter = game_system.counter + 1 if game_system.counter + 1 < len(game_system.active_players) else 0
        next_player = game_system.active_players[game_system.counter].name
        print(f"Turn ended for {player_id}. Next player: {next_player}. Counter: {game_system.counter}")
        emit('player_turn_response', {"message": f"Turn ended. Next player: {next_player}", "gameOver": gameOver}, broadcast=True)
    else:
        emit('player_turn_response', {"error": "Invalid action"})

@socketio.on('end_turn')
def end_turn():
    # Move to the next player
    current_player = game_system.active_players[game_system.counter].name
    game_system.active_players[game_system.counter].moved_by_suggestion = False
    game_system.counter = (game_system.counter + 1) % len(game_system.active_players)
    next_player = game_system.active_players[game_system.counter]
    if len(game_system.active_players) == 1:
        emit('game_over', {
            'message': f"{next_player.name} wins by default, as everyone else has made an incorrect accusation.",
            'winner': next_player.name               
        }, broadcast=True)
        return
    emit('next_turn', {
        'message': f"{current_player} has ended their turn. It's now {next_player.name}'s turn.",
        'current_player': next_player.name, 
        'character': next_player.character,
        'moved_by_suggestion': next_player.moved_by_suggestion
        }, broadcast=True)

@socketio.on('get_moves')
def get_moves(current_player):  # Add 'data' as a placeholder argument
    try:
        # Retrieve the current player's ID
        print(f"Received player_id: {current_player}")

        if not current_player:
            emit('move_options', {"error": "Missing playerId"})
            return

        # Find the player object in GameSystem
        player = next((p for p in game_system.active_players if p.name == current_player), None)
        if not player:
            emit('move_options', {"error": "Player not found"})
            return

        # Retrieve the player's character and current location
        player_character = player.character

        # Get current location of the player on the board
        current_location = board_manager.character_locations.get(player_character)
        if not current_location:
            emit('move_options', {"error": "Player's current location not found"})
            return

        # Get possible moves using `get_possible_moves`
        directions = board_manager.get_possible_moves(player_character)

        # Format the response with current location and options
        moves = []
        for i in range(len(directions)):
            moves.append(directions[i][1])
        response = {
            "currentLocation": current_location,
            "moves": moves
        }
        print(current_location)
        emit('move_options', response, room=request.sid)

    except ValueError as ve:
        print(f"Error: {ve}")
        emit('move_options', {"error": str(ve)})
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        emit('move_options', {"error": "An unexpected error occurred"})

@socketio.on('make_move')
def make_move(data):

    character = game_system.active_players[game_system.counter].character

    if not character or not data:
        emit('move_made', {'message': 'Invalid data. "character" and "new_room" are required.'}, broadcast=True)
        return
    
    board_manager.moveCharToRoom(character, data)
    try:
        board_state = board_manager.draw_detailed_board()
        emit('move_made', {"message": f"{character} moved to {data}.", "board": board_state}, broadcast=True)
    except Exception as e:
        emit('move_made', {"error": str(e)}, broadcast=True)


@socketio.on('make_suggestion')
def make_suggestion(data):
    # Parse data as JSON if it is a string
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError as e:
            print("JSONDecodeError:", e)
            emit('suggestion_made', {"error": "Invalid JSON format"})
            return
        
    socket_id = request.sid
    player_id = socket_player_map.get(socket_id)
    player = next((p for p in game_system.players if p.id == player_id), None)

    if player.name != game_system.active_players[game_system.counter].name:
        emit('suggestion_made', {"error": "It's not your turn."}, room=socket_id)
        return
    # player_id = game_system.active_players[game_system.counter].name

    print(f"{player_id} made a suggestion: {data}.")

    # Ensure the values are integers
    try:
        character_index = int(data['character'])
        weapon_index = int(data['weapon'])
        room_index = int(data['room'])
    except (ValueError, KeyError, TypeError) as e:
        print("Error parsing suggestion data:", e)
        emit('suggestion_made', {"error": "Invalid suggestion data"})
        return

    suggestion = Suggestion(
        cards[0][character_index - 1],
        cards[1][weapon_index - 1],
        cards[2][room_index - 1]
    )

    board_manager.moveCharToRoom(suggestion.character.name, suggestion.room.name)

    # set player that was moved by suggestion property to True
    for p in game_system.players:
        if p.character == suggestion.character.name:
            p.moved_by_suggestion = True

    # message = ""
    for p in game_system.players:
        incorrect_cards = suggestion.checkSuggestion(p.cards)
        if incorrect_cards:
            # Send the disproving cards only to the disproving player
            suggesting_player_socket_id = [sid for sid, pid in socket_player_map.items() if pid == p.id][0]
            emit('suggestion_incorrect', {
                "message": f"Choose which card to reveal is False to {player.name}.",
                "cards": incorrect_cards
            }, room=suggesting_player_socket_id)
            # Notify other players that the suggestion was disproved without revealing cards
            emit('suggestion_made', {
                "message": f"{player.name}'s suggestion is being disproven by {p.name}.",
            }, broadcast=True)
            break

    if len(incorrect_cards) == 0:
        # If no one could disprove, notify all
        emit('suggestion_made', {
            "message": f"No one could disprove {player.name}'s suggestion.",
        }, broadcast=True)


@socketio.on('disprove_suggestion')
def disprove_suggestion(disprove_player, revealed_card, current_player):
    player = next((p for p in game_system.players if p.name == current_player), None)
    socket_id = [sid for sid, pid in socket_player_map.items() if pid == player.id][0]
    emit('suggestion_disproved', {
        "message": f"{disprove_player} has the card {revealed_card}, disproving the suggestion made by {current_player}."
    }, room=socket_id)


@socketio.on('make_accusation')
def make_accusation(data):
    # Parse data as JSON if it is a string
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError as e:
            print("JSONDecodeError:", e)
            emit('accusation_made', {"error": "Invalid JSON format"})
            return

    socket_id = request.sid
    player_id = socket_player_map.get(socket_id)
    player = next((p for p in game_system.players if p.id == player_id), None)
    # player_id = game_system.active_players[game_system.counter].name
    if player.name != game_system.active_players[game_system.counter].name:
        emit('accusation_made', {"error": "It's not your turn."}, room=socket_id)
        return

    # Ensure the values are integers

    suspect = cards[0][int(data['character']) - 1]
    weapon = cards[1][int(data['weapon']) - 1]
    room = cards[2][int(data['room']) - 1]

    accusation = Accusation(
        suspect,
        weapon,
        room
    )

    result = accusation.checkAccusation(solution)

    if result:
        print(f"{player.name} has won the game.")
        emit('game_over', {"message": f"Correct accusation of Suspect: {suspect}   Weapon: {weapon}   Room: {room}. {player.name} wins!", 
                           "winner": player.name}, broadcast=True)
    else:
        # Remove the player from active players
        game_system.active_players.pop(game_system.counter)
        game_system.counter -= 1
        emit('accusation_made', {
            "message": f"{player.name} made an incorrect accusation and has lost the game."
        }, broadcast=True)
    
@socketio.on('chat_message')
def handle_chat_message(data):
    player_id = data.get('player_id')
    message = data.get('message')

    # Validate input
    if not player_id or not message:
        return

    # Optional: Get player name from player_id
    player = next((p for p in game_system.players if p.id == player_id), None)
    player_name = player.name if player else "Unknown Player"

    # Broadcast the message to all clients
    emit('chat_broadcast', {
        'player_id': player_id,
        'player_name': player_name,
        'message': message
    }, broadcast=True)

if __name__ == "__main__":
    # socketio.run(app, debug=True)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)