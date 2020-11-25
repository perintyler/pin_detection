# -*- coding: utf-8 -*-
"""Positional Pin Detection"""

from dataclasses import dataclass
from enum import Enum
import chess

SLIDING_PIECES = (chess.BISHOP, chess.ROOK, chess.QUEEN)
PIECE_VALUES = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
                                chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 10}

@dataclass
class Pin:
    """Pin Data Class

    A Pin stores the squares and piece types of the 3 pieces involved in a pin:
    the attacker, the defender, and the shielded piece.
    """

    # piece order -> attacker, defender, shielded
    squares: list
    pieceTypes: list

    @property
    def attacker(self): return self.squares[0], self.pieceTypes[0]
    @property
    def defender(self): return self.squares[1], self.pieceTypes[1]
    @property
    def shielded(self): return self.squares[2], self.pieceTypes[2]

    def is_absolute_pin(self):
        """Returns true if the piece is pinned to a king"""
        return board.piece_at(self.shielded).piece_type == KING

    def is_significant(self):
        """Returns true if the pinned piece is worth less in material value than
        the piece that it's pinned to (e.g. a rook pinned to a queen) or if the
        shielded piece is hanging.
        """
        # todo: if shielded piece is hanging, always return true
        defenderMaterialValue = PIECE_VALUES[self.defender[1]]
        shieldedMaterialValue = PIECE_VALUES[self.shielded[1]]
        return shieldedMaterialValue > defenderMaterialValue

    def __str__(self):
        pieceNames = map(chess.piece_name, self.pieceTypes)
        squareNames = map(chess.square_name, self.squares)
        pieceNames,squareNames = list(pieceNames),list(squareNames)
        return (f'The {pieceNames[0]} on {squareNames[0]} is pinning ' # attacker
                        f'the {pieceNames[1]} on {squareNames[1]} to '                 # defender
                        f'the {pieceNames[2]} on {squareNames[2]}.')                # shielded

    def __repr__(self):
        return f'<Pin squares={self.squares} significant={self.is_significant()}>'

# ------------------------------------------------------------------------------

def get_attacked_enemies(board, attackerSquare):
    """Returns the enemy pieces being attacked by the piece on the given square"""
    defenderColor = not board.piece_at(attackerSquare).color
    defenderOccupanciedSquares = board.occupied_co[defenderColor]
    attackedSquares = board.attacks(attackerSquare)
    return attackedSquares & defenderOccupanciedSquares

def peek_behind_enemy_for_pin(board, attackerSquare, enemySquare):
    """Returns the shielded piece if a pin exists, else returns None.

    A shielded piece will be located in the attackers 'blind spot' behind the
    pinned piece. Using what I call the 'peekaboo algorithm', the attacker can peek
    behind the enemy pieces that its threatening, revealing the shielded pieces if
    it exists. In practice, this is done by temporarily removing the pinned piece
    from the board and giving the attacker new vision. If the attacker can 'see'
    a new enemy piece with its new line of vision, a pin exists. This newly
    spotted enemy piece is the shielded piece in the pin. Determining if the
    attacker can see a new piece is made simple with graph theory. Simply perform
    set subtraction on the computed attack sets from before and after removing
    the enemy piece.

    Parameters:
        attackerSquare(int): the square containing a pin candidate (potential pin attacker)
        enemySquare(int): the square containing the attacked piece to peek behind

    Returns:
        pin(Pin): the pin created by the attack on the squares if it exists, else None
    """

    # if the attacker isn't a sliding piece, a pin doesn't exist: stop searching
    attacker = board.piece_at(attackerSquare)
    if attacker.piece_type not in SLIDING_PIECES: return

    # save enemy attacks pre-removal to be compared later with post-removal attacks,
    # then remove the enemy piece to simulate the 'peek behind', which gives
    # the attacker vision behind the (potentially pinned) enemy piece
    attackedEnemySquares = get_attacked_enemies(board, attackerSquare)
    attackedPiece = board.remove_piece_at(enemySquare)

    # find new attacks by subtracting the set of pre-removal attacks from the
    # updated post-removal set of attacks
    shieldedSquareSet = get_attacked_enemies(board, attackerSquare) \
                                            - attackedEnemySquares

    # put the removed piece back to reset the position to its correct state
    board.set_piece_at(enemySquare, attackedPiece)

    # If the subtracted attack set is empty, no pin exists. Otherwise, the set
    # will contain a single square which is occupied by the shielded piece.
    if shieldedSquareSet:
        pinSquares = (attackerSquare, enemySquare, shieldedSquareSet.pop())
        pieceTypes = [board.piece_at(square).piece_type for square in pinSquares]
        return Pin(pinSquares, pieceTypes)

def detect_pins(position, move, onlySignificantPins=True):
    """Detects all new pins that arise from a move at a position

    Pins are detected by generating a list of pin candidates that have the
    potential to create a new pin. Canidates will be pieces that gain vision
    on new squares following the made move. New vision can lead to new attacks
    on an enemy piece. Any time a new attack on an enemy piece opens up, the
    attacker needs to be checked for pins. There are 3 types of pins: created,
    discovered, and replacement. Finding candidates is different for each
    type (see README for details).

    Parameters:
        position (str): A FEN string describing a boards position
        move (str): A UCI notated string describing a legal move

    Returns:
        pins (list): list of detected pins that arise from the given move
    """

    board = chess.Board(position)
    move = chess.Move.from_uci(move)
    movingPiece = board.piece_at(move.from_square)
    colorToMove = board.turn
    pins = []

    def apply_move(undo=False):
        """ """
        board.remove_piece_at(move.to_square if undo else move.from_square)
        board.set_piece_at(move.from_square if undo else move.to_square, movingPiece)

    def check_for_discovered_pins(attackingColor):
        pinCanidates = board.attackers(attackingColor, move.from_square)
        apply_move()
        for attacker in pinCanidates:
            for defender in get_attacked_enemies(board, attacker):
                pin = peek_behind_enemy_for_pin(board, attacker, defender)
                if pin: pins.append(pin)
        apply_move(undo=True)

    def check_for_created_pins():
        apply_move()
        for defender in get_attacked_enemies(board, move.to_square):
            pin = peek_behind_enemy_for_pin(board, move.to_square, defender)
            if pin: pins.append(pin)
        apply_move(undo=False)

    check_for_discovered_pins(chess.WHITE)        # attacking discovered pins
    check_for_discovered_pins(chess.BLACK)        # enemy discovered pins
    check_for_created_pins()                                    # moving piece attack pin

    # filter out insignificant pins if indicated by param and return list of pins
    if not onlySignificantPins: return pins
    return [pin for pin in pins if pin.is_significant()]
