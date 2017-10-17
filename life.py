# Copyright © 2017 Zandr Martin

# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
# OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
import os
import random
import signal
import sys
import time

# time spent sleeping between generations
UI_TICK = 0.5

# there are 1/this live cells (on average) at the start of the game.
# higher numbers mean fewer live cells.
INITIAL_DENSITY = 7


class Term:
    ESC = '\033['
    cols, rows = os.get_terminal_size()

    def __init__(self):
        self.reset_cursor()

    def flush_print(self, text):
        sys.stdout.write(text)
        sys.stdout.flush()

    def esc_print(self, code):
        self.flush_print(self.ESC + code)

    def clear_screen(self):
        self.esc_print('2J')

    def reset_cursor(self):
        self.position_cursor(1, 1)

    def position_cursor(self, x, y):
        self.esc_print(f'{y};{x}f')

    def fill_cell(self):
        self.flush_print('█')

    def clear_cell(self):
        self.flush_print(' ')

    def show_cursor(self):
        self.esc_print('?25h')

    def hide_cursor(self):
        self.esc_print('?25l')

    def teardown(self):
        self.flush_print('\033c')


class Cell:
    registry = {}

    def __init__(self, x, y, is_alive=False):
        self.x = x
        self.y = y
        self.is_alive = is_alive
        self.next_state = None

        Cell.registry[(self.x, self.y)] = self

    @property
    def neighbors(self):
        if not hasattr(self, '_neighbors'):
            self._neighbors = []

            for x in [self.x - 1, self.x, self.x + 1]:
                for y in [self.y - 1, self.y, self.y + 1]:
                    if not (x == self.x and y == self.y):
                        try:
                            self._neighbors.append(self.registry[(x, y)])
                        except KeyError:
                            pass

        return self._neighbors

    @property
    def live_neighbors(self):
        return [n for n in self.neighbors if n.is_alive]

    def breed(self):
        if self.next_state is not None:
            self.is_alive = self.next_state == 'live'
            self.next_state = None

    def die(self):
        self.next_state = 'die'

    def live(self):
        self.next_state = 'live'


def create_cells():
    Cell.registry = {}
    for x in range(1, Term.cols + 1):
        for y in range(1, Term.rows + 1):
            Cell(x, y, is_alive=random.randint(0, INITIAL_DENSITY) == 1)


def main():
    term = Term()

    def reset_game(signal, frame):
        term.teardown()
        term.reset_cursor()
        Term.cols, Term.rows = os.get_terminal_size()
        term.clear_screen()
        create_cells()

    signal.signal(signal.SIGWINCH, reset_game)

    term.clear_screen()
    term.hide_cursor()
    create_cells()

    # rules:
    # live cells:
    # 1. 0 or 1 live neighbors: die
    # 2. 2 or 3 live neighbors: live
    # 3. 4+ live neighbors: die
    # dead cells:
    # 4. exactly 3 live neighbors: live
    try:
        while True:
            for cell in Cell.registry.values():
                term.position_cursor(cell.x, cell.y)

                if cell.is_alive:
                    if len(cell.live_neighbors) in (2, 3):
                        cell.live()
                    else:
                        cell.die()

                    term.fill_cell()

                else:
                    if len(cell.live_neighbors) == 3:
                        cell.live()

                    term.clear_cell()

            time.sleep(UI_TICK)

            for cell in Cell.registry.values():
                cell.breed()

    except KeyboardInterrupt:
        term.show_cursor()
        term.teardown()


if __name__ == '__main__':
    main()
