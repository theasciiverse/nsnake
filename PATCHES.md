# Changes from upstream

This is the Asciiverse packaging of [nSnake](https://github.com/alexdantas/nSnake)
by Alexandre Dantas (GPL-3.0), the classic snake game with textual
interface. Upstream is the `upstream` remote. The `asciiverse` branch
starts from upstream's `master` at `d018237` (2014-10-13), not the last
release, v3.0.1 (2014-07-31): the 50 commits after it fix the bold
colours, a string-splitting bug (#18) and an uninitialised variable, add
colour settings and new menu animations, and were never released. The
version string stays 3.0.1.

## Code

- **Centred again after a resize.** The layouts were centred when built,
  but a resize was never handled: the main menu's frame stretched with the
  terminal and the board stayed put. Input waited with `select()` and
  dropped what `getch()` returned on a timeout, which is when ncurses
  hands over `KEY_RESIZE`; it now waits with curses' `timeout()`, and the
  main menu and the game rebuild their windows centred
  (`Layout::recenter`). A terminal smaller than 80x24 keeps the old
  windows, clipped, instead of quitting.
- **Data folder.** Settings and scores go to `$XDG_DATA_HOME/nsnake`
  when it is set, `%APPDATA%\nsnake` on Windows, else
  `~/.local/share/nsnake` as before.
- **Bundled levels are found.** Levels were read only from the player's
  folder, so the bundled ones went unused until copied in by hand. They
  are now found in the player's folder, then in `levels/` where the game
  was started (av starts a title in its install folder), then in the
  system folder; each is listed once, sorted.
- **No shell for deleting files.** `rm_f` ran `rm -f` through the shell;
  it calls `remove()` now, which works with spaces in paths and on
  Windows.
- **Windows and macOS.** The timer kept microseconds since 1970 in
  `suseconds_t`, 32 bits on macOS (where it overflowed) and missing on
  Windows; it is `int64_t` now. `ESCDELAY` is set only with ncurses, and
  `mkdir()` takes one argument on Windows.

## Packaging (new files)

- `asciiverse/build.sh`, `asciiverse/package.sh`: build with upstream's
  Makefile (for Windows against PDCurses, through a one-line `ncurses.h`),
  and one archive per target with the bundled levels, the man page,
  COPYING and README.md.
- `.github/workflows/release.yml`: static Linux in Alpine (x86_64,
  aarch64), macOS (x86_64, arm64) and Windows x86_64 (MinGW and
  PDCurses), plus SHA256SUMS, on a tag.
- `asciiverse/record-preview.py`: records the catalog preview.

## Tested

Linux: native and static (Alpine) builds, at 80x24, 100x30 and 120x40,
resized while playing. Windows: built with MinGW and run under Wine 10
(menu, a game, quitting, settings in `%APPDATA%`); Wine's terminal does
not pass the arrow keys, so steering is unchecked on Windows. macOS: not
built here.

## Ours

- **How to play it, at the top of README.md.** A short note on installing and
  starting it with av, or from a release archive; the original text follows
  unchanged.
