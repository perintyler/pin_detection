# -*- coding: utf-8 -*-
"""Tests for Created, Discovered, and Replacement Pin Detection"""

from pin import detect_pins, Pin
from chess import parse_square

PRINT_TRACE = True # determines if error trace is printed upon test failure

# testing helper function
def test_pin_detection(board, move, *correctSquareSets):
  """Checks the number of pins detected and their squares for correctness"""
  pins = detect_pins(board, move)
  assert len(pins) == len(correctSquareSets)
  for pin, squareNames in zip(pins, correctSquareSets):
    correctSquares = tuple(map(parse_square, squareNames))
    assert pin.squares == tuple(correctSquares)

# test pin created by an attack from the moved piece
def test_created_pin():
  board = '7k/6q1/8/8/8/8/8/1KB5 w - - 0 1'
  move = 'c1b2'
  pin = ('b2', 'g7', 'h8')
  test_pin_detection(board, move, pin)

# test discovered pin by moving player
def test_attacker_discovered_pin():
  board = '7k/6q1/8/8/3P4/8/1B6/1K6 w - - 0 1'
  move = 'd4d5'
  pin = ('b2', 'g7', 'h8')
  test_pin_detection(board, move, pin)

# test discovered pin by non-moving player
def test_defender_discovered_pin():
  board = '7k/6q1/8/4p3/8/2B5/2K5/8 b - - 0 1'
  move = 'e5e4'
  pin = ('c3', 'g7', 'h8')
  test_pin_detection(board, move, pin)

# test a move that results in multiple pins
# position: https://imgur.com/a/nVLf1sp
def test_multiple_new_pins():
  board = '1q5k/2n3r1/8/8/8/8/4Q3/1K6 w - - 0 1'
  move = 'e2e5'
  pin1 = ('e5', 'c7', 'b8')
  pin2 = ('e5', 'g7', 'h8')
  test_pin_detection(board, move, pin1, pin2)

def test_replacement_pin():
  board = '8/8/8/8/Q2BB1rk/8/8/K7 w - - 0 1'
  move = 'd4e5'
  pin = ('g4', 'd4', 'a4')
  test_pin_detection(board, move, pin)

if __name__ == '__main__':
  for test in (test_attacker_discovered_pin,
              test_defender_discovered_pin,
              test_created_pin,
              test_multiple_new_pins,
              test_replacement_pin):
    try:
      test()
      print(f'{test.__name__} -> pass')
    except AssertionError as e:
      print(f'{test.__name__} -> fail')
      if PRINT_TRACE: print(e)
