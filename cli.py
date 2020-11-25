# -*- coding: utf-8 -*-
"""Command Line Tool"""

import argparse
from pin import detect_pins

parser = argparse.ArgumentParser(description='Pin Detection CLI')
parser.add_argument('position', type=str,
                    help='A FEN string representing a chess position')
parser.add_argument('move', type=str,
                    help='A move in UCI notation')
                    
if __name__ == '__main__':
  args = parser.parse_args()
  pins = detect_pins(args.position, args.move)
  for pin in pins:
    print(pin)
