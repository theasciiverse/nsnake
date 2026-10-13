#include <Engine/Graphics/Ncurses.hpp>

#include <ncurses.h>

bool Ncurses::init()
{
	initscr();
	// TODO check for failing

	cbreak();    // Character input doesnt require the <enter> key anymore
	curs_set(0); // Makes the blinking cursor invisible
	noecho();    // Wont print the keys received through input
	nodelay(stdscr, TRUE); // Wont wait for input
	keypad(stdscr, TRUE);  // Support for extra keys (life F1, F2, ... )

	// Ncurses' global variable meaning number of milliseconds
	// to wait after the user presses ESC.
	//
	// VIM uses 25ms, so should you.
	// Source: http://en.chys.info/2009/09/esdelay-ncurses/
	ESCDELAY = 25;

	refresh();   // Refresh the layout (prints whats in the layout bu
	return true;
}

void Ncurses::exit()
{
	erase();
	refresh();
	endwin();
}

int Ncurses::getInput(int delay_ms)
{
	// Waits up to #delay_ms for a key, or forever with -1,
	// with curses' own timeout rather than select(): that way
	// a resized terminal comes through as KEY_RESIZE, and it
	// also works where the keyboard is no file descriptor
	// (PDCurses on Windows).
	timeout(delay_ms);
	int c = getch();
	nodelay(stdscr, TRUE);

	return c; // ERR when nothing was pressed
}

