import React, { useState } from "react";
import "./css/GameScreen.css";

//==================================================
//                 IMAGE REFERENCES
//==================================================
const tileBasePath = "images/tiles/";
const charBasePath = "images/characters/";

const characterIcons = {
  "Miss Scarlett": charBasePath + "MissScarlett.png",
  "Professor Plum": charBasePath + "ProfessorPlum.png",
  "Colonel Mustard": charBasePath + "ColonelMustard.png",
  "Mrs. Peacock": charBasePath + "MrsPeacock.png",
  "Reverend Green": charBasePath + "ReverendGreen.png",
  "Mrs. White": charBasePath + "MrsWhite.png",
};

const tileImages = {
  empty: tileBasePath + "empty.png",
  blocked: tileBasePath + "blocked.png",
  room: tileBasePath + "room.png",
  study: tileBasePath + "study.png",
  hall: tileBasePath + "Hall.png",
  lounge: tileBasePath + "Lounge.png",
  library: tileBasePath + "Library.png",
  diningroom: tileBasePath + "DiningRoom.png",
  conservatory: tileBasePath + "Conservatory.png",
  ballroom: tileBasePath + "Ballroom.png",
  kitchen: tileBasePath + "Kitchen.png",
  billiardroom: tileBasePath + "BilliardRoom.png",
  hallway_horizontal: tileBasePath + "HallwayHorizontal.png",
  hallway_vertical: tileBasePath + "HallwayVertical.png",
};

