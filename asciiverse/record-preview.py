#!/usr/bin/env python3
"""Records asciiverse/nsnake.cast, the catalog preview, at 100x30
(hub/RECORDING.md): Arcade Mode at speed 5 with two fruits on the board,
played by a driver that reads the screen and steers the snake along the
shortest free path to the nearest fruit (or, with no path, into the move
that leaves it the most room). After about 40 seconds it quits with q.

nsnake runs from out/ (asciiverse/build.sh) by name, so the cast's header
holds no local path, in a throwaway folder with the bundled levels and a
throwaway data folder, so nothing touches your own settings or scores.

Needs asciinema 3.x and pyte (pip install pyte). Usage, from the repo
root: python3 asciiverse/record-preview.py"""
import collections, fcntl, os, pty, select, shutil, struct, sys, tempfile, termios, time
import pyte

# ncurses draws a run of one character with REP (CSI n b, "repeat the last
# character n times"), which pyte does not know: the board's top and bottom
# walls would read as one cell. Teach it here.
_draw = pyte.Screen.draw


def _draw_remembering(self, data):
    if data:
        self.last_char = data[-1]
    _draw(self, data)


def _repeat_last(self, n=1, *rest, **kw):
    if getattr(self, "last_char", None):
        _draw(self, self.last_char * max(1, n))


pyte.Screen.draw = _draw_remembering
pyte.Screen.repeat_last = _repeat_last
pyte.Stream.csi = dict(pyte.Stream.csi, b="repeat_last")

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COLS, ROWS, PLAY = 100, 30, 40.0
SETTINGS = """[game]
starting_speed=5
fruits_at_once=2
teleport=0
random_walls=0
board_size=2
"""

work = tempfile.mkdtemp(prefix="nsnake-preview-")
shutil.copytree(f"{root}/levels", f"{work}/levels")
os.makedirs(f"{work}/data/nsnake")
with open(f"{work}/data/nsnake/settings.ini", "w") as f:
    f.write(SETTINGS)
env = dict(os.environ, TERM="xterm-256color", COLORTERM="truecolor", LANG="C.UTF-8",
           HOME=work, XDG_DATA_HOME=f"{work}/data", PATH=f"{root}/out:{os.environ['PATH']}")

pid, fd = pty.fork()
if pid == 0:
    os.chdir(work)
    os.execvpe("asciinema", ["asciinema", "rec", "--overwrite", "-q", "--idle-time-limit", "2",
        "--window-size", f"{COLS}x{ROWS}", "--capture-env", "TERM,COLORTERM,LANG",
        "--title", "nSnake", "--command", "nsnake", f"{root}/asciiverse/nsnake.cast"], env)
fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", ROWS, COLS, 0, 0))
screen = pyte.Screen(COLS, ROWS)
stream = pyte.ByteStream(screen)
start = time.time()


def pump(seconds):
    end = time.time() + seconds
    while True:
        left = end - time.time()
        r, _, _ = select.select([fd], [], [], max(0.0, min(0.02, left)))
        if r:
            try:
                stream.feed(os.read(fd, 65536))
            except OSError:
                return False
        if left <= 0:
            return True


def key(k, wait=0.1):
    os.write(fd, k)
    pump(wait)


UP, DOWN, RIGHT, LEFT = b"\x1bOA", b"\x1bOB", b"\x1bOC", b"\x1bOD"
MOVES = {(0, -1): UP, (0, 1): DOWN, (1, 0): RIGHT, (-1, 0): LEFT}


def board():
    """Head, body, fruits and the free cells, read from the screen. The
    board is the area inside the walls (curses' checkerboard, which pyte
    keeps as 'a')."""
    rows = [screen.buffer[y] for y in range(ROWS)]
    walls = [(x, y) for y in range(ROWS) for x in range(COLS) if rows[y][x].data == "a"]
    if not walls:
        return None
    x0, x1 = min(w[0] for w in walls), max(w[0] for w in walls)
    y0, y1 = min(w[1] for w in walls), max(w[1] for w in walls)
    head, body, fruits, free = None, set(), [], set()
    for y in range(y0 + 1, y1):
        for x in range(x0 + 1, x1):
            c = rows[y][x].data
            if c == "@":
                head = (x, y)
            elif c == "o":
                body.add((x, y))
            elif c == "$":
                fruits.append((x, y))
                free.add((x, y))
            elif c == " ":
                free.add((x, y))
    return head, body, fruits, free


def room(cell, free):
    """How many free cells can be reached from cell."""
    seen, todo = {cell}, [cell]
    while todo and len(seen) < 400:
        x, y = todo.pop()
        for dx, dy in MOVES:
            n = (x + dx, y + dy)
            if n in free and n not in seen:
                seen.add(n)
                todo.append(n)
    return len(seen)


def choose(head, fruits, free, heading):
    """First step of the shortest free path to a fruit; without one, the
    neighbour with the most room. Never straight back into the body."""
    back = (-heading[0], -heading[1])
    prev = {head: None}
    q = collections.deque([head])
    target = None
    while q:
        c = q.popleft()
        if c in fruits:
            target = c
            break
        for d in MOVES:
            if c == head and d == back:
                continue
            n = (c[0] + d[0], c[1] + d[1])
            if n in free and n not in prev:
                prev[n] = c
                q.append(n)
    if target is not None:
        step = target
        while prev[step] != head:
            step = prev[step]
        d = (step[0] - head[0], step[1] - head[1])
        # a fruit in a pocket too small to get out of again is not worth it
        if room(step, free - {step}) > 12:
            return d
    best, best_room = heading, -1
    for d in MOVES:
        if d == back:
            continue
        n = (head[0] + d[0], head[1] + d[1])
        if n in free:
            r = room(n, free - {n})
            if r > best_room:
                best, best_room = d, r
    return best


pump(2.5)                  # the main menu, with its animation
key(b"\r", 1.5)            # Arcade Mode
heading, last = (1, 0), None
while time.time() - start < PLAY:
    pump(0.04)
    seen = board()
    if not seen or not seen[0]:
        if "Retry" in "\n".join(screen.display):
            key(b"\r", 1.5)        # Retry? Yes: a new game
            heading, last = (1, 0), None
        continue
    head, body, fruits, free = seen
    if head == last:
        continue
    if last is not None:
        heading = (head[0] - last[0], head[1] - last[1])
        if abs(heading[0]) + abs(heading[1]) != 1:
            heading = (1, 0)
    last = head
    d = choose(head, fruits, free, heading)
    if d != heading:
        key(MOVES[d], 0.02)

key(b"q", 1.0)
end = time.time() + 5
while time.time() < end:
    if not pump(0.1):
        break
    done, _ = os.waitpid(pid, os.WNOHANG)
    if done:
        break
else:
    os.kill(pid, 9)
try:
    os.waitpid(pid, 0)
except ChildProcessError:
    pass
shutil.rmtree(work, ignore_errors=True)
print(f"asciiverse/nsnake.cast: {time.time() - start:.0f} s", file=sys.stderr)
