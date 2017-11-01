#include <signal.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <time.h>
#include <unistd.h>

#define UI_TICK 300000000
#define DENSITY 7
#define CELL(r, c) cells[((r) * num_cols) + (c)]

bool win_changed = false;

size_t num_rows = 0,
       num_cols = 0,
       num_cells = 0;

typedef struct {
    size_t row;
    size_t col;
    bool alive;
    bool next;
} Cell;

Cell *cells = NULL;

void term_get_size(void) {
    struct winsize w;
    ioctl(STDOUT_FILENO, TIOCGWINSZ, &w);
    num_rows = w.ws_row;
    num_cols = w.ws_col;
    num_cells = num_rows * num_cols;
}

void term_position_cursor(size_t row, size_t col) {
    fprintf(stdout, "\033[%zd;%zdf", row + 1, col + 1);
}

void term_clear_screen(void) {
    fprintf(stdout, "\033[2J");
}

void term_show_cursor(void) {
    fprintf(stdout, "\033[?25h");
}

void term_hide_cursor(void) {
    fprintf(stdout, "\033[?25l");
}

void term_reset(void) {
    fprintf(stdout, "\033c");
}

void draw_cells(void) {
    Cell cell;
    for (size_t i = 0; i < num_cells; ++i) {
        cell = cells[i];
        term_position_cursor(cell.row, cell.col);
        fprintf(stdout, "%s", (cell.alive) ? "█" : " ");
    }
}

int sum_of_neighbors(Cell *cell) {
    int live_neighbors = 0;
    size_t row = cell->row,
           col = cell->col;

    if (row > 0) {
        if (col > 0) {
            live_neighbors += CELL(row - 1, col - 1).alive;
        }

        live_neighbors += CELL(row - 1, col).alive;

        if (col < num_cols - 1) {
            live_neighbors += CELL(row - 1, col + 1).alive;
        }
    }

    if (col > 0) {
        live_neighbors += CELL(row, col - 1).alive;
    }

    if (col < num_cols - 1) {
        live_neighbors += CELL(row, col + 1).alive;
    }

    if (row < num_rows - 1) {
        if (col > 0) {
            live_neighbors += CELL(row + 1, col - 1).alive;
        }

        live_neighbors += CELL(row + 1, col).alive;

        if (col < num_cols - 1) {
            live_neighbors += CELL(row + 1, col + 1).alive;
        }
    }

    return live_neighbors;
}

void next_generation(void) {
    Cell *cell;
    int n;

    for (size_t i = 0; i < num_cells; ++i) {
        // rules:
        // live cells:
        // 1. 0 or 1 live neighbors: die
        // 2. 2 or 3 live neighbors: live
        // 3. 4+ live neighbors: die
        // dead cells:
        // 4. exactly 3 live neighbors: live
        cell = &cells[i];
        n = sum_of_neighbors(cell);
        cell->next = (cell->alive) ? (n == 2 || n == 3) : (n == 3);
    }

    for (size_t i = 0; i < num_cells; ++i) {
        cell = &cells[i];
        cell->alive = cell->next;
        cell->next = false;
    }
}

void start_game(void) {
    term_get_size();

    if (cells) {
        free(cells);
    }

    cells = calloc(1, sizeof(Cell) * num_cells);
    size_t row = 0,
           col = 0;

    for (size_t i = 0; i < num_cells; ++i) {
        if (col == num_cols) {
            col = 0;
            row++;
        }

        cells[i].row = row;
        cells[i].col = col;
        cells[i].alive = ((rand() % DENSITY) == 1);
        cells[i].next = false;
        col++;
    }

    term_clear_screen();
    term_hide_cursor();

    struct timespec t = { .tv_sec = 0, .tv_nsec = UI_TICK };

    while (true) {
        draw_cells();
        nanosleep(&t, NULL);
        next_generation();

        if (win_changed) {
            win_changed = false;
            return;
        }
    }
}

void int_handler(int _) {
    term_show_cursor();
    term_reset();
    exit(EXIT_SUCCESS);
}

void winch_handler(int _) {
    win_changed = true;
}

int main() {
    srand(time(NULL));
    signal(SIGWINCH, winch_handler);
    signal(SIGINT, int_handler);

    while (true) {
        start_game();
    }

    return EXIT_SUCCESS;
}