function GameScreen({
  currentPlayer,
  onMove,
  onSuggestion,
  onAccusation,
  onDisproveSuggestion,
  onEndTurn,
  moves,
  location,
  gameState,
  character,
  playerId,
  localPlayer,
  revealOptions,
  disproveSuggestionState,
  socket,
  messages,
  inRoom,
  playerMoved,
  actionMade,
  cannotMove,
  movedBySuggestion,
}) {
  const [moveChoice, setMoveChoice] = useState("");
  const [suggestion, setSuggestion] = useState({
    character: "",
    weapon: "",
    room: "",
  });
  const [accusation, setAccusation] = useState({
    character: "",
    weapon: "",
    room: "",
  });
  const [revealedCard, setRevealedCard] = useState(null); // Revealed card
  const [chatInput, setChatInput] = useState("");

  const handleMove = () => {
    onMove(moveChoice);
  };

  const handleSuggestion = () => {
    if (!suggestion.character || !suggestion.weapon || !suggestion.room) {
      alert("Please complete all suggestion fields");
      return;
    }
    onSuggestion(suggestion);
  };

  const handleDisproveSuggestion = () => {
    if (!revealedCard) {
      alert("Please select the card to disprove.");
      return;
    }
    console.log("Incorrect Card: ", revealedCard);
    onDisproveSuggestion(revealedCard);
  };

  const handleAccusation = () => {
    if (!accusation.character || !accusation.weapon || !accusation.room) {
      alert("Please complete all accusation fields.");
      return;
    }
    onAccusation(accusation);
  };

  const handleEndTurn = () => {
    onEndTurn();
  };

  const isPlayerTurn = currentPlayer === localPlayer?.name;

  const sendChatMessage = () => {
    if (!chatInput.trim()) return;
    socket.emit("chat_message", { player_id: playerId, message: chatInput });
    setChatInput("");
  };

  return (
    <div className="game-screen">
      <div className="left-panel">
        <h2>
          Your Player: {localPlayer?.name} <br />
          Your Character: {localPlayer?.character} <br />
          Your Location: {localPlayer?.location} <br />
        </h2>
        <h3>
          Current Player: {currentPlayer} <br />
          Current Player's Character: {character} <br />
          Current Player's Location: {location} <br />
        </h3>

        {/* Actions */}
        <div>
          {!cannotMove || moves.length !== 0 ? (
            <div>
              <h3>Make a Move</h3>
              <select
                onChange={(e) => setMoveChoice(e.target.value)}
                value={moveChoice}
                disabled={!isPlayerTurn}
              >
                <option value="">Select Move</option>
                {moves.map((move, index) => (
                  <option key={index} value={move}>
                    {move}
                  </option>
                ))}
              </select>
              <button onClick={handleMove} disabled={!isPlayerTurn}>
                Move
              </button>
            </div>
          ) : (
            <h4>No possible moves available.</h4>
          )}
        </div>

        <div>
          {(movedBySuggestion || (playerMoved && inRoom)) && (
            <div>
              <h3>Make a Suggestion</h3>
              <select
                onChange={(e) =>
                  setSuggestion((prev) => ({
                    ...prev,
                    character: e.target.value,
                  }))
                }
                disabled={!isPlayerTurn}
              >
                <option value="">Select Suspect</option>
                <option value="1,Colonel Mustard">Colonel Mustard</option>
                <option value="2,Professor Plum">Professor Plum</option>
                <option value="3,Reverend Green">Reverend Green</option>
                <option value="4,Mrs. Peacock">Mrs. Peacock</option>
                <option value="5,Miss Scarlett">Miss Scarlett</option>
                <option value="6,Mrs. White">Mrs. White</option>
              </select>
              <select
                onChange={(e) =>
                  setSuggestion((prev) => ({ ...prev, weapon: e.target.value }))
                }
                disabled={!isPlayerTurn}
              >
                <option value="">Select Weapon</option>
                <option value="1,Dagger">Dagger</option>
                <option value="2,Candlestick">Candlestick</option>
                <option value="3,Revolver">Revolver</option>
                <option value="4,Rope">Rope</option>
                <option value="5,Lead Pipe">Lead Pipe</option>
                <option value="6,Wrench">Wrench</option>
              </select>
              <select
                onChange={(e) =>
                  setSuggestion((prev) => ({ ...prev, room: e.target.value }))
                }
                disabled={!isPlayerTurn}
              >
                <option value="">Select Room</option>
                <option value={location}>{location}</option>
              </select>
              <button onClick={handleSuggestion} disabled={!isPlayerTurn}>
                Suggest
              </button>
            </div>
          )}
        </div>

        <div>
          {disproveSuggestionState && revealOptions.length > 0 && (
            <div>
              <h3>Select a Card to Disprove</h3>
              <select
                onChange={(e) => setRevealedCard(e.target.value)}
                value={revealedCard || ""}
              >
                <option value="">Select a Card</option>
                {revealOptions.map((card, index) => (
                  <option key={index} value={card}>
                    {card}
                  </option>
                ))}
              </select>
              <button onClick={handleDisproveSuggestion}>
                Confirm Card to Disprove
              </button>
            </div>
          )}
        </div>

        <div>
          <h3>Make an Accusation</h3>
          <select
            onChange={(e) =>
              setAccusation((prev) => ({ ...prev, character: e.target.value }))
            }
            disabled={!isPlayerTurn}
          >
            <option value="">Select Suspect</option>
            <option value="1">Colonel Mustard</option>
            <option value="2">Professor Plum</option>
            <option value="3">Reverend Green</option>
            <option value="4">Mrs. Peacock</option>
            <option value="5">Miss Scarlett</option>
            <option value="6">Mrs. White</option>
          </select>
          <select
            onChange={(e) =>
              setAccusation((prev) => ({ ...prev, weapon: e.target.value }))
            }
            disabled={!isPlayerTurn}
          >
            <option value="">Select Weapon</option>
            <option value="1">Dagger</option>
            <option value="2">Candlestick</option>
            <option value="3">Revolver</option>
            <option value="4">Rope</option>
            <option value="5">Lead Pipe</option>
            <option value="6">Wrench</option>
          </select>
          <select
            onChange={(e) =>
              setAccusation((prev) => ({ ...prev, room: e.target.value }))
            }
            disabled={!isPlayerTurn}
          >
            <option value="">Select Room</option>
            <option value="1">Hall</option>
            <option value="2">Lounge</option>
            <option value="3">Library</option>
            <option value="4">Kitchen</option>
            <option value="5">Billiard Room</option>
            <option value="6">Study</option>
            <option value="7">Ballroom</option>
            <option value="8">Dining Room</option>
            <option value="9">Conservatory</option>
          </select>
          <button onClick={handleAccusation} disabled={!isPlayerTurn}>
            Accuse
          </button>
        </div>

        <div>
          {actionMade && (
            <div>
              <button
                class="red-button"
                onClick={handleEndTurn}
                disabled={!isPlayerTurn}
              >
                End Turn
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="center-panel">
        {gameState && gameState.length > 0 ? (
          <div className="board-container">
            <h2>Game Board</h2>
            <div className="board">
              {gameState.map((row, rowIndex) => (
                <div key={rowIndex} className="board-row">
                  {row.map((cell, cellIndex) => {
                    if (cell && typeof cell === "object" && cell.type) {
                      const { type, name, characters } = cell;

                      let tileImage = tileImages["empty"];

                      if (type === "blocked") {
                        tileImage = tileImages["blocked"];
                      } else if (type === "hallway") {
                        // Determine if it's horizontal or vertical
                        let isHorizontal = false;
                        let isVertical = false;

                        // Check left neighbor
                        if (
                          cellIndex > 0 &&
                          row[cellIndex - 1] &&
                          row[cellIndex - 1].type !== "blocked"
                        ) {
                          isHorizontal = true;
                        }
                        // Check right neighbor
                        if (
                          cellIndex < row.length - 1 &&
                          row[cellIndex + 1] &&
                          row[cellIndex + 1].type !== "blocked"
                        ) {
                          isHorizontal = true;
                        }
                        // Check top neighbor
                        if (
                          rowIndex > 0 &&
                          gameState[rowIndex - 1][cellIndex] &&
                          gameState[rowIndex - 1][cellIndex].type !== "blocked"
                        ) {
                          isVertical = true;
                        }
                        // Check bottom neighbor
                        if (
                          rowIndex < gameState.length - 1 &&
                          gameState[rowIndex + 1][cellIndex] &&
                          gameState[rowIndex + 1][cellIndex].type !== "blocked"
                        ) {
                          isVertical = true;
                        }

                        // Choose the tile image based on orientation
                        if (isVertical && !isHorizontal) {
                          tileImage = tileImages["hallway_vertical"];
                        } else if (!isVertical && isHorizontal) {
                          tileImage = tileImages["hallway_horizontal"];
                        } else {
                          tileImage = tileImages["hallway_horizontal"];
                        }
                      } else if (type === "room") {
                        const roomKey = name.toLowerCase().replace(/\s/g, "");
                        tileImage = tileImages[roomKey] || tileImages["room"];
                      }

                      const characterIconSrcs = (characters || [])
                        .map((charName) => {
                          const iconFilename = characterIcons[charName];
                          return iconFilename || null;
                        })
                        .filter((src) => src !== null);

                      return (
                        <div
                          key={cellIndex}
                          className={`board-cell ${type}`}
                          style={{ backgroundImage: `url(${tileImage})` }}
                        >
                          {type === "room" && (
                            <div className="room-label">{name}</div>
                          )}
                          {type === "hallway" && (
                            <div className="hallway-label">{name}</div>
                          )}

                          {characterIconSrcs.length > 0 && (
                            <div className="character-icons-container">
                              {characterIconSrcs.map((src, i) => (
                                <div key={i} className="character-icon-wrapper">
                                  <img
                                    src={src}
                                    alt={characters[i]}
                                    className="character-icon"
                                  />
                                  <div className="character-name">
                                    {characters[i]}
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      );
                    } else {
                      // Fallback if cell isn't structured
                      return (
                        <div key={cellIndex} className="board-cell">
                          <pre>{cell}</pre>
                        </div>
                      );
                    }
                  })}
                </div>
              ))}
            </div>
          </div>
        ) : (
          <p>Loading game board...</p>
        )}
      </div>

      <div className="right-panel">
        <div className="players-info">
          <h3>Player's Cards</h3>
          {localPlayer ? (
            <div className="player-details">
              {localPlayer.cards.length > 0 ? (
                <div className="cards-list">
                  {localPlayer.cards.map((card, cardIndex) => (
                    <span key={cardIndex} className="card-item">
                      {card.name}
                    </span>
                  ))}
                </div>
              ) : (
                <span className="no-cards">No cards assigned</span>
              )}
            </div>
          ) : (
            <p>No players found</p>
          )}
        </div>

        <div className="chat-container">
          <div className="chat-messages">
            {!isPlayerTurn && (
              <div className="system-message">
                <em>
                  It's currently {currentPlayer}'s turn. Please wait for your
                  turn.
                </em>
              </div>
            )}
            {messages.map((msg, index) => {
              const isOwnMessage = msg.player_id === playerId;
              const isSystemMessage = msg.player_id === "SYSTEM";

              const messageClass = isSystemMessage
                ? "system-message"
                : isOwnMessage
                ? "own-message"
                : "chat-message";

              return (
                <div key={index} className={messageClass}>
                  {isSystemMessage ? (
                    <em>{msg.message}</em>
                  ) : (
                    <>
                      <strong>{msg.player_name}:</strong> {msg.message}
                    </>
                  )}
                </div>
              );
            })}
          </div>

          <div className="chat-input">
            <input
              type="text"
              placeholder="Type your message..."
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
            />
            <button class="green-button" onClick={sendChatMessage}>
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default GameScreen;
